"""Presentation-only review capture; run after measured source geometry validation."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'art/landmarks_0_2_7/funduq';P=OUT/'previews';P.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'funduq_editable.blend'))
s=bpy.context.scene;s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world.color=(.16,.16,.16)
bpy.ops.object.camera_add(location=(14,-17,16));cam=bpy.context.object;cam.name='ReviewCamera';s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=15
center=Vector((0,0,2.2))
def look(pos):cam.location=pos;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.62,.62,.62);s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
for view,pos in [('front',(0,-20,2.2)),('back',(0,20,2.2)),('right',(20,0,2.2)),('left',(-20,0,2.2)),('top',(0,0,24)),('bottom',(0,0,-20)),('solid-gameplay',(14,-17,16)),('court-contact',(4,-6,7))]:
 look(pos);s.render.filepath=str(P/(view+'.png'));bpy.ops.render.render(write_still=True)
# Explicit independent far-LOD inspection, no simultaneously visible duplicates.
for lod in [1,2]:
 for c in bpy.data.collections:
  if c.name.startswith('Funduq_LOD'):c.hide_render=c.name!='Funduq_LOD'+str(lod)
 look((14,-17,16));s.render.filepath=str(P/f'LOD{lod}-solid.png');bpy.ops.render.render(write_still=True)
for c in bpy.data.collections:
 if c.name.startswith('Funduq_LOD'):c.hide_render=c.name!='Funduq_LOD0'
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
for pos,energy,size in [((1,-5,16),1800,9),((-8,-10,9),1500,8)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
look((14,-17,16));s.render.filepath=str(P/'material-gameplay.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.quit_blender()

