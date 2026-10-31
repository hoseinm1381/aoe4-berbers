"""Integrate refined art into a private copy of the tested Tuareg art candidate."""
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/tuareg_refined';WORK=ROOT/'output/tuareg_refined_trial';CANDIDATE=WORK/'candidate'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';ARCHIVER=EXT/'bin/sga-archiver.exe'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1';VERSION='0.1.5-tuareg-refined.1';PROJECT=ART/'garrison_library/Mods/tuareg_refined_art'
GM='scar/winconditions/berber_future_kingdom_GM.scar';MODULE='scar/Units/tuareg_q_art_guard_trial.scar'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args):
    p=subprocess.run([str(a) for a in args],capture_output=True,encoding='utf-8',errors='replace');assert p.returncode==0,p.stderr;return p.stdout
def inventory(path):return json.loads(run([ARCHIVER,'list',path,'--verify']))
def art_cook():
    report=json.loads((WORK/'garrison-art-build.json').read_text());assert report['status']=='succeeded'
    project=Path(report.get('project',str(PROJECT)))
    cook=json.loads((project/'mod-project.json').read_text())['cooks'][-1];assert not cook['live_reload'];assert sha(Path(cook['archive']))==cook['sha256'];return cook
def guard():
    rows=json.loads((WORK/'source-baseline.json').read_text())
    for file,value in rows.items():assert sha(ROOT/file)==value,file
    return len(rows)
def media_paths(inv):
    prefixes=[f'art/scenario/garrison/tuareg_refined_art/units/tuareg_age{a}/body/' for a in range(1,5)]+['art/scenario/tuareg/tuareg_agher_refined/','art/scenario/tuareg/tuareg_long_spear_refined/']
    return [r for r in inv['members'] if any(r['path'].lower().startswith(p) for p in prefixes)]
def prepare():
    assert not CANDIDATE.exists()
    sources=[ROOT/'Berber_future_kingdom.aoe4mod',*sorted(p for p in (ROOT/'assets').rglob('*') if p.is_file())]
    (WORK/'source-baseline.json').write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in sources},indent=2))
    before=ROOT/'output/tuareg_art_guard_trial/candidate';shutil.copytree(before,CANDIDATE);changed=[]
    for age in range(1,5):
        p=CANDIDATE/f'assets/attrib/instances/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.xml';raw=p.read_bytes()
        old=f'art\\scenario\\garrison\\tuareg_art_v2\\units\\tuareg_age{age}\\body\\model'.encode();new=old.replace(b'tuareg_art_v2',b'tuareg_refined_art');assert raw.count(old)==1
        shield=b'art\\scenario\\tuareg\\tuareg_agher_shield\\tuareg_agher_shield';newshield=b'art\\scenario\\tuareg\\tuareg_agher_refined\\tuareg_agher_refined';assert raw.count(shield)==1
        raw=raw.replace(old,new).replace(shield,newshield)
        raw=raw.replace(f'Tuareg Age {age}: Abbasid body, inherited Donso shield'.encode(),f'Tuareg Age {age}: refined weighted body and lower-fitted hide shield'.encode())
        p.write_bytes(raw);changed.append(p.relative_to(CANDIDATE).as_posix())
    for index in range(1,6):
        p=CANDIDATE/f'assets/attrib/instances/attachments/attachment_lists/garrison/tuareg_weapon_lists/tuareg_spear_visual_{index}.xml';raw=p.read_bytes()
        old=b'art\\scenario\\tuareg\\tuareg_leaf_spear\\tuareg_leaf_spear';new=b'art\\scenario\\tuareg\\tuareg_long_spear_refined\\tuareg_long_spear_refined';assert raw.count(old)>=1
        p.write_bytes(raw.replace(old,new));changed.append(p.relative_to(CANDIDATE).as_posix())
    for p in (before/'assets').rglob('*'):
        if p.is_file() and p.relative_to(before).as_posix() not in changed:assert sha(p)==sha(CANDIDATE/p.relative_to(before)),p
    (WORK/'candidate-source.json').write_text(json.dumps({'guid':GUID,'changed_sources':changed,'original_sources_preserved':guard(),'animation_controller':'byte-preserved; instant moving transition not solved','spear_length_m':4.375,'shield_height_m':1.15},indent=2));print('REFINED_CANDIDATE_PREPARED',flush=True)
def build():
    cook=art_cook();archive=Path(cook['archive']);rows=media_paths(inventory(archive));assert sum(r['path'].endswith('.rrgeom') for r in rows)==6
    staged=[]
    for row in rows:
        out=CANDIDATE/'assets'/row['path'];assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True);run([ARCHIVER,'extract-member',archive,row['path'],out]);staged.append({'path':row['path'],'sha256':sha(out)})
    (WORK/'candidate-media-sources.json').write_text(json.dumps({'art_archive_sha256':cook['sha256'],'files':staged},indent=2))
    sys.path.insert(0,str(ROOT/'art/tuareg_shield'));import shrek_trigger_probe as builder
    builder.WORK=WORK;builder.CANDIDATE=CANDIDATE;builder.build()
def package():
    guard();baseinfo=json.loads((ROOT/'output/tuareg_art_guard_trial/delivery.json').read_text());base=Path(baseinfo['archive']);assert sha(base)==baseinfo['archive_sha256']
    build=json.loads((WORK/'candidate-build.json').read_text());assert build['status']=='succeeded' and build['exit_code']==0
    donor=Path(build['archives'][0]['path']);assert sha(donor)==build['archives'][0]['sha256']
    source=json.loads((WORK/'candidate-source.json').read_text());tuning=['attrib/'+p.removeprefix('assets/attrib/instances/').removesuffix('.xml')+'.rgd' for p in source['changed_sources']]
    actual={r['path'].lower():r['path'] for r in inventory(donor)['members']};tuning=[actual[p.lower()] for p in tuning]
    package=WORK/'package';package.mkdir();middle=WORK/'tuning-graft.sga';final=package/'Berber_future_kingdom.sga'
    run([ARCHIVER,'graft',base,donor,middle,*tuning]);art=art_cook();media=media_paths(inventory(Path(art['archive'])))
    run([ARCHIVER,'graft',middle,art['archive'],final,*[r['path'] for r in media]])
    inv=inventory(final);old={r['path'].lower():r for r in inventory(base)['members']};new={r['path'].lower():r for r in inv['members']}
    changed=[k for k,v in old.items() if (v['crc'],v['size'])!=(new[k]['crc'],new[k]['size'])];assert set(changed)=={p.lower() for p in tuning}
    assert inv['archive']['name'].replace('-','').lower()==GUID and inv['archive']['verification']['verified']
    out=WORK/'readback';assert not out.exists();run([ARCHIVER,'unpack',final,'--output',out])
    for p in [GM,MODULE]:assert sha(out/new[p.lower()]['path'])==sha(CANDIDATE/'assets'/p)
    for row in json.loads((WORK/'candidate-media-sources.json').read_text())['files']:assert sha(out/row['path'])==row['sha256']
    result={'version':VERSION,'guid':GUID,'archive':str(final),'archive_sha256':sha(final),'members':len(new),'changed_baseline_members':changed,'unchanged_baseline_members':len(old)-len(changed),'added_members':sorted(set(new)-set(old)),
            'original_sources_preserved':guard(),'new_models':6,'spear_length_m':4.375,'spear_increase_percent':75,'shield_height_m':1.15,'guard_controller':'byte-identical to prior trial; existing body motion works','instant_moving_q':'unresolved','native_acceptance':'pending user'}
    (WORK/'archive-inventory.json').write_text(json.dumps(inv,indent=2));(package/'EVIDENCE.json').write_text(json.dumps(result,indent=2));shutil.copy2(WORK/'TEST-TRIAL.txt',package/'TEST-TRIAL.txt')
    for name in ('source-validation.json','shield-fit.json','garrison-art-build.json','candidate-build.json','art-cook.log'):
        shutil.copy2(WORK/name,package/name)
    successful_run=sorted((Path(json.loads((WORK/'garrison-art-build.json').read_text())['project'])/'dist/cook').iterdir(),key=lambda p:p.stat().st_mtime)[-1]
    shutil.copy2(successful_run/'logs/EssenceEditorLog.txt',package/'art-editor.log')
    shutil.copy2(WORK/'candidate-build/logs/EssenceEditorLog.txt',package/'tuning-editor.log')
    sys.path.insert(0,str(EXT));from garrison_shared import mod_bundle
    mod_bundle.write_manifest(package,bundle_key='berber_future_kingdom',members=[{'mod_key':'berber_future_kingdom','role':'tuning','path':final.name,'sha256':sha(final)}],details={'id':'berber_future_kingdom','name':'The Berber Dynasties','version':VERSION,'summary':'Refined Tuareg age skins, lower shield fit and 75% longer spear','author':'hossein81 and marcokistan','updated':'2026-10-11','min_garrison':'0.1.3','content_types':['game-mode','tuning-pack'],'description':'Stock-derived weighted anatomy, unique 1024 PBR atlases and tailored Tuareg wraps. Shield height retained, lower grip-relative fit; spear length 4.375m. Existing gameplay and native motion retained. Immediate moving Q remains unresolved. Solo visual trial.','changelog':'Improved art, shield fitting and longer spear; no gameplay rebalance or new animation claim.'})
    zip_path=WORK/f'berber_future_kingdom-{VERSION}.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None and hashlib.sha256(z.read(final.name)).hexdigest()==result['archive_sha256']
    result.update(zip=str(zip_path),zip_sha256=sha(zip_path));(WORK/'delivery.json').write_text(json.dumps(result,indent=2));print('REFINED_TRIAL_READY',str(zip_path),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','build','package']);globals()[p.parse_args().stage]()
