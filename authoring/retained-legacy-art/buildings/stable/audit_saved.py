import json,bpy,bmesh,math,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/stable';O=R/'output/buildings_batch/stable';reports=[]
try:
 for age in [2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Stable_Age{age}.blend'))
  obs=[o for o in bpy.data.objects if o.type=='MESH'];issues=[]
  for o in obs:
   bm=bmesh.new();bm.from_mesh(o.data)
   if bm.calc_volume(signed=True)<=0 or any(not e.is_manifold for e in bm.edges):issues.append(o.name+' volume/topology')
   bm.free()
   if not o.data.uv_layers or any(v<=0 for v in o.scale):issues.append(o.name+' UV/scale')
   if not all(math.isfinite(c) for v in o.data.vertices for c in v.co):issues.append(o.name+' finite')
   if 'garrison_building_first_stage' not in o:issues.append(o.name+' stage')
  manifest=json.loads((A/f'age{age}_construction.json').read_text());assert len(obs)==len(manifest['parts'])
  packed=[i.name for i in bpy.data.images if i.packed_file];assert len(packed)>=5,packed
  assert not issues,issues
  assert any(o['garrison_building_first_stage']==0 for o in obs)
  assert any(m.get('ber_owner_mask')==1 for m in bpy.data.materials)
  reports.append({'age':age,'meshes':len(obs),'packed_images':packed,'issues':issues,'stage_manifest_matches':True})
 (O/'saved_source_audit.json').write_text(json.dumps(reports,indent=2))
except Exception:(O/'audit_error.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
