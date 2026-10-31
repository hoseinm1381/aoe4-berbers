"""Recreate the stock Tuareg shield inspection assembly in a separate Blender process."""
import importlib
import json
import os
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'output/tuareg_shield_test'
EXT = Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0, str(EXT.parent))
garrison = importlib.import_module('garrison')
garrison.register()
projection = importlib.import_module('garrison.game_library')
animation = importlib.import_module('garrison.unit_animation')

scene = bpy.context.scene
scene.name = 'Tuareg Shield Ages I-IV'
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene.garrison.asset_library_root = str(ROOT/'art/tuareg_shield/garrison_library')
scene.garrison.game_asset_connection = str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.local.json')
scene.garrison.game_asset_index = str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.sqlite3')
socket = 'metarig_larmpalmsocket'
correction = Matrix(animation.BONE_AXES).inverted() @ Matrix(animation.COOKED_TO_BLENDER).inverted()
clip = json.loads((WORK/'evidence/stock-clip0.json').read_text())
preview_clips=[clip]+[json.loads((WORK/f'evidence/stock-clip{i}.json').read_text()) for i in (120,40)]
evidence = {'schema':'tuareg-shield-blender/v1','blender':bpy.app.version_string,
            'stock_clip':clip['name'],'native_runtime':'not_run','ages':[]}

def load(name, label):
    path = next((WORK/'decoded'/name).rglob('decoded-static.json'))
    report = json.loads(path.read_text())
    assert not report['missing_textures'], report['missing_textures']
    proxy = bpy.data.objects.new(label, None)
    scene.collection.objects.link(proxy)
    root = projection._apply_decoded_static(proxy, report, select_result=False, create_controls=True)
    root.name = label
    root['stock_source_manifest'] = str(path)
    root['tuareg_source_preserved'] = True
    return root, report

def children(root):
    return list(root.children_recursive)

for age in range(1,5):
    root, source = load(f'age{age}', f'Tuareg_Age_{age}')
    root['tuareg_age'] = age
    root.location.x = (age-1)*2.1
    rig = next(o for o in children(root) if o.type=='ARMATURE' and o.get('garrison_skeleton_status'))
    rig.name = f'Tuareg_Age_{age}_StockRig'
    assert len(rig.data.bones)==48 and socket in rig.data.bones
    shield, shield_source = load('shield', f'Tuareg_Age_{age}_DonsoShield')
    anchor = bpy.data.objects.new(f'Tuareg_Age_{age}_LeftPalmSocket', None)
    scene.collection.objects.link(anchor)
    anchor.parent = root
    anchor.matrix_parent_inverse = Matrix.Identity(4)
    constraint = anchor.constraints.new('COPY_TRANSFORMS')
    constraint.target = rig
    constraint.subtarget = socket
    shield.parent = anchor
    shield.matrix_parent_inverse = Matrix.Identity(4)
    shield.matrix_basis = correction
    shield['native_marker'] = 'MetaRig_LArmPalmSocket'
    shield['stock_model'] = 'art/civilizations/malian/weapons/mal_shield_donso/mal_shield_donso'
    errors=[];actions=[]
    for preview in preview_clips:
        target=animation.preview_target(rig)
        if target.animation_data and target.animation_data.action:
            target.animation_data.action.use_fake_user=True
            target.animation_data.action=None
        target, action = animation.import_clip_action(rig,preview,root_motion=False)
        actions.append(action.name)
        for frame in [1,max(1,preview['frame_count']//2),preview['frame_count']]:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            expected = rig.matrix_world @ rig.pose.bones[socket].matrix @ correction
            error=max(abs(a-b) for ra,rb in zip(shield.matrix_world,expected) for a,b in zip(ra,rb))
            errors.append(error)
    animation.activate_clip_action(target,bpy.data.actions[actions[0]])
    assert max(errors)<1e-5, (age,errors)
    body_meshes=[o for o in children(root) if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    evidence['ages'].append({'age':age,'bone_count':len(rig.data.bones),
        'stock_model_sha256':source['skeleton']['source_sha256'],
        'body_lod_meshes':len(body_meshes),'shield_source_sha256':shield_source['skeleton']['source_sha256'],
        'socket_matrix_max_error':max(errors),'preview_actions':actions})

scene.frame_set(1)
custom_shapes={bone.custom_shape for obj in scene.objects if obj.type=='ARMATURE' for bone in obj.pose.bones if bone.custom_shape}
for obj in scene.objects:
    if obj.type=='ARMATURE' or 'Ring' in obj.name or obj in custom_shapes:
        obj.hide_render=True
        obj.hide_set(True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/tuareg_shield/Tuareg_Shield_Ages_I_IV.blend'))
(WORK/'evidence/blender-assembly.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print('TUAREG_ASSEMBLY_SAVED='+json.dumps(evidence),flush=True)

# Presentation-only camera/lights are created after saving the editable assembly.
scene.render.engine='CYCLES'
scene.cycles.samples=24
scene.render.resolution_x=1200
scene.render.resolution_y=650
scene.render.resolution_percentage=100
scene.world.color=(0.3,0.3,0.3)
camera_data=bpy.data.cameras.new('QA camera')
camera=bpy.data.objects.new('QA camera',camera_data);scene.collection.objects.link(camera)
camera.location=(3.2,-7,3.8)
direction=Vector((3.2,0,1.0))-camera.location
camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO';camera_data.ortho_scale=9
scene.camera=camera
for label,location,power in [('key',(1,-4,6),1200),('fill',(7,2,5),1000)]:
    data=bpy.data.lights.new('QA '+label,'AREA');data.energy=power;data.shape='DISK';data.size=5
    light=bpy.data.objects.new('QA '+label,data);scene.collection.objects.link(light);light.location=location
    light.rotation_euler=(Vector((3.2,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(WORK/'evidence/tuareg-four-ages.png')
bpy.ops.render.render(write_still=True,scene=scene.name)
