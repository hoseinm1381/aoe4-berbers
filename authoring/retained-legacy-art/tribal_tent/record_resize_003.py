from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tribal_tent/iteration003';ART=ROOT/'art/tribal_tent/iterations/003';DESIGN=ROOT/'Design/asset_overhaul'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=read(OUT/'source-validation.json');check=read(OUT/'saved-source-verification.json')
assert report['status']==check['status']=='passed'
baseline=read(ROOT/'art/tribal_tent/iterations/002/iteration.json');assert sha(ROOT/baseline['blend'])==baseline['blend_sha256']
delivery=read(ROOT/'output/berber_update_0_2_0/delivery.json');assert sha(ROOT/'archives/Berber_future_kingdom.sga')==delivery['archive_sha256']
record={'asset_id':'building.tent','iteration':'003','recorded':'2026-10-12','approval_status':'requested_transform_saved',
    'approval_scope':'User accepted the model in game and requested 2.5x dimensions and opposite facing; new native result awaits next requested build.',
    'based_on_accepted_iteration':'002','blend':Path(report['blend']).relative_to(ROOT).as_posix(),'blend_sha256':report['blend_sha256'],
    'scale':2.5,'rotation_degrees':180,'ages':[1,2,3,4],'verification':'output/tribal_tent/iteration003/saved-source-verification.json',
    'export_status':'pending next requested build; re-export transformed meshes and construction stages',
    'mod_build':False,'native_acceptance':'pending','gameplay':'unchanged'}
write(ART/'iteration.json',record)
history=read(DESIGN/'tribal_tent/ITERATIONS.json');history['active_iteration']='003';history['iterations'].append(record);write(DESIGN/'tribal_tent/ITERATIONS.json',history)
manifest=read(DESIGN/'BUILD_MANIFEST.json');tent=next(x for x in manifest['approved_assets'] if x['asset_id']=='building.tent')
tent['next_revision']={'iteration':'003','source':record['blend'],'source_sha256':record['blend_sha256'],'scale':2.5,'rotation_degrees':180,'status':'queued_for_next_requested_build','scope':'exact user-requested transform; re-encode all four construction models/stamps before cooking'}
tent['native_observations']={'2026-10-12':'User says model is great; requests larger size and opposite facing. Supplied screenshot shows an Age II tent. Full four-age/construction/gameplay acceptance not inferred.'}
write(DESIGN/'BUILD_MANIFEST.json',manifest)
inventory=read(DESIGN/'ASSET_INVENTORY.json');item=next(x for x in inventory['items'] if x['id']=='building.tent')
item.update(iteration='003',visual_status='requested_resize_and_reverse_saved',next_build_source=record['blend'])
item['art_sources'].append(record['blend']);item['iteration_record']='art/tribal_tent/iterations/003/iteration.json';write(DESIGN/'ASSET_INVENTORY.json',inventory)
p=DESIGN/'PROGRESS.md';text=p.read_text(encoding='utf-8')
text+='\n- 2026-10-12: User likes the in-game tent model; requested uniform 2.5x dimensions and 180-degree reversed facing. Saved and reloaded iteration 003 for all four ages, with unchanged UVs/topology and exact vertex-transform verification. Accepted 002 and update 0.2.0 remain preserved. Queue 003 re-export/integration for the next requested build; gameplay/placement footprint source unchanged.\n';p.write_text(text,encoding='utf-8')
p=DESIGN/'ASSET_INVENTORY.md';text=p.read_text(encoding='utf-8').replace('002 approved; included in update 0.2.0; native test pending','002 included in 0.2.0; 003 size/facing adjustment saved for next build');p.write_text(text,encoding='utf-8')
print('TENT_003_RECORDED_FOR_NEXT_BUILD')
