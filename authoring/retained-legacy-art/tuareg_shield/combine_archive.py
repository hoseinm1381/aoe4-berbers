"""Add the 20 genuine Garrison variant resources to the complete editor cook."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shield_test'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
ARCHIVER=EXT/'bin/sga-archiver.exe'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inspect(path):return json.loads(subprocess.check_output([str(ARCHIVER),'list',str(path),'--verify'],text=True))
build=json.loads((WORK/'build-result.json').read_text())
assert build['status']=='succeeded' and build['exit_code']==0 and len(build['archives'])==1
base=Path(build['archives'][0]['path']);assert sha(base)==build['archives'][0]['sha256']
donor=WORK/'garrison-models.sga'
if not donor.exists():
    recorded=json.loads((WORK/'evidence/model-variant-inventory.json').read_text())
    shutil.copy2(Path(recorded['archive']['path']),donor)
base_inventory=inspect(base);donor_inventory=inspect(donor)
for inventory in [base_inventory,donor_inventory]:
    assert inventory['archive']['verification']['verified'] is True
    assert inventory['archive']['name'].replace('-','').lower()==GUID
integration=json.loads((WORK/'model-integration.json').read_text())
members=[Path(item['file']).relative_to('assets').as_posix() for item in integration['resources']]
assert len(members)==20 and set(members)<={r['path'] for r in donor_inventory['members']}
output=Path(build['run_root'])/'combined/Berber_future_kingdom.sga'
output.parent.mkdir(exist_ok=True);assert not output.exists()
result=subprocess.run([str(ARCHIVER),'graft',str(base),str(donor),str(output),*members],check=True,capture_output=True,text=True)
final=inspect(output)
assert final['archive']['verification']['verified'] is True
base_members={r['path']:r for r in base_inventory['members']}
final_members={r['path']:r for r in final['members']}
assert set(final_members)==set(base_members)|set(members)
for name,row in base_members.items():
    assert final_members[name]['crc']==row['crc'] and final_members[name]['size']==row['size'],name
assert len(final_members)==263
(WORK/'evidence/editor-inventory-v2.json').write_text(json.dumps(base_inventory,indent=2),encoding='utf-8')
(WORK/'evidence/garrison-graft-v2.json').write_text(result.stdout,encoding='utf-8')
report={'schema':'tuareg-shield-combined-archive/v1','status':'verified','archive':str(output),'sha256':sha(output),
        'editor_archive':str(base),'editor_archive_sha256':sha(base),'editor_members':len(base_members),
        'garrison_donor':str(donor),'garrison_donor_sha256':sha(donor),'grafted_members':members,
        'archive_members':len(final_members),'editor_members_preserved':len(base_members)}
(WORK/'release-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','archive','archive_members','editor_members_preserved']}))
