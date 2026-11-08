#!/usr/bin/env python3
"""Generate Sun video Kbuild directly from the OEM DDK source registry."""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VIDEO = ROOT / "device/nothing/FroggerPro-kernel/android_kernel_msm-6.6_nothing_sm7750/vendor/qcom/opensource/video-driver"


def generate():
    source = VIDEO / "video_modules.bzl"
    lines = ["# Generated from OEM Sun video module metadata.",
             "# SHA256 " + hashlib.sha256(source.read_bytes()).hexdigest(),
             "include $(VIDEO_ROOT)/Kbuild.lineage_headers",
             "ccflags-y += -DCONFIG_MSM_MMRM=1 -DCONFIG_MSM_VIDC_SUN=1"]
    count = 0
    for node in ast.walk(ast.parse(source.read_text())):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "module_entry":
            continue
        fields = {kw.arg: kw.value for kw in node.keywords}
        name = ast.literal_eval(fields["name"])
        entries = ast.literal_eval(fields["srcs"])
        conditional = ast.literal_eval(fields.get("config_srcs", ast.Dict(keys=[], values=[])))
        entries += conditional.get("CONFIG_MSM_VIDC_SUN", [])
        # video_driver_build.bzl resolves registry entries through native.glob.
        # Mirror that selection, including optional entries absent from this release.
        patterns = list(dict.fromkeys(entries))
        entries = list(dict.fromkeys(
            str(path.relative_to(VIDEO)) for pattern in patterns
            for path in sorted(VIDEO.glob(pattern)) if path.is_file()))
        omitted = [pattern for pattern in patterns if not list(VIDEO.glob(pattern))]
        if omitted:
            lines.append("# OEM native.glob omits absent entries: " + ", ".join(omitted))
        if not entries:
            raise ValueError("Empty OEM video module: " + name)
        lines += ["obj-m += " + name + ".o",
                  name + "-y := " + " ".join(str(Path(p).with_suffix(".o")) for p in entries)]
        count += len(entries)
    content = "\n".join(lines) + "\n"
    output = VIDEO / "Kbuild.sun.generated"
    if not output.exists() or output.read_text() != content:
        output.write_text(content)
    print("PASS: Sun video registry,", count, "validated source entries")


if __name__ == "__main__":
    generate()