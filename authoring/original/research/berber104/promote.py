"""Promote only new AI XML and the single controller-import removal."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=HERE/'promotion.json';assert not record.exists(),'Already promoted; inspect recorded hashes'
sources=list((HERE/'source/attrib/instances').rglob('*.xml'))
targets=[ROOT/'assets/attrib/instances'/p.relative_to(HERE/'source/attrib/instances') for p in sources]
assert all(not p.exists() for p in targets),'Existing editable AI XML must not be overwritten'
gm=ROOT/'assets/scar/winconditions/berber_future_kingdom_GM.scar'
before=gm.read_bytes();needle=b'import("ai/berber_ai_controller.scar")';assert before.count(needle)==1
backup=HERE/'pre-promotion-source';assert not backup.exists();backup.mkdir()
shutil.copyfile(gm,backup/gm.name);rows=[]
for source,target in zip(sources,targets):
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 assert sha(source)==sha(target)
 rows.append({'path':str(target),'before':None,'after':sha(target),'source':str(source)})
assert gm.read_bytes()==before,'Editable GM changed during promotion'
gm.write_bytes(before.replace(needle,b'-- Berber1.0.4: native AI owns computer players from match start.'))
rows.append({'path':str(gm),'before':hashlib.sha256(before).hexdigest(),'after':sha(gm),'backup':str(backup/gm.name),'change':'Only controller import replaced; all other editable bytes preserved'})
record.write_text(json.dumps({'status':'passed','files':rows},indent=2)+'\n')
print('PROMOTED',len(rows),'files; unrelated edits preserved')
