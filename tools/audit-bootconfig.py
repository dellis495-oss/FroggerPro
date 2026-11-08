#!/usr/bin/env python3
"""Check required FroggerPro identity and module/USB settings in vendor_boot."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("image", type=Path)
parser.add_argument("--unpack-tool", type=Path, required=True)
parser.add_argument("--output", type=Path)
args = parser.parse_args()
required = {
    "androidboot.hardware": "qcom",
    "androidboot.product.vendor.sku": "kera",
    "androidboot.load_modules_parallel": "true",
    "androidboot.usbcontroller": "a600000.dwc3",
}
with tempfile.TemporaryDirectory(prefix="frogger-bootconfig-") as directory:
    subprocess.run(
        [str(args.unpack_tool.resolve()), "--boot_img", str(args.image.resolve()),
         "--out", directory], check=True, stdout=subprocess.DEVNULL,
    )
    config = (Path(directory) / "bootconfig").read_text()
values = {}
for line in config.splitlines():
    key, separator, value = line.partition("=")
    if separator:
        values.setdefault(key.strip(), []).append(value.strip().strip('"'))
errors = [f"{key}: expected exactly [{value!r}], got {values.get(key, [])!r}"
          for key, value in required.items() if values.get(key) != [value]]
with args.image.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
report = {"image": str(args.image), "sha256": digest, "errors": errors,
          "required": required,
          "scope": "Packed vendor bootconfig only; does not validate AVB, ramdisk, modules or Android boot."}
text = json.dumps(report, indent=2) + "\n"
if args.output:
    args.output.write_text(text)
print(text, end="")
sys.exit(bool(errors))
