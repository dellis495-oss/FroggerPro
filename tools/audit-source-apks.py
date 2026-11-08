#!/usr/bin/env python3
"""Reject unresolved Git LFS APK inputs before starting the platform build."""
from pathlib import Path
import sys
import zipfile

root = Path(__file__).resolve().parents[4]
errors = []
apks = sorted([
    *(root / "external/prebuiltapks").rglob("*.apk"),
    *(root / "external/chromium-webview/prebuilt").rglob("*.apk"),
])
if not apks:
    errors.append("No external/prebuiltapks APK inputs found")
for apk in apks:
    with apk.open("rb") as stream:
        header = stream.read(64)
    if header.startswith(b"version https://git-lfs.github.com/spec/v1"):
        errors.append("Unresolved Git LFS pointer: " + str(apk.relative_to(root)))
        continue
    try:
        with zipfile.ZipFile(apk) as archive:
            if "AndroidManifest.xml" not in archive.namelist():
                errors.append("APK has no manifest: " + str(apk.relative_to(root)))
    except zipfile.BadZipFile:
        errors.append("Invalid APK archive: " + str(apk.relative_to(root)))
for error in errors:
    print(error, file=sys.stderr)
if errors:
    print("Restore exact LFS objects before building; do not bypass manifest checks.", file=sys.stderr)
else:
    print(f"PASS: {len(apks)} prebuilt APK inputs are real archives with manifests")
raise SystemExit(bool(errors))
