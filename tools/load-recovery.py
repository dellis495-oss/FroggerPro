#!/usr/bin/env python3
"""Verify a frozen FroggerPro bundle; use --sideload to install from recovery.

Default operation only reads local files. This helper never formats, unlocks,
changes slots, or reboots. Recovery chooses the inactive slot during installation.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

SERIAL = "003383663003343"
PARTITIONS = {
    "boot", "dtbo", "init_boot", "odm", "product", "pvmfw", "recovery",
    "system", "system_dlkm", "system_ext", "vbmeta", "vbmeta_system",
    "vbmeta_vendor", "vendor", "vendor_boot", "vendor_dlkm",
}
GATES = (
    "ota-integrity", "avb-chain", "payload-signature", "vendor-packed",
    "vendor_boot-fstab", "recovery-fstab", "recovery-ota-signature",
)


def verify(root):
    if (root / 'RELEASE_SECURITY.json').exists():
        release = json.loads((root / 'RELEASE_SECURITY.json').read_text())
        props = release.get('build_properties', {})
        if (root / 'verification/release-security.exit').read_text().strip() != '0' or release.get('errors'):
            raise ValueError('Production security audit did not pass')
        if props.get('ro.build.type') != 'user' or props.get('ro.build.tags') != 'release-keys' or props.get('ro.debuggable') != '0' or release.get('permissive_domains') != []:
            raise ValueError('Invalid production security properties')
    for gate in GATES:
        if (root / "verification" / (gate + ".exit")).read_text().strip() != "0":
            raise ValueError("Bundle verification did not pass: " + gate)
    report = json.loads((root / "verification/ota-integrity.json").read_text())
    if report.get("errors") or set(report["partitions"]) != PARTITIONS:
        raise ValueError("Incomplete or failed 16-partition verification report")
    otas = list(root.glob("e-*-UNOFFICIAL-FroggerPro.zip"))
    if len(otas) != 1:
        raise ValueError("Expected exactly one FroggerPro OTA in the bundle")
    ota = otas[0]
    with ota.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != report["ota_sha256"]:
            raise ValueError("OTA SHA256 mismatch")
    with zipfile.ZipFile(ota) as archive:
        metadata = dict(line.split("=", 1) for line in
                        archive.read("META-INF/com/android/metadata").decode().splitlines()
                        if "=" in line)
    if metadata.get("pre-device") != "FroggerPro" or metadata.get("ota-type") != "AB":
        raise ValueError("Wrong device or update type")
    if metadata.get("ota-wipe") == "yes" or metadata.get("ota-downgrade") == "yes":
        raise ValueError("Refusing wipe-requesting or downgrade OTA")
    for name, entry in sorted(report["partitions"].items()):
        image = root / "IMAGES" / (name + ".img")
        if image.stat().st_size != entry["bytes"]:
            raise ValueError("Image size mismatch: " + name)
        with image.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != entry["sha256"]:
                raise ValueError("Image SHA256 mismatch: " + name)
    print("PASS: OTA and all 16 image hashes match the verified recovery bundle", flush=True)
    return ota


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--sideload", action="store_true", help="Send verified OTA to the recovery sideload interface")
    parser.add_argument("--adb", default="adb", help="Path to Android platform-tools adb")
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    ota = verify(root)
    if not args.sideload:
        print("No phone changes made. Enable recovery's ADB sideload option, then rerun with --sideload.")
        return
    state = subprocess.run([args.adb, "-s", SERIAL, "get-state"],
                           capture_output=True, text=True, timeout=15)
    if state.returncode or state.stdout.strip() != "sideload":
        raise ValueError("Expected phone is not in recovery ADB sideload mode; no package sent")
    print("Sending the full OTA to recovery. The inactive slot's OS will be replaced; no wipe is requested.", flush=True)
    result = subprocess.run([args.adb, "-s", SERIAL, "sideload", str(ota)])
    (root / "sideload-transport.exit").write_text(str(result.returncode) + "\n")
    if result.returncode:
        raise RuntimeError("ADB transport failed; inspect recovery before retrying")
    print("Transport finished. Confirm recovery reports installation success before rebooting.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print("STOP: " + str(error), file=sys.stderr)
        raise SystemExit(1)
