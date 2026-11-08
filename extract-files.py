#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-License-Identifier: Apache-2.0
#

from pathlib import Path
import hashlib
import json
import re

import sqlite3

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
def patch_qcril_poweron(_ctx, _file, file_path, **_kwargs):
    with sqlite3.connect(file_path) as db:
        updated = db.execute(
            "UPDATE qcril_properties_table SET def_val=?, value=? WHERE property=?",
            ("0", "0", "persist.vendor.radio.poweron_opt"),
        )
        if updated.rowcount != 1:
            raise ValueError("Expected one QCRIL radio power setting")


blob_fixups: blob_fixups_user_type = {
    'vendor/etc/qcril_database/qcrilNr.db': blob_fixup().call(patch_qcril_poweron, need_tmp_dir=False),
    # QCRIL calls getppid and uname during delayed radio initialization.
    'vendor/etc/seccomp_policy/qcrilnr@2.0.policy': blob_fixup().add_line_if_missing('getppid: 1').add_line_if_missing('uname: 1'),
    # Restore the working hardware key service discovery contract.
    'vendor/etc/init/android.hardware.security.keymint-service-qti.rc': blob_fixup().regex_replace(
        '(service vendor\\.keymint-qti /vendor/bin/hw/android\\.hardware\\.security\\.keymint-service-qti\\n)(?!    interface aidl)',
        '\\1    interface aidl android.hardware.security.keymint.IKeyMintDevice/default\n    interface aidl android.hardware.security.keymint.IRemotelyProvisionedComponent/default\n    interface aidl android.hardware.security.secureclock.ISecureClock/default\n    interface aidl android.hardware.security.sharedsecret.ISharedSecret/default\n',
    ),
    # The Goodix HAL runs as system and opens these controls read/write.
    'vendor/etc/init/vendor.noth.fingerprint.goodix.config.rc': blob_fixup().regex_replace(
        r'\A(?!# FroggerPro fingerprint controls\n)',
        '# FroggerPro fingerprint controls\non post-fs-data\n    chown system system /proc/touchpanel/fod_mode\n    chmod 0660 /proc/touchpanel/fod_mode\n    chown system system /sys/panel_feature/fp_status\n    chmod 0660 /sys/panel_feature/fp_status\n\n',
    ).regex_replace(
        r'(?m)^    mkdir /data/vendor/fpdump/[ \t]*$',
        '    mkdir /data/vendor/fpdump 0700 system system',
    ).regex_replace(
        r'(?m)^    chmod 0777 /data/vendor/fpdump/[ \t]*$',
        '    chown system system /data/vendor/fpdump\n    chmod 0700 /data/vendor/fpdump',
    ),
    'vendor/etc/init/android.hardware.security.keymint-service.strongbox-thales.rc': blob_fixup().regex_replace(
        r'(?m)^    disabled\n', '',
    ).regex_replace(
        r'(service vendor\.keymint-strongbox [^\n]+\n)(?!    disabled\n)',
        r'\1    disabled\n',
    ),
    # ROW has no embedded-SE OMAPI provider (same selection as the working reference).
    # Keep optional Thales blobs for future SKU bring-up; do not start an unavailable HAL.
    'vendor/etc/init/android.hardware.weaver-service.thales.rc': blob_fixup().regex_replace(
        r'(?m)^    disabled\n', '',
    ).regex_replace(
        r'(service weaver_hal_service [^\n]+\n)(?!    disabled\n)',
        r'\1    disabled\n',
    ),
    # Keep the stock voice SDK on its matched private TensorFlow ABI.
    ('vendor/lib64/libVoiceSdk.so',
     'vendor/lib64/libcapiv2uvvendor.so',
     'vendor/lib64/liblistensoundmodel2vendor.so'): blob_fixup().replace_needed(
        'libtensorflowlite_c.so', 'libtensorflowlite_c_nothing.so',
    ),
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

class FroggerProModule(ExtractUtilsModule):
    """Preserve branch ABI/link ownership rules during every regeneration."""
    def write_makefiles(self, legacy, extract_factory):
        super().write_makefiles(legacy, extract_factory)
        rules = json.loads((Path(self.device_path) / 'configs/vendor-build-overrides.json').read_text())
        bp_path = Path(self.vendor_path) / 'Android.bp'
        seen = set()
        def apply(match):
            block = match.group(0)
            name = re.search(r'name: "([^"]+)"', block).group(1)
            seen.add(name)
            for key, value in rules['properties'].get(name, {}).items():
                line = f'    {key}: {str(value).lower()},'
                pattern = r'^    ' + re.escape(key) + r': (?:true|false),$'
                if re.search(pattern, block, re.M):
                    block = re.sub(pattern, line, block, flags=re.M)
                else:
                    block = block.replace(f'    name: "{name}",', f'    name: "{name}",\n' + line, 1)
            for old, new in rules['shared_libs_replace'].get(name, {}).items():
                block = block.replace('"' + old + '"', '"' + new + '"')
            for dependency in rules['shared_libs_add'].get(name, []):
                # These modules are 64-bit only. Never disable ELF validation.
                if '"' + dependency + '"' not in block:
                    block, count = re.subn(r'(shared_libs: \[)', r'\1\n                "' + dependency + '",', block, count=1)
                    if count != 1:
                        raise RuntimeError('Missing shared_libs in ' + name)
            return block
        text = re.sub(r'^cc_prebuilt_\w+ \{\n.*?^}\n', apply, bp_path.read_text(), flags=re.M | re.S)
        required = set(rules['properties']) | set(rules['shared_libs_add']) | set(rules['shared_libs_replace'])
        if required - seen:
            raise RuntimeError('Missing vendor build override modules: ' + ', '.join(sorted(required - seen)))
        # Raw audio blobs are selected as canonical source-namespace prebuilts.
        # Keeping their filegroups here makes full extraction regenerate them too.
        audio = json.loads((Path(self.device_path) / 'configs/stock-audio-core.json').read_text())
        for name, entry in audio['libraries'].items():
            raw = Path(self.vendor_path) / 'proprietary' / entry['file']
            if not raw.is_file() or hashlib.sha256(raw.read_bytes()).hexdigest() != entry['sha256']:
                raise RuntimeError('Matched stock audio blob missing or changed: ' + entry['file'])
            group = 'frogger_stock_audio_' + name.replace('-', '_') + '_blob'
            text += ('\nfilegroup {\n    name: ' + json.dumps(group) + ',\n'
                     '    srcs: [' + json.dumps('proprietary/' + entry['file']) + '],\n'
                     '    visibility: ["//hardware/qcom-caf/sm8750:__subpackages__"],\n}\n')
        bp_path.write_text(text)
        mk_path = Path(self.vendor_path) / (self.device + '-vendor.mk')
        lines = mk_path.read_text().splitlines(True)
        excludes = set(rules['package_excludes'])
        mk_path.write_text(''.join(line for line in lines if line.strip().rstrip('\\').strip() not in excludes))


module = FroggerProModule(
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
# CamX selects sm7750 for SoC 659; sm8750 alone is insufficient.
required_runtime_blobs = (
    'vendor/lib64/hw/fingerprint.default.so',
    'vendor/lib64/libgf_hal.so',
    'vendor/lib64/libvendor.goodix.hardware.biometrics.fingerprint.so',
    'system_ext/framework/qcrilhook.jar',
    'system_ext/etc/permissions/qcrilhook.xml',
    'vendor/lib64/com.qti.settings.sm7750.so',
    'vendor/bin/pd-mapper',
    'vendor/bin/pm-service',
    'vendor/bin/pm-proxy',
    'vendor/bin/audioadsprpcd',
    'vendor/etc/init/vendor.qti.audio_adsprpc-service.rc',
    'vendor/lib64/soundfx/libquasar.so',
    'vendor/lib64/soundfx/libAACeffect_NTaidl.so',
    'vendor/lib64/libtinyxml2_nothing.so',
    'vendor/lib64/libtensorflowlite_c_nothing.so',
) + tuple(entry['file'] for entry in json.loads(
    Path(__file__).with_name('configs').joinpath('stock-audio-core.json').read_text()
)['libraries'].values())


def validate_runtime_blob_list():
    file_list = Path(__file__).with_name('proprietary-files.txt')
    destinations = set()
    for line in file_list.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        path = line.lstrip('-').split(';', 1)[0].split('|', 1)[0]
        destinations.add(path.split(':', 1)[-1])
    # Device-owned hardware configuration must survive vendor regeneration too.
    device_dir = Path(__file__).parent
    restored = json.loads((device_dir / 'configs/runtime-restoration-manifest.json').read_text())
    absent_configs = [name for name in restored['files'] if not (device_dir / name).is_file()]
    if absent_configs:
        raise RuntimeError('Restored runtime configs missing: ' + ', '.join(absent_configs))
    missing = sorted(set(required_runtime_blobs) - destinations)
    if missing:
        raise RuntimeError('Runtime blobs missing from extraction list: ' + ', '.join(missing))


if __name__ == '__main__':
    validate_runtime_blob_list()
    utils = ExtractUtils.device(module)
    utils.run()
