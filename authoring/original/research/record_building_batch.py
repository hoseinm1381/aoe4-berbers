"""Verify source delivery coverage and preserve the mandatory native colour gate."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];DESIGN=ROOT/'Design/asset_overhaul';OUT=ROOT/'output/buildings_batch'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
batch=read(DESIGN/'BUILDINGS_BATCH.json');rows=[r for r in batch['rows'] if r['id']!='building.tent']
assert len(rows)==31 and all(r['status']=='source_delivery_present' for r in rows)
assert all(r['ages'] and r['preview'] and r['owner_masks'] for r in rows)
source_count=0;mask_audits=[]
for row in rows:
    assert len(row['sources'])==len(row['ages']),(row['id'],len(row['sources']),row['ages'])
    for source in row['sources']:
        assert sha(ROOT/source['path'])==source['sha256'];source_count+=1
    for path in row['owner_masks']:
        with Image.open(ROOT/path) as image:
            rgb=np.asarray(image.convert('RGB'))
            assert not np.any(rgb[:,:,1:]),path
            assert np.any(rgb[:,:,0]>0),path
            mask_audits.append({'path':path,'sha256':sha(ROOT/path),'size':list(image.size),'owner_pixels':int(np.count_nonzero(rgb[:,:,0]))})
delivery=read(ROOT/'output/berber_update_0_2_1/delivery.json')
assert sha(ROOT/'archives/Berber_future_kingdom.sga')==delivery['archive_sha256']
manifest=read(DESIGN/'BUILD_MANIFEST.json');assert sha(ROOT/manifest['production_project'])==manifest['production_project_sha256']
inventory=read(DESIGN/'ASSET_INVENTORY.json');by_id={r['id']:r for r in rows}
for item in inventory['items']:
    if item['id'] in by_id:
        row=by_id[item['id']]
        item.update(visual_status='source_authored_review_pending',integration_status='native_colour_and_export_integration_pending',
            requested_age_variants=row['ages'],art_sources=[x['path'] for x in row['sources']],preview=row['preview'],
            source_delivery_records=row['delivery_records'],player_colour_required=True,player_colour_status='owner_zones_masks_authored_native_encoder_unqualified')
write(DESIGN/'ASSET_INVENTORY.json',inventory)
manifest['updated']='2026-10-13';manifest['next_asset']='batch source review; native player-colour qualification required'
manifest['pending_assets']=[{'asset_id':r['id'],'age_variants':r['ages'],'sources':r['sources'],'delivery_records':r['delivery_records'],
    'approval':'pending user final review','player_colour_required':True,'native_colour':'unqualified structure source/packing/stream contract',
    'stage':'source_authored_not_integrated'} for r in rows]
manifest['building_batch']={'families':31,'source_age_variants':source_count,'fbx_state_exports':sum(r['fbx_count'] for r in rows),
    'review_gallery':'Design/asset_overhaul/BUILDINGS_REVIEW.html','coverage':'Design/asset_overhaul/BUILDINGS_BATCH.json',
    'native_colour_required':True,'native_colour_complete':False,'new_distributable_build':False}
write(DESIGN/'BUILD_MANIFEST.json',manifest)
proof={'date':'2026-10-13','source_building_landmark_families':31,'source_age_variants':source_count,
    'fbx_exports':sum(r['fbx_count'] for r in rows),'mask_audits':mask_audits,
    'all_source_hashes_verified':True,'all_source_masks_red_only_and_nonempty':True,'all_previews_present':True,
    'production_archive_0.2.1_unchanged':True,'project_guid_and_manifest_preserved':True,
    'native_player_colour':'mandatory unresolved gate; no native-complete claim',
    'remaining_gates':['structure material source/packed texture/geometry stream support','material-scoped stock variant access',
        'construction/damage/LOD/animation binding','wall navigation and dock exits','landmark render scale and Fez active-target wiring','native two-player-colour acceptance'],
    'tent':'accepted source003 preserved; four existing red-only masks retained; no native-colour004 produced'}
write(OUT/'BATCH_DELIVERY.json',proof)
p=DESIGN/'PROGRESS.md';text=p.read_text(encoding='utf-8')
text+='\n- 2026-10-13: User requested concurrent per-building source authoring, review only at end and mandatory native player colour. Created all31 other building/landmark families:92 age source variants and243 FBX state exports, with local research/donor references, construction/state manifests, inspected previews and saved-source audits. Central source hashes/red-only masks/preview coverage verified. Source gallery: BUILDINGS_REVIEW.html. No production build;0.2.1 archive/manifest preserved. Native player colour is NOT finished: static object export omits masks; unit substitution fails unit_collection; stock structure team layer7 identified but source packing/stream and material-scoped variant contracts remain unqualified. Tent003 remains preserved with masks, no false004/native colour claim. Full integration/native acceptance pending.\n'
p.write_text(text,encoding='utf-8')
human=DESIGN/'ASSET_INVENTORY.md';lines=human.read_text(encoding='utf-8').splitlines()
for i,line in enumerate(lines):
    if any(line.startswith('| '+id+' |') for id in by_id):
        columns=line.split('|');columns[-2]=' source authored; review/native colour pending ';lines[i]='|'.join(columns)
human.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:proof[k] for k in ('source_building_landmark_families','source_age_variants','fbx_exports','all_source_masks_red_only_and_nonempty','production_archive_0.2.1_unchanged','native_player_colour')}))
