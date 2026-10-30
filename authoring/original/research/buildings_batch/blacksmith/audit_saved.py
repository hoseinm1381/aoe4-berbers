import bpy,bmesh,json,math,traceback,os
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/blacksmith';O=R/'output/buildings_batch/blacksmith';report=[];success=False

def bb(o):
 pts=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]]
def inside_overlap(o,lo,hi):
 a,b=bb(o);return all(b[k]>lo[k]+1e-6 and a[k]<hi[k]-1e-6 for k in range(3))
try:
 for age in [2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Blacksmith_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   bpy.context.view_layer.update();meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];count=len(meshes)
   assert all(im.packed_file for im in bpy.data.images if im.type=='IMAGE')
   for o in meshes:
    assert o.data.uv_layers and all(math.isfinite(v) for ve in o.data.vertices for v in ve.co)
    bm=bmesh.new();bm.from_mesh(o.data);assert bm.calc_volume(signed=True)>0 and all(e.is_manifold for e in bm.edges);bm.free()
    o.data.calc_loop_triangles();uv=o.data.uv_layers.active
    for t in o.data.loop_triangles:
     a,b,c=[uv.data[i].uv for i in t.loops];assert abs((b-a).cross(c-a))>1e-10
   assert abs(bb(bpy.data.objects['foundation'])[0][2])<1e-6
   contacts=[]
   for child,parent in [('anvil','anvil_stump'),('hearth_base','court_floor'),('trough_bottom','court_floor'),('bench_top','bench_leg'),('store_roof','store_back'),('anvil_hammer_handle','anvil')]:
    gap=bb(bpy.data.objects[child])[0][2]-bb(bpy.data.objects[parent])[1][2];assert abs(gap)<1e-5;contacts.append({'interface':child+'/'+parent,'signed_gap_m':gap})
   # Conservative AABB exclusion works for real voids built with separate closed wall segments.
   voids={'flue':([-2.58,1.10,1.2],[-2.02,1.60,4.1]),'forge_mouth':([-2.90,.58,.83],[-1.75,1.84,1.72]),'front_passage':([-.40,-4,.20],[.90,.80,1.9]),'store_door':([1.37,.88,.20],[2.28,1.16,1.78]),'trough_basin':([1.19,-2.30,.45],[2.21,-.80,.73])}
   for name,(lo,hi) in voids.items():
    coll=[o.name for o in meshes if inside_overlap(o,lo,hi)];assert not coll,(name,coll)
   manifest=json.loads((A/f'age{age}_construction.json').read_text());assert len(manifest['parts'])==count
   owner=[o.name for o in meshes if o.data.materials[0].get('ber_owner_mask')==1];assert owner
   bpy.ops.wm.read_factory_settings(use_empty=True)
   with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Blacksmith_Age{age}.fbx'))
   imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==count and all(o.data.uv_layers for o in imported)
   report.append({'age':age,'saved_meshes':count,'fbx_meshes':len(imported),'packed_images':True,'uv_triangle_areas_positive':True,'stage_manifest_matches':True,'owner_zone_objects':owner,'contacts':contacts,'measured_voids_m':voids,'aabb_void_collision_count':0,'native_pathing':'not tested'})
 (O/'saved_source_fbx_audit.json').write_text(json.dumps(report,indent=2));success=True
except Exception:
 (O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender();os._exit(0 if success else 1)


