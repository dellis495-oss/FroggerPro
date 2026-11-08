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
# Match the real stock hardware feature declarations; these gate framework services.
# KeyMint already owns hardware_keystore.xml through its Soong module.
PRODUCT_COPY_FILES += $(filter-out %/android.hardware.hardware_keystore.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.hardware_keystore.xml,$(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/hardware-features,$(TARGET_COPY_OUT_VENDOR)/etc/permissions))
PRODUCT_PACKAGES += FroggerEuiccGoogle
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.telephony.euicc.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/android.hardware.telephony.euicc.xml \
    $(LOCAL_PATH)/configs/permissions/privapp-permissions-frogger-euicc.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/privapp-permissions-frogger-euicc.xml

# Privileged permission allowlists must share the APKs' system_ext partition.
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/permissions/privapp-permissions-frogger-telephony.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-frogger-telephony.xml
$(call inherit-product, device/nothing/FroggerPro/glyph.mk)
$(call inherit-product, device/nothing/FroggerPro/crdroid-settings.mk)

# Run the stock SoC detection before vendor HALs consume the QCV properties.
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/init/init.qti.qcv.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qti.qcv.sh
PRODUCT_VENDOR_PROPERTIES += ro.vendor.init_dev_config.path=/vendor/bin/init.qti.qcv.sh

# Enable early userspace diagnostics only when explicitly requested.
FROGGER_INIT_DIAGNOSTICS ?= false
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
    FroggerLineageOverlay \
    FroggerSystemUIOverlay \
    FroggerSettingsOverlay

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

# Inherit the platform's authenticated ADB and USB defaults. Production user
# builds already emit ro.adb.secure=1; a device override conflicts with it.


# Retain the working SKU audio policy and HAL registration configuration.
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/audio,$(TARGET_COPY_OUT_VENDOR)/etc/audio)
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/audio-root,$(TARGET_COPY_OUT_VENDOR)/etc)
# ConfigManager uses audio_get_configuration_paths(), which searches /vendor/etc
# and the active SKU directory, but never the generic /vendor/etc/audio directory.
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/audio/vendor_audio_interfaces.xml:$(TARGET_COPY_OUT_VENDOR)/etc/vendor_audio_interfaces.xml
# The physical KERA SKU must find the device's preserved audio effects config.
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/audio/sku_sun,$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_kera)

# Recovery imports this script through androidboot.hardware=qcom.
PRODUCT_COPY_FILES += \
    device/nothing/FroggerPro/recovery/init.recovery.qcom.rc:root/init.recovery.qcom.rc \
    device/nothing/FroggerPro/init/init.qcom.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/hw/init.qcom.rc \
    device/nothing/FroggerPro/init/init.froggerpro.glyph.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.froggerpro.glyph.rc \
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
    frogger.boot-control.recovery

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
    android.hardware.sensors-service.multihal \
    android.hardware.usb-service.qti \
    android.hardware.usb.gadget-service.qti \
    usb_compositions.conf \
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
    vendor.qti.hardware.vibrator.service.nothing \
    wpa_supplicant \
    wpa_supplicant.conf \
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
PRODUCT_VENDOR_PROPERTIES += vendor.usb.use_ffs_mtp=1

# Required default audio HAL loaded by audiohalservice.qti.
PRODUCT_PACKAGES += libaudiocorehal.default

# Qualcomm telephony utility classes required by qcrilmsgtunnel (Registrant).
PRODUCT_PACKAGES += \
    qti-telephony-utils \
    qti-telephony-utils-prd \
    qti_telephony_utils.xml \
    qti_telephony_utils_prd.xml \
    qti-telephony-hidl-wrapper \
    qti-telephony-hidl-wrapper-prd \
    qti_telephony_hidl_wrapper.xml \
    qti_telephony_hidl_wrapper_prd.xml \
    ims-ext-common \
    ims_ext_common.xml

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

# Stock QCA6750 configuration and firmware lookup links for the KERA WLAN driver.
# qcwcn already owns wpa_supplicant.conf through its Soong module.
PRODUCT_COPY_FILES += $(filter-out %/wpa_supplicant.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/wpa_supplicant.conf,$(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/wifi,$(TARGET_COPY_OUT_VENDOR)/etc/wifi))
PRODUCT_PACKAGES += frogger_qca6750_config_link frogger_qca6750_mac_link

# Match the stock dual-SIM default before the radio init triggers run.
PRODUCT_VENDOR_PROPERTIES += persist.radio.multisim.config=dsds
# Keep LTE and NR enabled on both slots after a clean install.
PRODUCT_SYSTEM_PROPERTIES += ro.telephony.default_network=26,26

# Active stock AIDL radio declarations; nested qspa fragments are not a substitute.
# Stock standard AIDL radio VINTF fragments
PRODUCT_PACKAGES += \
    frogger_radio_vintf_config \
    frogger_radio_vintf_data \
    frogger_radio_vintf_messaging \
    frogger_radio_vintf_modem \
    frogger_radio_vintf_network \
    frogger_radio_vintf_sap \
    frogger_radio_vintf_sim \
    frogger_radio_vintf_voice

# Stock classic Bluetooth profiles; absent properties default to disabled.
PRODUCT_VENDOR_PROPERTIES += \
    bluetooth.profile.a2dp.source.enabled=true \
    bluetooth.profile.avrcp.target.enabled=true \
    bluetooth.profile.avrcp.controller.enabled=true \
    bluetooth.profile.hfp.ag.enabled=true \
    bluetooth.profile.gatt.enabled=true \
    bluetooth.profile.hid.host.enabled=true \
    bluetooth.profile.hid.device.enabled=true \
    bluetooth.profile.map.server.enabled=true \
    bluetooth.profile.opp.enabled=true \
    bluetooth.profile.pbap.server.enabled=true \
    bluetooth.profile.bas.client.enabled=true
# Keep the stock vibrator service paired with its OEM implementation libraries.
$(call soong_config_set_bool,qti_vibrator,use_prebuilt_service,true)

# BlissLauncher requests the platform privileged wallpaper read permission.
PRODUCT_COPY_FILES += \
    device/nothing/FroggerPro/configs/permissions/privapp-permissions-frogger-launcher.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-frogger-launcher.xml

# Stock vendor init scripts, display/media boot configuration, and public libraries.
PRODUCT_PACKAGES += \
    init.qti.display_boot.rc \
    init.qti.display_boot.sh

PRODUCT_COPY_FILES +=     device/nothing/FroggerPro/init/init.qcom.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qcom.sh     device/nothing/FroggerPro/init/init.class_main.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.class_main.sh     device/nothing/FroggerPro/init/init.qcom.early_boot.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qcom.early_boot.sh     device/nothing/FroggerPro/init/init.qcom.post_boot.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qcom.post_boot.sh     device/nothing/FroggerPro/init/init.qti.media.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qti.media.sh     device/nothing/FroggerPro/init/init.qti.media.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.qti.media.rc     device/nothing/FroggerPro/init/system_dlkm_modprobe.sh:$(TARGET_COPY_OUT_VENDOR)/bin/system_dlkm_modprobe.sh     device/nothing/FroggerPro/init/vendor_modprobe.sh:$(TARGET_COPY_OUT_VENDOR)/bin/vendor_modprobe.sh     device/nothing/FroggerPro/init/init.qti.kernel.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qti.kernel.sh     device/nothing/FroggerPro/init/init.kernel.post_boot.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.kernel.post_boot.sh     device/nothing/FroggerPro/init/init.kernel.post_boot-kera.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.kernel.post_boot-kera.sh     device/nothing/FroggerPro/init/init.kernel.post_boot-kera_default_3_4_1.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.kernel.post_boot-kera_default_3_4_1.sh     device/nothing/FroggerPro/init/init.kernel.post_boot-kera_2_3_1.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.kernel.post_boot-kera_2_3_1.sh     device/nothing/FroggerPro/init/init.kernel.post_boot-kera_2_4_0.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.kernel.post_boot-kera_2_4_0.sh     device/nothing/FroggerPro/init/init.kernel.post_boot-kera_3_2_1.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.kernel.post_boot-kera_3_2_1.sh     device/nothing/FroggerPro/init/init.kernel.init_boot-memory.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.kernel.init_boot-memory.sh     device/nothing/FroggerPro/init/init.kernel.post_boot-memory.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.kernel.post_boot-memory.sh     device/nothing/FroggerPro/init/init.qti.write.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.qti.write.sh     device/nothing/FroggerPro/configs/public.libraries.txt:$(TARGET_COPY_OUT_VENDOR)/etc/public.libraries.txt     device/nothing/FroggerPro/configs/gnss_antenna_info.conf:$(TARGET_COPY_OUT_VENDOR)/etc/gnss_antenna_info.conf

PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/media,$(TARGET_COPY_OUT_VENDOR)/etc)
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/displayconfig,$(TARGET_COPY_OUT_VENDOR)/etc/displayconfig)
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/lvacfs_params,$(TARGET_COPY_OUT_VENDOR)/etc/lvacfs_params)
PRODUCT_COPY_FILES += $(call find-copy-subdir-files,*,device/nothing/FroggerPro/configs/camera_filter,$(TARGET_COPY_OUT_VENDOR)/etc/camera/filter)

# Stock RFS, Adreno, and WLAN OTA symlinks.
$(call inherit-product, hardware/qcom-caf/common/common.mk)
PRODUCT_PACKAGES += \
    frogger_symlink_firmware_wlanmdsp_otaupdate \
    frogger_symlink_lib64_libEGL_adreno_so \
    frogger_symlink_lib64_libGLESv2_adreno_so \
    frogger_symlink_lib64_libq3dtools_adreno_so
