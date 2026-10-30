import json,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_1';DESIGN=ROOT/'Design/asset_overhaul'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
delivery=read(OUT/'delivery.json');assert delivery['status']=='cook and archive readback passed'
assert sha(Path(delivery['zip']))==delivery['zip_sha256']
assert sha(ROOT/'archives/Berber_future_kingdom.sga')==delivery['archive_sha256']
with zipfile.ZipFile(delivery['zip']) as z:
    assert z.testzip() is None and json.loads(z.read('garrison.json'))['details']['version']=='0.2.1'
manifest=read(DESIGN/'BUILD_MANIFEST.json');last=manifest['latest_build']
tent=next(x for x in manifest['approved_assets'] if x['asset_id']=='building.tent');queued=tent.pop('next_revision')
tent.update(iteration='003',source=queued['source'],source_sha256=queued['source_sha256'],included_version='0.2.1',
    approval='User-requested 2.5x enlargement and 180-degree turn built as 0.2.1',
    garrison_source='art/tribal_tent/garrison_library_0_2_1/Mods/berber_tent_art_020',
    export_source='art/tribal_tent/game_export_0_2_1',build_recipe='research/build_berber_update_0_2_1.py',
    native_acceptance='pending user',scale=2.5,rotation_degrees=180)
for x in manifest['approved_assets']:
    if x['asset_id']=='unit.tuareg':x.update(included_version='0.2.1',integration_status='retained byte-identically from complete update 0.2.0')
latest={'version':'0.2.1','zip':Path(delivery['zip']).relative_to(ROOT).as_posix(),'zip_sha256':delivery['zip_sha256'],'archive_sha256':delivery['archive_sha256'],'evidence':'output/berber_update_0_2_1/delivery.json','native_acceptance':'pending user'}
manifest['latest_build']=latest;write(DESIGN/'BUILD_MANIFEST.json',manifest)
history=read(DESIGN/'BUILDS.json');assert not any(b['version']=='0.2.1' for b in history['builds']);history['builds'].append(latest);write(DESIGN/'BUILDS.json',history)
record=read(ROOT/'art/tribal_tent/iterations/003/iteration.json');assert sha(ROOT/record['blend'])==record['blend_sha256']
record.update(approval_status='user_requested_spec_built',included_version='0.2.1',export_status='four construction-stage models exported and cooked',mod_build=True,native_acceptance='pending user')
write(ROOT/'art/tribal_tent/iterations/003/iteration.json',record)
iterations=read(DESIGN/'tribal_tent/ITERATIONS.json');iterations['iterations']=[record if x['iteration']=='003' else x for x in iterations['iterations']];write(DESIGN/'tribal_tent/ITERATIONS.json',iterations)
inventory=read(DESIGN/'ASSET_INVENTORY.json')
for x in inventory['items']:
    if x['id']=='building.tent':x.update(integration_status='included_in_update_0.2.1_native_pending',included_version='0.2.1',visual_status='003_requested_size_and_facing_built')
    if x['id']=='unit.tuareg':x['included_version']='0.2.1'
write(DESIGN/'ASSET_INVENTORY.json',inventory)
p=DESIGN/'ASSET_INVENTORY.md';text=p.read_text(encoding='utf-8').replace('002 included in 0.2.0; 003 size/facing adjustment saved for next build','003 included in 0.2.1; enlarged/reversed native test pending');p.write_text(text,encoding='utf-8')
p=DESIGN/'PROGRESS.md';text=p.read_text(encoding='utf-8')+'\n- 2026-10-12: Requested update 0.2.1 built with all four tent ages uniformly 2.5x larger and rotated 180 degrees. Qualified atlases, UVs and stage names retained; fresh model cook and archive/ZIP readback passed. Eight tent model members changed; 328 members, including all Tuareg, tuning and SCAR, byte-preserved from 0.2.0. Native test pending. Version 0.2.0 and media rollback retained. Latest input/library: art/tribal_tent/game_export_0_2_1 and garrison_library_0_2_1.\n';p.write_text(text,encoding='utf-8')
print(json.dumps({'version':'0.2.1','zip_integrity':'passed','archive_hash':'verified','changed_members':len(delivery['changed_members']),'preserved_members':delivery['unchanged_members'],'records_updated':True}))
