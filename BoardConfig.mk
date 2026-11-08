#
# Nothing Phone (4a) Pro - FroggerPro
# Source-kernel bring-up configuration
#

DEVICE_PATH := device/nothing/FroggerPro

# Vendor service accounts, matching the FroggerPro vendor image.
TARGET_FS_CONFIG_GEN += $(DEVICE_PATH)/config.fs

# Proprietary vendor additions
-include vendor/nothing/FroggerPro/BoardConfigVendor.mk

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := generic

# Platform
TARGET_BOARD_PLATFORM := sun
TARGET_USES_VULKAN := true
TARGET_BOOTLOADER_BOARD_NAME := sun
TARGET_NO_BOOTLOADER := true
BOARD_ROOT_EXTRA_SYMLINKS += \
    /vendor/firmware_mnt:firmware \
    /vendor/bt_firmware:bt_firmware \
    /vendor/dsp:dsp

# Boot image format
BOARD_BOOT_HEADER_VERSION := 4
BOARD_INIT_BOOT_HEADER_VERSION := 4
BOARD_KERNEL_PAGESIZE := 4096

# Keep the matched stock DTB/DTBO pair during source-kernel bring-up.
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_PREBUILT_DTBIMAGE_DIR := $(DEVICE_PATH)/prebuilts/dtb

# Kernel built from source
BOARD_KERNEL_CMDLINE := androidboot.hardware=qcom androidboot.load_modules_parallel=true androidboot.usbcontroller=a600000.dwc3 androidboot.serialconsole=0 firmware_class.path=/vendor/firmware,/vendor/firmware_mnt/image,/firmware/image log_buf_len=1M nosoftlockup sysctl.kernel.firmware_config.force_sysfs_fallback=1
FROGGER_INIT_DIAGNOSTICS ?= false
ifeq ($(FROGGER_INIT_DIAGNOSTICS),true)
BOARD_KERNEL_CMDLINE += androidboot.frogger.init_log=1
endif
BOARD_KERNEL_BASE := 0x00000000
BOARD_KERNEL_IMAGE_NAME := Image
BOARD_USES_GENERIC_KERNEL_IMAGE := true
TARGET_KERNEL_VERSION := 6.6
TARGET_KERNEL_CLANG_VERSION := r563880c
# Default to the boot-verified kernel and its matching modules.
FROGGER_KERNEL_PROFILE ?= working
ifeq ($(FROGGER_KERNEL_PROFILE),working)
include $(DEVICE_PATH)/working-kernel.mk
else ifeq ($(FROGGER_KERNEL_PROFILE),source)
TARGET_KERNEL_SOURCE := device/nothing/FroggerPro-kernel/android_kernel_msm-6.6_nothing_sm7750
TARGET_KERNEL_CONFIG := gki_defconfig vendor/sun_perf.config vendor/FroggerPro.config
TARGET_KERNEL_EXT_MODULE_ROOT := device/nothing/FroggerPro-kernel/android_kernel_msm-6.6_nothing_sm7750/vendor
TARGET_KERNEL_EXT_MODULES := qcom/opensource/mmrm-driver qcom/opensource/mm-drivers/hw_fence qcom/opensource/mm-drivers/msm_ext_display qcom/opensource/mm-drivers/sync_fence qcom/opensource/securemsm-kernel qcom/opensource/audio-kernel qcom/opensource/synx-kernel qcom/opensource/display-drivers qcom/opensource/graphics-kernel qcom/opensource/touch-drivers qcom/opensource/dsp-kernel qcom/opensource/video-driver qcom/opensource/camera-kernel qcom/opensource/data-kernel/drivers/smem-mailbox qcom/opensource/wlan/platform qcom/opensource/bt-kernel qcom/opensource/datarmnet-ext/mem qcom/opensource/dataipa/drivers/platform/msm qcom/opensource/datarmnet/core qcom/opensource/datarmnet-ext/sch qcom/opensource/datarmnet-ext/aps qcom/opensource/datarmnet-ext/offload qcom/opensource/datarmnet-ext/perf_tether qcom/opensource/datarmnet-ext/shs qcom/opensource/datarmnet-ext/perf qcom/opensource/datarmnet-ext/wlan qcom/opensource/wlan/qcacld-3.0

# Match the OEM project define used by build.config.nothing.FroggerPro.
TARGET_KERNEL_ADDITIONAL_FLAGS += NT_PROJECT=FroggerPro
BOARD_USES_VENDOR_DLKMIMAGE := true
BOARD_USES_SYSTEM_DLKMIMAGE := true

include $(DEVICE_PATH)/kernel-modules.mk

else
$(error Unknown FROGGER_KERNEL_PROFILE $(FROGGER_KERNEL_PROFILE))
endif

# Physical partition sizes
BOARD_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE := 8388608
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_PVMFWIMAGE_PARTITION_SIZE := 1048576
AB_OTA_PARTITIONS += pvmfw
BOARD_DTBOIMG_PARTITION_SIZE := 52428800
BOARD_PREBUILT_DTBOIMAGE ?= $(DEVICE_PATH)/prebuilts/dtbo.img
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 104857600

# Stock recovery is a separate ramdisk-only image
BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE := true
BOARD_RAMDISK_USE_LZ4 := true

# A/B OTA
AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += \
    boot \
    dtbo \
    init_boot \
    recovery \
    system \
    system_ext \
    product \
    vendor \
    vendor_boot \
    odm \
    system_dlkm \
    vendor_dlkm

# Metadata is mounted before the system root switch.
BOARD_USES_METADATA_PARTITION := true

# Dynamic partitions
BOARD_SUPER_PARTITION_SIZE := 9663676416
BOARD_SUPER_PARTITION_GROUPS := qualcomm_dynamic_partitions

BOARD_QUALCOMM_DYNAMIC_PARTITIONS_PARTITION_LIST := \
    system \
    system_ext \
    product \
    vendor \
    odm \
    system_dlkm \
    vendor_dlkm

BOARD_QUALCOMM_DYNAMIC_PARTITIONS_SIZE := 9659482112

# Filesystems / flash geometry
BOARD_FLASH_BLOCK_SIZE := 262144
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true

# Recovery
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/recovery/recovery.fstab
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TARGET_RECOVERY_DENSITY := xxhdpi

# Stock recovery uses boot image header v4.
# Use the same header version for the generated boot images.
BOARD_RECOVERY_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_INIT_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)

# Stock regional/SOC VINTF manifests, registered as SKU manifests.
ODM_MANIFEST_SKUS += JPN
ODM_MANIFEST_JPN_FILES += vendor/nothing/FroggerPro/proprietary/odm/etc/vintf/manifest_JPN.xml
DEVICE_MANIFEST_SKUS += kera sun tuna
# Device-owned SKU manifests let assemble_vintf inject BOARD_SEPOLICY_VERS.
DEVICE_MANIFEST_KERA_FILES += $(DEVICE_PATH)/vintf/manifest_kera.xml
DEVICE_MANIFEST_SUN_FILES += $(DEVICE_PATH)/vintf/manifest_sun.xml
DEVICE_MANIFEST_TUNA_FILES += $(DEVICE_PATH)/vintf/manifest_tuna.xml
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/vintf/power.xml

# Missing Images & Partitions Filesystems
BOARD_ODMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_SYSTEM_DLKMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_SYSTEM_EXTIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_VENDOR_DLKMIMAGE_FILE_SYSTEM_TYPE := erofs

TARGET_COPY_OUT_ODM := odm
TARGET_COPY_OUT_SYSTEM_DLKM := system_dlkm
TARGET_COPY_OUT_VENDOR_DLKM := vendor_dlkm

# SELinux
# include vendor/nothing/NanoGlyph/sepolicy/config.mk
# include hardware/nothing/config.mk
# Qualcomm system_ext and product SELinux policies
include device/qcom/sepolicy/SEPolicy.mk

# Qualcomm vendor SELinux policies
include device/qcom/sepolicy_vndr/SEPolicy.mk
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/system_ext/private
BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/crdroid/vendor
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/crdroid/private
SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/crdroid/public
include device/lineage/sepolicy/libperfmgr/sepolicy.mk

# Wi-Fi
BOARD_WLAN_DEVICE := qcwcn
BOARD_HOSTAPD_DRIVER := NL80211
BOARD_HOSTAPD_PRIVATE_LIB := lib_driver_cmd_$(BOARD_WLAN_DEVICE)
BOARD_WPA_SUPPLICANT_DRIVER := $(BOARD_HOSTAPD_DRIVER)
BOARD_WPA_SUPPLICANT_PRIVATE_LIB := $(BOARD_HOSTAPD_PRIVATE_LIB)
BOARD_WPA_SUPPLICANT_PRIVATE_LIB_EVENT := "ON"
WIFI_DRIVER_STATE_CTRL_PARAM := "/dev/wlan"
WIFI_DRIVER_STATE_OFF := "OFF"
WIFI_DRIVER_STATE_ON := "ON"
WIFI_FEATURE_HOSTAPD_11AX := true
WIFI_FEATURE_SUPPLICANT_11AX := true
WIFI_HIDL_FEATURE_AWARE := true
WIFI_HIDL_FEATURE_DUAL_INTERFACE := true
WIFI_HIDL_UNIFIED_SUPPLICANT_SERVICE_RC_ENTRY := true
WPA_SUPPLICANT_VERSION := VER_0_8_X
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_SYSTEM_EXT := system_ext
PRODUCT_SOONG_NAMESPACES += hardware/qcom-caf/wlan
PRODUCT_SOONG_NAMESPACES += hardware/qcom-caf/wlan/qcwcn
PRODUCT_SOONG_NAMESPACES += hardware/qcom-caf/sm8750

# Stock vendor prebuilts own these install paths; retain source variants for linking.
SOONG_CONFIG_NAMESPACES += froggerpro_stock
SOONG_CONFIG_froggerpro_stock += source_libraries
SOONG_CONFIG_froggerpro_stock_source_libraries := \
    libvmmem \
    libalsautils \
    libalsautilsv2 \
    libandroid_runtime_lazy \
    libar-acdb \
    libar-gpr \
    libar-gsl \
    libar-pal \
    libats \
    libaudio_aidl_conversion_common_ndk \
    libaudioaidlcommon \
    libaudiochargerlistener \
    libbatterylistener \
    libbluetooth_audio_session \
    libbluetooth_audio_session_aidl \
    libbundleaidl \
    libcamera2ndk_vendor \
    libcodec2_aidl \
    libcodec2_hal_common \
    libcppbor_external \
    libcustomva_intf \
    libdisplayconfig.qti \
    libdisplaydebug \
    libdownmixaidl \
    libdrmutils \
    libdynamicsprocessingaidl \
    libfilefinder \
    libflatbuffers-cpp \
    libfmpal \
    libgpu_tonemapper \
    libhfp_pal \
    libhistogram \
    libhotword_intf \
    libipanat \
    libloudnessenhanceraidl \
    liblx-ar_util \
    liblx-osal \
    libmapperutils \
    libmediautils_vendor \
    libpalclient \
    libpaleventnotifier \
    libpalipcservice \
    libpsi \
    libqcompostprocbundle \
    libqcomvisualizer \
    libqcomvoiceprocessing \
    libqti_vndfwk_detect \
    libreverbaidl \
    libsdedrm \
    libsdmclient \
    libsdmcore \
    libsdmdal \
    libsdmutils \
    libsndcardparser \
    libsoft_attestation_cert \
    libtinyalsav2 \
    libvibratorutils \
    libvisualizeraidl \
    libvndfwk_detect_jni.qti \
    libvolumelistener \
    libvui_intf \
    libwifi-hal-ctrl \
    libwifi-hal-qcom \
    qti-audio-types-aidl-V1-ndk \
    vendor.display.config@1.0 \
    vendor.display.config@1.1 \
    vendor.display.config@1.10 \
    vendor.display.config@1.11 \
    vendor.display.config@1.2 \
    vendor.display.config@1.3 \
    vendor.display.config@1.4 \
    vendor.display.config@1.5 \
    vendor.display.config@1.6 \
    vendor.display.config@1.7 \
    vendor.display.config@1.8 \
    vendor.display.config@1.9 \
    vendor.display.config@2.0 \
    vendor.qti.hardware.bluetooth.audio-V1-ndk \
    vendor.qti.hardware.bluetooth_audio@2.0 \
    vendor.qti.hardware.bluetooth_audio@2.1 \
    vendor.qti.hardware.camera.aon-V1-ndk \
    vendor.qti.hardware.camera.aon-V2-ndk \
    vendor.qti.hardware.camera.offlinecamera-V1-ndk \
    vendor.qti.hardware.camera.offlinecamera-V2-ndk \
    vendor.qti.hardware.display.allocator@1.0 \
    vendor.qti.hardware.display.allocator@3.0 \
    vendor.qti.hardware.display.allocator@4.0 \
    vendor.qti.hardware.display.composer@1.0 \
    vendor.qti.hardware.display.composer@2.0 \
    vendor.qti.hardware.display.mapper@1.0 \
    vendor.qti.hardware.display.mapper@1.1 \
    vendor.qti.hardware.display.mapper@2.0 \
    vendor.qti.hardware.display.mapper@3.0 \
    vendor.qti.hardware.display.mapper@4.0 \
    vendor.qti.hardware.display.mapperextensions@1.0 \
    vendor.qti.hardware.display.mapperextensions@1.1 \
    vendor.qti.hardware.display.mapperextensions@1.2 \
    vendor.qti.hardware.display.mapperextensions@1.3 \
    vendor.qti.hardware.paleventnotifier-V2-ndk \
    vendor.qti.hardware.perf@2.0 \
    vendor.qti.hardware.perf@2.1 \
    vendor.qti.hardware.perf@2.2 \
    vendor.qti.hardware.qspa-V1-ndk \
    vendor.qti.hardware.servicetracker@1.0 \
    vendor.qti.hardware.servicetracker@1.1 \
    vendor.qti.hardware.servicetrackeraidl-V1-ndk \
    vendor.qti.hardware.systemhelper@1.0 \
    vendor.qti.hardware.systemhelperaidl-V1-ndk \
    vendor.qti.hardware.wifi.supplicant-V1-ndk \
    wifi_legacy

# Preserve stock configuration files at destinations also provided by source modules.
# Evaluate after Android resolves the partition path placeholders in PRODUCT_COPY_FILES.
SOONG_CONFIG_froggerpro_stock += copy_destinations
SOONG_CONFIG_froggerpro_stock_copy_destinations = $(sort $(foreach stock_copy,\
    $(filter vendor/nothing/FroggerPro/proprietary/%,$(PRODUCT_COPY_FILES)),\
    $(word 2,$(subst :, ,$(stock_copy)))))

# Source-built kernel modules are installed by vendor/lineage/build/tasks/kernel.mk.
# Do not load modules from the stock 6.6.127 kernel into the rebuilt kernel.

# AVB partition split/rollback locations verified from the matched stock dump.
# Development signing for the generated images.
BOARD_AVB_ENABLE := true
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 0
BOARD_AVB_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_ALGORITHM := SHA256_RSA4096
BOARD_AVB_BOOT_KEY_PATH := $(BOARD_AVB_KEY_PATH)
BOARD_AVB_BOOT_ALGORITHM := $(BOARD_AVB_ALGORITHM)
BOARD_AVB_BOOT_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_BOOT_ROLLBACK_INDEX_LOCATION := 3
BOOT_OS_VERSION := 16
INIT_BOOT_OS_VERSION := 16
BOOT_SECURITY_PATCH := $(PLATFORM_SECURITY_PATCH)
BOARD_AVB_RECOVERY_KEY_PATH := $(BOARD_AVB_KEY_PATH)
BOARD_AVB_RECOVERY_ALGORITHM := $(BOARD_AVB_ALGORITHM)
BOARD_AVB_RECOVERY_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_RECOVERY_ROLLBACK_INDEX_LOCATION := 1
BOARD_AVB_VBMETA_SYSTEM := system system_ext product
BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := $(BOARD_AVB_KEY_PATH)
BOARD_AVB_VBMETA_SYSTEM_ALGORITHM := $(BOARD_AVB_ALGORITHM)
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX_LOCATION := 2
BOARD_AVB_VBMETA_VENDOR := vendor odm system_dlkm vendor_dlkm
BOARD_AVB_VBMETA_VENDOR_KEY_PATH := $(BOARD_AVB_KEY_PATH)
BOARD_AVB_VBMETA_VENDOR_ALGORITHM := $(BOARD_AVB_ALGORITHM)
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_VENDOR_ROLLBACK_INDEX_LOCATION := 4
AB_OTA_PARTITIONS += vbmeta vbmeta_system vbmeta_vendor

# Enable shared Qualcomm display include paths and kernel UAPI dependencies.
$(call soong_config_set,qtidisplay,default,true)

# Fields required by the selected Qualcomm display allocator implementation.
$(call soong_config_set,qtidisplay,gralloc_handle_has_reserved_size,true)
$(call soong_config_set,qtidisplay,gralloc_handle_has_custom_content_md_reserved_size,true)

$(call soong_config_set,qtidisplay,gralloc_handle_has_ubwcp_format,true)
$(call soong_config_set,qtidisplay,mapper_ext,true)
$(call soong_config_set,qtidisplay,composer_version,v3_3)
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += device/nothing/FroggerPro/framework_compatibility_matrix.xml
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += $(DEVICE_PATH)/vintf/nanoglyph-framework-matrix.xml

# Match the existing metadata filesystem and stock vendor identity.
BOARD_BOOTCONFIG += \
    androidboot.hardware=qcom \
    androidboot.load_modules_parallel=true \
    androidboot.usbcontroller=a600000.dwc3 \
    androidboot.product.vendor.sku=kera
VENDOR_SECURITY_PATCH := 2026-04-05

# Select the complete OEM audio core for this device while retaining source modules elsewhere.
FROGGER_USE_STOCK_AUDIO_CORE ?= true
SOONG_CONFIG_NAMESPACES += froggerpro
SOONG_CONFIG_froggerpro += stock_audio_core
SOONG_CONFIG_froggerpro_stock_audio_core := $(FROGGER_USE_STOCK_AUDIO_CORE)

# Keep display userspace ABI paired with the preserved proprietary extension.
$(call soong_config_set_bool,froggerpro,preserved_display,true)
