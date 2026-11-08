#!/usr/bin/env python3
"""Audit platform privileged permissions across all packaged privileged APKs."""
import argparse, json, re, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("product_out", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[4]
aapt = root / "out/host/linux-x86/bin/aapt2"
android = "{http://schemas.android.com/apk/res/android}"
permissions = {}
for node in ET.parse(root / "frameworks/base/core/res/AndroidManifest.xml").iter("permission"):
    level = node.get(android + "protectionLevel", "normal")
    privileged = "privileged" in level.split("|")
    if level.startswith("0x") or level.isdigit():
        privileged = bool(int(level, 0) & 0x10)
    if privileged:
        permissions[node.get(android + "name")] = level

missing, checked = [], 0
for partition in ("system", "system_ext", "product", "vendor", "odm"):
    allow = {}
    for directory in ("etc/permissions", "etc/sysconfig"):
        for xml in (args.product_out / partition / directory).glob("*.xml"):
            for node in ET.parse(xml).iter("privapp-permissions"):
                allow.setdefault(node.get("package"), set()).update(child.get("name") for child in node if child.tag in ("permission", "deny-permission"))
    for apk in (args.product_out / partition / "priv-app").glob("*/*.apk"):
        checked += 1
        text = subprocess.check_output([str(aapt), "dump", "permissions", str(apk)], text=True)
        package = re.search(r"^package: (\S+)", text, re.M).group(1)
        requested = set(re.findall(r"^uses-permission: name='([^']+)'", text, re.M))
        for name in sorted(requested & permissions.keys() - allow.get(package, set())):
            missing.append({"partition": partition, "package": package, "permission": name, "apk": str(apk)})
report = {"checked_apks": checked, "missing": missing,
          "scope": "Framework privileged requests of all packaged priv-app APKs and partition-local explicit grants/denials, matching this branch's enforcement regardless of signing key. Shared-UID grants, updated data apps, APEX apps and custom permission owners require runtime validation."}
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
sys.exit(bool(missing))
