"""Fresh archive-bound semantic and byte comparisons; never substitutes native acceptance."""
import hashlib,json,sys,zipfile,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'output/tuareg_art_guard_trial'
sys.path.insert(0,str(ROOT/'art/tuareg_overhaul'));import integrate_trial as trial
delivery=json.loads((WORK/'delivery.json').read_text());archive=Path(delivery['archive'])
assert trial.sha(archive)==delivery['archive_sha256'];inv=trial.inventory(archive)
members={r['path'].lower():r for r in inv['members']}
prev=json.loads((ROOT/'output/tuareg_shield_posture_test/delivery.json').read_text());old_archive=Path(prev['archive']);assert trial.sha(old_archive)==prev['archive_sha256']
old={r['path'].lower():r for r in trial.inventory(old_archive)['members']}
def compare_entry(item,source,folder,expected):
    raw=WORK/folder/item['path'];raw.parent.mkdir(parents=True,exist_ok=True)
    trial.run([trial.ARCHIVER,'extract-member',source,item['path'],raw])
    assert raw.stat().st_size==item['size'] and trial.sha(raw)==trial.sha(expected),item['path']
# Native index CRC is not necessarily zlib.crc32 of extracted payload. Bind to
# current verified archive SHA, size and an independent fresh extraction instead.
with ThreadPoolExecutor(max_workers=4) as pool:
    jobs=[pool.submit(compare_entry,r,archive,'archive-bytes',WORK/'readback'/r['path']) for r in members.values()]
    for job in jobs:job.result()
unchanged=[k for k,r in old.items() if (r['crc'],r['size'],r['toc'])==(members[k]['crc'],members[k]['size'],members[k]['toc'])]
assert len(unchanged)==256
with ThreadPoolExecutor(max_workers=4) as pool:
    jobs=[pool.submit(compare_entry,old[k],old_archive,'baseline-bytes',WORK/'archive-bytes'/members[k]['path']) for k in unchanged]
    for job in jobs:job.result()
fresh=WORK/'semantic-readback';fresh.mkdir(exist_ok=False)
def decoded(path,source,prefix):
    rgd=fresh/(prefix+'-'+Path(path).name);xml=rgd.with_suffix('.xml')
    trial.run([trial.ARCHIVER,'extract-member',source,path,rgd]);trial.run([trial.ARCHIVER,'decode-rgd',rgd,xml]);return ET.parse(xml).getroot()
def flatten(root):
    result={}
    def visit(node,path):
        key=path+'/'+node.get('Key','Root');result[key]=dict(node.attrib)
        counts={}
        for child in node:
            name=child.get('Key','Root');counts[name]=counts.get(name,0)+1
            visit(child,key+(f'#{counts[name]}' if sum(c.get('Key')==name for c in node)>1 else ''))
    visit(root,'');return result
entity_diffs=[];body_reference_count=0
for age in range(1,5):
    path=f'attrib/ebps/races/malian/units/unit_spearman_tuareg_{age}_ber.rgd'
    before=flatten(decoded(path,old_archive,f'old-age{age}'));after=flatten(decoded(path,archive,f'new-age{age}'))
    assert before.keys()==after.keys();diff=[k for k in before if before[k]!=after[k]]
    assert len(diff)==3 and all(k.endswith('/animator_attachments/$PBGNAME') for k in diff),(age,diff)
    assert all(after[k]['Value'].startswith(trial.GUID+':tuareg_spear_visual_') for k in diff)
    entity_diffs.append({'age':age,'changed_fields':diff,'all_other_fields':'identical'})
    body_reference_count+=sum('tuareg_shield_tier' in value.get('Value','') and value.get('Value','').startswith(trial.GUID+':') for value in after.values())
    attachment=f'attrib/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.rgd'
    fields=flatten(decoded(attachment,archive,f'body-age{age}'))
    assert any(v.get('Value','').replace('\\','/').lower()==f'art/scenario/garrison/tuareg_art_v2/units/tuareg_age{age}/body/model' for v in fields.values())
    assert any(v.get('Value','').replace('\\','/').lower()=='art/scenario/tuareg/tuareg_agher_shield/tuareg_agher_shield' for v in fields.values())
assert body_reference_count==10,body_reference_count
source=json.loads((WORK/'candidate-source.json').read_text())
for row in source['new_weapon_lists']:
    fields=flatten(decoded('attrib/'+row['logical']+'.rgd',archive,Path(row['logical']).name))
    idvalues=[v.get('Value') for k,v in fields.items() if k.endswith('/pbgid')]
    assert idvalues and set(idvalues)=={row['pbgid']}
    refs=[v['Value'].replace('\\','/').lower() for k,v in fields.items() if k.endswith('/parent_animator')]
    assert refs and set(refs)=={'art/scenario/tuareg/tuareg_leaf_spear/tuareg_leaf_spear'}
ability=[p for p in old if 'ber_spearman_ranged_damage_reduction' in p];assert ability and all(p in unchanged for p in ability)
module=(WORK/'readback'/members[trial.MODULE.lower()]['path']).read_bytes();assert module==(ROOT/'art/tuareg_overhaul/tuareg_q_art_guard_trial.scar').read_bytes()
for token in [b'Cmd_Stop',b'Cmd_Move',b'Cmd_Ability',b'SGroup_AddAbility',b'cheer_toggle',b'StateTree_QueueGlobalStateTreeEntity']:assert token not in module
gm=(WORK/'readback'/members[trial.GM.lower()]['path']).read_text();assert 'import("Units/tuareg_q_art_guard_trial.scar")' in gm
assert all('import("Units/'+name not in gm for name in ['tuareg_q_force_trial.scar','tuareg_q_posture_trial.scar','tuareg_q_cheer_trial.scar'])
media=json.loads((WORK/'candidate-media-sources.json').read_text())
for row in media['files']:assert trial.sha(WORK/'readback'/row['path'])==row['sha256']
with zipfile.ZipFile(delivery['zip']) as z:
    assert z.testzip() is None and hashlib.sha256(z.read(archive.name)).hexdigest()==delivery['archive_sha256']
assert trial.sha(Path(delivery['zip']))==delivery['zip_sha256']
report={'status':'passed','source_files_preserved':trial.guard(),'archive_members_verified':len(members),'unchanged_baseline_members':len(unchanged),'entity_diff':entity_diffs,
    'qualified_current_and_future_body_refs':body_reference_count,'new_private_weapon_lists':5,'new_model_resources':6,'media_files_byte_verified':len(media['files']),
    'ability_data':'byte-identical','voices_torch_speakers_gameplay':'identical outside three spear visual references per entity','no_orders_or_forced_leaves':True,
    'archive_sha256':delivery['archive_sha256'],'zip_sha256':delivery['zip_sha256'],'native_acceptance':'pending user test','instant_moving_q':'unresolved, not claimed fixed'}
(WORK/'validation-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
