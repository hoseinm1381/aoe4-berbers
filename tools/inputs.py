"""Fetch/verify release inputs and restore editable masters without old drives."""
import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def verify(pack):
    path=ROOT/'inputs'/pack['name']
    assert path.is_file(),f'Missing {path}; run python tools/inputs.py fetch'
    assert path.stat().st_size==pack['bytes'],path
    assert sha(path)==pack['sha256'],path
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None,path
    return path


def fetch():
    for pack in read(ROOT/'inputs/manifest.json')['packs']:
        path=ROOT/'inputs'/pack['name']
        if path.exists():
            verify(pack);print('VERIFIED',pack['name'],flush=True);continue
        path.parent.mkdir(parents=True,exist_ok=True)
        assert pack['url'].startswith('https://github.com/hoseinm1381/aoe4-berbers/releases/download/')
        part=path.with_suffix('.download')
        assert not part.exists(),f'Inspect incomplete download first: {part}'
        with urllib.request.urlopen(pack['url']) as response,part.open('xb') as out:
            while chunk:=response.read(4*1024*1024):
                out.write(chunk)
        assert part.stat().st_size==pack['bytes'] and sha(part)==pack['sha256'],part
        os.replace(part,path);verify(pack)
        print('FETCHED',pack['name'],flush=True)


def replacements(destination):
    roots=[('E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai',destination/'original'),
           ('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014',destination/'external')]
    pairs=[]
    for old,new in roots:
        # JSON, Python escaped literals, ordinary Windows and slash paths.
        for separator in ['\\\\','\\','/']:
            pairs.append((old.replace('/',separator),str(new).replace('\\','/')))
    return pairs


def relocate_text(raw,destination):
    try:
        text=raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return raw
    for old,new in replacements(destination):
        text=text.replace(old,new)
    return text.encode('utf-8')


def restore(destination):
    destination=destination.resolve()
    assert not destination.exists(),f'Choose an empty destination; existing edits are protected: {destination}'
    manifest=read(ROOT/'inputs/manifest.json')
    packs={p['name']:p for p in manifest['packs'] if p['kind']=='editable-masters'}
    archives={name:zipfile.ZipFile(verify(pack)) for name,pack in packs.items()}
    receipts=[]
    try:
        for row in read(ROOT/'source/master-index.json')['files']:
            name=Path(row['path'])
            assert not name.is_absolute() and '..' not in name.parts,row['path']
            target=(destination/name).resolve()
            assert target.is_relative_to(destination)
            raw=archives[row['pack']].read(row['member'])
            assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
            if target.suffix.lower() in ('.py','.json','.xml','.txt','.md','.csv','.scar','.lua','.burnproj','.aoe4mod','.rdo'):
                raw=relocate_text(raw,destination)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
            if len(str(target)) > 230 and target.suffix.lower() in ('.png','.dds','.tga','.jpg','.jpeg','.tif','.tiff'):
                short=destination/'_images'/(row['sha256']+target.suffix.lower())
                short.parent.mkdir(exist_ok=True)
                if not short.exists():short.write_bytes(raw)
            receipts.append({'path':row['path'],'packed_sha256':row['sha256'],'restored_sha256':hashlib.sha256(raw).hexdigest()})
    finally:
        for archive in archives.values():archive.close()
    (destination/'RESTORE_RECEIPT.json').write_text(json.dumps({'files':receipts,'verified_source_blobs':True},indent=2)+'\n')
    print('RESTORED',len(receipts),'editable files to',destination,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['fetch','verify','restore-masters']);p.add_argument('--destination',type=Path,default=ROOT/'authoring');a=p.parse_args()
    if a.action=='fetch':fetch()
    elif a.action=='verify':
        for row in read(ROOT/'inputs/manifest.json')['packs']:
            verify(row);print('VERIFIED',row['name'],flush=True)
    else:restore(a.destination)
