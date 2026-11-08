#!/usr/bin/env python3
"""Check imported APK shared-library declarations against the assembled product.

This checks registered library files and transitive registry dependencies, not
Java ABI compatibility. Conditional overlays are skipped only when their actual
assembled system-property condition excludes the entire package.
"""
import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("product_out", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[4]
partitions = ("system", "system_ext", "product", "vendor", "odm")
properties, libraries, errors, excluded = {}, {}, [], []
for partition in partitions:
    directory = args.product_out / partition
    for prop in (directory / "build.prop", directory / "etc/build.prop"):
        if prop.is_file():
            for line in prop.read_text().splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    key, value = line.split("=", 1)
                    properties[key.strip()] = value.strip()
    for folder in ("etc/permissions", "etc/sysconfig"):
        for xml in (directory / folder).glob("*.xml"):
            for node in ET.parse(xml).iter("library"):
                if node.get("name") and node.get("file"):
                    libraries[node.get("name")] = {
                        "file": node.get("file"),
                        "dependencies": node.get("dependency", "").split(":"),
                        "declaration": str(xml),
                    }

def check_library(name, apk, visited):
    if name in visited:
        return
    visited.add(name)
    entry = libraries.get(name)
    if entry is None:
        errors.append({"apk": str(apk), "library": name, "error": "unregistered required library"})
        return
    path = args.product_out / entry["file"].lstrip("/")
    if not path.is_file():
        errors.append({"apk": str(apk), "library": name, "error": "registered file absent", "file": str(path)})
    for dependency in filter(None, entry["dependencies"]):
        check_library(dependency, apk, visited)

checked = 0
source = root / "vendor/nothing/FroggerPro/proprietary"
for apk in sorted(source.rglob("*.apk")):
    installed = args.product_out / apk.relative_to(source)
    if not installed.is_file():
        continue
    text = subprocess.check_output([str(root / "out/host/linux-x86/bin/aapt2"), "dump", "badging", str(installed)], text=True)
    condition = re.search(r"^overlay:.*requiredPropertyName='([^']+)'.*requiredPropertyValue='([^']+)'", text, re.M)
    if condition:
        names, values = condition.group(1).split(","), condition.group(2).split(",")
        # Bootloader-derived properties are not represented in build.prop. An
        # absent ro.boot.* must never hide a required telephony dependency.
        if len(names) == len(values) and any(not k.startswith("ro.boot.") and properties.get(k, "") != v for k, v in zip(names, values)):
            excluded.append({"apk": str(installed), "reason": "package excluded by overlay property condition", "condition": dict(zip(names, values)), "actual": {k: properties.get(k, "") for k in names}})
            continue
    checked += 1
    for name in re.findall(r"^uses-library:'([^']+)'", text, re.M):
        check_library(name, installed, set())

report = {"checked_imported_apks": checked, "excluded_conditional_packages": excluded,
          "errors": errors, "scope": "Required Java shared libraries of installed imported APKs, including transitive XML dependencies and existing JARs. Conditional package exclusions use assembled build.prop defaults; boot-derived conditions remain conservatively active. Init-time property changes require runtime validation. Does not validate Java ABI, native JNI dependencies, APEX libraries or runtime behavior."}
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
sys.exit(bool(errors))
