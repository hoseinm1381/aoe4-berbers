import bpy
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/marrakech';O=R/'output/buildings_batch/marrakech'
try:
 for age in [3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Marrakech_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   sc=bpy.context.scene;cam=sc.camera;target=Vector((0,0,2.1));sc.cycles.samples=2;sc.render.resolution_x=384;sc.render.resolution_y=384
   for name,loc in [('front',(0,-12,1.5)),('back',(0,12,1.5)),('left',(-12,0,1.5)),('right',(12,0,1.5)),('top',(0,0,12)),('bottom',(0,0,-12))]:
    cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
   for ob in sc.objects:
    if 'roof' in ob.name or 'parapet' in ob.name:ob.hide_render=True
   cam.location=(8,-10,11);cam.rotation_euler=(Vector((0,1,.7))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'age{age}_interior.png');bpy.ops.render.render(write_still=True)
finally:bpy.ops.wm.quit_blender()
