import bpy,json,bmesh,math,traceback,os,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/dock';O=R/'output/buildings_batch/dock';report=[]
exit_code=0
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]
try:
 for age in [1,2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Dock_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];count=len(objs);images=[im for im in bpy.data.images if im.type=='IMAGE'];assert len(images)==5;assert all(im.packed_file for im in images)
   assert len(json.loads((A/f'age{age}_construction.json').read_text())['parts'])==count
   mats=[m for m in bpy.data.materials if m.name.startswith('BerberDock_')];assert all(m.get('ber_owner_mask') in [0,1] for m in mats);assert sum(m['ber_owner_mask'] for m in mats)==1
   saved_triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objs)
   bpy.context.view_layer.update();door=bounds(bpy.data.objects['horseshoe_door']);wall=bounds(bpy.data.objects['warehouse_front']);door_recess=door[0][1]-wall[0][1];assert abs(door_recess-.035)<1e-5;assert door[1][1]<wall[1][1];assert abs(door[0][2]-.85)<1e-5
   shutters=[o for o in objs if o.name.startswith('warehouse_shutter')];assert len(shutters)==2
   for ob in shutters:
    b=bounds(ob);assert b[0][1]>wall[0][1] and b[1][1]<wall[1][1];assert abs((b[1][0]-b[0][0])-.60)<1e-5
   upper_recess=None
   if age>=3:
    store=bounds(bpy.data.objects['upper_roof_storage']);insert=bounds(bpy.data.objects['upper_store_recessed_louver']);upper_recess=insert[0][1]-store[0][1];assert abs(upper_recess-.1075)<1e-5;assert insert[1][1]<store[0][1]+.14
   bpy.ops.wm.read_factory_settings(use_empty=True)
   with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Dock_Age{age}.fbx'))
   imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==count;assert all(o.data.uv_layers for o in imported)
   assert sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in imported)==saved_triangles
   report.append({'age':age,'saved_meshes':count,'fbx_meshes':len(imported),'triangles':saved_triangles,'packed_images':5,'stage_manifest_matches':True,'owner_material_annotations_verified':True,'uvs_preserved':True,'door_inset':door_recess,'door_ground_contact':True,'shutters_seated_inside_cut_wall':True,'upper_store_insert_recess':upper_recess})
 (O/'saved_source_fbx_audit.json').write_text(json.dumps(report,indent=2))
except Exception:
 exit_code=1;(O/'AUDIT_ERROR.txt').write_text(traceback.format_exc())
finally:
 # Imported FBX leaves a dirty disposable scene. Close this private verifier even if Blender's GUI quit asks to save.
 bpy.ops.wm.quit_blender();sys.stdout.flush();sys.stderr.flush();os._exit(exit_code)
