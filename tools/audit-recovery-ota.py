#!/usr/bin/env python3
"""Verify Android whole-file OTA signature against certificates in a packed recovery.

Requires cryptography and asn1crypto. This is an offline signature check, not an
installation test or a substitute for payload/AVB verification.
"""
import argparse
import gzip
import hashlib
import io
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

from asn1crypto import cms
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils


def recovery_files(image, root, wanted):
    found = {}
    with tempfile.TemporaryDirectory(prefix="frogger-recovery-keys-") as tmp:
        subprocess.run([
            "python3", str(root / "system/tools/mkbootimg/unpack_bootimg.py"),
            "--boot_img", str(image), "--out", tmp,
        ], check=True, stdout=subprocess.DEVNULL)
        archive = Path(tmp) / "ramdisk"
        data = archive.read_bytes()
        if data.startswith(b"\x1f\x8b"):
            data = gzip.decompress(data)
        elif not data.startswith((b"070701", b"070702")):
            data = subprocess.check_output([
                str(root / "out/host/linux-x86/bin/lz4"), "-d", "-c", str(archive),
            ])
        pos = 0
        while pos + 110 <= len(data):
            if data[pos:pos + 6] not in (b"070701", b"070702"):
                raise ValueError("Unsupported recovery CPIO header")
            fields = [int(data[pos + 6 + i * 8:pos + 14 + i * 8], 16) for i in range(13)]
            name = data[pos + 110:pos + 110 + fields[11] - 1].decode()
            start = (pos + 110 + fields[11] + 3) & ~3
            body = data[start:start + fields[6]]
            pos = (start + fields[6] + 3) & ~3
            if name == "TRAILER!!!":
                break
            name = name.lstrip("./")
            if name in wanted:
                found[name] = body
                if wanted <= found.keys():
                    return found
    raise ValueError("Required recovery files missing: " + repr(wanted - found.keys()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--ota", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-default-group-migration", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    wanted = {"system/etc/security/otacerts.zip"}
    if args.require_default_group_migration:
        wanted.add("system/bin/update_engine_sideload")
    files = recovery_files(args.recovery.resolve(), root, wanted)
    with zipfile.ZipFile(io.BytesIO(files["system/etc/security/otacerts.zip"])) as archive:
        certs = [x509.load_pem_x509_certificate(archive.read(n))
                 for n in archive.namelist() if n.endswith("x509.pem")]
    if args.require_default_group_migration:
        marker = b"Replacing inactive recovery partition from default group: "
        if marker not in files["system/bin/update_engine_sideload"]:
            raise ValueError("Packed recovery updater lacks the default-group migration fix")
    length = args.ota.stat().st_size
    with args.ota.open("rb") as stream:
        stream.seek(-6, 2)
        footer = stream.read()
        if footer[2:4] != b"\xff\xff":
            raise ValueError("Missing Android OTA signature footer")
        start = int.from_bytes(footer[:2], "little")
        comment = int.from_bytes(footer[4:], "little")
        if not 6 < start <= comment or comment + 22 > length:
            raise ValueError("Invalid OTA signature bounds")
        stream.seek(-comment - 22, 2)
        eocd = stream.read()
        if not eocd.startswith(b"PK\x05\x06") or b"PK\x05\x06" in eocd[4:]:
            raise ValueError("Invalid or ambiguous ZIP end record")
        signature = cms.ContentInfo.load(eocd[-start:-6])["content"]["signer_infos"][0]
        if signature["signed_attrs"].native is not None:
            raise ValueError("Unsupported signed attributes; use the branch recovery verifier")
        algorithm_name = signature["digest_algorithm"]["algorithm"].native
        algorithms = {"sha1": hashes.SHA1, "sha256": hashes.SHA256}
        algorithm = algorithms[algorithm_name]()
        digest = hashes.Hash(algorithm)
        remaining = length - comment - 2
        stream.seek(0)
        while remaining:
            block = stream.read(min(8 * 1024 * 1024, remaining))
            if not block:
                raise ValueError("Truncated OTA")
            digest.update(block)
            remaining -= len(block)
        hashed = digest.finalize()
    matched = None
    for cert in certs:
        key = cert.public_key()
        expected_digest = cert.signature_hash_algorithm.name
        if expected_digest == "md5":
            expected_digest = "sha1"  # Historical SignApk/recovery convention.
        if expected_digest != algorithm_name:
            continue
        if not isinstance(key, rsa.RSAPublicKey):
            continue
        try:
            key.verify(signature["signature"].native, hashed,
                       padding.PKCS1v15(), utils.Prehashed(algorithm))
            matched = cert.fingerprint(hashes.SHA256()).hex()
            break
        except InvalidSignature:
            continue
    if matched is None:
        raise ValueError("OTA signature is not trusted by this recovery")
    with args.recovery.open("rb") as stream:
        recovery_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    report = {"recovery": str(args.recovery), "recovery_sha256": recovery_hash,
              "ota": str(args.ota), "digest": algorithm_name,
              "trusted_certificate_sha256": matched, "errors": [],
              "scope": "Whole-file OTA signature against packed recovery certificates; installation and payload/AVB checks are separate."}
    report["default_group_migration_required"] = args.require_default_group_migration
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: OTA whole-file signature trusted by packed recovery")


if __name__ == "__main__":
    main()
