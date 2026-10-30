import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/siege';O=R/'output/buildings_batch/siege';records=[]
sheet=Image.new('RGB',(1536,800),'#25252a');draw=ImageDraw.Draw(sheet)
for age in [3,4]:
    d=json.loads((O/f'age{age}_validation.json').read_text());assert all(o['finite'] and o['positive_scale'] and o['non_manifold']==0 and o['degenerate_faces']==0 and o['uv_zero_area_faces']==0 and o['outward_signed_volume']>0 for o in d['objects']);assert all(c['pass'] for c in d['contacts'])
    im=Image.open(O/f'age{age}_preview.png').convert('RGB');sheet.paste(im,((age-3)*768,0));draw.text(((age-3)*768+15,780),f'SIEGE WORKSHOP AGE {age} | native owner colour pending',fill='white')
    sides=Image.new('RGB',(768,552),'#25252a');dr=ImageDraw.Draw(sides)
    for j,name in enumerate(['front','back','left','right','top','bottom']):
        sides.paste(Image.open(O/f'age{age}_{name}.png').convert('RGB'),((j%3)*256,(j//3)*276+20));dr.text(((j%3)*256+8,(j//3)*276+4),name,fill='white')
    sides.save(O/f'age{age}_six_sides.png')
    fs=[A/f'Berber_Siege_Age{age}.blend',A/f'Berber_Siege_Age{age}.fbx',A/f'age{age}_construction.json']
    records.append({'age':age,'objects':len(d['objects']),'measured_contacts':len(d['contacts']),'files':[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in fs]})
sheet.save(O/'contact_sheet.png')
r,g,b=Image.open(A/'pattern.png').convert('RGB').split();assert r.getextrema()==(0,255) and g.getextrema()==(0,0) and b.getextrema()==(0,0)
report={'key':'siege','status':'source geometry/export verified; native integration pending','required_ages':[3,4],'minimum_age_evidence':'research/buildings_batch/siege/AGE_AND_TARGET_EVIDENCE.json','footprint_m':[6,6],'central_working_lane_m':2.0,'front_hall_clear_width_m':4.54,'origin':'centre ground z=0','ages':records,'owner_mask':{'red':r.getextrema(),'green':g.getextrema(),'blue':b.getextrema(),'neutral_sources':True,'native_status':'blocked static shader route; not native ready'},'donor':'UNTouched_Abbasid_Siege_Age3_Reference.blend','geometry_reused':False,'native_gates':['owner colours','stage activation','LOD','destruction','unit spawn/rally/exits','scale/orientation/placement'],'production_edits':False,'cook':False}
(O/'delivery.json').write_text(json.dumps(report,indent=2))
print(records)
