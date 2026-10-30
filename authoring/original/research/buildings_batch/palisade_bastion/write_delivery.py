import json,hashlib
from pathlib import Path
from PIL import Image
R=Path.cwd();A=R/'art/buildings/palisade_bastion';O=R/'output/buildings_batch/palisade_bastion'
assert json.loads((O/'SAVED_SOURCE_AUDIT.json').read_text())['status']=='pass'
assert json.loads((O/'JOIN_GUARDS.json').read_text())['status']=='pass'
im=Image.open(A/'pattern.png').convert('RGB');px=list(im.getdata());assert all(g==0 and b==0 for r,g,b in px);assert {r for r,g,b in px}=={0,255}
assert Image.open(A/'normal.png').convert('RGB').getpixel((0,0))==(128,128,255)
files=[p for p in A.iterdir() if p.suffix in ['.blend','.fbx','.png','.json','.py']];assert len([p for p in files if p.suffix=='.fbx'])==20
d={'key':'palisade_bastion','status':'source_delivered_native_integration_pending','minimum_age':1,'ages':[1,2,3,4],'variants':['terminal','straight','corner_90','junction_T','junction_cross'],'packed_age_blends':4,'fbx_state_exports':20,'maps':['albedo.png','roughness.png','normal.png','metal.png','pattern.png'],'owner_colour':'neutral visible cloth zones plus ber_owner_mask and red-only pattern; native structure shader/export blocked under shared contract','stage_manifest':'per-age explicit FirstVisible0/20/40/60/80/100','state_manifest':'per-age objects and explicit logical socket endpoints','donor':'Installed Malian alternate_sua English/common bastion, read-only decoded own reference preserved;18 collection partitions','age_evidence':'research/buildings_batch/palisade_bastion/AGE_AND_TARGET_EVIDENCE.json','preview':'output/buildings_batch/palisade_bastion/contact_sheet.png','validation':['SAVED_SOURCE_AUDIT.json','JOIN_GUARDS.json','age1_validation.json','age2_validation.json','age3_validation.json','age4_validation.json'],'history':'research/buildings_batch/palisade_bastion/HISTORY.json','build_recipe':'art/buildings/palisade_bastion/build_palisade_bastion.py','rebuild_runner':'research/buildings_batch/palisade_bastion/run_hidden.py','inspected':'four age previews, six-side views and five-state source galleries','native_pending':['owner-colour shader/export','cap state selector and exact stamp/bone binding','construction auto-complete stage policy','arbitrary angle and slope/terrain joins','LOD/damage/destruction','native solo match and multiplayer'],'cook':False,'production_modified':False,'files':[{'path':str(p.relative_to(R)).replace('\\','/'),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
d['preview']='output/buildings_batch/palisade_bastion/contact_sheet_final_002.png'
d['state_galleries']=['output/buildings_batch/palisade_bastion/age1_state_gallery.png']+[f'output/buildings_batch/palisade_bastion/age{a}_state_gallery_final.png' for a in [2,3,4]]
d['inspection']='research/buildings_batch/palisade_bastion/INSPECTION.md'
(O/'delivery.json').write_text(json.dumps(d,indent=2))
print('DELIVERY',len(files),'files, 4 ages,20 FBX; source guards pass; native gates pending')
