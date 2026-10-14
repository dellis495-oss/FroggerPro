# SPDX-License-Identifier: Apache-2.0

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)
$(call inherit-product, device/nothing/FroggerPro/device.mk)

PRODUCT_NAME := lineage_FroggerPro
PRODUCT_DEVICE := FroggerPro
PRODUCT_BRAND := Nothing
PRODUCT_MODEL := FroggerPro
PRODUCT_MANUFACTURER := Nothing

# Build the protected VM firmware image included in the A/B OTA partition list.
PRODUCT_BUILD_PVMFW_IMAGE := true

# Enable Lineage BoardConfig exports even when invoked without breakfast.
LINEAGE_BUILD := FroggerPro
