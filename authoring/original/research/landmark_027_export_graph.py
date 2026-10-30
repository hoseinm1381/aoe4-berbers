"""Supported construction-model selector graft against actual landmark graphs."""
import sys,json,hashlib,struct,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7/qualification'
sys.path.insert(0,r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison')
from garrison_shared import relic_chunky as rc,building_project as bp
def selectors(raw):
 result={}
 for c in rc.walk(rc.parse(raw).roots):
  if c.tag!=b'MSD ' or len(c.payload)<=4:continue
  name,at=rc.read_lp_string(c.payload,0);count=struct.unpack_from('<I',c.payload,at)[0];at+=4;members=[]
  for i in range(count):
   value,at=rc.read_lp_string(c.payload,at);members.append(value)
  assert at==len(c.payload),(name,at,len(c.payload))
  result[name]=members
 return result
def conditions(raw):
 result=[]
 for c in rc.walk(rc.parse(raw).roots):
  if c.tag!=b'CNBP':continue
  at=4;count=struct.unpack_from('<I',c.payload)[0];rows=[]
  for i in range(count):
   kind,flag,string_type=struct.unpack_from('<IBI',c.payload,at);at+=9
   assert (kind,flag,string_type)==(2,0,1),(kind,flag,string_type)
   machine,at=rc.read_lp_string(c.payload,at);value,at=rc.read_lp_string(c.payload,at)
   assert machine=='life_cycle_state';rows.append(value)
  assert at==len(c.payload)
  result.append(rows)
 return result
new=next((OUT/'readback').rglob('model.rgm')).read_bytes();rows=json.loads((OUT/'source/building.json').read_text())['parts'];report={}
for key,stem in [('ribat','mal_landmark_b_age02'),('funduq','abb_arsenal_control_age03')]:
 stock=next((ROOT/'output/berber_update_0_2_7/inventory/extracted').rglob(stem+'.rgm'));graph=stock.read_bytes()
 for profile in ['english-house','english-barracks']:
  try:
   encoded=bp.construction_model(new,graph,rows,profile_id=profile)
   tables=selectors(encoded);bad={k:[m for m in v if not m.startswith('garrison_part_')] for k,v in tables.items()};bad={k:v for k,v in bad.items() if v}
   dst=OUT/f'{key}-{profile}.rgm';dst.write_bytes(encoded)
   predicates=conditions(encoded);assert len(predicates)==len(tables)
   enabled={}
   for state in ['construct_'+f'{s:02}' for s in range(0,100,5)]+['healthy','preview','targeting']:
    enabled[state]=sorted({member for table,predicate in zip(tables.values(),predicates) if state in predicate for member in table})
   expected={state:sorted(r['name'] for r in rows if state in ['healthy','preview','targeting'] or r['first_stage']<=int(state.rsplit('_',1)[1])) for state in enabled}
   assert enabled==expected,(key,profile,enabled,expected)
   report[key+'_'+profile]={'stock_sha256':hashlib.sha256(graph).hexdigest(),'encoded_sha256':hashlib.sha256(encoded).hexdigest(),'tables':tables,'predicates':dict(zip(tables,predicates)),'enabled_parts_per_state':enabled,'all_stage_visibility_exact_expected':True,'unresolved_donor_members':bad,'state_route':'Exact original stock RGO retained; RGM selector graph emitted by installed supported building_project.construction_model. Stage tables partition parts; native CNBP lists activate each bucket from its first stage through completion.'}
  except Exception as error:report[key+'_'+profile]={'error':str(error)}
(OUT/'graph-evidence.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:({'error':v['error']} if 'error' in v else {'selectors':len(v['tables']),'unresolved':len(v['unresolved_donor_members']),'names':list(v['tables'])}) for k,v in report.items()},indent=2))
