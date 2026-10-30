from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
R=Path.cwd();A=R/'art/buildings/palisade';O=R/'output/buildings_batch/palisade'
audit=json.loads((O/'saved_source_fbx_audit.json').read_text());assert len(audit)==4
pattern=Image.open(A/'pattern.png').convert('RGB');assert pattern.getextrema()==((0,255),(0,0),(0,0))
files=[(f'age{a}_preview.png',f'Age {a}') for a in range(1,5)]+[(f'{s}_preview.png',s) for s in ['corner_90','end_socket','slope_up_6m','slope_down_6m']]
im=Image.new('RGB',(1536,840),'#ddd7ca');draw=ImageDraw.Draw(im)
for i,(file,label) in enumerate(files):
 pic=Image.open(O/file).convert('RGB');pic.thumbnail((384,384));x=(i%4)*384;y=(i//4)*420;im.paste(pic,(x+(384-pic.width)//2,y));draw.text((x+12,y+389),label,fill='black')
im.save(O/'contact_sheet.png')
six=Image.new('RGB',(1536,1120),'#ddd7ca');draw=ImageDraw.Draw(six)
for a in range(1,5):
 for i,side in enumerate(['front','back','left','right','top','bottom']):
  p=Image.open(O/f'age{a}_{side}.png').convert('RGB');p.thumbnail((256,256));x=i*256;y=(a-1)*280;six.paste(p,(x,y));draw.text((x+8,y+261),f'I{a} {side}',fill='black')
six.save(O/'six_side_contact_sheet.png')
artifacts=[{'path':str(p.relative_to(R)).replace('\\','/'),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(A.glob('*')) if p.is_file() and p.suffix in ['.blend','.fbx','.png','.json','.py']]
delivery={'schema':'berber-building-delivery/v1','key':'palisade','ages':[1,2,3,4],'minimum_age':1,'status':'source_and_fbx_verified_native_integration_pending','donor':'Malian alternate_sua uses English/common6m age01','state_count_per_age':11,'fbx_count':44,'source_mesh_counts':[r['source_meshes'] for r in audit],'player_colour':{'mask_red_only':True,'same_albedo_uv':True,'neutral_visible_stripes':True,'native_status':'blocked_shared_contract'},'checks':{'closed_volumes':True,'finite':True,'positive_transforms':True,'nonzero_uv_area':True,'ground_affine_slope':True,'post_footing_contacts':True,'fbx_reimport_bounds':True,'packed_maps':True},'previews':['output/buildings_batch/palisade/contact_sheet.png','output/buildings_batch/palisade/six_side_contact_sheet.png'],'remaining_gates':['native owner shader','wall stamps/age-stage selectors','terrain conform/navigation','assembly with gate/bastion','LOD/damage/burn/snow','two-owner solo match'],'cook_run':False,'production_edited':False,'artifacts':artifacts}
(O/'delivery.json').write_text(json.dumps(delivery,indent=2))
