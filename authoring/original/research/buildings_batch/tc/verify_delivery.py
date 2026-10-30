import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];O=R/'output/buildings_batch/tc';A=R/'art/buildings/tc'
assert (O/'BUILD_COMPLETE.json').is_file(),'No successful final build'
records=[]
for age in range(1,5):
 d=json.loads((O/f'age{age}_validation.json').read_text()); assert d['footprint_m']==[8,8]
 assert all(o['non_manifold_edges']==0 and o['degenerate_faces']==0 and o['positive_volume']>0 and o['uv_present'] and o['uv_in_atlas'] for o in d['objects'])
 assert all(c.get('pass',True) for c in d['contacts'])
 paths=[A/f'Berber_TC_Age{age}.blend',A/f'Berber_TC_Age{age}.fbx',A/f'age{age}_construction.json',O/f'age{age}_preview.png']
 for p in paths:assert p.is_file() and p.stat().st_size>0
 av=next(o['positive_volume'] for o in d['objects'] if o['object']=='courtyard_arcade_wall'); uncut=.32*3.5*(2.55+age*.3-.50)*(8/9.6)*(8/8.8); assert av<uncut*.80
 records.append({'arcade_remaining_solid_fraction':av/uncut,'age':age,'mesh_objects':len(d['objects']),'triangles':sum(o['triangles'] for o in d['objects']),'contact_tests':sum('pass'in c for c in d['contacts']),'files':[{'path':str(p.relative_to(R)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]})
im=Image.open(A/'pattern.png').convert('RGB');r,g,b=im.split();assert g.getextrema()==(0,0) and b.getextrema()==(0,0) and r.getextrema()[1]==255
sheet=Image.new('RGB',(1280,1360),'#242424');draw=ImageDraw.Draw(sheet)
for age in range(1,5):
 img=Image.open(O/f'age{age}_preview.png').convert('RGB');img.thumbnail((640,640));x=((age-1)%2)*640;y=((age-1)//2)*680;sheet.paste(img,(x,y+35));draw.text((x+20,y+12),f'BERBER TOWN CENTER - AGE {age}',fill='white')
sheet.save(O/'contact_sheet.png')
sides=Image.new('RGB',(900,640),'#242424');dr=ImageDraw.Draw(sides)
for n,name in enumerate(['front','back','left','right','top','bottom']):
 img=Image.open(O/f'age4_{name}.png').convert('RGB');img.thumbnail((300,300));x=(n%3)*300;y=(n//3)*320;sides.paste(img,(x,y+20));dr.text((x+10,y+4),name,fill='white')
sides.save(O/'age4_six_sides.png')
report={'status':'source_and_fbx_verified','ages':records,'owner_mask':{'size':im.size,'red':r.getextrema(),'green':g.getextrema(),'blue':b.getextrema(),'dynamic_native':'pending'},'native_acceptance':'pending','cook':False,'integration_edits':False,'footprint':[8,8],'exit_marker_binding':'existing gameplay not edited; author anchors not native-qualified'}
(O/'DELIVERY_VALIDATION.json').write_text(json.dumps(report,indent=2));print(json.dumps([{k:v for k,v in a.items() if k!='files'} for a in records],indent=2))
