import bpy,json,traceback
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/mosque';O=R/'output/buildings_batch/mosque';rows=[]
try:
 for age in [3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Mosque_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];imgs=[i for i in bpy.data.images if i.name.startswith('Mosque_')]
   def edge(name,side):
    ob=bpy.data.objects[name];pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];return (min if side==0 else max)(p.y for p in pts)
   joins={str(x):edge('gallery_roof_'+str(x),0)-edge('entrance_cap',1) for x in [-3.38,3.38]}
   rec={'age':age,'mesh_objects':len(meshes),'packed_images':{i.name:bool(i.packed_file) for i in imgs},'owner_materials':{m.name:m.get('ber_owner_mask') for m in bpy.data.materials},'all_mesh_uv':all(bool(o.data.uv_layers) for o in meshes),'all_stage_properties':all('garrison_building_first_stage' in o for o in meshes),'gallery_roof_to_cap_signed_gaps':joins,'fbx_bytes':(A/f'Berber_Mosque_Age{age}.fbx').stat().st_size}
   assert all(abs(v)<1e-5 for v in joins.values())
   assert len(imgs)==5 and all(rec['packed_images'].values()) and rec['all_mesh_uv'] and rec['all_stage_properties'] and rec['fbx_bytes']>10000
   rows.append(rec)
 (O/'saved_source_audit.json').write_text(json.dumps(rows,indent=2));print('SAVED_SOURCE_AUDIT_PASS',flush=True)
except Exception:
 (O/'SOURCE_AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
