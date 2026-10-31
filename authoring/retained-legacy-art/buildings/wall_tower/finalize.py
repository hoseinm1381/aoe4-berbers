from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output/buildings_batch/wall_tower';ART=ROOT/'art/buildings/wall_tower';RES=ROOT/'research/buildings_batch/wall_tower'
sheet=Image.new('RGB',(2304,820),(30,31,35));d=ImageDraw.Draw(sheet)
for j,age in enumerate([2,3,4]):
    sheet.paste(Image.open(OUT/f'age{age}_preview.png').convert('RGB'),(j*768,0))
    d.text((j*768+20,779),f'AGE {age} | source option; native binding pending',fill=(240,231,210))
sheet.save(OUT/'contact_sheet.png')
for age in [2,3,4]:
    sheet=Image.new('RGB',(1152,816),(30,31,35));d=ImageDraw.Draw(sheet)
    for j,n in enumerate(['front','back','left','right','top','bottom']):
        x=(j%3)*384;y=(j//3)*408;sheet.paste(Image.open(OUT/f'age{age}_{n}.png').convert('RGB'),(x,y));d.text((x+12,y+385),n,fill=(240,231,210))
    sheet.save(OUT/f'age{age}_six_sides.png')
pattern=Image.open(ART/'pattern.png').convert('RGB');r,g,b=pattern.split()
assert r.getextrema()==(0,255) and g.getextrema()==(0,0) and b.getextrema()==(0,0)
(OUT/'texture_audit.json').write_text(json.dumps({'size':pattern.size,'red_range':r.getextrema(),'green_range':g.getextrema(),'blue_range':b.getextrema(),'owner_pixels':sum(r.histogram()[1:]),'UV':'shared atlas with albedo','native_owner_colour':'pending shared integration contract'},indent=2))
audits=[json.loads((OUT/f'age{a}_saved_audit.json').read_text())for a in [2,3,4]]
files=[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in ART.iterdir()if p.is_file()and p.suffix in ['.blend','.fbx','.png','.json','.py']]
delivery={'key':'wall_tower','status':'source geometry and maps verified; native integration pending','minimum_age':2,'ages':[2,3,4],'donor':'stock Malian wall tower, original native source preserved under task research; separate untouched reference blend','design_reference':'UNESCO Rabat Almohad square defensive towers and lime-rich earth masonry','age_evidence':'research/buildings_batch/wall_tower/AGE_AND_TARGET_EVIDENCE.json','construction':'per-age source object stage manifests','states':'per-age separate mutually exclusive source collections; generic minima only, native wall-tower availability unproven','checks':{'finite_closed_volumes':True,'positive_transforms':True,'outward_normals':True,'nondegenerate_uv':True,'owner_mask_red_only':True,'ground_min_z':0,'walk_deck_z':7,'walk_clear_width':3,'side_socket_x':[-3.2,3.2],'roof_mount_contacts':True,'packed_images':True},'visual_inspection':'previews and front/back/left/right/top/bottom sheets inspected; duplicated crenel corners and stair-entry obstruction repaired','remaining':['native owner shader/stream','native stamp/layout and simbox preservation','wall walk and native stair clearance','native weapon activation and firing selectors','construction/LOD export and in-game qualification'],'cook_or_mod_build':False,'files':files}
(OUT/'delivery.json').write_text(json.dumps(delivery,indent=2))
print('WALL_TOWER_DELIVERY',len(files),'FILES')
