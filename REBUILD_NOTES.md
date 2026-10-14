# FroggerPro reproducible bring-up build

## Fixes retained in the active tree

- BoardConfig.mk: TARGET_USES_VULKAN=true; metadata partition enabled;
  sun bootconfig SKU; 50 MiB DTBO partition; Power base manifest included.
- vintf/power.xml: IPower/default version 5; shipping FCM 202404.
  This branch rejects an explicit kernel target-level at this shipping level.
- device.mk: skiavkthreaded rendering; complete configs/audio and audio-root
  installation; QSEE vendor runtime; audio core default HAL; native vendor
  service manager; snapalloc and display tables; fastbootd modules.
- configs/audio: working SKU sun policy, mixer/resource configurations,
  primary audio-module configuration, and vendor HAL registration XML.
- configs/audio-root: absolute XInclude dependencies for SKU audio policy.
- init/init.qcom.rc: Adreno EGL/Vulkan selectors; corrected modprobe --all=
  argument; vendor firmware mounts and USB init import.
- fstab.qcom: ext4 metadata and physical first-stage AVB entries.
- init/ueventd.qcom.rc and init/init.qti.keymaster.sh: stock device permissions
  and Gatekeeper security-level selection.

These files are build inputs; the archived extracted aosp-device-tree directory
is not the authoritative BoardConfig for this product.

## Release verification

A successful build must report VINTF COMPATIBLE. Extract the resulting vendor
image with fsck.erofs and verify the audio files, IPower declaration, sun SKU,
ro.hwui.use_vulkan=true, and debug.renderengine.backend=skiavkthreaded.
Inspect recovery for fastbootd and its implementation under system/lib64/hw.
Verify AVB descriptors against the complete matching image set before flashing.
Do not use earlier ZIPs or diagnostic vbmeta with a newly built partition set.

## Temporary diagnostics

The ext4-aware init logger was compiled separately and saved under
out/bootloop-diagnostics/corrected-20261011. system/core/init/util.cpp was restored
byte-for-byte from /tmp/frogger-init-util-pre-ext4-diag.cpp. Rebuild init_first_stage
before generating future release images because its current installed build
output is diagnostic even though the source has been restored.
Reference-kernel recovery images are diagnostic artifacts, not the final ROM.
The working Android session currently uses reference kernel 6.6.139; retain the
matched kernel/module/boot-chain relationship when preparing final images.

## Current validation limits

Corrected CP2A images passed build, VINTF, EROFS, and full super-content checks;
the complete super and matching slot-A boot images were flashed successfully.
The source-kernel normal boot test froze at the logo. A later reference-kernel
Android session is booted with root ADB: wlan0 is up, camera is user-confirmed,
and the current navigation/padding overlays were recovered into source.
Bluetooth and source-kernel normal boot remain unverified. Reference recovery
exposes root ADB.
Persistent source-kernel log segments include recovery-mode records; those
service errors must not be attributed to normal boot without proving mode/time.

## Recovery USB timing test

recovery/init.recovery.qcom.rc now waits up to 30 seconds for the UDC, replacing
its prior 1-second wait. Saved source recovery logs show UDC checks timing out
around 9 seconds and dwc3 completing initialization around 16 seconds. This is
a controlled timing hypothesis; connection testing remains required. It is not
a verified normal-boot fix.

Release init_first_stage rebuild after removal of temporary logging completed
successfully; installed ramdisk/init no longer contains the diagnostic log path.

## Glyph Matrix bring-up (2026-10-12)

The reference-kernel Android session is booted with root ADB. The user confirmed
visible Matrix output with the ten-second cross test after correcting HAL
brightness from a percentage to its 0..4095 scale (test value 512). Earlier
values 5 and 20 rounded the pixels to zero; they did not prove a hardware fault.

Build inputs now include glyph.mk (13x13/169 logical, 137 physical channels),
LightState frame parcel support and a device-gated GlyphLights adapter in
frameworks/base/services/core/java/com/android/server/lights. The adapter
preserves LightsService permissions and per-light session priority, applies
stock ordinal arbitration, trims the stock circular row mask, and clears
output when requests disappear. The AW20144 sysfs directory receives the
existing sysfs_leds label for hal_light access in enforcing mode. Current
runtime is permissive; enforcing validation remains necessary.

Nothing OS Glyph Toy binding and third-party 404+ compatibility are not yet
implemented or verified. The framework bridge has not yet been flashed.
Source-kernel normal boot remains unverified; do not claim an arbitrary rebuilt
boot chain reproduces the reference-kernel Android result.

Old top-level ZIPs/images are archived in
out/target/product/FroggerPro/fail/20261012-before-glyph with original paths,
sizes, timestamps and SHA-256 hashes in manifest.json. Historical diagnostic
symlinks point to these exact archived images, not future regenerated output.

The standalone javac compile of the modified LightState, GlyphLights and
LightsService passed against the current framework/services build libraries.
The Android bridge harness passed; services instrumentation tests are added
but have not yet run. Full Soong build and image/runtime validation are pending.

## Host build controls

Use tools/build-safe.sh from this device directory (or its full path from the
Lineage root). With no arguments it builds bacon; pass module names for a
focused build. It selects CP2A, four permitted CPUs/four jobs, low priority,
GOMEMLIMIT=14GiB and GOGC=50. Soong's worker launcher runs under env -i;
build/soong/ui/build/soong.go now forwards only explicitly supplied GOMEMLIMIT,
GOGC and GOMAXPROCS so those resource settings actually reach the worker.
The heap limit is a Go soft limit, not a hard process-RSS guarantee.

## Working-session retention checks

The live Morpho stabilizer library exactly matches the source blob SHA-256
(e5df31b076896a342dbb99acc90124052f1f0224a95e6f6a8ea80e2b08aa6328),
including the confirmed return patch at 0x31c02c. The live vendor metadata library
matches the built system/lib64/libcamera_metadata.so byte-for-byte (SHA-256
f3e2723a2d6fd16d180694d29c5628128bc393a909c99c92990d992ab049587c), but
its vendor placement was supplied by an overlay. The
frogger_camera_metadata_vendor prebuilt module now retains that exact vendor
placement, with provenance and its hash in prebuilts/camera/PROVENANCE.md. The working Wi-Fi init overlay was copied into
init/init.vendor.wlan.rc and added to active PRODUCT_COPY_FILES; it creates
/data/vendor/wifi/wpa/sockets before early-boot WLAN enablement.

Exact slot-A boot-chain images and effective vendor/system module directories
are saved in out/bootloop-diagnostics/working-20261012. The effective modules
have 6.6.139 vermagic; the source-kernel build uses 6.6.127. Do not mix these sets.
Vendor, vendor_dlkm and system_dlkm currently have overlayfs mounts; a successful
live test does not prove the underlying partition images contain every fix.

Blueprint now sorts primary-builder environment keys before emitting Ninja
commands. Previously, map iteration changed assignment order across identical
invocations and needlessly invalidated the graph when several resource knobs
were supplied. TestPrimaryBuilderEnvironmentIsDeterministic passed with the
bundled Go toolchain. The safe wrapper uses nice 5 to match nsjail's worker
priority; an earlier nice-10 invocation produced a nonfatal setpriority warning.

The focused build of framework-minus-apex, services, both padding overlays,
frogger_camera_metadata_vendor and selinux_policy completed successfully after
correcting the frame methods' @hide Javadoc tags. The current API check passed;
the frame methods remain outside the public SDK API. The installed vendor
camera metadata prebuilt retains the exact working hash. Framework installation,
full ROM packaging and enforcing-mode hardware validation remain pending.

The working-phone ROM backup is complete at
out/bootloop-diagnostics/working-20261012: raw super and 112 physical images
were individually verified against phone SHA-256 hashes in recovery. Userdata
was excluded by explicit choice. Working overlay files, padding APKs and module
sets are also saved. The phone returned to Android with boot_completed=1 and
kernel 6.6.139. Backup README records its existing disabled-verification state
and the current odm AVB hashtree mismatch separately from backup integrity.
