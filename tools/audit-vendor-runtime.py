#!/usr/bin/env python3
"""Audit complete active audio runtime wiring; run after building vendorimage."""
import argparse, json, re, sys
import xml.etree.ElementTree as ET
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument("product_out", type=Path)
parser.add_argument("--output", type=Path)
args = parser.parse_args()
vendor = args.product_out / "vendor"
files = {p.name for p in vendor.rglob("*") if p.is_file()}
errors, optional = [], []
required = ["libagm_mixer_plugin.so", "libagm_pcm_plugin.so", "libagm_compress_plugin.so", "libsndcardparser.so", "libagmipcservice.so", "libpalipcservice.so", "libsoundtriggerhal.qti.so", "libpaleventnotifier.so", "lib_bt_bundle.so", "lib_bt_aptx.so", "lib_bt_ble.so", "libhotword_intf.so", "libcustomva_intf.so"]
for name in required:
    if name not in files: errors.append("Missing runtime library: " + name)
rc = "\n".join(p.read_text(errors="replace") for p in (vendor / "etc/init").rglob("*.rc"))
for service in ["vendor.pd_mapper", "vendor.per_mgr", "vendor.per_proxy", "vendor.sensors-hal-multihal"]:
    count = len(re.findall(r"^service\s+" + re.escape(service) + r"\s", rc, re.M))
    if count != 1: errors.append(f"Expected one service {service}, found {count}")
for name in ["bin/pd-mapper", "bin/pm-service", "bin/pm-proxy", "bin/audioadsprpcd", "etc/card-defs.xml"]:
    if not (vendor / name).is_file(): errors.append("Missing file: " + name)
config = vendor / "etc/audio/sku_kera"
for name in ["audio_effects_config.xml", "mixer_paths_kera_qrd.xml", "resourcemanager_kera_qrd.xml"]:
    if not (config / name).is_file(): errors.append("Missing KERA config: " + name)
# Audit active effects and virtual-card plugins, not alternative stub effect configs.
for path in [config / "audio_effects_config.xml", vendor / "etc/card-defs.xml", *config.glob("resourcemanager_kera*.xml")]:
    if not path.exists(): continue
    for name in sorted(set(re.findall(r"[A-Za-z0-9_+.@-]+\.so", path.read_text()))):
        if name not in files: errors.append(f"{path.name} references missing {name}")
interfaces = vendor / "etc/audio/vendor_audio_interfaces.xml"
if interfaces.exists():
    for node in ET.parse(interfaces).iter("library"):
        name = node.get("libraryName")
        if name and name not in files:
            target = errors if node.get("mandatory") == "true" else optional
            target.append("Audio interface library absent: " + name)
report = {"product_out": str(args.product_out), "errors": errors, "optional_findings": optional, "scope": "Active audio plugins/configuration, DSP/peripheral startup and sensor service uniqueness; ELF checks are performed by Soong. Does not prove hardware functionality."}
text = json.dumps(report, indent=2) + "\n"
if args.output: args.output.write_text(text)
print(text, end="")
sys.exit(bool(errors))
