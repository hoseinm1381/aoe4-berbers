import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/wall_gate';O=R/'output/buildings_batch/wall_gate'
try:
 reports=[]
 for age in [2,3,4]:
  for state,suffix in [('closed',''),('open','_Open')]:
   bpy.ops.wm.read_factory_settings(use_empty=True)
   with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
    bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_StoneGate_Age{age}{suffix}.fbx'))
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    gate=bpy.data.objects['bone_gate'];parts=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent==gate]
    pts=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box];low=min(v.z for v in pts);expect=.08 if state=='closed' else 6.08
    assert abs(low-expect)<1e-4,(age,state,low)
    deck=bpy.data.objects['continuous_rampart_deck'];z=max((deck.matrix_world@Vector(v)).z for v in deck.bound_box);assert abs(z-7)<1e-4
    reports.append({'age':age,'state':state,'moving_meshes':len(parts),'blade_bottom':low,'deck_z':z,'native_binding':'not qualified'})
 (O/'fbx_readback_audit.json').write_text(json.dumps(reports,indent=2));print('FBX_READBACK_PASS',flush=True)
except Exception:(O/'FBX_AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
