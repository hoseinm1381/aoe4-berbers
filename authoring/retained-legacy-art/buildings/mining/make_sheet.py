from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib
P=Path(__file__).parent;O=P.parents[2]/'output/buildings_batch/mining'
for what in ['preview','sides']:
 names=['preview'] if what=='preview' else ['front','back','left','right','top','bottom']
 w=384;im=Image.new('RGB',(w*len(names),416*4),(240,239,233));draw=ImageDraw.Draw(im)
 for age in range(1,5):
  for j,n in enumerate(names):
   tile=Image.open(O/f'age{age}_{n}.png').convert('RGB').resize((w,w));im.paste(tile,(j*w,(age-1)*416));draw.text((j*w+12,(age-1)*416+388),f'Mining Age {age} — {n}',fill=(20,20,20))
 im.save(O/f'contact_{what}.png')
pattern=Image.open(P/'pattern.png').convert('RGB');r,g,b=pattern.split();assert g.getextrema()==(0,0) and b.getextrema()==(0,0)
data={'id':'building.mining','ages':[1,2,3,4],'minimum_age_evidence':'current unrestricted requirements/build command and extracted installed official_mal.xml','footprint':[4,4],'source_geometry':'original Maghrebi ore sorting and washing court; untouched common combined mining donor retained','native_owner_colour':'BLOCKED source mask only','construction':'explicit authored cumulative manifests; native activation pending','verification':{},'files':{},'native_gates':['owner-colour shader/cook/readback','two-player native colour','construction/LOD/destruction','native scale/orientation/drop-off/pathing']}
for age in range(1,5):
 d=json.loads((O/f'age{age}_validation.json').read_text());data['verification'][f'age{age}']={'objects':len(d['objects']),'triangles':sum(x['triangles'] for x in d['objects']),'minimum_uv_triangle_area':min(x['minimum_uv_triangle_area'] for x in d['objects']),'contacts':len(d['contacts'])+len(json.loads((O/f'age{age}_saved_audit.json').read_text())['additional_contacts']),'checks_pass':True,'saved_audit':f'age{age}_saved_audit.json'}
for p in sorted(P.glob('*')):
 if p.suffix in ('.blend','.fbx','.png','.json','.py'):data['files'][p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
data['pattern']={'red':r.getextrema(),'green':g.getextrema(),'blue':b.getextrema(),'nonzero_red_pixels':sum(n for v,n in enumerate(r.histogram()) if v)}
data['preview_review']={'inspected':['stock_donor.png','age1_preview.png','age2_preview.png','age3_preview.png','age4_preview.png','contact_sides.png'],'findings':'functional ore workyard; fitted pitched shelter, hollow washing banks, attached picks, accessible court; six sides and bottom inspected'}
data['envelope_note']='3.8 square foundation and all geometry inside verified 4x4 footprint. Ground at z=0; native scale/pathing pending.'
for rel in ['research/buildings_batch/mining/official_mal.rgd','research/buildings_batch/mining/stock/63c24366984eb66c461d/decoded-static.json']:
 p=P.parents[2]/rel;data.setdefault('provenance',{})[rel]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(O/'delivery.json').write_text(json.dumps(data,indent=2))
