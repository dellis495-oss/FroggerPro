PRODUCT_PACKAGES += \
    FroggerProPrivacy \
    GlyphBridge \
    HieroGlyphFroggerPro \
    vendor.nukisystems.nanoglyph.matrix-service

PRODUCT_COPY_FILES += \
    device/nothing/FroggerPro/prebuilts/crdroid/privapp-permissions-FroggerProPrivacy.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/privapp-permissions-FroggerProPrivacy.xml \
    device/nothing/FroggerPro/prebuilts/crdroid/privapp_whitelist_org.nukisystems.hieroglyph.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp_whitelist_org.nukisystems.hieroglyph.xml \
    device/nothing/FroggerPro/prebuilts/crdroid/whitelist_org.nukisystems.hieroglyph.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/sysconfig/whitelist_org.nukisystems.hieroglyph.xml

PRODUCT_PACKAGES += android.hardware.biometrics.face-service.noth
PRODUCT_COPY_FILES += \
    device/nothing/FroggerPro/prebuilts/crdroid/face/license.lic:$(TARGET_COPY_OUT_VENDOR)/etc/license.lic
