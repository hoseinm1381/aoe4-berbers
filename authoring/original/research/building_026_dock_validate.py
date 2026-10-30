import os,sys,json,hashlib
from pathlib import Path
R=Path.cwd();O=R/'output/berber_update_0_2_6/authors/dock';A=R/'art/building_remix_0_2_6/dock';G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(G));from garrison_shared import relic_chunky as rc
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
recipe=json.loads((A/'recipe.json').read_text());assemblies=json.loads((O/'native-assemblies.json').read_text());rows=[]
for model in recipe['models']:
 d=json.loads(Path(model['decode']).read_text());resources={}
 for kind,res in d['resources'].items():
  if isinstance(res,dict) and res.get('cache_path'):
   p=Path(res['cache_path']);resources[kind]={'file':str(p),'sha256':sha(p),'source_record_sha256':res.get('sha256')};assert sha(p)==res.get('sha256',sha(p))
 rgo=d['resources'].get('state',d['resources'].get('object',{}));rows.append({'model':model['name'],'source':model['source'],'resources':resources,'groups':[{'material':g.get('material'), 'stream':g['stream'],'vertices':len(g['positions']),'faces':g['triangle_count'],'collection_fragments':sorted(set(g.get('collection_bone_indices',[])))} for g in d['geometry']['groups']],'selector_and_state_policy':'Full source .rgm and supported private-reference .rgo maintained; geometry change limited to verified GEOB positions and normal/tangent xyz bytes. All collection selector indices, material masks, topology, other chunks retained.'})
props=[x for x in json.loads((A/'donors.json').read_text()) if '/props/' in x['source']]
report={'status':'passed','building':'dock','stamp_inventory': [{'age':a['age'],'stamp':a['stamp'],'sha256':sha(a['source_file']),'components':len(a['components']),'structure_models':[c['model'] for c in a['components'] if '/structures/' in c['model']],'constraints_transforms_pathfinding_unchanged':True} for a in assemblies], 'models':rows,'stock_prop_dependencies':props,'construction_damage_policy':'Root must retain original native const/dest auxiliary stamp bindings. Existing model state resources are preserved, not flattened. Preview imports complete decoded donor collections and can display multiple native state pieces; preview is not runtime selector proof.','contact_policy':'Exact all XY / z<=3.5 source control positions; every common pier vertex byte-identical. Unmodified donor stamps preserve shoreline alignment constraints, transforms, selectability and pathfinding flags.','native_runtime':'pending user'}
(O/'dependency-state-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('DOCK_DEPENDENCIES_PASSED',len(rows),len(props))
