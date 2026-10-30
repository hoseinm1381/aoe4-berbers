"""040 coherent native buildings: retain031 detailed donor edits, remove overlay composition.
Run with system Python. Does not edit prior releases or shared integration files.
"""
import hashlib,json,shutil,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'art/building_remix_0_3_1'; NEW=ROOT/'art/building_remix_0_4_0'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
global_recipe=json.loads((OLD/'recipe.json').read_text())
models=global_recipe['models']
carriers={r['name']:r for r in global_recipe['texture_carriers']}
for family in ('keep','marrakech','siege'):
 out=NEW/family;out.mkdir(parents=True,exist_ok=True)
 rows=[]
 for model in models:
  if model['family']!=family:continue
  row=dict(model);name=row['name'];age=row['age']
  for key in ('native_geometry','remix_projection'):
   src=Path(row[key]);dst=out/src.name
   shutil.copy2(src,dst);row[key]=str(dst);row[key+'_sha256']=sha(dst)
  row['blend']=str(out/f'Berber_{family}_Age{age}_040.blend')
  row['texture_inputs']=[carriers[n] for n in sorted({e['carrier'] for m in row.get('materials',[]) for e in m.get('repaint',[])})]
  row['composition']='one complete native donor; no supplementary shell or yard kit'
  row['inherited_visual_allowlist']='principal only plus native player flag if required; no other visible architecture or props'
  row['preserve']='all031 native regional vertex edits, native UV/material/owner mask, construction selectors and opaque chunks'
  for key in list(row):
   if any(t in key for t in ('fbx','static','supplement','validation')):row.pop(key,None)
  original=json.loads(Path(row['decoded']).read_text())
  changed=json.loads(Path(row['remix_projection']).read_text())
  oldgroups=original['geometry']['groups'];newgroups=changed['geometry']['groups']
  assert len(oldgroups)==len(newgroups)
  boundary=2.2 if family=='keep' else 2.15 if family=='siege' else None
  unchanged=0;moved=0;maxlow=0
  for a,b in zip(oldgroups,newgroups):
   assert a['triangles']==b['triangles'] and a['uv_layers']==b['uv_layers']
   for p,q in zip(a['positions'],b['positions']):
    distance=sum((x-y)**2 for x,y in zip(p,q))**.5
    moved+=distance>.005
    if boundary is not None and p[2]<=boundary:
     maxlow=max(maxlow,distance);unchanged+=1
  assert boundary is None or maxlow==0,(family,age,maxlow)
  pts=[p for g in newgroups for p in g['positions']]
  row['bounds_m']=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
  row['source_checks']={'uv_topology_exact':True,'retained031_moved_vertices':moved,'fixed_lower_vertices':unchanged,'fixed_lower_max_displacement_m':maxlow,'lower_plane_m':boundary,'040_geometry_equal031':sha(model['native_geometry'])==sha(row['native_geometry'])}
  rows.append(row)
 assert len(rows)==2,(family,len(rows))
 recipe={'schema':'berber.coherent-native-repair/v040','family':family,'models':rows,'repair':{'keep':'Remove plain three-tower square bastion and inner parapet shell; retain detailed reshaped native round/battered core.','marrakech':'Remove inherited skull-tower, detached gate, eight stalls and three tents; retain one connected031 kasbah.','siege':'Remove secondary yard roof/hoist kit and inherited competing stamp architecture; retain reshaped031 L-shaped workshop.'}[family],'source_recipe':'research/berber_040_keep_repair_sources.py','blender_recipe':'research/berber_040_keep_repair_blender.py','native_runtime':'unverified'}
 (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
 print('040_NATIVE_READY',family,[(r['name'],r['bounds_m']) for r in rows])
