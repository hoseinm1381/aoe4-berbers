import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/palisade_bastion';O=R/'output/buildings_batch/palisade_bastion'
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_PalisadeBastion_Age{age}.blend'))
  ctx=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);ctx.__enter__()
  states=json.loads((A/f'age{age}_states.json').read_text())['states']
  for i,(name,s) in enumerate(states.items()):
   for n in s['objects']:
    ob=bpy.data.objects[n];ob.hide_render=False;ob.hide_set(False);ob.location.x+=(i-2)*1.5
  sc=bpy.context.scene;sc.render.resolution_x=1280;sc.render.resolution_y=768;sc.cycles.samples=4;cam=sc.camera;cam.location=(5,-14,9);cam.rotation_euler=(Vector((0,0,2.3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9
  sc.render.filepath=str(O/f'age{age}_state_gallery.png');bpy.ops.render.render(write_still=True)
except Exception:
 import traceback;(O/'GALLERY_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender()
