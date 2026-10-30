"""Package and verify the tightly scoped 0.5.1 skin revision."""
from __future__ import annotations
import argparse
import hashlib
import html
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import shutil
from PIL import Image
from berber_050_common import ROOT, OUT as OLD, GUID, read, write, sha
from berber_050_admission import EXPECTED
from berber_051_skin import OUT, ART, BASE, BASE_SHA

REQUIRED={'garrison.json','Berber_future_kingdom.sga','COVERAGE.json','EVIDENCE.json',
          'INSTALL_AND_TEST.txt','SKIN_REVIEW.html','REBUILD_051.md'}


def verify_zip(path, expected):
    with ZipFile(path) as z:
        names=z.namelist()
        if z.testzip() is not None or len(names)!=len(set(names)) or not REQUIRED<=set(names):
            raise ValueError('ZIP CRC/membership failed')
        if any(Path(n).is_absolute() or '..' in Path(n).parts or '\\' in n for n in names):
            raise ValueError('Unsafe ZIP path')
        if hashlib.sha256(z.read('Berber_future_kingdom.sga')).hexdigest()!=expected:
            raise ValueError('ZIP SGA hash differs')
        m=__import__('json').loads(z.read('garrison.json'))
        if m['details']['version']!='0.5.1' or m['members'][0]['sha256']!=expected:
            raise ValueError('Version/hash metadata differs')
        c=__import__('json').loads(z.read('COVERAGE.json'))
        required={(f,a) for f,ages in EXPECTED.items() for a in ages}
        actual={(r['family'],r['age']) for r in c['rows']}
        if actual!=required or len(c['rows'])!=39:raise ValueError('Coverage incomplete')
        return {'zip_readable':True,'members':names,'sga_sha256':expected,'manifest_version':'0.5.1'}


def package(images):
    r=read(OUT/'composition-report.json')
    if r['status']!='passed' or sha(r['archive'])!=r['archive_sha256'] or sha(BASE)!=BASE_SHA:
        raise ValueError('Validated current archive and protected baseline required')
    for path,digest in read(OUT/'texture-cook.json')['source_hashes'].items():
        if sha(path)!=digest:raise ValueError('Inputs changed after validated native cook')
    for row in r['payloads']:
        if sha(row['file'])!=row['sha256']:raise ValueError('Payload changed after final validation')
    destination=OUT/'package';destination.mkdir(exist_ok=True)
    shutil.copy2(r['archive'],destination/'Berber_future_kingdom.sga')
    manifest=read(OLD/'package/garrison.json')
    manifest['members'][0]['sha256']=r['archive_sha256']
    manifest['details'].update(version='0.5.1',updated='2026-10-16',summary='Fair exposed skin; approved unit models retained',
        description='Minimal 0.5.0 skin revision. Native fair-skin palettes and exposed baked skin only. Geometry, rigs, animation, clothing, mounts, player-colour masks and gameplay preserved. Native appearance acceptance pending.',
        changelog='Skin palette references and five baked exposed-skin albedos only; no geometry or gameplay changes.')
    write(destination/'garrison.json',manifest)
    coverage=read(OLD/'package/COVERAGE.json')
    coverage.update(version='0.5.1',skin_revision={'palette_model_resources':48,'baked_skin_model_resources':5,
        'total_model_resources_including_existing_tuareg':53,'base_family_age_entries':39,
        'geometry_and_age_bindings':'byte-identical to 0.5.0','native_appearance_and_player_colour':'pending'})
    for row in coverage['rows']:
        baked=row['family']=='tuareg' or (row['family']=='zenata' and row['age']==4)
        row['skin_revision']='baked exposed skin only' if baked else 'native fair skin palette only'
        row['native_appearance_animation_player_colour']='pending fresh-match acceptance'
    write(destination/'COVERAGE.json',coverage)
    write(destination/'EVIDENCE.json',{'version':'0.5.1','project_guid':GUID,'baseline_sha256':BASE_SHA,
        'candidate_sga_sha256':r['archive_sha256'],'composition':r,
        'fresh_texture_cook':read(OUT/'texture-cook.json'),
        'native_appearance_player_colour_animation':'pending user testing'})
    shutil.copy2(ROOT/'Design/asset_overhaul/BERBER_051_REBUILD.md',destination/'REBUILD_051.md')
    (destination/'INSTALL_AND_TEST.txt').write_text(
        'BERBER 0.5.1 CANDIDATE\n\nClose AoE4, import this ZIP into Garrison and enable Berber. '
        'Select Tuning Pack The Berber Dynasties, Game Mode Berber Civilization and civilization Malians. '
        'Keep the verified 0.5.0 ZIP for rollback.\n\n'
        'This revision changes exposed human skin appearance. All models, rigs, animations, attributes, '
        'age bindings, clothing, mounts and equipment retain 0.5.0 bytes.\n\n'
        'In a fresh match check every family/age, including trader male/female, camel armour states '
        'and Regicide King. Inspect faces, hands, exposed arms/legs at near/far LOD in two player colours. '
        'Check beard/hair/eyes, clothing/mounts and movement/combat/work/trade/relic states. '
        'Native appearance, player colour, loading and animation acceptance remain pending.\n',encoding='utf8')
    cards=[]; review_records=[]
    for index,path in enumerate(images):
        path=Path(path)
        if not path.is_file():raise ValueError(f'Missing review image: {path}')
        name=f'{index:02d}-{path.stem}.jpg';target=destination/'review'/name;target.parent.mkdir(exist_ok=True)
        with Image.open(path) as im:im.convert('RGB').save(target,quality=92)
        cards.append(f'<figure><figcaption>{html.escape(path.stem)}</figcaption><a href="review/{html.escape(name)}"><img src="review/{html.escape(name)}"></a></figure>')
        review_records.append({'source':str(path),'source_sha256':sha(path),'delivered':str(target),'sha256':sha(target)})
    page='''<!doctype html><meta charset="utf-8"><title>Berber 0.5.1 skin review</title>
<style>body{max-width:1400px;margin:32px auto;padding:0 20px;background:#161b24;color:#e7edf5;font:16px system-ui}img{max-width:100%}figure{margin:25px 0;padding:15px;background:#232c39}code{word-break:break-all}</style>
<h1>Berber 0.5.1 — exposed skin revision</h1><p>Approved 0.5.0 models are retained. 48 private human materials use one native fair-skin palette; four Tuareg and Zenata IV use bounded baked-skin edits. Geometry, skeletons, animations, all attributes/age references, clothing, mounts and owner-colour masks remain unchanged.</p>
<p>Native loading, appearance and player-colour acceptance are pending. These are Blender authoring comparisons. The native palette's complete row/column layout is retained; no shader-row behavior was invented.</p>
<p>See COVERAGE.json for all 39 family/age entries, EVIDENCE.json for exact 53 modified archive members and one palette addition, and REBUILD_051.md for retained inputs.</p>'''+''.join(cards)
    (destination/'SKIN_REVIEW.html').write_text(page,encoding='utf8')
    write(OUT/'review-images.json',review_records)
    archive=OUT/'berber_future_kingdom-0.5.1.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(destination.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(destination).as_posix())
    result=verify_zip(archive,r['archive_sha256'])
    result.update(status='passed',zip=str(archive),zip_sha256=sha(archive),sga=str(destination/'Berber_future_kingdom.sga'),
        baseline_sha256=BASE_SHA,native_acceptance='pending')
    write(OUT/'release-validation.json',result)
    (OUT/'SHA256SUMS.txt').write_text(result['zip_sha256']+'  '+archive.name+'\n'+result['sga_sha256']+'  package/Berber_future_kingdom.sga\n',encoding='utf8')
    print('051_ZIP_VERIFIED',result['zip_sha256'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--images',nargs='+',type=Path,required=True)
    package(parser.parse_args().images)
