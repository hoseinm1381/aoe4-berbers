import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(r'E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai'); A=R/'art/buildings/tc'; O=R/'output/buildings_batch/tc'
bpy.ops.wm.open_mainfile(filepath=str(A/'Untouched_Abbasid_TC_Age1.blend'))
with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.render.resolution_x=640;s.render.resolution_y=480;s.render.resolution_percentage=100
 s.world=bpy.data.worlds.new('reference studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
 bpy.ops.object.camera_add(location=(14,-18,13));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=16;s.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-5,-8,13));bpy.context.object.data.energy=2200;bpy.context.object.data.size=8
 s.render.filepath=str(O/'untouched_donor_preview.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.quit_blender()
