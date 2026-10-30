import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/mosque';O=R/'output/buildings_batch/mosque';D=R/'research/buildings_batch/mosque'
rows=[]
for age in [3,4]:
 v=json.loads((O/f'age{age}_validation.json').read_text());rows.append({'age':age,'objects':len(v['objects']),'triangles':sum(x['triangles'] for x in v['objects']),'contacts':len(v['contacts']),'void_guards':len(v['void_guards']),'numeric_pass':all(x['non_manifold']==0 and x['degenerate_faces']==0 and x['uv_zero_area_faces']==0 and x['outward_volume']>0 and x['finite'] and x['positive_scale'] for x in v['objects']) and all(x['pass'] for x in v['contacts']+v['void_guards'])})
pattern=Image.open(A/'pattern.png').convert('RGB');channels=pattern.split();assert channels[1].getextrema()==(0,0) and channels[2].getextrema()==(0,0)
sheet=Image.new('RGB',(1536,808),'#dddddd');draw=ImageDraw.Draw(sheet)
for j,age in enumerate([3,4]):sheet.paste(Image.open(O/f'age{age}_preview.png').convert('RGB'),(j*768,40));draw.text((j*768+24,14),f'Berber Mosque — Age {age}',fill='black')
sheet.save(O/'contact_sheet.png')
six=Image.new('RGB',(6*320,2*348),'#dddddd');draw=ImageDraw.Draw(six)
for row,age in enumerate([3,4]):
 for col,name in enumerate(['front','back','left','right','top','bottom']):six.paste(Image.open(O/f'age{age}_{name}.png').convert('RGB'),(col*320,row*348+28));draw.text((col*320+8,row*348+8),f'Age {age} {name}',fill='black')
six.save(O/'six_sides.png')
evidence={'minimum_age':3,'required_ages':[3,4],'target':'ebps/races/malian/buildings/building_unit_religious_mal','live_builder':'assets/attrib/instances/sbps/races/malian/berbers/unit_villager_1_mal.xml:1479','installed_requirement':'mal.xml:1055-1075 completed castle_age; core.xml:922-942 same requirement','footprint':'core.xml:103-106 site_ext 8x8 forced axis aligned','origin':[0,0,0],'render_bounds_are_footprint':False}
(D/'AGE_AND_TARGET_EVIDENCE.json').write_text(json.dumps(evidence,indent=2))
delivery={'key':'mosque','inventory_id':'building.mosque','status':'authored_source_export_numeric_checks_passed','ages':[3,4],'footprint_m':[8,8],'age_evidence':evidence,'donor':'untouched installed Abbasid monastery age03 decoded with Garrison; geometry not reused','checks':rows,'owner_mask':{'red':channels[0].getextrema(),'green':channels[1].getextrema(),'blue':channels[2].getextrema(),'uv':'same atlas as albedo','native_status':'blocked static structure contract, pending qualification'},'construction':'explicit cumulative object-stage manifests; source only','visual_states':['default minbar with three empty relic shelves','optional expanded minbar panels source state; native mapping pending'],'visual_review':'perspective, six sides and roof-hidden interior inspected; see INSPECTION.md','native_gates':['owner shader','construction selectors','minbar and relic upgrade/attachment mapping','native exits and rally/emergence','LOD and damage','scale orientation and two-owner match'],'production_changed':False,'cook':False,'files':[{'path':str(p.relative_to(R)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in A.iterdir() if p.is_file() and p.suffix not in ['.blend1']]}
delivery['saved_source_audit']=json.loads((O/'saved_source_audit.json').read_text())
assert all(all(abs(v)<1e-5 for v in rec['gallery_roof_to_cap_signed_gaps'].values()) for rec in delivery['saved_source_audit'])
assert all(x['numeric_pass'] for x in rows)
(O/'delivery.json').write_text(json.dumps(delivery,indent=2));print(json.dumps(rows))
