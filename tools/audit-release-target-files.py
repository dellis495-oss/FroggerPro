#!/usr/bin/env python3
"""Audit real release APK/APEX signatures, boot security, policy and AVB chain."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

from cryptography import x509
from cryptography.hazmat.primitives import hashes


def properties(text):
    return dict(line.split('=', 1) for line in text.splitlines()
                if '=' in line and not line.startswith('#'))


def run(command):
    return subprocess.check_output([str(x) for x in command], text=True,
                                   stderr=subprocess.STDOUT)


def audit_avb_flags(host, image_dir):
    flags = {}
    for partition in ('vbmeta', 'boot', 'recovery', 'vbmeta_system', 'vbmeta_vendor'):
        output = run([host / 'avbtool', 'info_image', '--image',
                      image_dir / (partition + '.img')])
        match = re.search(r'^\s*Flags:\s*(\d+)\s*$', output, re.MULTILINE)
        if not match or int(match.group(1)) != 0:
            raise ValueError('AVB verification flags must be zero for ' + partition)
        flags[partition] = int(match.group(1))
    return flags


def audit_lineage(host, artifact):
    output = run([host / 'apksigner', 'lineage', '--in', artifact, '--print-certs'])
    blocks = [block for block in re.split(r'(?=Signer #\d+ in lineage certificate DN:)', output)
              if 'Has installed data capability' in block]
    if len(blocks) < 2:
        raise ValueError('Missing certificate-rotation proof')
    for predecessor in blocks[:-1]:
        for capability in ('shared UID', 'permission', 'rollback', 'auth'):
            match = re.search(r'Has ' + capability + r' capability\s*:\s*(true|false)', predecessor)
            if not match or match.group(1) != 'false':
                raise ValueError('Old test signer retains ' + capability + ' authority')
        if not re.search(r'Has installed data capability\s*:\s*true', predecessor):
            raise ValueError('Rotation does not preserve installed app data')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-files', type=Path, required=True)
    parser.add_argument('--keys', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    host = root / 'out/host/linux-x86/bin'
    keys = args.keys.resolve()
    apex_key_map = json.loads((keys / 'apex-key-map.json').read_text())
    main_certificates = {
        str((root / 'build/make/target/product/security' / (old + '.x509.pem')).resolve()):
        keys / (new + '.x509.pem')
        for old, new in [('testkey', 'releasekey'), ('platform', 'platform'),
                         ('shared', 'shared'), ('networkstack', 'networkstack'), ('media', 'media')]
    }
    old_certificates = [Path(name) for name in main_certificates]
    old_certificates += [(root / name).with_suffix('.x509.pem') for name, entry in apex_key_map.items()
                         if entry['kind'] == 'container']
    public_development_signers = {
        x509.load_pem_x509_certificate(path.read_bytes()).fingerprint(hashes.SHA256()).hex()
        for path in old_certificates
    }
    report = {'errors': [], 'apk_signatures': {}, 'apex_signatures': {},
              'scope': 'Offline release contents; enforcing runtime and data migration require phone validation.'}
    try:
        with zipfile.ZipFile(args.target_files) as archive, tempfile.TemporaryDirectory(dir=args.output.parent) as directory:
            tmp = Path(directory).resolve()
            names = set(archive.namelist())
            props = {}
            for name in ('SYSTEM/build.prop', 'SYSTEM/system/build.prop', 'SYSTEM/etc/prop.default'):
                if name in names:
                    props.update(properties(archive.read(name).decode()))
            for name, expected in {'ro.build.type': 'user', 'ro.build.tags': 'release-keys',
                                   'ro.debuggable': '0', 'ro.secure': '1'}.items():
                if props.get(name) != expected:
                    raise ValueError(name + ': expected ' + expected + ', got ' + repr(props.get(name)))
            report['build_properties'] = {k: props.get(k) for k in
                                          ('ro.build.type', 'ro.build.tags', 'ro.debuggable', 'ro.secure',
                                           'ro.build.fingerprint', 'ro.build.version.incremental')}
            certs = {}
            for line in archive.read('META/apkcerts.txt').decode().splitlines():
                item = dict(re.findall(r'(\w+)="([^"]*)"', line))
                if item:
                    certs[item['name']] = item['certificate']
            apexes = {item['name']: item for item in (
                dict(re.findall(r'(\w+)="([^"]*)"', line)) for line in
                archive.read('META/apexkeys.txt').decode().splitlines()) if item}
            count = 0
            for name in sorted(names):
                if name.split('/')[0] not in {'SYSTEM', 'SYSTEM_EXT', 'PRODUCT', 'VENDOR', 'ODM'}:
                    continue
                kind = 'apk' if name.endswith('.apk') else 'apex' if name.endswith(('.apex', '.capex')) else None
                if not kind:
                    continue
                filename = Path(name).name
                apex = apexes.get(filename.removesuffix('.capex') + '.apex' if name.endswith('.capex') else filename)
                certificate = apex.get('container_certificate') if kind == 'apex' and apex else certs.get(filename)
                if certificate == 'PRESIGNED':
                    artifact = tmp / ('presigned-' + str(count) + Path(name).suffix)
                    count += 1
                    artifact.write_bytes(archive.read(name))
                    output = run([host / 'apksigner', 'verify', '--min-sdk-version', '28', '--print-certs', artifact])
                    match = re.search(r'certificate SHA-256 digest: ([a-f0-9]+)', output)
                    if not match:
                        raise ValueError('Missing upstream signing certificate for ' + name)
                    digest = match.group(1)
                    if digest in public_development_signers and filename != 'com.android.apex.cts.shim.apex':
                        raise ValueError('PRESIGNED package retains public development signer: ' + name)
                    report[kind + '_signatures'][name] = {'upstream_presigned': True, 'certificate_sha256': digest}
                    artifact.unlink()
                    continue
                # Releasetools preserves original apkcerts/apexkeys metadata.
                # Resolve the explicit migration map, then inspect the actual
                # signature; original metadata paths do not prove key identity.
                if kind == 'apex' and apex:
                    record = apex_key_map.get(apex['container_private_key'])
                    certificate = str(Path(record['prefix']).with_suffix('.x509.pem')) if record else certificate
                elif certificate:
                    certificate = str(main_certificates.get(str((root / certificate).resolve()), certificate))
                if not certificate or not Path(certificate).resolve().is_relative_to(keys):
                    raise ValueError('Non-private or absent expected signing certificate for ' + name)
                expected = x509.load_pem_x509_certificate(Path(certificate).read_bytes()).fingerprint(hashes.SHA256()).hex()
                artifact = tmp / ('artifact-' + str(count) + Path(name).suffix)
                count += 1
                artifact.write_bytes(archive.read(name))
                output = run([host / 'apksigner', 'verify', '--min-sdk-version', '28', '--print-certs', artifact])
                match = re.search(r'certificate SHA-256 digest: ([a-f0-9]+)', output)
                if not match or match.group(1) != expected:
                    raise ValueError('Actual signing certificate mismatch for ' + name)
                audit_lineage(host, artifact)
                entry = {'certificate_sha256': expected, 'restricted_rotation_proof_verified': True}
                if kind == 'apex':
                    record = apex_key_map.get(apex['private_key'])
                    payload_key = Path(record['prefix']).with_suffix('.pem') if record else Path(apex['private_key'])
                    if not payload_key.resolve().is_relative_to(keys):
                        raise ValueError('Non-private APEX payload signing key for ' + name)
                    original = artifact
                    if name.endswith('.capex'):
                        original = tmp / ('original-' + str(count) + '.apex')
                        run([host / 'deapexer', 'decompress', '--input', artifact, '--output', original])
                    with zipfile.ZipFile(original) as apex_archive:
                        actual = apex_archive.read('apex_pubkey')
                        payload_image = tmp / 'apex-payload.img'
                        with apex_archive.open('apex_payload.img') as source, payload_image.open('wb') as dest:
                            shutil.copyfileobj(source, dest)
                    public = tmp / 'apex-public.avbpubkey'
                    run([host / 'avbtool', 'extract_public_key', '--key', payload_key, '--output', public])
                    if public.read_bytes() != actual:
                        raise ValueError('Actual APEX payload public key mismatch for ' + name)
                    run([host / 'avbtool', 'verify_image', '--image', payload_image,
                         '--key', payload_key, '--accept_zeroed_hashtree'])
                    payload_image.unlink()
                    entry['payload_public_key_sha256'] = hashlib.sha256(actual).hexdigest()
                    entry['payload_signature_verified'] = True
                    contents = tmp / 'apex-contents'
                    contents.mkdir()
                    run([host / 'deapexer', '--debugfs_path', host / 'debugfs_static',
                         '--fsckerofs_path', host / 'fsck.erofs', 'extract', original, contents])
                    for embedded in contents.rglob('*.apk'):
                        if not embedded.resolve().is_relative_to(contents):
                            raise ValueError('APEX APK escapes extraction directory')
                        label = name + '!/' + str(embedded.relative_to(contents))
                        output = run([host / 'apksigner', 'verify', '--min-sdk-version', '28', '--print-certs', embedded])
                        match = re.search(r'certificate SHA-256 digest: ([a-f0-9]+)', output)
                        if not match:
                            raise ValueError('No embedded APK certificate: ' + label)
                        digest = match.group(1)
                        certificate = certs.get(embedded.name)
                        if certificate == 'PRESIGNED':
                            if digest in public_development_signers:
                                raise ValueError('Public development signer inside APEX: ' + label)
                            embedded_entry = {'upstream_presigned': True, 'certificate_sha256': digest}
                        else:
                            expected_path = main_certificates.get(str((root / certificate).resolve())) if certificate else None
                            if expected_path is None and certificate:
                                priv_key = certificate.replace('.x509.pem', '.pk8')
                                record = apex_key_map.get(priv_key)
                                if record and record.get('kind') == 'container':
                                    expected_path = Path(record['prefix']).with_suffix('.x509.pem')
                            if expected_path is None and certificate and Path(certificate).resolve().is_relative_to(keys):
                                expected_path = Path(certificate)
                            is_module_cert = False
                            if expected_path is None and certificate and (root / certificate).is_file():
                                expected_path = (root / certificate).resolve()
                                is_module_cert = True
                            if expected_path is None:
                                raise ValueError('Missing private signer mapping inside APEX: ' + label)
                            if is_module_cert and digest in public_development_signers:
                                raise ValueError('Public development signer inside APEX: ' + label)
                            expected = x509.load_pem_x509_certificate(expected_path.read_bytes()).fingerprint(hashes.SHA256()).hex()
                            if expected != digest:
                                raise ValueError('Embedded APK certificate mismatch: ' + label)
                            if not is_module_cert:
                                audit_lineage(host, embedded)
                                embedded_entry = {'certificate_sha256': digest, 'restricted_rotation_proof_verified': True}
                            else:
                                embedded_entry = {'certificate_sha256': digest, 'module_certificate_verified': True}
                        report['apk_signatures'][label] = embedded_entry
                    shutil.rmtree(contents)
                    if original != artifact:
                        original.unlink()
                report[kind + '_signatures'][name] = entry
                artifact.unlink()
            image_dir = tmp / 'IMAGES'
            image_dir.mkdir()
            for name in sorted(names):
                if name.startswith('IMAGES/') and name.endswith('.img') and len(Path(name).parts) == 2:
                    with archive.open(name) as source, (image_dir / Path(name).name).open('wb') as dest:
                        shutil.copyfileobj(source, dest)
            public = tmp / 'release.avbpubkey'
            report['avb_flags'] = audit_avb_flags(host, image_dir)
            recovery_report = tmp / 'recovery-security.json'
            run(['python3', root / 'device/nothing/FroggerPro/tools/audit-recovery-security.py',
                 '--image', image_dir / 'recovery.img', '--output', recovery_report])
            report['recovery_security'] = json.loads(recovery_report.read_text())
            run([host / 'avbtool', 'extract_public_key', '--key', keys / 'avb.pem', '--output', public])
            command = [host / 'avbtool', 'verify_image', '--image', image_dir / 'vbmeta.img',
                       '--key', keys / 'avb.pem', '--follow_chain_partitions']
            for name, location in [('boot', 3), ('recovery', 1), ('vbmeta_system', 2), ('vbmeta_vendor', 4)]:
                command += ['--expected_chain_partition', name + ':' + str(location) + ':' + str(public)]
            output = run(command)
            args.output.with_suffix('.avb.log').write_text(output)
            report['avb_public_key_sha256'] = hashlib.sha256(public.read_bytes()).hexdigest()
            # This target installs its combined policy in ODM; other targets
            # use VENDOR. Inspect every packaged precompiled policy, requiring
            # at least one rather than assuming a particular partition.
            policy_sources = [partition + '/etc/selinux/precompiled_sepolicy'
                              for partition in ('ODM', 'VENDOR')
                              if partition + '/etc/selinux/precompiled_sepolicy' in names]
            if not policy_sources:
                raise ValueError('No packaged precompiled SELinux policy')
            for source in policy_sources:
                policy = tmp / ('precompiled-' + source.split('/')[0].lower())
                policy.write_bytes(archive.read(source))
                permissive = run([host / 'sepolicy-analyze', policy, 'permissive']).strip()
                if permissive:
                    raise ValueError('Permissive domains in ' + source + ': ' + permissive)
            report['precompiled_policy_sources'] = policy_sources
            report['permissive_domains'] = []
            for name in ('boot', 'vendor_boot'):
                unpack = tmp / ('unpack-' + name)
                output = run(['python3', root / 'system/tools/mkbootimg/unpack_bootimg.py',
                              '--boot_img', image_dir / (name + '.img'), '--out', unpack])
                if (unpack / 'bootconfig').exists():
                    output += (unpack / 'bootconfig').read_text()
                if re.search(r'androidboot\.selinux\s*=\s*"?permissive|androidboot\.frogger\.init_log\s*=\s*"?1', output):
                    raise ValueError('Permissive or diagnostic argument in actual ' + name)
            if not report['apk_signatures'] or not report['apex_signatures']:
                raise ValueError('Release APK/APEX inventory unexpectedly empty')
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        report['errors'].append(str(error))
        if isinstance(error, subprocess.CalledProcessError) and error.output:
            report['errors'].append(error.output[-8000:])
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('Release contents audit:', 'FAIL' if report['errors'] else 'PASS')
    if report['errors']:
        print('\n'.join(report['errors']))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
