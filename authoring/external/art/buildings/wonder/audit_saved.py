import bpy,json,traceback,bmesh
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/wonder';O=R/'output/buildings_batch/wonder'
try:
 bpy.ops.wm.open_mainfile(filepath=str(A/'Berber_Wonder_Age4.blend'))
 with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
  meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];imgs=[i for i in bpy.data.images if i.name.startswith('Wonder_')]
  def edge(name,side,axis=2):
   ob=bpy.data.objects[name];pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];return (min if side==0 else max)(p[axis] for p in pts)
  joins={}
  for child,parent in [('axial_nave_clerestory','main_hypostyle_roof'),('axial_nave_clerestory.001','main_hypostyle_roof'),('raised_axial_nave_roof','axial_nave_clerestory'),('banner_anchored_rod','owner_tower_banner'),('banner_anchored_rod.001','owner_tower_banner.001')]:
   joins[child+' to '+parent]=edge(child,0)-edge(parent,1)
  assert all(abs(v)<1e-5 for v in joins.values()),joins
  pattern=bpy.data.images.get('Wonder_pattern');badmask=0;owner_loops=0;stone_loops=0
  for o in meshes:
   owner=o.data.materials[0].get('ber_owner_mask');uv=o.data.uv_layers.active
   for p in o.data.polygons:
    for li in p.loop_indices:
     u,v=uv.data[li].uv;x=min(255,int(u*256));y=min(255,int(v*256));rgb=pattern.pixels[(y*256+x)*4:(y*256+x)*4+3]
     badmask+=int(abs(rgb[0]-owner)>.01 or rgb[1]>.01 or rgb[2]>.01)
     owner_loops+=int(owner==1);stone_loops+=int(owner==0)
  rec={'age':4,'mesh_objects':len(meshes),'packed_images':{i.name:bool(i.packed_file) for i in imgs},'owner_materials':{m.name:m.get('ber_owner_mask') for m in bpy.data.materials},'all_mesh_uv':all(bool(o.data.uv_layers) for o in meshes),'all_stage_properties':all('garrison_building_first_stage' in o for o in meshes),'owner_pattern_uv_samples':owner_loops,'neutral_pattern_uv_samples':stone_loops,'incorrect_pattern_samples':badmask,'additional_signed_contact_gaps':joins,'fbx_bytes':(A/'Berber_Wonder_Age4.fbx').stat().st_size,'native_owner_colour':'pending blocked integration'}
  assert len(imgs)==5 and all(rec['packed_images'].values()) and rec['all_mesh_uv'] and rec['all_stage_properties'] and rec['fbx_bytes']>10000 and badmask==0 and owner_loops>0 and stone_loops>0
 (O/'saved_source_audit.json').write_text(json.dumps(rec,indent=2));print('SAVED_SOURCE_AUDIT_PASS',flush=True)
except Exception:
 (O/'SOURCE_AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
