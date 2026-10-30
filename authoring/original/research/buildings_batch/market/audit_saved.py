import bpy,json,bmesh,math,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/market';O=R/'output/buildings_batch/market';report=[]
def bb(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]
try:
 for age in [2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Market_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   bpy.context.view_layer.update();objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];contacts=[]
   for o in objs:
    if '_sales_counter' in o.name:
     side=o.name.split('_')[0];wall=bpy.data.objects[side+'_warehouse'];cb=bb(o);wb=bb(wall);gap=cb[0][0]-wb[1][0] if side=='west' else wb[0][0]-cb[1][0];assert abs(gap)<1e-5;contacts.append({'part':o.name,'contact':'warehouse wall shelf edge','measured_gap':gap})
    if '_shade_post' in o.name:assert abs(bb(o)[0][2]-.19)<1e-5
   assert len(contacts)==6
   assert all(im.packed_file for im in bpy.data.images if im.type=='IMAGE')
   saved_count=len(objs);stage_count=len(json.loads((A/f'age{age}_construction.json').read_text())['parts']);assert stage_count==saved_count
   bpy.ops.wm.read_factory_settings(use_empty=True)
   with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Market_Age{age}.fbx'))
   imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==saved_count
   assert all(o.data.uv_layers for o in imported)
   report.append({'age':age,'saved_meshes':saved_count,'fbx_meshes':len(imported),'packed_images':True,'manifest_matches_meshes':True,'shelf_contacts':contacts,'post_ground_contact':True})
 (O/'saved_source_fbx_audit.json').write_text(json.dumps(report,indent=2))
except Exception:(O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
