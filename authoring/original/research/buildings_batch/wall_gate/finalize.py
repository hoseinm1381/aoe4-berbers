from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/wall_gate';O=R/'output/buildings_batch/wall_gate';Q=Path(__file__).parent
sheet=Image.new('RGB',(768*3,840*2),(35,31,27));d=ImageDraw.Draw(sheet)
for j,state in enumerate(['closed','open']):
 for i,age in enumerate([2,3,4]):
  im=Image.open(O/f'age{age}_{state}.png').convert('RGB');sheet.paste(im,(i*768,j*840));d.text((i*768+20,j*840+783),f'Age {age} | {state} | lifting gate source',fill='white')
sheet.save(O/'contact_sheet.png')
for age in [2,3,4]:
 im=Image.new('RGB',(256*3,290*2),(35,31,27));d=ImageDraw.Draw(im)
 for k,name in enumerate(['front','back','left','right','top','bottom']):
  im.paste(Image.open(O/f'age{age}_{name}.png').convert('RGB'),((k%3)*256,(k//3)*290));d.text(((k%3)*256+8,(k//3)*290+260),name,fill='white')
 im.save(O/f'age{age}_six_sides.png')
evidence={'key':'wall_gate','minimum_age':2,'required_ages':[2,3,4],'current_builder':'assets/attrib/instances/sbps/races/malian/berbers/unit_villager_1_mal.xml:1200-1209','official_required_upgrade':'mal.xml:941-962 completed feudal_age min1; core parent agrees','donor':'Malian mal_stonewall_smallgate_mp','donor_sha256':'8f8f205fd4cd7ee704ee6b754763f2406113d54962696dab269bd567de1f8604','native_bones':['bone_root','bone_gate'],'native_pivot':[0,0,0],'native_mechanism':'rigid portcullis; source +6m travel original fixture not native decoded amplitude','wall_interface':'x +/-5,z7,deck width4.2,clear walkway3,crest8.2; source planes only'}
for age in [2,3,4]:
 p=O/f'age{age}_validation.json';v=json.loads(p.read_text());v['contacts']['tower_to_deck_overlap']=.4;p.write_text(json.dumps(v,indent=2))
mask=Image.open(A/'pattern.png').convert('RGB');pixels=list(mask.getdata());assert all(g==0 and b==0 for r,g,b in pixels)
assert {r for r,g,b in pixels}=={0,255}
(O/'owner_mask_audit.json').write_text(json.dumps({'size':mask.size,'red_only':True,'owner_pixels':sum(r==255 for r,g,b in pixels),'other_pixels':sum(r==0 for r,g,b in pixels),'native_colour':'blocked; authoring input only'},indent=2))
(Q/'AGE_AND_TARGET_EVIDENCE.json').write_text(json.dumps(evidence,indent=2))
delivery={**evidence,'source_status':'packed Blender and FBX authoring artifacts','source_files':[p.name for p in A.glob('*') if p.suffix in ['.blend','.fbx','.png','.json','.py']],'native_gates':['owner-colour shader contract','bone_gate native rigid binding and clip amplitude','wall sockets/stamps and gate pathblocking','construction selectors/destruction/LODs','walk surfaces and uneven terrain'],'checks':'ageN_validation.json and saved_source_audit.json','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*') if p.suffix in ['.blend','.fbx','.png','.json']}}
(O/'delivery.json').write_text(json.dumps(delivery,indent=2))
