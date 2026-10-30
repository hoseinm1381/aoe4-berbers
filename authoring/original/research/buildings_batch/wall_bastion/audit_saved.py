import bpy,bmesh,json,math,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/wall_bastion';O=R/'output/buildings_batch/wall_bastion';angles={'default':[],'end':[0],'corner':[0,90],'thru':[0,180],'tee':[0,90,270],'cross':[0,90,180,270],'why':[0,120,240]};result=[]
try:
 for age in (2,3,4):
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Bastion_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   packed=[i.name for i in bpy.data.images if i.packed_file];assert len(packed)==5,packed
   rec={'age':age,'packed_images':packed,'variants':[]}
   for kind,ts in angles.items():
    col=bpy.data.collections[kind];meshes=[ob for ob in col.objects if ob.type=='MESH'];rays=[];contacts=[]
    for t in ts:
     for r in (0,.5,1.5,2.5,2.999):
      for across in (-1.49,0,1.49):
       ar=math.radians(t);xx=r*math.sin(ar)+across*math.cos(ar);yy=r*math.cos(ar)-across*math.sin(ar);hits=[]
       for ob in meshes:
        inv=ob.matrix_world.inverted();hit,p,n,idx=ob.ray_cast(inv@Vector((xx,yy,15)),inv.to_3x3()@Vector((0,0,-1)))
        if hit:hits.append((ob.matrix_world@p).z)
       z=max(hits) if hits else None;assert z is not None and abs(z-7)<1e-5,(age,kind,t,r,across,z);rays.append({'xyz':[xx,yy,z],'pass':True})
    for ob in meshes:
     pts=[ob.matrix_world@v.co for v in ob.data.vertices];mn=min(p.z for p in pts);mx=max(p.z for p in pts)
     if 'guard_' in ob.name:assert abs(mn-7)<1e-5;contacts.append({'object':ob.name,'guard_to_walk_gap':mn-7})
     if 'merlon_' in ob.name:assert abs(mn-7.6)<1e-5;contacts.append({'object':ob.name,'merlon_to_guard_gap':mn-7.6})
    rec['variants'].append({'kind':kind,'rays':rays,'seating':contacts,'mesh_count':len(meshes)})
   result.append(rec)
 for age in (2,3,4):
  for kind,ts in angles.items():
   bpy.ops.wm.read_factory_settings(use_empty=True)
   with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
    bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Bastion_Age{age}_{kind}.fbx'));meshes=[ob for ob in bpy.context.scene.objects if ob.type=='MESH'];sockets=[ob for ob in bpy.context.scene.objects if ob.type=='EMPTY'];assert len(sockets)==len(ts);assert meshes
    assert all(math.isfinite(k) for ob in meshes for v in ob.data.vertices for k in v.co)
    for ob in sockets:assert abs(ob.matrix_world.translation.z-7)<1e-4,ob.matrix_world.translation
    result.append({'fbx_age':age,'kind':kind,'meshes':len(meshes),'sockets':len(sockets),'finite':True,'socket_z7':True})
 (O/'saved_and_fbx_audit.json').write_text(json.dumps(result,indent=2))
except Exception:
 (O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
