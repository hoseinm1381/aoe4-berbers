"""Read the preserved animation assembly without changing its live Blender file."""
import importlib
import json
import os
from pathlib import Path
import sys
import bpy

ROOT=Path(__file__).resolve().parents[2]
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent))
g=importlib.import_module('garrison');g.register()
animation=importlib.import_module('garrison.unit_animation')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/tuareg_shield/Tuareg_Shield_Ages_I_IV.blend'))
scene=bpy.context.scene;scene.frame_set(1)
rig=bpy.data.objects['Tuareg_Age_1_StockRig'];target=animation.preview_target(rig)
rows=[]
for bone in target.pose.bones:
    if 'larm' in bone.name or bone.parent is None:
        rows.append({'name':bone.name,'parent':bone.parent.name if bone.parent else None,
                     'head':list(bone.head),'tail':list(bone.tail),
                     'matrix':list(sum((list(r) for r in bone.matrix),[]))})
result={'target':target.name,'rig':rig.name,'action':target.animation_data.action.name,
        'bones':rows,'frame_end':scene.frame_end}
(ROOT/'output/tuareg_ability_pose_test/pose-source-inspection.json').write_text(json.dumps(result,indent=2))
print('POSE_SOURCE='+json.dumps(result),flush=True)
