import bpy,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/keep';O=R/'output/buildings_batch/keep'
try:
 for age in [3,4]:
    bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Keep_Age{age}.blend'))
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
      s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.background_type='VIEWPORT';s.display.shading.background_color=(.17,.17,.17);s.render.resolution_x=s.render.resolution_y=400;c=s.camera
      for key,loc in [('front',(0,-15,2.3)),('back',(0,15,2.3)),('left',(-15,0,2.3)),('right',(15,0,2.3)),('top',(0,0,16)),('bottom',(0,0,-15))]:
        c.location=loc;c.rotation_euler=(Vector((0,0,2.3))-c.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'age{age}_solid_{key}.png');bpy.ops.render.render(write_still=True)
except Exception:(O/'SOLID_VIEW_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
