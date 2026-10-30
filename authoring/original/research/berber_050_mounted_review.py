"""Build packed private mounted review Blends and textured LOD1 evidence."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from berber_050_common import ROOT, ART, sha

OUT = ART / 'mounted'
MANIFEST = OUT / 'mounted-manifest.json'
BLENDER = Path('E:/Blender5.2/blender.exe')


def save(doc):
    temp = MANIFEST.with_suffix('.json.tmp')
    temp.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf8')
    temp.replace(MANIFEST)


def run(label,script,input_path,log_path):
    cmd = [str(BLENDER),'--factory-startup','--offline-mode','-noaudio','-b','-t','4',
           '--python',str(ROOT/'research'/script),'--',str(input_path)]
    with log_path.open('w',encoding='utf8') as output:
        result = subprocess.run(cmd,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,timeout=180)
    if result.returncode:
        tail = '\n'.join(log_path.read_text(encoding='utf8',errors='replace').splitlines()[-20:])
        raise RuntimeError(f'{label} failed ({result.returncode})\n{tail}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--names',nargs='*')
    parser.add_argument('--skip-reviewed',action='store_true')
    parser.add_argument('--lod-only',action='store_true')
    args = parser.parse_args()
    doc = json.loads(MANIFEST.read_text(encoding='utf8'))
    for row in doc['variants']:
        name = row['private_variant_name']
        if args.names is not None and name not in args.names:
            continue
        if args.skip_reviewed and row.get('editable_blend_sha256'):
            continue
        folder = OUT/name
        recipe = folder/'recipe.json'
        blend = folder/(name+'.blend')
        if not args.lod_only:
            print('BLEND',name,flush=True)
            run(name,'berber_050_mounted_blender.py',recipe,folder/'blend.log')
        if not blend.is_file():
            raise FileNotFoundError(blend)
        if args.lod_only:
            print('LOD_RENDER',name,flush=True)
            run(name,'berber_050_mounted_lod_render.py',blend,folder/'lod-render.log')
            for lod in (2,3):
                for label in ('donor','candidate'):
                    key=f'preview_{label}_lod{lod}'
                    path=folder/f'textured-{label}-lod{lod}.png'
                    if not path.is_file() or path.stat().st_size<1000:
                        raise ValueError(f'{name}: missing LOD render {path}')
                    row[key]=str(path.relative_to(ROOT))
                    row[key+'_sha256']=sha(path)
            if name.startswith(('mehari','sanhaja','zenata_age04')):
                for label in ('donor','candidate'):
                    key=f'preview_{label}_rider_only'
                    path=folder/f'textured-{label}-rider-only.png'
                    if not path.is_file() or path.stat().st_size<1000:
                        raise ValueError(f'{name}: missing rider-only render {path}')
                    row[key]=str(path.relative_to(ROOT))
                    row[key+'_sha256']=sha(path)
            save(doc)
            print('LOD_REVIEW_SAVED',name,flush=True)
            continue
        print('RENDER',name,flush=True)
        run(name,'berber_050_mounted_render.py',blend,folder/'render.log')
        for key, filename in (
            ('editable_blend',name+'.blend'),
            ('preview_donor_lod1','textured-donor.png'),
            ('preview_candidate_lod1','textured-candidate.png'),
            ('preview_rider_close','textured-rider-close.png'),
            ('preview_team_red','textured-team-red.png'),
            ('preview_team_blue','textured-team-blue.png')):
            path = folder/filename
            if not path.is_file() or path.stat().st_size < 1000:
                raise ValueError(f'{name}: missing or tiny {filename}')
            row[key] = str(path.relative_to(ROOT))
            row[key+'_sha256'] = sha(path)
        save(doc)
        print('REVIEW_SAVED',name,sha(blend),flush=True)


if __name__=='__main__':
    main()
