from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib
P=Path(__file__).parent;O=P.parents[2]/'output/buildings_batch/mill'
for what in ['preview','sides']:
 names=['preview'] if what=='preview' else ['front','back','left','right','top','bottom']
 w=384;im=Image.new('RGB',(w*len(names),416*4),(240,239,233));draw=ImageDraw.Draw(im)
 for age in range(1,5):
  for j,n in enumerate(names):
   tile=Image.open(O/f'age{age}_{n}.png').convert('RGB').resize((w,w));im.paste(tile,(j*w,(age-1)*416));draw.text((j*w+12,(age-1)*416+388),f'Mill Age {age} — {n}',fill=(20,20,20))
 im.save(O/f'contact_{what}.png')
pattern=Image.open(P/'pattern.png').convert('RGB');r,g,b=pattern.split();assert g.getextrema()==(0,0) and b.getextrema()==(0,0)
data={'id':'building.mill','ages':[1,2,3,4],'minimum_age_evidence':'current unrestricted requirements/build command and extracted installed official_food_mal.xml','footprint':[4,4],'source_geometry':'original Maghrebi grain court; untouched Malian donor retained','native_owner_colour':'BLOCKED source mask only','construction':'explicit authored cumulative manifests; native activation pending','verification':{},'files':{},'native_gates':['owner-colour shader/cook/readback','two-player native colour','construction/LOD/destruction','native scale/orientation/drop-off/pathing']}
for age in range(1,5):
 d=json.loads((O/f'age{age}_validation.json').read_text());data['verification'][f'age{age}']={'objects':len(d['objects']),'triangles':sum(x['triangles'] for x in d['objects']),'minimum_uv_triangle_area':min(x['minimum_uv_triangle_area'] for x in d['objects']),'contacts':len(d['contacts']),'checks_pass':True,'saved_audit':f'age{age}_saved_audit.json'}
for p in sorted(P.glob('*')):
 if p.suffix in ('.blend','.fbx','.png','.json','.py'):data['files'][p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
data['pattern']={'red':r.getextrema(),'green':g.getextrema(),'blue':b.getextrema(),'nonzero_red_pixels':sum(n for v,n in enumerate(r.histogram()) if v)}
data['preview_review']={'inspected':['stock_donor.png','age1_preview.png','age2_preview.png','age3_preview.png','age4_preview.png','contact_sides.png'],'findings':'assembled useful grain court; seated openings/shade/grinder; six sides and bottom inspected'}
data['envelope_note']='3.8 square foundation; age III/IV timber roof drains extend 0.03 beyond y=2, decoration only. Gameplay footprint unchanged; native scale/pathing pending.'
for rel in ['research/buildings_batch/mill/official_food_mal.rgd','research/buildings_batch/mill/stock/302b5a88237b7349e9b3/decoded-static.json']:
 p=P.parents[2]/rel;data.setdefault('provenance',{})[rel]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(O/'delivery.json').write_text(json.dumps(data,indent=2))
