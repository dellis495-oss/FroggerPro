#!/usr/bin/env python3
"""Verify final vendor EROFS bytes, runtime assets and AVB without mounting it."""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument("product_out", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[4]
product = args.product_out.resolve()
image = product / "vendor.img"
host = root / "out/host/linux-x86/bin"
errors = []
def sha256_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
with tempfile.TemporaryDirectory(prefix="frogger-vendor-audit-", dir=product) as tmp:
    tmp = Path(tmp)
    raw = image
    if image.open("rb").read(4) == bytes.fromhex("3aff26ed"):
        raw = tmp / "vendor.raw.img"
        subprocess.run([str(host / "simg2img"), str(image), str(raw)], check=True)
    vendor = tmp / "vendor"
    subprocess.run([str(host / "fsck.erofs"), "--extract=" + str(vendor), str(raw)], check=True)
    runtime = subprocess.run(["python3", str(root / "device/nothing/FroggerPro/tools/audit-vendor-runtime.py"), str(tmp)], capture_output=True, text=True)
    print(runtime.stdout, end="")
    if runtime.returncode:
        try:
            errors.extend(json.loads(runtime.stdout)["errors"])
        except (ValueError, KeyError):
            errors.append("Runtime audit failed: " + runtime.stderr)
    device = root / "device/nothing/FroggerPro"
    pairs = [(device / "init/init.froggerpro.glyph.rc", vendor / "etc/init/init.froggerpro.glyph.rc"),
             (root / "vendor/nothing/FroggerPro/proprietary/vendor/lib64/com.qti.settings.sm7750.so", vendor / "lib64/com.qti.settings.sm7750.so")]
    for source in (device / "configs/wifi").rglob("*"):
        if source.is_file() and source.name != "wpa_supplicant.conf":
            pairs.append((source, vendor / "etc/wifi" / source.relative_to(device / "configs/wifi")))
    for source, packed in pairs:
        if not packed.is_file() or hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(packed.read_bytes()).digest():
            errors.append("Packed file differs from source: " + str(packed.relative_to(vendor)))
    for name, target in {"WCNSS_qcom_cfg.ini": "/vendor/etc/wifi/qca6750/WCNSS_qcom_cfg.ini", "wlan_mac.bin": "/mnt/vendor/persist/qca6750/wlan_mac.bin"}.items():
        path = vendor / "firmware/wlan/qca_cld/qca6750" / name
        if not path.is_symlink() or str(path.readlink()) != target:
            errors.append("Incorrect WLAN firmware link: " + str(path.relative_to(vendor)))
    subprocess.run([str(host / "avbtool"), "verify_image", "--image", str(image)], check=True)
report = {"image": str(image), "sha256": sha256_file(image), "errors": errors,
          "scope": "Packed EROFS integrity, active runtime inventory, exact camera/Glyph/WLAN source bytes, firmware links and embedded AVB integrity. Hardware and chain trust require separate validation."}
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
raise SystemExit(bool(errors))
