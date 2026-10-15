#
# Copyright 2014 The Android Open-Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Match the launch API level in stock C5.0-260902-1559 vendor/build.prop.
PRODUCT_SHIPPING_API_LEVEL := 36
# The stock vendor still depends on HIDL HALs past framework compatibility level 8.
PRODUCT_HIDL_ENABLED := true
$(call inherit-product, device/nothing/FroggerPro/glyph.mk)

# Run the stock SoC detection before vendor HALs consume the QCV properties.
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/init/init.qti.qcv.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qti.qcv.sh
PRODUCT_VENDOR_PROPERTIES += ro.vendor.init_dev_config.path=/vendor/bin/init.qti.qcv.sh

# Keep early userspace diagnostics enabled by default for bring-up.
FROGGER_INIT_DIAGNOSTICS ?= true
ifeq ($(FROGGER_INIT_DIAGNOSTICS),true)
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/init/init.frogger-diagnostics.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.frogger-diagnostics.rc
endif

# Temporary diagnostic authentication uses the branch-provided adb_keys module.
ifeq ($(FROGGER_INIT_DIAGNOSTICS),true)
PRODUCT_ADB_KEYS := $(LOCAL_PATH)/prebuilts/adb_keys.pub
endif

# Preserve the verified on-device navigation and SystemUI padding overlays.
PRODUCT_PACKAGES += \
    FroggerFrameworkOverlay \
    FroggerSystemUIOverlay

# Do not install libcamera_metadata to vendor; it is an LLNDK library provided by system
# and duplicating it in vendor causes linkerconfig to crash at boot with duplicate provider error.
# PRODUCT_PACKAGES += frogger_camera_metadata_vendor

# Dynamic partition images are sized from their contents.
PRODUCT_USE_DYNAMIC_PARTITIONS := true
PRODUCT_USE_DYNAMIC_PARTITION_SIZE := true

$(call inherit-product, frameworks/native/build/phone-xhdpi-6144-dalvik-heap.mk)

PRODUCT_VENDOR_PROPERTIES += \
    ro.sf.lcd_density=480 \
    debug.renderengine.backend=skiavkthreaded

# Default to unsecure ADB on userdebug for non-interactive diagnostics and developer access
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    ro.adb.secure=0 \
    persist.sys.usb.config=adb


# Retain the working SKU audio policy and HAL registration configuration.
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/audio,$(TARGET_COPY_OUT_VENDOR)/etc/audio)
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/audio-root,$(TARGET_COPY_OUT_VENDOR)/etc)
# The physical KERA SKU must find the device's preserved audio effects config.
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/audio/sku_sun,$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_kera)

# Recovery imports this script through androidboot.hardware=qcom.
PRODUCT_COPY_FILES += \
    device/nothing/FroggerPro/recovery/init.recovery.qcom.rc:root/init.recovery.qcom.rc \
    device/nothing/FroggerPro/init/init.qcom.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/hw/init.qcom.rc \
    device/nothing/FroggerPro/init/init.vendor.wlan.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.vendor.wlan.rc \
    device/nothing/FroggerPro/init/ueventd.qcom.rc:$(TARGET_COPY_OUT_VENDOR)/etc/ueventd.rc \
    device/nothing/FroggerPro/init/init.qti.keymaster.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qti.keymaster.sh \
    device/nothing/FroggerPro/init/firmware-mountpoint:$(TARGET_COPY_OUT_VENDOR)/firmware_mnt/.placeholder \
    device/nothing/FroggerPro/init/firmware-mountpoint:$(TARGET_COPY_OUT_VENDOR)/bt_firmware/.placeholder \
    device/nothing/FroggerPro/init/firmware-mountpoint:$(TARGET_COPY_OUT_VENDOR)/dsp/.placeholder \
    device/nothing/FroggerPro/init/init.froggerpro.usb.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/hw/init.froggerpro.usb.rc \
    device/nothing/FroggerPro/fstab.qcom:$(TARGET_COPY_OUT_VENDOR)/etc/fstab.qcom \
    device/nothing/FroggerPro/fstab.qcom:$(TARGET_COPY_OUT_VENDOR)/etc/fstab.default \
    device/nothing/FroggerPro/fstab.qcom:$(TARGET_COPY_OUT_VENDOR)/etc/fstab.emmc \
    device/nothing/FroggerPro/fstab.qcom:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/first_stage_ramdisk/fstab.qcom \
    device/nothing/FroggerPro/fstab.qcom:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/first_stage_ramdisk/fstab.default \
    device/nothing/FroggerPro/fstab.qcom:$(TARGET_COPY_OUT_VENDOR_RAMDISK)/first_stage_ramdisk/fstab.emmc

$(call inherit-product, vendor/nothing/FroggerPro/FroggerPro-vendor.mk)

# Runtime providers for the non-installable stock AIDL link modules.
# Product selection avoids a required edge that propagates mixed AIDL versions.
PRODUCT_PACKAGES += \
    vendor.qti.hardware.display.config-V5-ndk.vendor \
    android.hardware.graphics.allocator-V1-ndk.vendor \
    android.media.audio.common.types-V3-ndk.vendor \
    android.hardware.audio.core-V2-ndk.vendor \
    android.hardware.audio.effect-V2-ndk.vendor \
    android.hardware.audio.common-V3-ndk.vendor \
    android.hardware.audio.core.sounddose-V2-ndk.vendor

PRODUCT_PACKAGES += \
    android.hardware.graphics.common-V5-ndk.vendor \
    android.hardware.security.sharedsecret-V2-ndk.vendor

# Fastbootd must be present in the recovery image.  Without these modules,
# dynamic-partition fastbootd boots but has no USB fastboot transport.
PRODUCT_PACKAGES += \
    fastbootd \
    android.hardware.fastboot-service.example_recovery \
    android.hardware.boot-service.default_recovery

# QSEE's vendor HAL cannot load the system_ext copy across linker namespaces.
PRODUCT_PACKAGES += vendor.qti.hardware.qseecom-V1-ndk.vendor

# Export the source display AIDL runtime modules to Make.
PRODUCT_SOONG_NAMESPACES += vendor/qcom/opensource/commonsys-intf/display
PRODUCT_SOONG_NAMESPACES += vendor/qcom/opensource/audio-hal/st-hal-ar
$(call soong_config_set,qtiaudio,headers_namespace,hardware/qcom-caf/sm8750)
$(call soong_config_set,qtiaudio,libarpal_namespace,hardware/qcom-caf/sm8750)

# Source replacements for the stock HALs excluded from proprietary-files.txt.
PRODUCT_PACKAGES += \
    android.hardware.bluetooth.audio-impl \
    android.hardware.drm-service.clearkey \
    android.hardware.health-service.qti \
    android.hardware.health-service.qti_recovery \
    android.hardware.sensors-service.nothing-multihal \
    android.hardware.usb-service.qti \
    android.hardware.usb.gadget-service.qti \
    android.hardware.wifi-service \
    android.hardware.wifi-service.xml \
    android.hardware.wifi.hostapd.xml \
    android.hardware.wifi.supplicant.xml \
    audiohalservice.qti \
    libagmipcservice \
    libpalipcservice \
    libsoundtriggerhal.qti \
    libbundleaidl \
    libreverbaidl \
    libdownmixaidl \
    libloudnessenhanceraidl \
    libdynamicsprocessingaidl \
    libvisualizeraidl \
    libqcomvisualizer \
    libqcompostprocbundle \
    libqcomvoiceprocessing \
    libvolumelistener \
    libquasar \
    libAACeffect_NTaidl \
    hostapd \
    libaudiocorehal.qti \
    libaudioeffecthal.qti \
    mapper.qti \
    sensors.dynamic_sensor_hal \
    vendor.qti.hardware.display.allocator-service \
    vendor.qti.hardware.display.composer-service \
    vendor.qti.hardware.display.demura-service \
    vendor.qti.hardware.memtrack-service \
    vendor.qti.hardware.vibrator.service \
    wpa_supplicant \
    update_engine \
    update_engine_sideload \
    snapuserd \
    snapuserd_ramdisk \
    toolbox_ramdisk \
    update_verifier

# Qualcomm display services still publish legacy vendor Binder interfaces.
PRODUCT_PACKAGES += vndservicemanager hwservicemanager
PRODUCT_SYSTEM_PROPERTIES += hwservicemanager.always_sets_disabled=false

# Enable Virtual A/B OTA
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/vabc_features.mk)

# Required by the vendor display concurrency manager.
PRODUCT_PACKAGES += vendor.qti.hardware.display.snapalloc-impl

# Explicitly install the audio declarations required by the core HAL.
PRODUCT_PACKAGES += manifest_audiocorehal_default.xml

# Stock display format, alignment, and panel calibration tables.
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/display,$(TARGET_COPY_OUT_VENDOR)/etc/display)
PRODUCT_VENDOR_PROPERTIES += vendor.gralloc.enable_snapalloc=1

# Required default audio HAL loaded by audiohalservice.qti.
PRODUCT_PACKAGES += libaudiocorehal.default

# Qualcomm telephony utility classes required by qcrilmsgtunnel (Registrant).
PRODUCT_PACKAGES += \
    qti-telephony-utils \
    qti-telephony-utils-prd

# Private stock XMLDocument ABI for the proprietary power parser.
PRODUCT_PACKAGES += libtinyxml2_nothing

ifeq ($(FROGGER_INIT_DIAGNOSTICS),true)
PRODUCT_COPY_FILES += device/nothing/FroggerPro/init/frogger-boot-state.sh:$(TARGET_COPY_OUT_VENDOR)/bin/frogger-boot-state.sh
endif

# PAL virtual card 100 uses the AGM tinyalsa plugins and sound-card parser.
PRODUCT_PACKAGES += \
    libagm_mixer_plugin \
    libagm_pcm_plugin \
    libagm_compress_plugin \
    libsndcardparser

# Complete PAL runtime plugin set referenced by the device resource-manager XML.
PRODUCT_PACKAGES += \
    libpaleventnotifier \
    lib_bt_bundle \
    lib_bt_aptx \
    lib_bt_ble \
    libhotword_intf \
    libcustomva_intf

# Optional Bluetooth SW registration uses this branch's current AIDL implementation.
PRODUCT_PACKAGES += android.hardware.bluetooth.audio_sw
