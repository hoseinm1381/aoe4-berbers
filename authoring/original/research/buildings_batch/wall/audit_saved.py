import bpy,bmesh,json,math,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/wall';O=R/'output/buildings_batch/wall'
result=[]
try:
 for age in (2,3,4):
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Wall_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   scene=bpy.context.scene;cam=scene.camera;scene.render.resolution_x=400;scene.render.resolution_y=400
   saved={'age':age,'packed_images':[i.name for i in bpy.data.images if i.packed_file],'variants':[]}
   assert len(saved['packed_images'])>=5
   for c in bpy.data.collections:
    c.hide_render=True
    for ob in c.objects:ob.hide_set(True)
   for kind,target,scale,loc in [('corner_90',(-1.5,1.5,4),18,(17,-20,17)),('slope_up_6m',(0,0,4),13,(13,-18,14)),('end_6m',(0,0,4),13,(13,-18,14)),('damaged_6m',(0,0,4),13,(13,-18,14)),('destroyed_6m',(0,0,1),9,(9,-12,8))]:
    col=bpy.data.collections[kind];col.hide_render=False
    for ob in col.objects:ob.hide_set(False)
    cam.data.ortho_scale=scale;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(O/f'age{age}_{kind}.png');bpy.ops.render.render(write_still=True)
    col.hide_render=True
    for ob in col.objects:ob.hide_set(True)
   # Actual slope merlon bottom-to-parapet top planes: both x endpoints, no gap.
   slopechecks=[]
   for ob in bpy.data.collections['slope_up_6m'].objects:
    if ob.type=='MESH' and 'merlon' in ob.name and 'cap' not in ob.name:
     for v in ob.data.vertices:
      co=ob.matrix_world@v.co
      gap=co.z-(7.6+1.2*co.x/6)
      if gap<.3:slopechecks.append(abs(gap)<1e-5)
   assert slopechecks and all(slopechecks)
   saved['slope_seating_samples']=len(slopechecks)
   # Ray checks in corner clear turning interior, against every visible corner mesh.
   rays=[]
   points=[(-5.8,0),(-3,0),(-1.2,0),(0,0),(0,1.2),(0,3),(0,5.8),(-3,-1.49),(-3,1.49),(-1.49,3),(1.49,3)]
   for x,y in points:
    hitz=[]
    for ob in bpy.data.collections['corner_90'].objects:
     if ob.type!='MESH':continue
     inv=ob.matrix_world.inverted();hit,p,n,idx=ob.ray_cast(inv@Vector((x,y,20)),inv.to_3x3()@Vector((0,0,-1)))
     if hit:hitz.append((ob.matrix_world@p).z)
    z=max(hitz) if hitz else None;rays.append({'xy':[x,y],'highest_z':z,'pass':z is not None and abs(z-7)<1e-5})
   assert all(v['pass'] for v in rays),rays
   saved['corner_walk_rays']=rays
   result.append(saved)
 for age in (2,3,4):
  for kind in ('straight_6m','corner_90','slope_up_6m'):
   bpy.ops.wm.read_factory_settings(use_empty=True)
   with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
    bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Wall_Age{age}_{kind}.fbx'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];sockets=[o for o in bpy.context.scene.objects if o.type=='EMPTY'];assert meshes and len(sockets)==2
    finite=all(math.isfinite(k) for ob in meshes for v in ob.data.vertices for k in v.co);assert finite
    result.append({'fbx_age':age,'variant':kind,'mesh_count':len(meshes),'sockets':[{'name':o.name,'position':list(o.location)} for o in sockets],'finite':finite})
 (O/'saved_and_fbx_audit.json').write_text(json.dumps(result,indent=2))
except Exception:
 (O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
