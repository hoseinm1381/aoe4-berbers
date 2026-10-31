"""Read the installed Showcase's ability clip and compare the native skeleton."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shrek_animation_test';WORK.mkdir(exist_ok=True)
PREVIOUS=ROOT/'output/tuareg_ability_pose_test'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
shrek=PREVIOUS/'showcase-tuning-readback/art/scenario/a4etk_shrek_fitted_v3/a4etk_shrek_fitted_v3.rhka'
stock=ROOT/'output/tuareg_shield_test/evidence/source/art/civilizations/common/humans/archetypes/base_spearshield/base_spearshield.rhka'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
record={'schema':'tuareg-shrek-animation-inspection/v1','shrek_sha256':sha(shrek),'stock_sha256':sha(stock),'samples':[]}
for label,file in [('shrek',shrek),('spearshield',stock)]:
    raw=file.read_bytes()
    record[label+'_animation_types']=sorted({m.group().decode() for m in re.finditer(rb'hka[A-Za-z0-9_]{3,}',raw)})
for label,file,index in [('shrek',shrek,0),('shrek',shrek,7)]:
    path=WORK/f'{label}-clip-{index}.json'
    if not path.exists():
        result=subprocess.run([str(EXT/'bin/core/garrison-core.exe'),'-m','src.core.animation_clip',
             '--source',str(file),'--expected-sha256',sha(file),'--clip-index',str(index),'--output',str(path)],capture_output=True,text=True)
        (WORK/f'{label}-clip-{index}.log').write_text(result.stdout+result.stderr)
        assert result.returncode==0,(result.returncode,result.stderr[-1200:])
    data=json.loads(path.read_text())
    bones=[(r['bone_name'].lower(),r['parent_index']) for r in data['samples'][0]['bones']]
    target=json.loads((ROOT/'output/tuareg_shield_test/evidence/stock-clip0.json').read_text())
    target_bones=[(r['bone_name'].lower(),r['parent_index']) for r in target['samples'][0]['bones']]
    record['samples'].append({'source':label,'index':index,'name':data['name'],
        'bones':len(bones),'hierarchy_matches_spearshield':bones==target_bones,
        'frames':data['frame_count'],'last_time':data['samples'][-1]['time_seconds'],
        'motion':data.get('motion'),'first_bones':bones[:3]})
(WORK/'inspection.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2),flush=True)
