from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];DESIGN=ROOT/'Design/asset_overhaul';OUT=ROOT/'output/berber_update_0_2_0'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
delivery=read(OUT/'delivery.json');assert delivery['status']=='build and readback passed; native acceptance pending'
zip_path=Path(delivery['zip']);assert sha(zip_path)==delivery['zip_sha256']
assert sha(ROOT/'archives/Berber_future_kingdom.sga')==delivery['archive_sha256']
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    package=read(OUT/'package/garrison.json');assert package['details']['version']=='0.2.0'
    assert hashlib.sha256(z.read('Berber_future_kingdom.sga')).hexdigest()==delivery['archive_sha256']
manifest=read(DESIGN/'BUILD_MANIFEST.json')
tent=manifest['pending_assets'].pop(next(i for i,v in enumerate(manifest['pending_assets']) if v['asset_id']=='building.tent'))
tent.update(approval='Iteration 002 accepted by user 2026-10-12',stage='included_in_update_native_pending',
    integration_status='production identity source and current cook combined with Garrison visual resources',
    garrison_source='art/tribal_tent/garrison_library_0_2_0/Mods/berber_tent_art_020',
    export_source='art/tribal_tent/game_export_0_2_0_v3/Berber_Tribal_Tent_Game_Export_0_2_0.blend',
    build_recipe='research/build_berber_update_0_2_0.py',construction='English House construction visuals; Tent gameplay retained',
    damage_geometry='inherited stock support; custom damage/ruins pending',owner_colour='static palette; dynamic owner-colour shader pending',
    included_version='0.2.0',native_acceptance='pending user')
manifest['approved_assets'].append(tent)
tuareg=next(v for v in manifest['approved_assets'] if v['asset_id']=='unit.tuareg')
tuareg.update(integration_status='ported into current production source and update 0.2.0',included_version='0.2.0',native_update_acceptance='pending user; previous appearance approval retained')
manifest['latest_build']={'version':'0.2.0','zip':zip_path.relative_to(ROOT).as_posix(),'zip_sha256':delivery['zip_sha256'],'archive_sha256':delivery['archive_sha256'],'evidence':'output/berber_update_0_2_0/delivery.json','native_acceptance':'pending user'}
manifest['next_asset']='pending user selection'
manifest['integration_rules'].append('Tent identity XML registers references only: every release must combine the exact approved Garrison tier RGDs and cooked model/stamp media after production cook. An ordinary Content Editor cook alone is incomplete.')
manifest['build_policy']='Build on user request; every delivered version updates the same Berber bundle and original project GUID. Include approved progress so far, with native acceptance separate.'
write(DESIGN/'BUILD_MANIFEST.json',manifest)
inventory=read(DESIGN/'ASSET_INVENTORY.json')
for item in inventory['items']:
    if item['id']=='building.tent':item.update(visual_status='approved_iteration_002',integration_status='included_in_update_0.2.0_native_pending',accepted_iteration='002',included_version='0.2.0',native_acceptance='pending user')
    if item['id']=='unit.tuareg':item.update(integration_status='ported_into_production_update_0.2.0',included_version='0.2.0',native_update_acceptance='pending user; remaining work deferred to end')
write(DESIGN/'ASSET_INVENTORY.json',inventory)
p=DESIGN/'ASSET_INVENTORY.md';text=p.read_text(encoding='utf-8').replace('001 general designs approved; 002 style review pending','002 approved; included in update 0.2.0; native test pending');p.write_text(text,encoding='utf-8')
p=DESIGN/'PROGRESS.md';text=p.read_text(encoding='utf-8')
text=text.replace('Main-source integration is pending.', 'Accepted Tuareg art and stock-guard Q are now integrated into production update 0.2.0; native update acceptance remains pending.')
text=text.replace('- Port accepted source/media/reference wiring into the main project when executing the production integration/build request.','- Main source/media/reference port completed in 0.2.0; verify the consolidated native match.')
text=text.replace('Current asset: Tribal Tent, four age variants. Iteration 001 general designs are approved and preserved; iteration 002 AoE4-inspired finish is saved and awaits style review. No export or mod build.',
    'Current asset: Tribal Tent 002 approved and included in Berber update 0.2.0 alongside the accepted Tuareg. Construction, age switching, influence/production, fitting and damage behaviour await native testing. Next asset awaits user selection.')
text+='\n- 2026-10-12: User approved Tent 002 and requested a build including Tuaregs. Shipped update 0.2.0 under the original GUID/bundle. Model export, production cook and archive/ZIP readback passed. Ability, weapons, upgrades, SBPS, voices and locale sources unchanged. Native test pending; moving-Q delay, dynamic tent owner colour and custom ruins remain outstanding. Rollback: output/berber_update_0_2_0/rollback.\n'
p.write_text(text,encoding='utf-8')
write(DESIGN/'BUILDS.json',{'builds':[manifest['latest_build']]})
print(json.dumps({'version':'0.2.0','zip_bytes':zip_path.stat().st_size,'archive_members':delivery['members'],'records_updated':True,'native_acceptance':'pending user'}))
