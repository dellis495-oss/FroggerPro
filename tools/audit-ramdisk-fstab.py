#!/usr/bin/env python3
"""Verify metadata filesystem agreement in finished FroggerPro boot ramdisks."""
import argparse, gzip, hashlib, json, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('image',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
r=Path(__file__).resolve().parents[4]
found={};errors=[]
with tempfile.TemporaryDirectory(prefix='frogger-fstab-') as tmp:
    subprocess.run(['python3',str(r/'system/tools/mkbootimg/unpack_bootimg.py'),'--boot_img',str(a.image.resolve()),'--out',tmp],check=True,stdout=subprocess.DEVNULL)
    for archive in Path(tmp).glob('*ramdisk*'):
        if not archive.is_file():continue
        data=archive.read_bytes()
        if data[:2]==b'\x1f\x8b':data=gzip.decompress(data)
        elif not data.startswith((b'070701',b'070702')):
            data=subprocess.check_output([str(r/'out/host/linux-x86/bin/lz4'),'-d','-c',str(archive)])
        pos=0
        while pos+110<=len(data):
            assert data[pos:pos+6] in (b'070701',b'070702'), 'Unsupported CPIO header'
            f=[int(data[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
            name=data[pos+110:pos+110+f[11]-1].decode()
            start=(pos+110+f[11]+3)&~3
            body=data[start:start+f[6]]
            pos=(start+f[6]+3)&~3
            if name=='TRAILER!!!':break
            if 'fstab' not in Path(name).name or not body:continue
            lines=[x.split() for x in body.decode(errors='replace').splitlines() if x.strip() and not x.lstrip().startswith('#')]
            meta=[x[2] for x in lines if len(x)>2 and x[1]=='/metadata']
            if not meta:continue
            key=archive.name+':'+name;found[key]=meta
            if meta!=['f2fs','ext4']:errors.append(key+': expected F2FS then ext4 metadata alternatives, got '+repr(meta))
if not found:errors.append('No metadata fstab found in boot ramdisk')
with a.image.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
report={'image':str(a.image),'sha256':digest,'fstabs':found,'errors':errors,'scope':'Actual ramdisk metadata alternatives/order; does not format or prove data/encryption validity.'}
a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
