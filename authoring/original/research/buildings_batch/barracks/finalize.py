import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/barracks';O=R/'output/buildings_batch/barracks';Q=Path(__file__).parent
sheet=Image.new('RGB',(768,808),'#dad8ce');d=ImageDraw.Draw(sheet)
for age in range(1,5):
 im=Image.open(O/f'age{age}_preview.png').convert('RGB');im.thumbnail((768,768));x=((age-1)%2)*384;y=((age-1)//2)*404;im.thumbnail((384,384));sheet.paste(im,(x,y+20));d.text((x+10,y+4),f'AGE {age}',fill='black')
sheet.save(O/'age_contact_sheet.png')
sheet=Image.new('RGB',(1536,1112),'#dad8ce');d=ImageDraw.Draw(sheet)
for age in range(1,5):
 for j,side in enumerate(['front','back','left','right','top','bottom']):
  x=j*256;y=(age-1)*278;sheet.paste(Image.open(O/f'age{age}_{side}.png').convert('RGB'),(x,y+22));d.text((x+8,y+5),f'Age {age} {side}',fill='black')
sheet.save(O/'sixside_contact_sheet.png')
rows=[]
for age in range(1,5):
 v=json.loads((O/f'age{age}_validation.json').read_text());rows.append({'age':age,'objects':len(v['objects']),'guards_pass':all(x['finite'] and x['positive_scale'] and x['non_manifold']==0 and x['degenerate_faces']==0 and x['uv_zero_area_faces']==0 and x['outward_signed_volume']>0 for x in v['objects']) and all(c['pass'] for c in v['contacts'])})
im=Image.open(A/'pattern.png').convert('RGB');assert all(g==0 and b==0 for r,g,b in im.getdata())
files=[{'path':str(p.relative_to(R)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in A.iterdir() if p.suffix in ['.blend','.fbx','.png','.json']]
delivery={'key':'barracks','inventory_id':'building.barracks','ages':[1,2,3,4],'footprint_m':[6,6],'origin':[0,0,0],'target':'ebps/races/malian/buildings/building_unit_infantry_mal','donor':'Abbasid barracks combined age01, installed Garrison decoded read-only; untouched reference retained','geometry_reuse':False,'checks':rows,'mask':'red-only shared UV, neutral cloth annotations; native route blocked','construction':'cumulative object stage manifests, source only','native_gates':['shader owner colour route','native attachment marker mapping / emergence / rally','construction selectors','LOD and damage state','small cook/readback','solo scale appearance two-owner colour'],'production_changed':False,'files':files}
delivery['saved_source_fbx_audit']=json.loads((O/'saved_source_fbx_audit.json').read_text())
delivery['age_evidence']='research/buildings_batch/barracks/AGE_AND_TARGET_EVIDENCE.json'
delivery['active_modular_states']='Stock military outskirts _01 (I onward) and _03 (III onward) retained; no modular replacement claim'
delivery['visual_review']='All four perspectives and six orthographic sides inspected; coplanar west wall repaired and regenerated'
delivery['process_status']={'build_exit':0,'audit':'completed saved report for all ages; task-owned audit GUI remained alive after script, terminated exact recorded PID 23684','audit_exit_after_cleanup':4294967295}
(O/'delivery.json').write_text(json.dumps(delivery,indent=2));print(json.dumps(rows))

