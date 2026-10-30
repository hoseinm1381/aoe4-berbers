import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];A=ROOT/'art/buildings/market';O=ROOT/'output/buildings_batch/market'
assert (O/'BUILD_COMPLETE.json').exists()
records=[];sheet=Image.new('RGB',(1536,1616),(30,30,34));draw=ImageDraw.Draw(sheet)
for age in [2,3,4]:
 d=json.loads((O/f'age{age}_validation.json').read_text());assert all(o['finite'] and o['positive_scale'] and o['non_manifold']==0 and o['degenerate_faces']==0 and o['uv_zero_area_faces']==0 and o['outward_signed_volume']>0 for o in d['objects']);assert all(c['pass'] for c in d['contacts'])
 manifest=json.loads((A/f'age{age}_construction.json').read_text());assert len(manifest['parts'])==len(d['objects']);assert any(p['first_stage']==0 for p in manifest['parts'])
 files=[A/f'Berber_Market_Age{age}.blend',A/f'Berber_Market_Age{age}.fbx',A/f'age{age}_construction.json',O/f'age{age}_preview.png']
 assert all(p.is_file() and p.stat().st_size>0 for p in files)
 records.append({'age':age,'objects':len(d['objects']),'contacts':len(d['contacts']),'files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files]})
 im=Image.open(O/f'age{age}_preview.png').convert('RGB');x=((age-2)%2)*768;y=((age-2)//2)*808;sheet.paste(im,(x,y));draw.text((x+20,y+780),f'TRIBAL MARKET AGE {age} - native player colour pending',fill='white')
 sides=Image.new('RGB',(768,552),'#25252a');dr=ImageDraw.Draw(sides)
 for j,name in enumerate(['front','back','left','right','top','bottom']):
  im=Image.open(O/f'age{age}_{name}.png').convert('RGB');sides.paste(im,((j%3)*256,(j//3)*276+20));dr.text(((j%3)*256+10,(j//3)*276+4),name,fill='white')
 sides.save(O/f'age{age}_six_sides.png')
sheet.save(O/'contact_sheet.png')
im=Image.open(A/'pattern.png').convert('RGB');r,g,b=im.split();assert r.getextrema()==(0,255) and g.getextrema()==(0,0) and b.getextrema()==(0,0)
report={'key':'market','status':'source_geometry_export_verified','required_ages':[2,3,4],'age_evidence':'official core.xml requirement_ext completed feudal_age; live XML parent_pbg; builder sbps/races/malian/berbers/unit_villager_1_mal.xml:935','footprint_m':[8,8],'gate_clearance_m':1.8,'ages':records,'owner_mask':{'red':r.getextrema(),'green':g.getextrema(),'blue':b.getextrema(),'native_colour':'pending blocked static shader route'},'donor':'UNTouched_Abbasid_Market_Age2_Reference.blend','preview_inspection':'per-age perspective and six sides visually inspected','native_gates':['owner colours','stage selectors','LOD','destruction','native exits/spawn/traversability','placement scale/orientation'],'production_edits':False,'cook':False}
(O/'delivery.json').write_text(json.dumps(report,indent=2));print(json.dumps([{'age':r['age'],'objects':r['objects'],'contacts':r['contacts']} for r in records],indent=2))
