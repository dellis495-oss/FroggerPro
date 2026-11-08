#!/usr/bin/env python3
"""Inspect the actual recovery ramdisk security policy and boot-control service."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


def audit(image, root, tmp):
    host = root / 'out/host/linux-x86/bin'
    unpacked = subprocess.check_output(
        ['python3', str(root / 'system/tools/mkbootimg/unpack_bootimg.py'),
         '--boot_img', str(image.resolve()), '--out', str(tmp)], text=True)
    if re.search(r'androidboot\.selinux\s*=\s*"?permissive|androidboot\.frogger\.init_log\s*=\s*"?1', unpacked):
        raise ValueError('Recovery has permissive or diagnostic boot arguments')
    # default.prop is a symlink to prop.default in this branch's recovery.
    wanted = {'sepolicy', 'system_ext_file_contexts', 'prop.default',
              'system/etc/init/boot-control.qti.rc',
              'system/bin/hw/android.hardware.boot-service.qti.recovery'}
    files = {}
    for ramdisk in tmp.glob('*ramdisk*'):
        if not ramdisk.is_file():
            continue
        data = ramdisk.read_bytes()
        if data.startswith(b'\x1f\x8b'):
            data = gzip.decompress(data)
        elif not data.startswith((b'070701', b'070702')):
            data = subprocess.check_output([str(host / 'lz4'), '-d', '-c', str(ramdisk)])
        position = 0
        while position + 110 <= len(data):
            if data[position:position + 6] not in (b'070701', b'070702'):
                raise ValueError('Invalid recovery CPIO header')
            fields = [int(data[position + 6 + i * 8:position + 14 + i * 8], 16)
                      for i in range(13)]
            name = data[position + 110:position + 110 + fields[11] - 1].decode()
            start = (position + 110 + fields[11] + 3) & ~3
            end = start + fields[6]
            if end > len(data):
                raise ValueError('Truncated recovery CPIO member')
            position = (end + 3) & ~3
            if name == 'TRAILER!!!':
                break
            if name.startswith('./'):
                name = name[2:]
            if name in wanted:
                if name in files:
                    raise ValueError('Duplicate recovery security member: ' + name)
                files[name] = (fields[1], data[start:end])
    if wanted - files.keys():
        raise ValueError('Missing recovery security members: ' + repr(sorted(wanted - files.keys())))
    binary_mode, binary = files['system/bin/hw/android.hardware.boot-service.qti.recovery']
    if not binary.startswith(b'\x7fELF') or not binary_mode & 0o111:
        raise ValueError('Recovery boot-control service is not executable ELF')
    rc = files['system/etc/init/boot-control.qti.rc'][1].decode()
    if 'service vendor.boot-qti /system/bin/hw/android.hardware.boot-service.qti.recovery' not in rc:
        raise ValueError('Recovery boot-control service path mismatch')
    if 'seclabel u:r:frogger_recovery_bootctl:s0' not in rc:
        raise ValueError('Recovery boot-control service domain mismatch')
    contexts = files['system_ext_file_contexts'][1].decode()
    mapping = (r'/system/bin/hw/android\.hardware\.boot-service\.qti\.recovery',
               'u:object_r:frogger_recovery_bootctl_exec:s0')
    if not any(tuple(line.split()) == mapping for line in contexts.splitlines()):
        raise ValueError('Recovery boot-control executable label missing')
    props = files['prop.default'][1].decode()
    for key, expected in {'ro.adb.secure': '1', 'ro.secure': '1', 'ro.debuggable': '0'}.items():
        values = re.findall(r'^' + re.escape(key) + r'=(.*)$', props, re.MULTILINE)
        if not values or any(value.strip() != expected for value in values):
            raise ValueError('Incorrect recovery security property: ' + key + ': ' + repr(values))
    policy = tmp / 'actual-recovery-policy'
    policy.write_bytes(files['sepolicy'][1])
    analyze = str(host / 'sepolicy-analyze')
    if subprocess.check_output([analyze, str(policy), 'permissive'], text=True).strip():
        raise ValueError('Permissive domains in packed recovery policy')
    domains = subprocess.check_output([analyze, str(policy), 'attribute', 'coredomain'], text=True).split()
    if 'frogger_recovery_bootctl' not in domains:
        raise ValueError('Recovery boot-control system domain absent from packed policy')
    return {'permissive_domains': [], 'boot_control_domain': 'frogger_recovery_bootctl',
            'authenticated_adb': True, 'debuggable': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'errors': [], 'scope': 'Packed recovery contents; does not prove runtime boot or slot switching.'}
    try:
        with tempfile.TemporaryDirectory(prefix='frogger-recovery-security-') as directory:
            report.update(audit(args.image, Path(__file__).resolve().parents[4], Path(directory)))
        with args.image.open('rb') as stream:
            report['sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        report['errors'].append(str(error))
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('Packed recovery security:', 'FAIL' if report['errors'] else 'PASS')
    raise SystemExit(bool(report['errors']))


if __name__ == '__main__':
    main()
