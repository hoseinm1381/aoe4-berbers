from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/blacksmith';O=R/'output/buildings_batch/blacksmith';Q=R/'research/buildings_batch/blacksmith'
a=json.loads((O/'saved_source_fbx_audit.json').read_text());assert len(a)==3
sheet=Image.new('RGB',(1536,800),(28,30,34));d=ImageDraw.Draw(sheet)
for i,age in enumerate([2,3,4]):
 im=Image.open(O/f'age{age}_preview.png').convert('RGB').resize((512,512));sheet.paste(im,(i*512,0));d.text((i*512+16,525),f'BERBER BLACKSMITH AGE {age} | SOURCE',fill='white')
 for j,v in enumerate(['front','back','left','right','top','bottom']):
  im=Image.open(O/f'age{age}_{v}.png').convert('RGB').resize((166,166));x=i*512+(j%3)*170;y=550+(j//3)*190
  # six-side contact sheet separately, avoiding overly small final perspective
sheet=sheet.crop((0,0,1536,550));sheet.save(O/'contact_sheet.png')
sides=Image.new('RGB',(1536,1160),(28,30,34));d=ImageDraw.Draw(sides)
for i,age in enumerate([2,3,4]):
 for j,v in enumerate(['front','back','left','right','top','bottom']):
  im=Image.open(O/f'age{age}_{v}.png').convert('RGB').resize((256,256));x=j*256;y=i*385;sides.paste(im,(x,y));d.text((x+8,y+263),f'Age {age} {v}',fill='white')
sides=sides.crop((0,0,1536,3*385-90));sides.save(O/'six_side_contact_sheet.png')
p=Image.open(A/'pattern.png').convert('RGB');r,g,b=p.split();assert g.getextrema()==(0,0) and b.getextrema()==(0,0) and r.getextrema()==(0,255)
(O/'texture_audit.json').write_text(json.dumps({'red_range':r.getextrema(),'green_range':g.getextrema(),'blue_range':b.getextrema(),'size':p.size,'native_owner_colour':'pending'},indent=2))
delivery={'key':'blacksmith','required_ages':[2,3,4],'status':'source_delivered_native_integration_pending','source_dir':'art/buildings/blacksmith','evidence_dir':'research/buildings_batch/blacksmith','minimum_age_evidence':'AGE_AND_TARGET_EVIDENCE.json','footprint_m':[8,8],'donor':'UNTouched_Abbasid_Blacksmith_Age2_Reference.blend','geometry_reuse':False,'recipe':'build_blacksmith.py','history':['iteration1.log','repair_preview.py'],'maps':['albedo.png','pattern.png','normal.png','roughness.png','metal.png'],'owner_colour':'Neutral cloth stripes plus red-only mask authored; static native route blocked/pending','validation':'saved_source_fbx_audit.json','previews':'contact_sheet.png','six_side_views':'six_side_contact_sheet.png','construction_manifests':[f'age{i}_construction.json' for i in [2,3,4]],'native_outskirts':'mal_tech_03 identified, source props included; native attachment bindings pending','native_stages_LOD_damage_FX_pathing':'not tested','cook':False,'package':False,'files':[]}
for p in sorted(A.glob('*')):
 if p.suffix in ['.blend','.fbx','.png','.py','.json']:delivery['files'].append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(O/'delivery.json').write_text(json.dumps(delivery,indent=2))
for p in A.glob('*.blend1'):p.unlink()
print('FINALIZED',[(x['age'],x['saved_meshes'],x['fbx_meshes']) for x in a])
