"""Author an editable animation preview; NOT a supported game export.

The installed Garrison 0.1.3 exporter refuses a new ability clip. This file
preserves the working assembly and prepares only the missing source motion.
Native playback needs an admitted base_spearshield clip/control and upper-body
layering before integration. No tuning, SCAR, native asset or package is changed.
"""
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_ability_pose_test'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent))
g=importlib.import_module('garrison');g.register()
animation=importlib.import_module('garrison.unit_animation')
source=ROOT/'art/tuareg_shield/Tuareg_Shield_Ages_I_IV.blend'
destination=ROOT/'art/tuareg_shield/Tuareg_Shield_Q_RaiseHold_SOURCE_ONLY.blend'
assert not destination.exists(),'Preserve existing animation authoring work.'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene;scene.render.fps=30;scene.frame_set(1)
socket='metarig_larmpalmsocket'
upper_name='metarig_larmupper1'
correction=Matrix(animation.BONE_AXES).inverted() @ Matrix(animation.COOKED_TO_BLENDER).inverted()
report={'schema':'tuareg-q-source-animation/v1','status':'source_only_not_exportable',
        'blender':bpy.app.version_string,'source':str(source),'source_sha256':source_hash,
        'output':str(destination),'desired_active_seconds':15,'preview_seconds':15.4,
        'fps':30,'key_times':'raise 0-0.4s; hold to 15s; lower 15-15.4s',
        'export_blocker':'Garrison 0.1.3: new ability clip replacement timing is not qualified',
        'runtime_requirement':'private base_spearshield ability pose/control plus upper-body layering during movement/combat',
        'native_runtime':'not_implemented','ages':[]}

def matrix_error(a,b):return max(abs(x-y) for ra,rb in zip(a,b) for x,y in zip(ra,rb))

for age in range(1,5):
    rig=bpy.data.objects[f'Tuareg_Age_{age}_StockRig']
    target=animation.preview_target(rig)
    scene.frame_set(1);bpy.context.view_layer.update()
    original_action=target.animation_data.action
    original_action.use_fake_user=True
    baseline={b.name:b.matrix_basis.copy() for b in target.pose.bones}
    original_root=target.pose.bones['metarig_root'].matrix.copy()
    initial_socket=target.pose.bones[socket].matrix.translation.copy()
    original_upper=target.pose.bones[upper_name].matrix.copy()
    shoulder=original_upper.translation.copy()
    direction=initial_socket-shoulder
    axis=direction.cross(Vector((0,0,1))).normalized()
    action=bpy.data.actions.new(f'Tuareg_Q_RaiseHoldLower_Age{age}_SOURCE_ONLY')
    action.use_fake_user=True
    action['native_export_status']='not_supported_by_installed_Garrison'
    action['gameplay_trigger']='not_bound'
    action['upper_body_overlay_required']=True
    action['active_seconds']=15.0
    target.animation_data.action=None
    for bone in target.pose.bones:bone.matrix_basis=baseline[bone.name]

    def trial(angle):
        for bone in target.pose.bones:bone.matrix_basis=baseline[bone.name]
        bpy.context.view_layer.update()
        rotation=Quaternion(axis,angle).to_matrix().to_4x4()
        target.pose.bones[upper_name].matrix=Matrix.Translation(shoulder) @ rotation @ Matrix.Translation(-shoulder) @ original_upper
        bpy.context.view_layer.update()
        return target.pose.bones[socket].matrix.translation.z-initial_socket.z

    low=0.0;high=math.radians(80)
    assert trial(high)>0.20,'Arm cannot reach requested preview height'
    for _ in range(30):
        mid=(low+high)/2
        if trial(mid)<0.20:low=mid
        else:high=mid
    trial((low+high)/2)
    raised=target.pose.bones[upper_name].matrix_basis.copy()
    base_rotation=baseline[upper_name].to_quaternion()
    raised_rotation=raised.to_quaternion()
    assert (raised.translation-baseline[upper_name].translation).length<1e-5
    assert max(abs(v-1) for v in raised.to_scale())<1e-5
    for bone in target.pose.bones:bone.matrix_basis=baseline[bone.name]
    target.animation_data_create();target.animation_data.action=action
    for bone in target.pose.bones:
        bone.rotation_mode='QUATERNION'
        for channel in ('location','rotation_quaternion','scale'):
            bone.keyframe_insert(data_path=channel,frame=1,group=bone.name)
    upper=target.pose.bones[upper_name]
    for frame,weight in [(1,0),(4,0.15625),(7,0.5),(10,0.84375),(13,1),
                         (451,1),(454,0.84375),(457,0.5),(460,0.15625),(463,0)]:
        upper.rotation_quaternion=base_rotation.slerp(raised_rotation,weight)
        upper.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=upper.name)
    action['changed_bones']=upper_name
    errors=[];heights=[];root_errors=[];scale_errors=[]
    shield=bpy.data.objects[f'Tuareg_Age_{age}_DonsoShield']
    for frame in (1,7,13,180,300,451,457,463):
        scene.frame_set(frame);bpy.context.view_layer.update()
        expected=rig.matrix_world @ rig.pose.bones[socket].matrix @ correction
        errors.append(matrix_error(shield.matrix_world,expected))
        heights.append((frame,rig.pose.bones[socket].matrix.translation.z))
        root_errors.append(matrix_error(target.pose.bones['metarig_root'].matrix,original_root))
        scale_errors.append(max(abs(v-1) for b in target.pose.bones for v in b.scale))
    lift=heights[2][1]-heights[0][1]
    assert abs(lift-0.20)<1e-4,(age,lift)
    assert max(errors)<1e-5 and max(root_errors)<1e-5 and max(scale_errors)<1e-5
    assert abs(heights[-1][1]-heights[0][1])<1e-5
    report['ages'].append({'age':age,'action':action.name,'bones':len(rig.data.bones),
        'shield_lift_preview_m':lift,'shield_socket_matrix_error':max(errors),
        'stationary_root_error':max(root_errors),'unit_scale_error':max(scale_errors),
        'socket_height_samples':heights,'original_stock_action_preserved':original_action.name})

scene.frame_start=1;scene.frame_end=463;scene.frame_set(13)
scene['tuareg_q_animation_status']='SOURCE ONLY: no supported native ability export/control'
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
report['output_sha256']=hashlib.sha256(destination.read_bytes()).hexdigest()
(WORK/'blender-source-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SOURCE_ONLY_ANIMATION='+json.dumps(report),flush=True)

# Presentation cameras are added after the editable source is saved.
scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.resolution_x=1200;scene.render.resolution_y=650;scene.render.resolution_percentage=100
scene.world.color=(0.3,0.3,0.3)
camera_data=bpy.data.cameras.new('Source QA camera')
camera=bpy.data.objects.new('Source QA camera',camera_data);scene.collection.objects.link(camera)
camera.location=(3.2,-7,3.8);camera_data.type='ORTHO';camera_data.ortho_scale=9
camera.rotation_euler=(Vector((3.2,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
for label,location,power in [('key',(1,-4,6),1200),('fill',(7,2,5),1000)]:
    data=bpy.data.lights.new('Source QA '+label,'AREA');data.energy=power;data.size=5
    light=bpy.data.objects.new('Source QA '+label,data);scene.collection.objects.link(light);light.location=location
    light.rotation_euler=(Vector((3.2,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
for frame,label in [(1,'lowered'),(13,'raised')]:
    scene.frame_set(frame);scene.render.filepath=str(WORK/f'blender-source-{label}.png')
    bpy.ops.render.render(write_still=True)
