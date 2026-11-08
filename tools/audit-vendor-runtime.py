#!/usr/bin/env python3
"""Audit active audio, camera and network runtime wiring; run after building vendorimage."""
import argparse, hashlib, json, re, sqlite3, sys
import xml.etree.ElementTree as ET
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument("product_out", type=Path)
parser.add_argument("--output", type=Path)
args = parser.parse_args()
vendor = args.product_out / "vendor"
files = {p.name for p in vendor.rglob("*") if p.is_file()}
errors, optional = [], []
# The DSP graph ABI is a matched set; a mixture can link yet fail at runtime.
audio_manifest = Path(__file__).resolve().parents[1] / "configs/stock-audio-core.json"
for name, entry in json.loads(audio_manifest.read_text())["libraries"].items():
    library = args.product_out / entry["file"]
    if not library.is_file():
        errors.append("Missing matched audio core library: " + name)
    elif hashlib.sha256(library.read_bytes()).hexdigest() != entry["sha256"]:
        errors.append("Mismatched audio core library: " + name)
# The preserved display stack must stay ABI-coherent with its proprietary extension.
display_manifest = Path(__file__).resolve().parents[1] / "configs/preserved-display-stack.json"
for name, entry in json.loads(display_manifest.read_text()).items():
    library = vendor / entry["file"]
    if not library.is_file():
        errors.append("Missing matched display component: " + name)
    elif hashlib.sha256(library.read_bytes()).hexdigest() != entry["sha256"]:
        errors.append("Mismatched display component: " + name)
mixer = vendor / "etc/audio/sku_kera/mixer_paths_kera_qrd.xml"
if mixer.is_file():
    paths = {node.get("name"): node for node in ET.parse(mixer).getroot().findall("path")}
    speaker = paths.get("speaker")
    controls = {} if speaker is None else {node.get("name"): node.get("value") for node in speaker.findall("ctl")}
    for amp in (0, 1):
        for suffix, value in (("prof", "Music"), ("switch", "Enable")):
            if controls.get(f"aw_dev_{amp}_{suffix}") != value:
                errors.append(f"Speaker route missing amplifier {amp} {suffix}={value}")
# A2DP belongs to the software Bluetooth module; primary wins lookup if duplicated.
primary_config = vendor / "etc/audio/audio_module_config_primary.xml"
if not primary_config.is_file():
    errors.append("Missing primary audio module configuration")
else:
    for port in ET.parse(primary_config).iter("devicePort"):
        if port.get("connection") == "bt-a2dp" and port.get("role") == "sink":
            errors.append("Primary HAL intercepts software A2DP output: " + str(port.get("tagName")))
for unsupported in ("android.hardware.security.keymint-service.strongbox-thales.xml",
                    "android.hardware.security.sharedsecret-service.strongbox-thales.xml"):
    if (vendor / "etc/vintf/manifest" / unsupported).exists():
        errors.append("Unavailable unconditional ROW StrongBox declaration: " + unsupported)
# An unconditional Thales declaration makes credential changes wait on missing ROW OMAPI.
if (vendor / "etc/vintf/manifest/android.hardware.weaver-service.thales.xml").exists():
    errors.append("Unsupported unconditional Thales Weaver declaration for ROW")
weaver_init = vendor / "etc/init/android.hardware.weaver-service.thales.rc"
if weaver_init.is_file():
    weaver_service = re.search(r"(?m)^service weaver_hal_service [^\n]+\n((?:[ \t]+[^\n]*\n)*)", weaver_init.read_text())
    if weaver_service is None or not re.search(r"(?m)^\s+disabled\s*$", weaver_service.group(1)):
        errors.append("Optional Thales Weaver starts without an available ROW OMAPI backend")
bluetooth_manifest = vendor / "etc/vintf/manifest/audio-core-bluetooth.xml"
if not bluetooth_manifest.is_file() or not any(
        hal.findtext("name") == "android.hardware.audio.core"
        and hal.findtext("version") == "4"
        and "IModule/bluetooth" in [node.text for node in hal.findall("fqname")]
        for hal in ET.parse(bluetooth_manifest).getroot().findall("hal")):
    errors.append("Missing VINTF declaration for the Bluetooth software audio module")
# HCI transport permissions and classic profiles are independent requirements:
# an enabled adapter alone does not establish pairing or usable media audio.
ueventd = vendor / "etc/ueventd.rc"
if not ueventd.is_file() or not re.search(
        r"^/dev/ttyHS0\s+0660\s+bluetooth\s+net_bt\s*$",
        ueventd.read_text() if ueventd.is_file() else "", re.M):
    errors.append("Missing stock Bluetooth HCI UART ownership in active ueventd.rc")
properties = {}
for prop in (vendor / "build.prop", vendor / "etc/build.prop"):
    if prop.is_file():
        for line in prop.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                properties[key.strip()] = value.strip()
for profile in ("a2dp.source", "avrcp.target", "avrcp.controller", "hfp.ag",
                "gatt", "hid.host", "hid.device", "map.server", "opp",
                "pbap.server", "bas.client"):
    if properties.get("bluetooth.profile." + profile + ".enabled") != "true":
        errors.append("Missing enabled stock Bluetooth profile: " + profile)
required = ["libtensorflowlite_c_nothing.so", "libVoiceSdk.so", "liblistensoundmodelaidl.so", "liblistensoundmodel2vendor.so", "libagm_mixer_plugin.so", "libagm_pcm_plugin.so", "libagm_compress_plugin.so", "libsndcardparser.so", "libagmipcservice.so", "libpalipcservice.so", "libsoundtriggerhal.qti.so", "libpaleventnotifier.so", "lib_bt_bundle.so", "lib_bt_aptx.so", "lib_bt_ble.so", "libhotword_intf.so", "libcustomva_intf.so"]
for name in required:
    if name not in files: errors.append("Missing runtime library: " + name)
# The stock AIDL service can register without the hardware module and stall cleanup.
for name in ["lib64/hw/fingerprint.default.so", "lib64/libgf_hal.so",
             "lib64/libvendor.goodix.hardware.biometrics.fingerprint.so",
             "bin/hw/vendor.nothing.hardware.biometrics.fingerprint-service",
             "etc/init/vendor.noth.fingerprint.goodix.config.rc",
             "etc/init/vendor.nothing.hardware.biometrics.fingerprint-service.rc",
             "etc/vintf/manifest/vendor.nothing.hardware.biometrics.fingerprint-service.xml"]:
    if not (vendor / name).is_file(): errors.append("Missing fingerprint runtime asset: " + name)
# Supplicant creates its private config from this template after a clean reset.
if not (vendor / "etc/wifi/wpa_supplicant.conf").is_file():
    errors.append("Missing clean-reset supplicant configuration template")
# The stock system-UID fingerprint HAL must open FOD controls read/write.
fingerprint_init = vendor / "etc/init/vendor.noth.fingerprint.goodix.config.rc"
if fingerprint_init.is_file():
    text = fingerprint_init.read_text()
    for path in ("/proc/touchpanel/fod_mode", "/sys/panel_feature/fp_status"):
        for command in ("chown system system ", "chmod 0660 "):
            if command + path not in text:
                errors.append("Missing fingerprint control ownership: " + command + path)
# QCRIL aborts during bring-up if its socket directory or these syscalls are missing.
qcril_policy = vendor / "etc/seccomp_policy/qcrilnr@2.0.policy"
allowed_syscalls = set()
if qcril_policy.is_file():
    allowed_syscalls = {line.split("#", 1)[0].strip() for line in qcril_policy.read_text().splitlines()}
for syscall in ("getppid", "uname"):
    if f"{syscall}: 1" not in allowed_syscalls:
        errors.append("Missing QCRIL syscall allowance: " + syscall)

# The data plugin is loadable only after the QCRIL database/state lifecycle exists.
qcom_init = vendor / "etc/init/hw/init.qcom.rc"
for command in ("mkdir /data/vendor/radio 0770 system radio",
                "mkdir /data/vendor/modem_config 0570 radio root",
                "mkdir /dev/socket/qmux_radio 0770 radio radio",
                "chmod 2770 /dev/socket/qmux_radio",
                "mkdir /data/vendor/tombstones/rfs/modem 0771 system system",
                "copy /vendor/etc/qcril_database/qcrilNr.db /data/vendor/radio/qcrilNr_prebuilt.db",
                "write /data/vendor/radio/prebuilt_db_support 1",
                "write /data/vendor/radio/db_check_done 0",
                "write /data/vendor/radio/copy_complete 0",
                "write /data/vendor/radio/copy_complete 1"):
    if not qcom_init.is_file() or command not in qcom_init.read_text():
        errors.append("Missing QCRIL clean-reset initialization: " + command)
if qcom_init.is_file():
    for line in qcom_init.read_text().splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[0] == "copy" and fields[2] == "/data/vendor/radio/qcrilNr.db":
            errors.append("Init overwrites the writable QCRIL database")
            break
qcril_db = vendor / "etc/qcril_database/qcrilNr.db"
if not qcril_db.is_file():
    errors.append("Missing QCRIL database seed")
else:
    with sqlite3.connect(qcril_db) as conn:
        row = conn.execute("SELECT def_val, value FROM qcril_properties_table WHERE property='persist.vendor.radio.poweron_opt'").fetchone()
        if row != ("0", "0"):
            errors.append(f"Expected qcrilNr.db persist.vendor.radio.poweron_opt=('0', '0'), found {row}")
for rfs_link, rfs_target in {
    "rfs/msm/mpss/readonly/firmware": "/vendor/firmware_mnt",
    "rfs/msm/mpss/readonly/vendor/firmware": "/vendor/firmware",
    "rfs/msm/mpss/readwrite": "/mnt/vendor/persist/rfs/msm/mpss",
    "rfs/msm/mpss/shared": "/mnt/vendor/persist/rfs/shared",
    "rfs/msm/mpss/hlos": "/mnt/vendor/persist/hlos_rfs/shared",
    "rfs/msm/mpss/ramdumps": "/data/vendor/tombstones/rfs/modem",
}.items():
    link_path = vendor / rfs_link
    if not link_path.is_symlink() or str(link_path.readlink()) != rfs_target:
        errors.append(f"Missing or invalid RFS symlink {rfs_link} -> {rfs_target}")
# CamX selects this plugin for FroggerPro's SoC 659, independently of DT_NEEDED.
for name in ["lib64/com.qti.settings.sm7750.so", "lib64/hw/camera.qcom.so",
             "lib64/hw/com.qti.chi.override.so", "etc/init/init.froggerpro.glyph.rc",
             "etc/wifi/qca6750/WCNSS_qcom_cfg.ini", "bin/init.qcom.sh",
             "bin/init.class_main.sh", "bin/irsc_util", "etc/sec_config",
             "etc/public.libraries.txt", "etc/displayconfig/display_id_4630947050240568210.xml",
             "etc/media_codecs.xml", "etc/media_codecs_google_audio.xml",
             "etc/media_codecs_google_c2_audio.xml"]:
    if not (vendor / name).is_file(): errors.append("Missing device runtime asset: " + name)
# Check the packed labels and permissions implicated by the camera and face logs.
policy_dir = vendor / "etc/selinux"
for filename, entry in (
    ("vendor_service_contexts", "com.nothing.camera.postproc.IPostProcService/default u:object_r:vendor_frogger_camera_postproc_service:s0"),
    ("vendor_property_contexts", "persist.vendor.face. u:object_r:vendor_frogger_face_config_prop:s0 prefix"),
):
    contexts = policy_dir / filename
    if not contexts.is_file() or not any(
        line.split() == entry.split() for line in contexts.read_text().splitlines()
    ):
        errors.append("Missing vendor SELinux context: " + entry.split()[0])

vendor_policy = policy_dir / "vendor_sepolicy.cil"
policy_text = vendor_policy.read_text() if vendor_policy.is_file() else ""
for domain, target, object_class, permission in (
    ("hal_camera_default", "vendor_frogger_camera_postproc_service", "service_manager", "add"),
    ("vendor_hal_camera_default", "vendor_frogger_camera_postproc_service", "service_manager", "find"),
    ("hal_face_default", "vendor_frogger_face_config_prop", "property_service", "set"),
):
    prefix = f"(allow {domain} {target} ({object_class} ("
    if not any(
        permission in match.split() for match in re.findall(re.escape(prefix) + r"([^)]*)", policy_text)
    ):
        errors.append(f"Missing vendor SELinux permission: {domain} {permission} {target}")

for interface in ["config", "data", "messaging", "modem", "network", "sap", "sim", "voice"]:
    path = vendor / f"etc/vintf/manifest/android.hardware.radio.{interface}.xml"
    if not path.is_file(): errors.append("Missing active radio VINTF fragment: " + str(path))
for feature in ["wifi", "telephony.gsm", "camera.front", "sensor.accelerometer", "sensor.gyroscope", "sensor.light", "sensor.proximity"]:
    if not (vendor / f"etc/permissions/android.hardware.{feature}.xml").is_file():
        errors.append("Missing hardware feature declaration: " + feature)
rc = "\n".join(p.read_text(errors="replace") for p in (vendor / "etc/init").rglob("*.rc"))
for service in ["vendor.pd_mapper", "vendor.per_mgr", "vendor.per_proxy", "vendor.sensors-hal-multihal", "irsc_util", "qcom-sh", "qcom-c_main-sh"]:
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
# Match system/media/audio/include/system/audio_config.h and ConfigManager.cpp.
# Merely finding the XML in /vendor/etc/audio does not make it discoverable.
search_paths = [args.product_out / "odm/etc", config, vendor / "etc", args.product_out / "system/etc"]
interfaces = next((path / "vendor_audio_interfaces.xml" for path in search_paths
                   if (path / "vendor_audio_interfaces.xml").is_file()), None)
if interfaces is None:
    errors.append("Audio registration XML is absent from the loader's search paths")
else:
    libraries = list(ET.parse(interfaces).iter("library"))
    names = [node.get("libraryName") for node in libraries]
    bluetooth = [node for node in libraries if node.get("libraryName") == "android.hardware.bluetooth.audio_sw.so"]
    if len(bluetooth) != 1 or bluetooth[0].get("method") != "registerIModuleBluetoothSWQti":
        errors.append("Missing Bluetooth software audio module registration entry")
    for required_library in ["libagmipcservice.so", "libpalipcservice.so", "libaudiocorehal.qti.so", "libaudioeffecthal.qti.so"]:
        entries = [node for node in libraries if node.get("libraryName") == required_library]
        if len(entries) != 1 or entries[0].get("mandatory") != "true":
            errors.append("Expected one mandatory audio registration: " + required_library)
    if all(name in names for name in ["libagmipcservice.so", "libpalipcservice.so", "libaudiocorehal.qti.so"]):
        if not names.index("libagmipcservice.so") < names.index("libpalipcservice.so") < names.index("libaudiocorehal.qti.so"):
            errors.append("AGM and PAL must register before the Qualcomm audio core")
    for node in libraries:
        name = node.get("libraryName")
        if name and name not in files:
            target = errors if node.get("mandatory") == "true" else optional
            target.append("Audio interface library absent: " + name)
report = {"product_out": str(args.product_out), "errors": errors, "optional_findings": optional, "scope": "Active audio plugins/configuration, DSP/peripheral startup, camera settings, radio manifests, Wi-Fi config and hardware features; ELF checks are performed by Soong. Does not prove hardware functionality."}
text = json.dumps(report, indent=2) + "\n"
if args.output: args.output.write_text(text)
print(text, end="")
sys.exit(bool(errors))
