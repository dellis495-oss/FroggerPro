#!/usr/bin/env python3
"""Validate and sign a production FroggerPro target-files archive offline.

Default operation validates inputs and writes a command plan; --execute runs it.
Private keys stay outside the checkout. This never installs or flashes a phone.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile


def pairs(text):
    return dict(line.split('=', 1) for line in text.splitlines()
                if '=' in line and not line.startswith('#'))


def plan(args, root):
    if args.build_status.read_text().strip() != '0':
        raise ValueError('The complete user build must pass before signing')
    if args.output.exists():
        raise ValueError('Refusing to overwrite an existing signed archive')
    keys = args.keys.resolve()
    if keys.is_relative_to(root):
        raise ValueError('Private release keys must be outside the source tree')
    stat = keys.stat()
    if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
        raise ValueError('Private key directory must be owned by this user and mode0700')
    apex_map = json.loads((keys / 'apex-key-map.json').read_text())
    with zipfile.ZipFile(args.input) as archive:
        metadata = pairs(archive.read('META/misc_info.txt').decode())
        props = {}
        for name in ('SYSTEM/build.prop', 'SYSTEM/system/build.prop'):
            if name in archive.namelist():
                props.update(pairs(archive.read(name).decode()))
        if props.get('ro.build.type') != 'user':
            raise ValueError('Release signing requires a production user target')
        device = props.get('ro.product.system.device') or props.get('ro.product.device')
        if device != 'FroggerPro':
            raise ValueError('Target device must be FroggerPro')
        for name in archive.namelist():
            if name.endswith(('/cmdline', '/bootconfig')):
                text = archive.read(name).decode(errors='strict')
                if re.search(r'androidboot\.selinux\s*=\s*"?permissive', text):
                    raise ValueError('Explicit permissive boot argument: ' + name)
                if re.search(r'androidboot\.frogger\.init_log\s*=\s*"?1', text):
                    raise ValueError('Diagnostic init logging enabled: ' + name)
        apexes = [dict(re.findall(r'(\w+)="([^"]*)"', line)) for line in
                  archive.read('META/apexkeys.txt').decode().splitlines() if line.strip()]
    tool = root / 'out/host/linux-x86/bin/sign_target_files_apks'
    help_text = subprocess.run([str(tool), '--help'], capture_output=True,
                               text=True, check=True).stdout
    if '--signing_lineage' not in help_text:
        raise ValueError('Rebuild sign_target_files_apks with per-key lineage support first')
    java_home = root / 'prebuilts/jdk/jdk21/linux-x86'
    if not (java_home / 'bin/java').is_file():
        raise ValueError('Missing bundled JDK21 used by this production build')
    command = [str(tool), '-p', str(root / 'out/host/linux-x86'),
               '--java_path', str(java_home / 'bin/java'), '-o']
    dev = str(Path(metadata['default_system_dev_certificate']).parent)
    for old, new in [('testkey', 'releasekey'), ('platform', 'platform'),
                     ('shared', 'shared'), ('networkstack', 'networkstack'), ('media', 'media')]:
        prefix = keys / new
        for suffix in ('.pk8', '.x509.pem', '.lineage'):
            if not prefix.with_suffix(suffix).is_file():
                raise ValueError('Missing release key/certificate/lineage for ' + new)
        command += ['-k', dev + '/' + old + '=' + str(prefix),
                    '--signing_lineage', str(prefix) + '=' + str(prefix.with_suffix('.lineage'))]
    mapped_containers = set()
    for entry in apexes:
        if entry['private_key'] == 'PRESIGNED':
            continue
        payload = Path(apex_map[entry['private_key']]['prefix']).with_suffix('.pem')
        container = Path(apex_map[entry['container_private_key']]['prefix'])
        if not payload.is_file() or not container.with_suffix('.lineage').is_file():
            raise ValueError('Incomplete private APEX inputs: ' + entry['name'])
        command += ['--extra_apex_payload_key', entry['name'] + '=' + str(payload),
                    '-e', entry['name'] + '=' + str(container),
                    '--signing_lineage', str(container) + '=' + str(container.with_suffix('.lineage'))]
        container_src = str(Path(entry['container_private_key']).with_suffix(''))
        if not container_src.startswith(dev + '/') and container_src not in mapped_containers:
            mapped_containers.add(container_src)
            command += ['-k', container_src + '=' + str(container)]
    avb = keys / 'avb.pem'
    if not avb.is_file():
        raise ValueError('Missing private AVB key')
    for partition in ('vbmeta', 'boot', 'recovery', 'vbmeta_system', 'vbmeta_vendor'):
        if 'avb_' + partition + '_key_path' not in metadata:
            raise ValueError('Expected AVB chain is absent: ' + partition)
        command += ['--avb_' + partition + '_key', str(avb),
                    '--avb_' + partition + '_algorithm', 'SHA256_RSA4096']
        if partition.startswith('vbmeta'):
            # Release signing must re-enable verification even if unsigned
            # bring-up inputs carried disabled-verification flags.
            command += ['--avb_' + partition + '_extra_args', '--flags 0']
    command += [str(args.input.resolve()), str(args.output.resolve())]
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--keys', type=Path, required=True)
    parser.add_argument('--build-status', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    command = plan(args, root)
    args.plan.write_text(json.dumps(command, indent=2) + '\n')
    if args.execute:
        # /tmp on the build host is a small RAM filesystem. Full target-files
        # extraction must use disk space alongside the output archive.
        with tempfile.TemporaryDirectory(prefix='release-signing-', dir=args.output.parent) as directory:
            environment = os.environ.copy()
            environment['TMPDIR'] = str(Path(directory).resolve())
            environment['JAVA_HOME'] = str(root / 'prebuilts/jdk/jdk21/linux-x86')
            environment['PATH'] = environment['JAVA_HOME'] + '/bin:' + environment.get('PATH', '')
            subprocess.run(command, check=True, cwd=root, env=environment)
    else:
        print('Validated release-signing command saved; no archive signed or phone changed.')


if __name__ == '__main__':
    main()
