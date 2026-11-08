#!/usr/bin/env python3
"""Import the OEM Sun WLAN platform configuration for native Kbuild."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VENDOR = ROOT / "device/nothing/FroggerPro-kernel/android_kernel_msm-6.6_nothing_sm7750/vendor/qcom/opensource"


def generate():
    platform = VENDOR / "wlan/platform"
    options = {}
    lines = ["# Generated from OEM Sun WLAN platform defconfigs."]
    for module in ["cnss2", "icnss2", "cnss_genl", "cnss_prealloc", "cnss_utils"]:
        source = platform / module / "sun_gki_defconfig"
        lines.append("# " + module + " SHA256 " + hashlib.sha256(source.read_bytes()).hexdigest())
        for line in source.read_text().splitlines():
            if not line.startswith("CONFIG_"):
                continue
            key, value = line.split("=", 1)
            if key in options and options[key] != value:
                raise ValueError("Conflicting OEM WLAN option: " + key)
            options[key] = value
    for key, value in sorted(options.items()):
        lines.append("export " + key + " := " + value)
        suffix = "_MODULE" if value == "m" else ""
        lines.append("subdir-ccflags-y += -D" + key + suffix + "=1")
    lines.append("subdir-ccflags-y += -I$(WLAN_PLATFORM_ROOT)/inc -I$(WLAN_PLATFORM_ROOT)/cnss_utils -I$(KERNEL_SRC)/vendor/qcom/opensource/data-kernel/drivers/smem-mailbox/include")
    output = platform / "Kbuild.sun_config"
    content = "\n".join(lines) + "\n"
    if not output.exists() or output.read_text() != content:
        output.write_text(content)
    print("PASS: WLAN Sun configuration,", len(options), "OEM options")


if __name__ == "__main__":
    generate()