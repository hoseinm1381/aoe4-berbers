"""Verify the current archive/ZIP and byte-preserved gameplay, using fresh extraction."""
import json,sys,hashlib,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'output/tuareg_refined_trial'
sys.path.insert(0,str(ROOT/'art/tuareg_refined'));import integrate_trial as trial
delivery=json.loads((WORK/'delivery.json').read_text());archive=Path(delivery['archive']);assert trial.sha(archive)==delivery['archive_sha256']
baseinfo=json.loads((ROOT/'output/tuareg_art_guard_trial/delivery.json').read_text());base=Path(baseinfo['archive']);assert trial.sha(base)==baseinfo['archive_sha256']
current={r['path'].lower():r for r in trial.inventory(archive)['members']};old={r['path'].lower():r for r in trial.inventory(base)['members']}
unchanged=[k for k,r in old.items() if (r['crc'],r['size'],r['toc'])==(current[k]['crc'],current[k]['size'],current[k]['toc'])]
assert len(unchanged)==308
def raw_compare(row,source,folder,expected):
    p=WORK/folder/row['path'];p.parent.mkdir(parents=True,exist_ok=True);trial.run([trial.ARCHIVER,'extract-member',source,row['path'],p])
    assert p.stat().st_size==row['size'] and trial.sha(p)==trial.sha(expected),row['path']
with ThreadPoolExecutor(max_workers=4) as pool:
    jobs=[pool.submit(raw_compare,r,archive,'fresh-archive-bytes',WORK/'readback'/r['path']) for r in current.values()]
    for job in jobs:job.result()
with ThreadPoolExecutor(max_workers=4) as pool:
    jobs=[pool.submit(raw_compare,old[k],base,'fresh-baseline-bytes',WORK/'fresh-archive-bytes'/current[k]['path']) for k in unchanged]
    for job in jobs:job.result()
semantics=WORK/'semantic-readback';semantics.mkdir(exist_ok=False)
def fields(logical,source,prefix):
    rgd=semantics/(prefix+'-'+Path(logical).name);xml=rgd.with_suffix('.xml');trial.run([trial.ARCHIVER,'extract-member',source,logical,rgd]);trial.run([trial.ARCHIVER,'decode-rgd',rgd,xml]);root=ET.parse(xml).getroot();data={}
    def visit(node,path):
        key=path+'/'+node.get('Key','Root');data[key]=dict(node.attrib);seen={}
        for child in node:
            name=child.get('Key','Root');seen[name]=seen.get(name,0)+1
            visit(child,key+(f'#{seen[name]}' if sum(c.get('Key')==name for c in node)>1 else ''))
    visit(root,'');return data
diffs=[]
for age in range(1,5):
    logical=f'attrib/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.rgd';a=fields(logical,base,f'old-age{age}');b=fields(logical,archive,f'new-age{age}')
    assert a.keys()==b.keys();changes=[k for k in a if a[k]!=b[k]];assert len(changes)==2
    assert all('animator' in k for k in changes),changes
    values=[v.get('Value','').replace('\\','/').lower() for v in b.values()]
    assert f'art/scenario/garrison/tuareg_refined_art/units/tuareg_age{age}/body/model' in values
    assert 'art/scenario/tuareg/tuareg_agher_refined/tuareg_agher_refined' in values
    diffs.append({'body_age':age,'changed_visual_fields':changes,'identity_and_other_fields':'identical'})
for index in range(1,6):
    logical=f'attrib/attachments/attachment_lists/garrison/tuareg_weapon_lists/tuareg_spear_visual_{index}.rgd';a=fields(logical,base,f'old-spear{index}');b=fields(logical,archive,f'new-spear{index}')
    assert a.keys()==b.keys();changes=[k for k in a if a[k]!=b[k]]
    assert changes and all(k.endswith('/parent_animator') for k in changes),changes
    assert all(b[k]['Value'].replace('\\','/').lower()=='art/scenario/tuareg/tuareg_long_spear_refined/tuareg_long_spear_refined' for k in changes)
    diffs.append({'spear_list':index,'changed_visual_fields':changes,'identity_variants_and_other_fields':'identical'})
for key in old:
    if '/ebps/' in key or '/sbps/' in key or '/weapon/' in key or '/abilities/' in key or '/upgrade/' in key:assert key in unchanged,key
for path in [trial.GM,trial.MODULE]:assert trial.sha(WORK/'readback'/current[path.lower()]['path'])==trial.sha(WORK/'candidate/assets'/path)
module=(WORK/'readback'/current[trial.MODULE.lower()]['path']).read_bytes();assert module==(ROOT/'art/tuareg_overhaul/tuareg_q_art_guard_trial.scar').read_bytes()
with zipfile.ZipFile(delivery['zip']) as z:assert z.testzip() is None and hashlib.sha256(z.read(archive.name)).hexdigest()==delivery['archive_sha256']
assert trial.sha(Path(delivery['zip']))==delivery['zip_sha256']
report={'status':'passed','original_sources_preserved':trial.guard(),'archive_members':len(current),'unchanged_baseline_members':len(unchanged),'new_media_files':len(set(current)-set(old)),
 'visual_changes':diffs,'gameplay_entities_squads_weapons_abilities_upgrades_voices':'byte-preserved','native_guard_controller':'byte-preserved','spear_length_m':4.375,'shield_height_m':1.15,
 'zip_sha256':delivery['zip_sha256'],'archive_sha256':delivery['archive_sha256'],'native_art_acceptance':'pending user test','instant_moving_guard':'unresolved'}
(WORK/'validation-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
