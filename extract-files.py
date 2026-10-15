#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-License-Identifier: Apache-2.0
#

from pathlib import Path
import re

from extract_utils.fixups_blob import blob_fixup, blob_fixups_user_type
from extract_utils.fixups_lib import (
    lib_fixups_user_type,
    lib_fixup_remove_proto_version_suffix,
    lib_fixup_vendorcompat,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

# Preserve the implicit stock root identity explicitly for init verification.
blob_fixups: blob_fixups_user_type = {
    # poweropt modules embed XMLDocument with the stock layout, incompatible with v11.
    (
        'vendor/bin/poweropt-service',
        'vendor/lib64/libpowercore.so',
        'vendor/lib64/libcamerapoweroptfeature.so',
        'vendor/lib64/libgamepoweroptfeature.so',
        'vendor/lib64/liboffscreenpoweroptfeature.so',
        'vendor/lib64/libaodoptfeature.so',
        'vendor/lib64/libpsmoptfeature.so',
        'vendor/lib64/libvideooptfeature.so',
        'vendor/lib64/libstandbyfeature.so',
        'vendor/lib64/liblearningmodule.so',
        'vendor/lib64/libpowercallback.so',
    ): blob_fixup().replace_needed(
        'libtinyxml2.so', 'libtinyxml2_nothing.so',
    ),
    # Keep Thales on its stock KeyMint V3 utility without replacing source V4.
    ('vendor/bin/hw/android.hardware.security.keymint-service.strongbox-thales',
     'vendor/lib64/libjc_keymint-thales.so'): blob_fixup().replace_needed(
        'lib_android_keymaster_keymint_utils.so',
        'lib_android_keymaster_keymint_utils_nothing.so',
    ),
    'vendor/etc/init/qms.rc': blob_fixup().regex_replace(
        r'(service vendor\.qms /vendor/bin/qms\n)(?!    user root\n)',
        r'\1    user root\n',
    ),
    'vendor/etc/init/vendor.dpmd.rc': blob_fixup().regex_replace(
        r'(service vendor\.dpmd /vendor/bin/vendor\.dpmd\n)(?!    user root\n)',
        r'\1    user root\n',
    ),
}


def lib_fixup_nothing(lib: str, partition: str) -> str:
    return f'{lib}_nothing' if partition in ('vendor', 'odm') else lib


link_only_aidl = (
    'android.hardware.graphics.common-V5-ndk',
    'vendor.qti.hardware.display.config-V5-ndk',
    'android.hardware.graphics.allocator-V1-ndk',
    'android.media.audio.common.types-V3-ndk',
    'android.hardware.audio.core-V2-ndk',
    'android.hardware.audio.effect-V2-ndk',
    'android.hardware.audio.common-V3-ndk',
    'android.hardware.audio.core.sounddose-V2-ndk',
    'android.hardware.security.sharedsecret-V2-ndk',
)

# Route blob dependencies to the renamed vendor modules; ELF filenames stay intact.
lib_fixups: lib_fixups_user_type = {
    'libprotobuf-cpp-full-6.33.5': lib_fixup_remove_proto_version_suffix,
    ('libprotobuf-cpp-full-21.12', 'libprotobuf-cpp-lite-21.12'): lib_fixup_vendorcompat,
    link_only_aidl: lib_fixup_nothing,
}

module = ExtractUtilsModule(
    'FroggerPro',
    'nothing',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=[
        'hardware/qcom-caf/sm8750',
        'hardware/qcom-caf/wlan',
        'hardware/qcom-caf/wlan/qcwcn',
        'vendor/qcom/opensource/commonsys-intf/display',
    ],
)

# Keep the entire imported runtime set in extraction, not only in hand-edited
# generated vendor makefiles. Source-built PAL/AGM plugins stay in device.mk.
required_runtime_blobs = (
    'vendor/bin/pd-mapper',
    'vendor/bin/pm-service',
    'vendor/bin/pm-proxy',
    'vendor/bin/audioadsprpcd',
    'vendor/bin/hw/android.hardware.sensors-service.nothing-multihal',
    'vendor/etc/init/vendor.qti.audio_adsprpc-service.rc',
    'vendor/etc/init/android.hardware.sensors-service.nothing-multihal.rc',
    'vendor/etc/vintf/manifest/android.hardware.sensors.nothing-multihal.xml',
    'vendor/lib64/soundfx/libquasar.so',
    'vendor/lib64/soundfx/libAACeffect_NTaidl.so',
    'vendor/lib64/libtinyxml2_nothing.so',
)


def validate_runtime_blob_list():
    file_list = Path(__file__).with_name('proprietary-files.txt')
    destinations = set()
    for line in file_list.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        path = line.lstrip('-').split(';', 1)[0].split('|', 1)[0]
        destinations.add(path.split(':', 1)[-1])
    missing = sorted(set(required_runtime_blobs) - destinations)
    if missing:
        raise RuntimeError('Runtime blobs missing from extraction list: ' + ', '.join(missing))


if __name__ == '__main__':
    validate_runtime_blob_list()
    utils = ExtractUtils.device(module)
    utils.run()

    # Keep old AIDL prebuilts as blob link dependencies without installing a
    # second copy over the source-built library with the same SONAME.
    vendor_bp = Path(__file__).resolve().parents[3] / 'vendor/nothing/FroggerPro/Android.bp'
    bp_text = vendor_bp.read_text()
    for source_name in link_only_aidl:
        name = source_name + '_nothing'
        pattern = r'(name: "' + re.escape(name) + r'",)'
        bp_text, count = re.subn(pattern, r'\1\n    installable: false,', bp_text)
        if count != 1:
            raise RuntimeError(f'Expected one link-only prebuilt: {name}')
    # Preserve the existing bring-up fixes across makefile regeneration.
    # These camera plugins resolve symbols from their loading process.
    for name in ('libVoiceSdk', 'libmorpho_RapidEffect'):
        pattern = r'(name: "' + re.escape(name) + r'",)'
        bp_text, count = re.subn(pattern, r'\1\n    allow_undefined_symbols: true,', bp_text)
        if count != 1:
            raise RuntimeError(f'Expected one camera plugin: {name}')

    # Existing providers needed by symbols not recorded as DT_NEEDED entries.
    for name, dependency in (
        ('vendor.qti.diaghal-V1-ndk', 'libwifi-hal-qcom'),
        ('libntcamskia', 'libnativewindow'),
    ):
        pattern = (r'(name: "' + re.escape(name) +
                   r'",.*?shared_libs: \[)(.*?)(\n            \],)')
        bp_text, count = re.subn(
            pattern,
            lambda match: match[1] + match[2] +
                f'\n                "{dependency}",' + match[3],
            bp_text,
            flags=re.DOTALL,
        )
        if count != 1:
            raise RuntimeError(f'Expected one dependency list: {name}')

    # The vendor QSEE HAL needs this AIDL library in its own linker namespace.
    pattern = r'(name: "vendor\.qti\.hardware\.qseecom-V1-ndk",)'
    bp_text, count = re.subn(pattern, r'\1\n    vendor_available: true,', bp_text)
    if count != 1:
        raise RuntimeError('Expected one QSEE AIDL library')

    vendor_bp.write_text(bp_text)

    # Non-installable Soong link modules are not exported as Make packages.
    vendor_mk = vendor_bp.with_name('FroggerPro-vendor.mk')
    mk_lines = vendor_mk.read_text().splitlines()
    link_names = {name + '_nothing' for name in link_only_aidl}
    vendor_mk.write_text('\n'.join(
        line for line in mk_lines
        if line.strip().removesuffix('\\').strip() not in link_names
    ) + '\n')
