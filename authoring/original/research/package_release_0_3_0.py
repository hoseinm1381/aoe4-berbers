import json,os,subprocess,hashlib,zipfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_3_0'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';ARCH=EXT/'bin/sga-archiver.exe'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def run(label,args):
    with (OUT/(label+'.log')).open('w',encoding='utf-8') as f:
        p=subprocess.run([str(a) for a in args],stdout=f,stderr=subprocess.STDOUT,timeout=1200)
    assert p.returncode==0,(label,p.returncode)
    return (OUT/(label+'.log')).read_text(encoding='utf-8')
bindings=read(OUT/'bindings-report.json');assert bindings['status']=='passed' and len(bindings['families'])==31
art=read(OUT/'art-build.json');assert art['status']=='passed'
old=read(ROOT/'output/berber_update_0_2_1/delivery.json');base=Path(old['archive']);assert sha(base)==old['archive_sha256']
donor=Path(art['cook']['archive']);assert sha(donor)==art['cook']['sha256']
inventory=json.loads(run('art-inventory',[ARCH,'list',donor,'--verify']))
media=[r['path'] for r in inventory['members'] if r['path'].startswith(('art/scenario/garrison/berber_buildings_030/','art/stamps/garrison/berber_buildings_030/'))]
assert sum(p.endswith('.rrgeom') for p in media)==92
folder=OUT/'package';folder.mkdir(exist_ok=True);middle=OUT/'with-art.sga';final=folder/'Berber_future_kingdom.sga'
run('graft-all-art',[ARCH,'graft',base,donor,middle,*media])
filelist=OUT/'bindings-list.txt';filelist.write_text('\n'.join(x['member']+'='+x['file'] for x in bindings['payloads'])+'\n',encoding='utf-8')
run('set-owned-bindings',[ARCH,'set-members',middle,filelist,final])
new=json.loads(run('final-inventory',[ARCH,'list',final,'--verify']));assert new['archive']['verification']['verified']
assert new['archive']['name'].replace('-','').lower()=='1d3145e8f1b2427f8bb0067851fcf0f1'
fresh=OUT/'final-readback';run('final-unpack',[ARCH,'unpack',final,'--output',fresh])
allowed={x['member'] for x in bindings['payloads']}|set(media)
unchanged=[];changed=[]
for p in (OUT/'baseline-readback').rglob('*'):
    if not p.is_file():continue
    name=p.relative_to(OUT/'baseline-readback').as_posix();assert (fresh/name).exists()
    if sha(p)!=sha(fresh/name):assert name in allowed;changed.append(name)
    else:unchanged.append(name)
for item in bindings['payloads']:assert sha(fresh/item['member'])==item['sha256']
for name in media:assert sha(fresh/name)==sha(OUT/'donor-readback'/name)
evidence={'version':'0.3.0','status':'art cook and archive readback passed; native acceptance pending',
    'building_families_bound':31,'new_building_age_models':92,'retained_tent_ages':4,'Tuareg':'retained byte-identically from0.2.1',
    'families':bindings['families'],'changed_existing_members':changed,'unchanged_existing_members':len(unchanged),
    'native_player_colour':'not qualified; fixed source palettes retained',
    'known_test_limits':['Healthy/static construction visuals use the English House visual encoding profile; native per-building playback not accepted',
        'Gates use closed static visual geometry in this first model trial; native open/close game commands remain inherited',
        'Farm/camp growth/resource alternatives and optional emplacement variants are authored but not all selected by native graph',
        'Wall/walk/terrain and dock ship/shoreline behaviour require native checks',
        'Stock damage/wreck/outskirts support retained where present; new custom ruined models not claimed'],
    'archive':str(final),'archive_sha256':sha(final),'native_acceptance':'pending user'}
write(folder/'EVIDENCE.json',evidence)
manifest=read(ROOT/'output/berber_update_0_2_1/package/garrison.json');manifest['members'][0]['sha256']=sha(final)
manifest['details'].update(version='0.3.0',summary='All31 Berber building and landmark model families — native trial',description='Includes92 newly cooked building age models, the larger reversed tent and accepted Tuareg art. Static visual trial; owner colour and functional animation/navigation acceptance remain pending.',changelog='Private visual tier bindings for every building family, including active Fez target. Existing gameplay data and Tuareg resources preserved.')
write(folder/'garrison.json',manifest)
instructions='''BERBER0.3.0 — ALL BUILDING MODELS TEST
Close AoE4. Import berber_future_kingdom-0.3.0.zip into Garrison, confirm0.3.0, enable and launch through Play.
Fresh custom match: Tuning The Berber Dynasties; Game Mode Berber Civilization; Civilization Malians.
All31 new building/landmark families are wired to their new age models. The4 tent variants and Tuareg body/shield/long spear/Q resources from0.2.1 are retained.
Test first ordinary buildings by age, construction and production; then all six landmarks, existing structures after age-up, placement and ground/overlap. Check the Fez landmark because its flat build-command target has also been visually bound.
TEST KNOWN LIMITS: native player-colour shader is not qualified; palette is currently fixed. Gate visual geometry is a static closed model in this first trial even though inherited game commands/pathing may open; report this for0.3.x. Crop/resource and optional emplacement alternative meshes are authored but not fully controlled. Check wall connectors/walking/slopes, dock cardinal placement/ship exits and native selection. Inherited damaged/wreck/outskirt geometry may appear stock.
Record building, age, whether built before age-up, screenshot/video and warnings.log. Confirm Tuareg movement/combat/Q and Tent influence/free-villager logic remain unchanged; moving Q delay is retained.
ROLLBACK: close game and reimport0.2.1 ZIP; source/model hash records and previous archive remain preserved.
This package is a user-authorized full-model trial, not native acceptance or multiplayer certification.
'''
(folder/'INSTALL_AND_TEST.txt').write_text(instructions,encoding='utf-8')
for n in ('export-report.json','art-build.json','bindings-report.json','texture-normalization.json'):shutil.copy2(OUT/n,folder/n)
archivezip=OUT/'berber_future_kingdom-0.3.0.zip'
with zipfile.ZipFile(archivezip,'w',zipfile.ZIP_DEFLATED) as z:
    for p in folder.iterdir():z.write(p,p.name)
with zipfile.ZipFile(archivezip) as z:assert z.testzip() is None and hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
evidence.update(zip=str(archivezip),zip_sha256=sha(archivezip));write(OUT/'delivery.json',evidence)
rollback=OUT/'rollback';rollback.mkdir(exist_ok=True);shutil.copy2(ROOT/'archives/Berber_future_kingdom.sga',rollback/'Berber_future_kingdom-0.2.1.sga')
shutil.copy2(final,ROOT/'archives/Berber_future_kingdom.sga')
print('BERBER0.3.0_READY',str(archivezip),flush=True)
