"""Capture requested release inputs and explicit unresolved native contracts."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_3_0';OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
batch=json.loads((ROOT/'Design/asset_overhaul/BUILDINGS_BATCH.json').read_text(encoding='utf-8'))
base=json.loads((ROOT/'output/berber_update_0_2_1/delivery.json').read_text(encoding='utf-8'))
assert sha(Path(base['archive']))==base['archive_sha256']
assert sha(ROOT/'archives/Berber_future_kingdom.sga')==base['archive_sha256']
rows=[]
for row in batch['rows']:
    if row['id']=='building.tent':continue
    for source in row['sources']:
        path=ROOT/source['path'];assert sha(path)==source['sha256']
    rows.append({'id':row['id'],'ages':row['ages'],'sources':row['sources'],'targets':row['blueprint_targets'],'source_paths':row['source_paths'],'delivery_records':row['delivery_records'],'export_status':'author FBX/stage manifests; Garrison construction export not yet recorded','native_player_colour':'unqualified'})
colour=json.loads((ROOT/'output/buildings_batch/player_colour/qualification.json').read_text(encoding='utf-8'))
structure=json.loads((ROOT/'output/buildings_batch/player_colour/structure_probe/qualification.json').read_text(encoding='utf-8'))
report={'requested_version':'0.3.0','project_guid':'1d3145e8-f1b2-427f-8bb0-067851fcf0f1','status':'inputs_verified_native_integration_gates_unresolved',
        'verified_base_version':'0.2.1','verified_base_archive_sha256':base['archive_sha256'],'families':len(rows),'age_sources':sum(len(r['sources']) for r in rows),
        'inputs':rows,'colour_probe':colour,'structure_probe':structure,'required_before_complete_release':[
            'Qualified native player-colour encoding for every building; source masks alone do not meet the standing requirement',
            'Garrison one-atlas construction export/cook and verified model dependencies for 92 source variants',
            'Private age attachment wiring preserving actual parent categories/graphs, source identities and gameplay',
            'Native gate motion, farm/camp state, wall walking/terrain and dock/ship interfaces; authored Actions are not native replacements',
            'Landmark render-scale reconciliation and Fez actual build-target visual wiring',
            'Fresh production cook, archive readback and complete package verification'],
        'production_modified':False,'zip_created':False,'no_relabelled_baseline':True}
(OUT/'release-input-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(OUT/'SOURCE_HASHES.json').write_text(json.dumps({s['path']:s['sha256'] for r in rows for s in r['sources']},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified_families':len(rows),'verified_age_sources':report['age_sources'],'status':report['status'],'zip_created':False}))
