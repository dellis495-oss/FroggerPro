#!/usr/bin/env python3
"""Translate the OEM Sun camera DDK source selection to native Kbuild."""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
KERNEL = ROOT / "device/nothing/FroggerPro-kernel/android_kernel_msm-6.6_nothing_sm7750"
CAMERA = KERNEL / "vendor/qcom/opensource/camera-kernel"


def literal(node, values):
    if isinstance(node, ast.Name):
        return values[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return literal(node.left, values) + literal(node.right, values)
    if isinstance(node, ast.Dict):
        return {literal(k, values): literal(v, values) for k, v in zip(node.keys, node.values)}
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal(v, values) for v in node.elts]
    return ast.literal_eval(node)


def generate():
    config_source = CAMERA / "project_defconfig.bzl"
    values = {}
    for node in ast.parse(config_source.read_text()).body:
        if not isinstance(node, ast.Assign):
            continue
        key = node.targets[0].id
        if key in ("common_configs", "dependency_config"):
            values[key] = literal(node.value, values)
        elif key == "project_configs":
            values[key] = literal(node.value.args[0], values)
    options = values["common_configs"] + values["project_configs"][":sun"]
    source = CAMERA / "camera_modules.bzl"
    calls = [node for node in ast.walk(ast.parse(source.read_text()))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == "ddk_module"]
    if len(calls) != 1:
        raise ValueError("Expected one OEM camera module")
    fields = {kw.arg: kw.value for kw in calls[0].keywords}
    base = literal(fields["srcs"], {})
    conditional = literal(fields["conditional_srcs"], {})
    all_sources = set(base)
    for choices in conditional.values():
        for entries in choices.values():
            all_sources.update(entries)
    for entry in all_sources:
        if not (CAMERA / entry).is_file():
            raise ValueError("Missing OEM camera source: " + entry)
    lines = ["# Generated from OEM Sun camera DDK metadata."]
    for path in (source, config_source):
        lines.append("# " + path.name + " SHA256 " + hashlib.sha256(path.read_bytes()).hexdigest())
    lines += ["include $(KERNEL_SRC)/$(M)/Kbuild.lineage_headers"]
    for option in options:
        name, value = option.split("=", 1)
        lines += [name + " := " + value, "ccflags-y += -D" + name + "=1"]
    directories = sorted({p.parent.relative_to(CAMERA).as_posix() for p in CAMERA.rglob("*.h")})
    lines += ["ccflags-y += -I$(CAMERA_KERNEL_ROOT) -include $(CAMERA_BUILD_BANNER)",
              "ccflags-y += " + " ".join("-I$(CAMERA_KERNEL_ROOT)/" + p for p in directories),
              "obj-m += camera.o",
              "camera-y := " + " ".join(str(Path(p).with_suffix(".o")) for p in dict.fromkeys(base))]
    # Keep native kernel config conditions live; deduplicate sources already in the base list.
    for option, choices in conditional.items():
        lines.append("ifneq ($(filter y m,$(" + option + ")),)")
        lines.append("camera-y += " + " ".join(str(Path(p).with_suffix(".o")) for p in choices.get(True, []) if p not in base))
        if choices.get(False):
            lines += ["else", "camera-y += " + " ".join(str(Path(p).with_suffix(".o")) for p in choices[False] if p not in base)]
        lines.append("endif")
    content = "\n".join(lines) + "\n"
    output = CAMERA / "Kbuild.sun.generated"
    if not output.exists() or output.read_text() != content:
        output.write_text(content)
    print("PASS: Sun camera metadata,", len(all_sources), "validated source files")


if __name__ == "__main__":
    generate()