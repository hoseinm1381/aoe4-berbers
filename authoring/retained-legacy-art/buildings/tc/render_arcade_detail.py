import bpy
from pathlib import Path
from mathutils import Vector
R=Path(r'E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai');A=R/'art/buildings/tc';O=R/'output/buildings_batch/tc'
for age in range(1,5):
 bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_TC_Age{age}.blend'))
 with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
  s=bpy.context.scene;cam=s.camera;cam.location=(1.5,.65,1.65);cam.rotation_euler=(Vector((-2.40,0,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type="PERSP";cam.data.lens=26;s.cycles.samples=4;s.render.resolution_x=640;s.render.resolution_y=480;s.render.filepath=str(O/f'age{age}_arcade_detail.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.quit_blender()

