#!/usr/bin/env python3
"""Freeze and verify a completed local FroggerPro build; never flashes a device."""
from pathlib import Path
import argparse, shutil, subprocess, json, zipfile
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build-status', type=Path, required=True)
parser.add_argument('--bundle', type=Path, required=True)
parser.add_argument('--ota', type=Path, required=True, help='Exact OTA produced by the successful build')
parser.add_argument('--build-log', type=Path)
parser.add_argument('--target-files', type=Path, help='Exact signed target-files ZIP for a release')
parser.add_argument('--ota-public-key', type=Path, help='Public PEM for the actual OTA signing key')
parser.add_argument('--release-keys', type=Path, help='Run production audit using private key identities; never copied')
args = parser.parse_args()
build_log = args.build_log or args.build_status.with_suffix('.log')
r = Path(__file__).resolve().parents[4]
assert args.build_status.read_text().strip() == '0', 'Build has not succeeded; do not publish'
b=args.bundle.resolve()
o=r/'out/target/product/FroggerPro';t=o/'obj/PACKAGING/target_files_intermediates/lineage_FroggerPro-target_files'
ota=args.ota.resolve()
assert ota.parent == o and ota.is_file(), 'Select the OTA from this product output directory'
assert t.joinpath('IMAGES').is_dir() and t.joinpath('META').is_dir(), 'Target-files staging is missing'
if args.release_keys:
    assert args.target_files and args.ota_public_key, 'Release requires explicit signed target files and OTA public key'
b.mkdir(exist_ok=False);(b/'verification').mkdir()
if args.target_files:
    with zipfile.ZipFile(args.target_files) as archive:
        for name in archive.namelist():
            parts=Path(name).parts
            if not parts or parts[0] not in ('IMAGES','META') or name.endswith('/'):
                continue
            assert '..' not in parts and not Path(name).is_absolute(), 'Unsafe target-files path'
            dest=b/name;dest.parent.mkdir(parents=True,exist_ok=True)
            with archive.open(name) as source,dest.open('wb') as output:shutil.copyfileobj(source,output)
else:
    for n in ['IMAGES','META']:shutil.copytree(t/n,b/n)
shutil.copy2(ota,b/ota.name)
old=r/'frogger-build-artifacts/20261016-runtime-init/verification'
shutil.copy2(old/'update_metadata_pb2.py',b/'verification/update_metadata_pb2.py')
shutil.copy2(args.ota_public_key or old/'ota-public-key.pem',b/'verification/ota-public-key.pem')
s=(old/'verify_ota.py').read_text().replace('e-4.4-a17-20261016-UNOFFICIAL-FroggerPro.zip',ota.name)
(b/'verification/verify_ota.py').write_text(s)
def run(n,args):
    with (b/'verification'/(n+'.log')).open('w') as f:p=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
    (b/'verification'/(n+'.exit')).write_text(str(p.returncode));assert p.returncode==0,n+' failed'
h=r/'out/host/linux-x86/bin';dev=r/'device/nothing/FroggerPro'
if args.release_keys:
    run('release-security',['python3',str(dev/'tools/audit-release-target-files.py'),
        '--target-files',str(args.target_files.resolve()),'--keys',str(args.release_keys.resolve()),
        '--output',str(b/'verification/release-security.json')])
    shutil.copy2(b/'verification/release-security.json',b/'RELEASE_SECURITY.json')
run('ota-integrity',['python3',str(b/'verification/verify_ota.py')])
run('avb-chain',[str(h/'avbtool'),'verify_image','--image',str(b/'IMAGES/vbmeta.img'),'--follow_chain_partitions'])
run('payload-signature',[str(h/'delta_generator'),'--in_file='+str(b/'verification/payload.bin'),'--public_key='+str(b/'verification/ota-public-key.pem')])
run('recovery-ota-signature',['python3',str(dev/'tools/audit-recovery-ota.py'),'--recovery',str(b/'IMAGES/recovery.img'),'--ota',str(b/ota.name),'--output',str(b/'verification/recovery-ota-signature.json'),'--require-default-group-migration'])
run('vendor-packed',['python3',str(dev/'tools/audit-packed-vendor.py'),str(b/'IMAGES'),'--output',str(b/'verification/vendor-packed.json')])
for n in ['vendor_boot','recovery']:
    run(n+'-fstab',['python3',str(dev/'tools/audit-ramdisk-fstab.py'),str(b/'IMAGES'/(n+'.img')),'--output',str(b/'verification'/(n+'-fstab.json'))])
report=json.loads((b/'verification/ota-integrity.json').read_text())
shutil.copy2(args.build_status, b/'verification/build.exit')
shutil.copy2(build_log, b/'verification/build.log')
(b/'SHA256SUMS').write_text(report['ota_sha256']+'  '+ota.name+'\n'+''.join(v['sha256']+'  IMAGES/'+k+'.img\n' for k,v in sorted(report['partitions'].items())))
shutil.copy2(dev/'tools/load-recovery.py',b/'LOAD_RECOVERY.py')
(b/'README.md').write_text('Canonical full OTA/image set: fingerprint FOD control ownership, QCRIL data database lifecycle, supplicant template and metadata filesystem agreement baked in. Payload/image hashes, signatures, AVB, packed runtime inventory and boot/recovery fstabs passed. Final-image fingerprint, radio, Wi-Fi, camera, Glyph and audio behavior still require device validation; cellular requires a SIM. Development permissive diagnostics and branch test keys remain; not a release-validation claim. No device operations were performed by this verifier.\n')
(b/'RECOVERY_INSTALL.md').write_text('Run python3 LOAD_RECOVERY.py to verify this bundle. On the intended FroggerPro, enter this matching e/OS recovery and select its ADB sideload option. Run python3 LOAD_RECOVERY.py --sideload to send the full OTA. Recovery replaces the inactive slot OS; the package requests no user-data wipe. ADB transport exit 0 is not proof of install success: read recovery logs/result before rebooting, then verify the running build and boot completion. Stock recovery does not trust this development OTA. Do not force direct fastboot flashing into an occupied super layout or delete partitions to bypass space errors.\n')
if args.release_keys:
    (b/'README.md').write_text('Private release-signed production user build. Offline APK/APEX signature identities, private AVB chain, payload/image agreement, OTA and packed-recovery trust, non-debug properties, no permissive domains, no permissive/diagnostic boot arguments and packed runtime gates passed. Device enforcing boot, data migration and reboot verification are separate required deployment checks; see the deployment checkpoint. No private signing keys are included.\n')
    (b/'RECOVERY_INSTALL.md').write_text('Verify with python3 LOAD_RECOVERY.py. A previously test-signed recovery does not trust this private release OTA: install the matching coherent release recovery/AVB boot chain using the documented phone-specific procedure first. Verify the running recovery, enter ADB sideload, then run python3 LOAD_RECOVERY.py --sideload. No wipe is requested. Confirm actual recovery install success before normal reboot, then verify user/release-keys/Enforcing, data access, selected slot and a second boot. Keep signing keys private and backed up. Do not relock or erase the phone as part of this installation.\n')
(args.build_status.parent/'freeze-verify.exit').write_text('0');print('Verified canonical runtime bundle:',b,flush=True)
