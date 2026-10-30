import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/wall';O=R/'output/buildings_batch/wall';Q=R/'research/buildings_batch/wall'
def sheet(kinds,name,size=300):
 im=Image.new('RGB',(size*len(kinds),3*(size+30)),(25,28,31));draw=ImageDraw.Draw(im)
 for row,age in enumerate((2,3,4)):
  for col,kind in enumerate(kinds):
   p=O/f'age{age}_{kind}.png';view=Image.open(p).convert('RGB');view.thumbnail((size,size));x=col*size;y=row*(size+30);im.paste(view,(x,y));draw.text((x+5,y+size+5),f'Age {age}: {kind}',fill=(235,232,219))
 im.save(O/name)
sheet(['preview','corner_90','slope_up_6m','end_6m','damaged_6m','destroyed_6m'],'wall_contact_sheet.png')
sheet(['front','back','left','right','top','bottom'],'wall_six_side_sheet.png',240)
audit=json.loads((O/'saved_and_fbx_audit.json').read_text())
age_evidence={'key':'wall','minimum_age':2,'required_ages':[2,3,4],'current_builder':'assets/attrib/instances/sbps/races/malian/berbers/unit_villager_1_mal.xml:1041','current_entity_override':'none found under assets/attrib/instances; installed inherited target inspected','installed_malian_entity':'attrib/ebps/races/malian/buildings/building_defense_wall_mal/building_defense_wall_mal.rgd','age_requirement':'mal.xml lines 908-928 required_player_upgrade completed feudal_age min1; official core requirement agrees','stock_lengths_m':[1,3,6],'gapfill_lengths_m':[1,2,3,4],'walkable_width_m':3,'primary_walkable_height_m':7,'evidence':['mal.xml:578','mal.xml:611'],'footprint':'slotted spline envelope; no render bounds treated as gameplay footprint'}
(Q/'AGE_AND_TARGET_EVIDENCE.json').write_text(json.dumps(age_evidence,indent=2))
interface={'units':'metres','orientation':'length +X, width +Y, up +Z','origin':'ground center','all_ages':[2,3,4],'walk_z':7,'walk_clear_width':3,'walk_y_interval':[-1.5,1.5],'deck_y_interval':[-2.1,2.1],'base_y_interval':[-2.9,2.9],'parapet_y_interval':[[-2.2,-1.5],[1.5,2.2]],'crest_z':8.2,'straight_sockets':'x±length/2,y0,z7 normals outward ±X','elbow_sockets':[[-6,0,7],[0,6,7]],'slope':'source rise±1.2m over6m, socket z6.4/7.6; no native terrain conform proof','stock_render_bounds':'6m x±3, yapprox±3, lower donor extension -3, crest8.2578125; not footprint','binding':'native entity walk extension and selectors must be retained by integration'}
(Q/'WALL_INTERFACE.json').write_text(json.dumps(interface,indent=2))
files=[]
for p in sorted(A.iterdir()):
 if p.is_file() and p.suffix in ('.blend','.fbx','.png','.json','.py'):
  files.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
validations=[json.loads((O/f'age{a}_validation.json').read_text()) for a in (2,3,4)]
delivery={'schema':'berber-building-source-delivery/v1','key':'wall','required_ages':[2,3,4],'status':'source_delivered_native_integration_pending','donor':'untouched installed Malian 6m segment geometry with native construction/healthy/damaged/wreck groups preserved','age_evidence':'research/buildings_batch/wall/AGE_AND_TARGET_EVIDENCE.json','interface':'research/buildings_batch/wall/WALL_INTERFACE.json','variants':['straight_1m','straight_3m','straight_6m','gap_1m','gap_2m','gap_3m','gap_4m','slope_up_6m','slope_down_6m','end_6m','corner_90','damaged_6m','destroyed_6m'],'source_checks':{'objects':sum(len(v['objects']) for v in validations),'closed_outward_volumes':True,'finite_geometry':True,'degenerate_faces':0,'zero_uv_faces':0,'positive_transforms':True,'numeric_straight_joins':9,'straight_walk_rays':45,'corner_walk_rays':33,'slope_seating_samples':sum(v.get('slope_seating_samples',0) for v in audit),'fbx_reimports':9,'packed_images_per_age':5},'maps':{'albedo':'albedo.png','roughness':'roughness.png','normal':'normal.png (flat tangent normal neutral source)','metal':'metal.png','owner_pattern':'pattern.png red-only authored input sharing albedoUV'},'player_colour':'neutral owner band annotation and saved source mask; native structure shader support blocked per shared contract','previews':'output/buildings_batch/wall/wall_contact_sheet.png','six_sides':'output/buildings_batch/wall/wall_six_side_sheet.png','native_gates':['structure owner shader and two-player colour','wall segment/gap/cap/damage/destruction selectors','construction state activation','native terrain conform and slotted-spline placement','walk navigation onto/along gate/bastion/tower','LOD/snow/burn/damage visibility and native origin orientation'],'production_modified':False,'cook':False,'files':files}
(O/'delivery.json').write_text(json.dumps(delivery,indent=2))
print(json.dumps(delivery['source_checks']))
