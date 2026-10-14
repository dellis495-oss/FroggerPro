# FroggerPro bring-up

Extract the matching dump from the Android source root:

```sh
device/nothing/FroggerPro/extract-files.sh device/nothing/FroggerPro/froggerpro
device/nothing/FroggerPro/setup-makefiles.sh
```

The shell entry points use the current Python extract-utils and generate
`vendor/nothing/FroggerPro/FroggerPro-vendor.mk`. `proprietary-files.txt` is
the active list; `proprietary-files1.txt` is a reference copy.

Six Thales configuration files are mapped from the dump's
`odm/overlayfs_origin/vendor` directory to their vendor install paths.
Use this matching dump for those mappings; extraction over adb does not
necessarily expose the same files or regional variants.

SenseTime `license.lic`, the Nothing face HAL, its init/VINTF configuration,
`libstfaceunlockppl.so`, and the face evaluation init script are excluded.
The face HAL links to that pipeline, which exposes license initialization.
Stock face unlock is therefore disabled; no replacement is implemented.
The raw dump and bundled vendor archives still contain unfiltered files:
do not include them when publishing the device tree.

BoardConfig selects the kernel source at
`device/nothing/FroggerPro-kernel/android_kernel_msm-6.6_nothing_sm7750`
with `gki_defconfig vendor/sun_perf.config vendor/FroggerPro.config`.
Stock 6.6.127 module inputs are removed; modules must come from the source
build. DTBO remains a stock prebuilt from the matching dump, with its
50,331,648-byte partition size. Recovery fstab uses EROFS for the generated
system, system_ext, product, vendor, and odm images.

Validated: all active proprietary entries exist after extraction; vendor
makefile generation and Android build-variable parsing pass. This is not a
verified bootable port. A full kernel/ROM build and device testing remain
necessary, including DTB/vendor ramdisk assembly, complete external driver
coverage, custom vendor service IDs, device SELinux policy, and AVB/partition
geometry. Firmware OTA entries were removed because this tree has no
firmware extraction list or radio-image registration rules.

Proprietary-file audit (2026-10-10):

- Restored the stock Bluetooth, AIDL boot-control, Qualcomm thermal, and
  TEE/SPU/Thales KeyMint services together with their missing shared libraries
  and init/VINTF files. Thales KeyMint configurations use the same ODM overlay
  mapping as the other Thales configurations. The stock KeyMint utility library
  keeps those prebuilts on their matching API V3 dependency chain, with a
  separate module name and SONAME to avoid replacing the source V4 variant;
  the Thales service and library have their DT_NEEDED references updated. SPU
  KeyMint uses the matching stock SharedSecret V2 prebuilt for link checking
  because source V2 is unfrozen in this branch. The prebuilt is non-installable;
  the source SharedSecret V2 module supplies the single installed runtime.
- Selected the source replacements for the omitted audio, Bluetooth audio,
  display, mapper, sensors, health, USB, Wi-Fi and vibrator components in
  device.mk. Wi-Fi service, supplicant and hostapd VINTF fragments are selected
  explicitly because their binaries do not install those fragments themselves.
- Restored the radio and sensor init scripts referenced by stock init services,
  and mapped the FM script to vendor/bin to match init.qti.fm.rc.
- Existing camera plugin symbol exceptions and camera/Wi-Fi dependencies are
  now maintained by extract-files.py. The existing hal_proxy_daemon ELF-check
  exception is recorded in proprietary-files.txt so regeneration preserves it.

Original definitions are saved under metadata-repair-backup/proprietary-audit;
backup Android build files have .backup suffixes to avoid build discovery.

Static audit validation: 2,690 active entries; all dump inputs and extracted
outputs exist; no duplicate destinations. Makefile regeneration is stable.
Restored service binaries are AArch64 and their DT_NEEDED libraries appear in
the generated dependency lists. Thales VINTF XML parsing passes.
All six restored service init scripts pass host_init_verifier using the
existing vendor account definitions.

Init and recovery USB repairs (2026-10-10):

- Recovery now imports the matched stock `init.recovery.qcom.rc`, including
  ConfigFS selection, the bootloader-provided UDC name, peripheral mode, and
  the bootdevice symlink. The generic recovery init script owns ADB/sideload
  gadget binding and FunctionFS.
- `kernel-modules.mk` packages 138 rebuilt boot drivers and their symbol
  dependencies into vendor_boot and recovery. Its 126 load entries follow
  matched stock boot order and add USB/storage platform roots. Stock kernel
  binaries are not copied. `ipclite.ko` is absent from this source build.
  The Sun vendor load list now contains 119 drivers rather than being empty.
- Normal boot imports a device-owned init entry point for early/late mounts,
  vendor module loading, and the USB gadget HAL's ConfigFS setup.
  `fstab.qcom` preserves the matched stock data encryption and firmware mount
  settings while selecting EROFS for all generated logical partitions.
  The `default`, `emmc`, and `qcom` suffixes use this same corrected fstab in
  both vendor and the first-stage ramdisk.
- The matched stock DTB is included in vendor_boot alongside the existing
  stock DTBO. The DTB is a hardware description; the kernel and modules remain
  source-built. Source DTB generation is not yet configured.
- Stock init scripts for excluded WFD HDCP and Wi-Fi QoS binaries are filtered
  out. WLAN startup actions remain in the device init script.

Validation: Android's combined host init verifier accepts all 220 normal-boot
init scripts with the updated vendor scripts, and both recovery init scripts.
The actual Lineage kernel packaging macro and depmod successfully package the
138 early modules with no unknown symbols or missing packaged dependencies.
Module lists must be re-audited when kernel configuration changes. On-device
boot, USB enumeration, HAL behavior, and encrypted data mounts still need
verification. Rebuild the ROM to incorporate vendor init/fstab changes; a
recovery-only rebuild does not update normal-boot vendor configuration.
