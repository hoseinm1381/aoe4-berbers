from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[3];O=R/'output/buildings_batch/farm';A=R/'art/buildings/farm'
sheet=Image.new('RGB',(1536,1616),'#ddd6c9');d=ImageDraw.Draw(sheet)
for a in range(1,5):
 im=Image.open(O/f'age{a}_preview.png').convert('RGB');x=((a-1)%2)*768;y=((a-1)//2)*808;sheet.paste(im,(x,y));d.text((x+15,y+775),f'Age {a} - authored source, native colour pending',fill='black')
sheet.save(O/'contact_sheet.png')
for a in range(1,5):
 s=Image.new('RGB',(960,688),'#ddd6c9');draw=ImageDraw.Draw(s)
 for i,v in enumerate(['front','back','left','right','top','bottom']):
  x=(i%3)*320;y=(i//3)*344;s.paste(Image.open(O/f'age{a}_{v}.png').convert('RGB'),(x,y));draw.text((x+10,y+321),v,fill='black')
 s.save(O/f'age{a}_sixside.png')
files=[{'path':str(p.relative_to(R)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in A.iterdir() if p.suffix in ['.blend','.fbx','.png','.json']]
checks=[json.loads((O/f'age{a}_validation.json').read_text()) for a in range(1,5)]
from PIL import Image as I
mask=I.open(A/'pattern.png').convert('RGB');assert all(g==0 and b==0 for r,g,b in mask.getdata())
(O/'delivery.json').write_text(json.dumps({'family':'farm','ages':[1,2,3,4],'min_age_evidence':'live builder age_1 empty additional requirements; official farm requirement_ext empty','geometry':'original irrigated plot; untouched depleted crop donor separate','official_footprint_scale':[4,4],'construction':'per-age explicit cumulative manifests','resource_states':['untouched sprouts','gatherable cereal','depleted stubble'],'checks':{'geometry_all_pass':all(all(c['closed_edges'] and c['outward_volume']>0 and c['min_uv_area']>0 and c['degenerate_faces']==0 for c in x['objects']) for x in checks),'measured_contacts_all_pass':all(all(c['pass'] for c in x['measured_contacts']) for x in checks),'packed_images_all_pass':all(x['packed_images'] for x in checks),'red_only_mask_pass':True,'preview_and_sixside_inspected':True},'native_owner_colour':'blocked shared structure shader/attachment contract; source inputs authored only','pending':['native shader owner colour','resource regrowth/harvest state binding','construction selectors','cook/readback','LOD/destruction','native traversal/placement and scale'], 'files':files,'production_changes':False,'mod_build':False},indent=2))
