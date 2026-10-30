from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];O=R/'output/buildings_batch/dock';A=R/'art/buildings/dock';Q=R/'research/buildings_batch/dock'
sheet=Image.new('RGB',(1536,1536),'#292e31');draw=ImageDraw.Draw(sheet)
for i,age in enumerate([1,2,3,4]):
 im=Image.open(O/f'age{age}_preview.png').convert('RGB');sheet.paste(im,((i%2)*768,(i//2)*768));draw.text(((i%2)*768+18,(i//2)*768+18),f'Dock age {age}',fill='white')
sheet.save(O/'contact_sheet.png')
for age in [1,2,3,4]:
 s=Image.new('RGB',(1200,800),'#292e31');d=ImageDraw.Draw(s)
 for i,name in enumerate(['front','back','left','right','top','bottom']):
  s.paste(Image.open(O/f'age{age}_{name}.png').convert('RGB'),((i%3)*400,(i//3)*400));d.text(((i%3)*400+8,(i//3)*400+8),name,fill='white')
 s.save(O/f'age{age}_sixside.png')
im=Image.open(A/'pattern.png').convert('RGB');assert all(g==b==0 for r,g,b in im.getdata());assert any(r>0 for r,g,b in im.getdata());assert im.size==Image.open(A/'albedo.png').size
for p in A.glob('*.blend1'):p.unlink()
ages=[json.loads((O/f'age{age}_validation.json').read_text()) for age in [1,2,3,4]]
delivery={'key':'dock','name':'Maghrebi Harbour Dock','minimum_age':1,'required_ages':[1,2,3,4],'target':'ebps/races/malian/buildings/building_unit_naval_mal','source_directory':str(A),'research':'research/buildings_batch/dock/README.md','donor':'UNTouched_Stock_Dock_and_Piers_Reference.blend','donor_geometry_reused':False,'packed_maps':['albedo.png','normal.png','roughness.png','metal.png','pattern.png'],'owner_colour':'red-only mask and neutral owner material; static native shader route blocked','construction':'ageN_construction.json cumulative source stages; native binding pending','native_layout_policy':'preserve original layout_docks naval markers and simboxes; author empties not native markers','numeric_checks':'finite geometry, positive transforms, closed/outward mesh volumes, nondegenerate faces and UV area, measured contacts, empty 2.8m central launch corridor','geometry_summary':[{'age':v['age'],'objects':len(v['objects']),'triangles':sum(r['triangles'] for r in v['objects'])} for v in ages],'source_fbx_audit':'saved_source_fbx_audit.json','previews':'contact_sheet.png and ageN_sixside.png','native_gates':['owner colour','construction selectors','shoreline datum and orientation','simbox and marker mapping','naval spawn and vessel clearance','LOD/damage/fire'],'production_changed':False,'cook_performed':False,'status':'source authoring delivered; native integration pending'}
delivery['files']=[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in A.iterdir() if p.suffix in ['.blend','.fbx','.png','.json','.py']]
audit=json.loads((O/'saved_source_fbx_audit.json').read_text());assert [x['age'] for x in audit]==[1,2,3,4]
delivery['saved_source_and_fbx_reimport']='passed all four ages: five packed maps, identical mesh/triangle counts, UV preservation, owner annotations, measured door/shutter/upper-store insert fitting'
delivery['source_ship_clearance_probes']='source_ship_clearance_probes.json: 2.5m central proxy clear; 3.8m offset proxy clear only to Y=-.56; wider apron collision disclosed'
delivery['inspection_notes']='Final four perspective previews and 24 six-side views inspected. Shade rear support and true upper-store recess repaired before final review. Clear central lane, seated piers/piles, useful storage and age progression visible.'
(O/'delivery.json').write_text(json.dumps(delivery,indent=2))
(Q/'AGE_AND_TARGET_EVIDENCE.json').write_text(json.dumps({'minimum_age':1,'ages':[1,2,3,4],'live_builder_lines':[443,456],'live_parent_line':587,'official_default_requirement':'dock_blocked=false usage flag only; no completed age upgrade','official_site_footprint':[8,8],'placement_uses_simbox_scale':True,'required_pass_cells':{'infantry':14,'water_default':7},'water_rally':True,'minimum_spawn_clearance_search_range':30,'native_layout':'layout.xml default parent_animator layout_docks; raw RGO/RGM preserved','native_marker_transforms':'pending decoder; not inferred from render bounds'},indent=2))
print('DOCK_FINALIZED')
