"""Post-construction source checks and presentation captures; does not overwrite source."""
import bpy,importlib,json,sys,os,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/tuareg_lower_shield';OUT=ROOT/'output/tuareg_lower_shield_trial/qa';OUT.mkdir(exist_ok=True)
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison import unit_animation as anim
bpy.ops.wm.open_mainfile(filepath=str(ART/'Tuareg_Lower_Shield_Ages_I_IV.blend'))
scene=bpy.context.scene
for o in scene.objects:
    if o.type in ('LIGHT','CAMERA') or o.name=='Cube':o.hide_render=True
    if o.type=='ARMATURE':o.hide_render=True;o.data.pose_position='POSE'
rigs=[bpy.data.objects[f'Refined_Age_{a}_NativeRig'] for a in range(1,5)]
sample=json.loads((ROOT/'output/tuareg_refined_trial/clips/clip143.json').read_text())
sample['samples']=sample['samples'][:3];sample['frame_count']=3
correction=Matrix(anim.BONE_AXES).inverted()@Matrix(anim.COOKED_TO_BLENDER).inverted()
shield=bpy.data.objects['tuareg_agher_refined'];spear=bpy.data.objects['tuareg_long_spear_refined']
shield.hide_render=True;spear.hide_render=True
checks=[]
for age,rig in enumerate(rigs,1):
    rig.hide_set(False);target,action=anim.import_clip_action(rig,sample,root_motion=False)
    for label,source,socket in [('shield',shield,'metarig_larmpalmsocket'),('spear',spear,'metarig_rarmpalmsocket')]:
        copy=source.copy();copy.data=source.data.copy();scene.collection.objects.link(copy);copy.name=f'QA age{age} {label}';copy.hide_render=False
        anchor=bpy.data.objects.new(f'QA age{age} {label} socket',None);scene.collection.objects.link(anchor)
        anchor.parent=rig.parent;anchor.matrix_parent_inverse=Matrix.Identity(4)
        con=anchor.constraints.new('COPY_TRANSFORMS');con.target=rig;con.subtarget=socket
        copy.parent=anchor;copy.matrix_parent_inverse=Matrix.Identity(4);copy.matrix_basis=correction
        scene.frame_set(1);bpy.context.view_layer.update()
        expected=rig.matrix_world@rig.pose.bones[socket].matrix@correction
        err=max(abs(a-b) for ar,br in zip(copy.matrix_world,expected) for a,b in zip(ar,br));assert err<1e-5
        checks.append({'age':age,'equipment':label,'socket':socket,'matrix_error':err})
    body=bpy.data.objects[f'Tuareg_Refined_Age_{age}'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    assert all(math.isfinite(c) for v in mesh.vertices for c in v.co);ev.to_mesh_clear()

scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world.color=(.23,.23,.23)
camdata=bpy.data.cameras.new('QA presentation camera');cam=bpy.data.objects.new('QA presentation camera',camdata);scene.collection.objects.link(cam)
camdata.type='ORTHO';camdata.ortho_scale=9.0;cam.location=(2.6,-8,4.0);look=Vector((2.8,0,2.0));cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
for position,power in [((1,-3,5),850),((6,2,4),600)]:
    data=bpy.data.lights.new('QA softbox','AREA');data.energy=power;data.size=4
    light=bpy.data.objects.new('QA softbox',data);scene.collection.objects.link(light);light.location=position;light.rotation_euler=(look-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/'four-ages-assembled.png');bpy.ops.render.render(write_still=True)
for o in scene.objects:
    if o.type=='MESH':o.hide_render=not o.name.startswith('Tuareg_Refined_Age_')
for rig in rigs:rig.data.pose_position='REST'
bpy.context.view_layer.update();camdata.ortho_scale=7.8
scene.render.resolution_y=650
cam.location=(2.8,-7,2.4);look=Vector((2.8,0,.98));cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/'four-ages-bodies.png');bpy.ops.render.render(write_still=True)
# Six orthographic shape checks on the constructed Age II mesh, without equipment occlusion.
for o in scene.objects:
    if o.type=='MESH':o.hide_render=o.name!='Tuareg_Refined_Age_2'
rigs[1].data.pose_position='REST';bpy.context.view_layer.update()
camdata.ortho_scale=2.2;look=Vector((1.9,0,.98));scene.render.resolution_x=500;scene.render.resolution_y=600
for name,direction in [('front',(0,-4,0)),('back',(0,4,0)),('left',(4,0,0)),('right',(-4,0,0)),('top',(0,0,4)),('bottom',(0,0,-4))]:
    cam.location=look+Vector(direction);cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
(OUT/'checks.json').write_text(json.dumps({'socket_checks':checks,'deformation':'finite stock calm-idle frame1 across all ages','six_sides':True,'native_runtime':'pending'},indent=2))
print('SOURCE_QA_READY',flush=True)
