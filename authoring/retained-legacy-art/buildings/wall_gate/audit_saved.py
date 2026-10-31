import bpy,bmesh,json,math,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/wall_gate';O=R/'output/buildings_batch/wall_gate'
def bounds(o):
 v=[o.matrix_world@Vector(c) for c in o.bound_box];return [[min(p[k] for p in v) for k in range(3)],[max(p[k] for p in v) for k in range(3)]]
def hits(origin,dir,objs):
 result=[]
 for ob in objs:
  inv=ob.matrix_world.inverted();ok,loc,no,idx=ob.ray_cast(inv@Vector(origin),(inv.to_3x3()@Vector(dir)).normalized(),distance=100)
  if ok:result.append(ob.name)
 return result
try:
 audits=[]
 for age in [2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_StoneGate_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   sc=bpy.context.scene;sc.frame_set(1);bpy.context.view_layer.update();meshes=[o for o in sc.objects if o.type=='MESH']
   gate=bpy.data.objects['bone_gate'];assert (gate.location-Vector((0,0,0))).length<1e-8
   assert gate.parent.name=='bone_root' and gate.animation_data.action.name=='Portcullis_LiftClose_SOURCE'
   deck=bounds(bpy.data.objects['continuous_rampart_deck']);assert abs(deck[1][2]-7)<1e-6 and abs(deck[0][1]+2.1)<1e-5 and abs(deck[1][1]-2.1)<1e-5
   contacts=[]
   for side in ['left','right']:
    tower=bounds(bpy.data.objects[side+'_tower_pier']);gap=deck[0][2]-tower[1][2];assert gap<=0;contacts.append({'interface':side+' tower/deck','signed_gap_m':gap})
   crest=max(bounds(o)[1][2] for o in meshes if o.name.startswith('crenellation'));assert abs(crest-8.2)<1e-5
   for side,x in [('left',-5),('right',5)]:assert (bpy.data.objects['SOURCE_socket_'+side].location-Vector((x,0,7))).length<1e-8
   uv_errors=[];mesh_errors=[]
   for ob in meshes:
    bm=bmesh.new();bm.from_mesh(ob.data);vol=bm.calc_volume(signed=True);non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-9 for f in bm.faces);bm.free()
    if non or deg or vol<=0 or min(ob.scale)<=0:mesh_errors.append(ob.name)
    uv=ob.data.uv_layers.active
    for poly in ob.data.polygons:
     p=[uv.data[i].uv for i in poly.loop_indices];area=abs(sum(p[i].x*p[(i+1)%len(p)].y-p[(i+1)%len(p)].x*p[i].y for i in range(len(p)))/2)
     if area<1e-9 or any(not math.isfinite(c) for q in p for c in q):uv_errors.append(ob.name)
   assert not mesh_errors and not uv_errors
   packed=[{'name':i.name,'packed':bool(i.packed_file)} for i in bpy.data.images if i.type=='IMAGE'];assert all(i['packed'] for i in packed)
   sc.frame_set(40);bpy.context.view_layer.update();assert abs(gate.location.z-6)<1e-7
   clear=[]
   for x in [-1.7,-.85,0,.85,1.7]:
    for z in [.15,1,2,3,4,4.9]:
     h=hits((x,-30,z),(0,1,0),meshes);assert not h,(x,z,h);clear.append([x,z])
   blade=[o for o in meshes if o.parent==gate];blade_min=min(bounds(o)[0][2] for o in blade);assert blade_min>5.9
   # Moving blade depth is in front of fixed deck, including hardware.
   blade_ymax=max(bounds(o)[1][1] for o in blade);assert blade_ymax<deck[0][1]
   walk=[]
   for x in [-4.9,-3,0,3,4.9]:
    for y in [-1.4,0,1.4]:
     ob=bpy.data.objects['continuous_rampart_deck'];ok,loc,n,idx=ob.ray_cast(ob.matrix_world.inverted()@Vector((x,y,8)),Vector((0,0,-1)),distance=3);loc=ob.matrix_world@loc;assert ok and abs(loc.z-7)<1e-5;walk.append([x,y,loc.z])
   audits.append({'age':age,'mesh_count':len(meshes),'mesh_errors':mesh_errors,'uv_errors':uv_errors,'contacts':contacts,'walk_surface_samples':walk,'open_passage_clear_ray_samples':clear,'open_blade_bottom':blade_min,'blade_ymax':blade_ymax,'deck_ymin':deck[0][1],'crest':crest,'packed_images':packed,'native_runtime':'unqualified'})
 (O/'saved_source_audit.json').write_text(json.dumps(audits,indent=2));print('SAVED_SOURCE_AUDIT_PASS',flush=True)
except Exception:(O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
