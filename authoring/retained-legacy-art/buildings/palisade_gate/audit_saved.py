import bpy,bmesh,json,math,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/palisade_gate';O=R/'output/buildings_batch/palisade_gate'
reports=[]
def bounds(o):
 pts=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
try:
 for age in range(1,5):
  path=A/f'Berber_PalisadeGate_Age{age}.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   bpy.context.scene.frame_set(1)
   for side,x in [('left',-2.05658977144858),('right',2.0571998845716175)]:
    ob=bpy.data.objects[side+'_diagonal_brace'];length=abs(x)-.015;old=max(v.co.z for v in ob.data.vertices)-min(v.co.z for v in ob.data.vertices);new=math.sqrt(4.36**2+(length-.12)**2)
    for v in ob.data.vertices:v.co.z*=new/old
    ob.rotation_euler.y=(1 if side=='left' else -1)*math.atan((length-.12)/4.36);ob.location.z=2.66
   if age==4:
    for ob in bpy.data.objects:
     if ob.name.startswith('pier_cap'):ob.location.z=1.115
   bpy.context.view_layer.update();checks=[]
   for side in ['left','right']:
    post=bounds(bpy.data.objects[side+'_palm_gatepost']);foot=bounds(bpy.data.objects[side+'_stone_footing']);lintel=bounds(bpy.data.objects['mortised_palm_lintel']);checks.append({'interface':side+' post/footing','signed_gap':post[0][2]-foot[1][2],'expected':-.2});checks.append({'interface':side+' lintel/post','signed_gap':lintel[0][2]-post[1][2],'expected':-.36})
   for side in ['left','right']:
    br=bounds(bpy.data.objects[side+'_diagonal_brace']);cross=[bounds(ob) for ob in bpy.data.objects if ob.name.startswith(side+'_door_crossbeam')]
    low=min(cross,key=lambda q:q[0][2]);high=max(cross,key=lambda q:q[1][2]);checks.append({'interface':side+' brace/lower beam','signed_gap':br[0][2]-low[1][2],'expected':None,'pass':br[0][2]<low[1][2]});checks.append({'interface':side+' brace/upper beam','signed_gap':high[0][2]-br[1][2],'expected':None,'pass':high[0][2]<br[1][2]})
   if age==4:
    caps=[ob for ob in bpy.data.objects if ob.name.startswith('pier_cap')]
    for ob in caps:
     side='left' if ob.location.x<0 else 'right';gap=bounds(ob)[0][2]-bounds(bpy.data.objects[side+'_earth_pier_base'])[1][2];checks.append({'interface':side+' pier cap/base','signed_gap':gap,'expected':0})
   for c in checks:
    if c['expected'] is not None:c['pass']=abs(c['signed_gap']-c['expected'])<1e-5
   assert all(c['pass'] for c in checks),checks
   hinges=[]
   for side,x in [('left',-2.05658977144858),('right',2.0571998845716175)]:
    ob=bpy.data.objects['door_'+side+'_HINGE'];error=(ob.location-Vector((x,-.15005000912143784,0))).length;assert error<1e-6,error;assert ob.animation_data and ob.animation_data.action;hinges.append({'side':side,'hinge_error_m':error,'action':ob.animation_data.action.name,'closed_rotation_degrees':math.degrees(ob.rotation_euler.z)})
   for name in ['albedo','pattern','roughness','normal','metal']:
    matches=[im for im in bpy.data.images if name in im.name.lower()]
    if not matches:matches=[bpy.data.images.load(str(A/(name+'.png')))]
    for im in matches:im.use_fake_user=True;im.pack()
   packed=[{'name':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if im.type=='IMAGE'];assert all(im['packed'] for im in packed)
   geometry=[]
   for ob in [ob for ob in bpy.context.scene.objects if ob.type=='MESH']:
    bm=bmesh.new();bm.from_mesh(ob.data);v=bm.calc_volume(signed=True);nm=sum(not e.is_manifold for e in bm.edges);dg=sum(f.calc_area()<1e-9 for f in bm.faces);bm.free();assert v>0 and nm==0 and dg==0
    geometry.append({'object':ob.name,'volume':v,'nonmanifold':nm,'degenerate':dg})
   bpy.ops.object.select_all(action='DESELECT')
   for ob in bpy.context.scene.objects:
    if ob.type in {'MESH','EMPTY'}:ob.select_set(True)
   bpy.ops.export_scene.fbx(filepath=str(A/f'Berber_PalisadeGate_Age{age}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=True,bake_anim_use_all_actions=False,path_mode='COPY',embed_textures=True)
   bpy.context.scene.frame_set(40);bpy.ops.export_scene.fbx(filepath=str(A/f'Berber_PalisadeGate_Age{age}_Open.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True);bpy.context.scene.frame_set(1)
   # Restore presentation camera source pose; scene remains the closed fixture.
   cam=bpy.context.scene.camera;cam.location=(11,-15,10);cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.render.resolution_x=768;bpy.context.scene.render.resolution_y=768
   bpy.ops.wm.save_as_mainfile(filepath=str(path));cam.location=(0,15,3);cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.render.resolution_x=256;bpy.context.scene.render.resolution_y=256;bpy.context.scene.render.filepath=str(O/f'age{age}_back.png');bpy.ops.render.render(write_still=True);reports.append({'age':age,'contacts':checks,'hinges':hinges,'images':packed,'source_frame':1,'geometry':geometry})
 (O/'saved_source_audit.json').write_text(json.dumps(reports,indent=2))
except Exception:(O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
