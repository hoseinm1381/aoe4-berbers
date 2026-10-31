import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/tlemcen';O=R/'output/buildings_batch/tlemcen'
try:
 for age in [3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Tlemcen_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
   for o in meshes:
    if o.name.startswith('gallery_roof_'):
     # Preserve rear contact y=.385, stretch front to enclosure front y=-3.61.
     fac=3.995/3.69;o.location.y=-1.6125+(o.location.y+1.46)*fac
     for v in o.data.vertices:v.co.y*=fac
     o.data.update()
   bpy.ops.object.select_all(action='DESELECT')
   for o in meshes:o.select_set(True)
   bpy.context.view_layer.objects.active=meshes[0]
   bpy.ops.export_scene.fbx(filepath=str(A/f'Berber_Tlemcen_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
   sc=bpy.context.scene;cam=sc.camera;target=Vector((0,0,2.1));sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768;cam.location=(8,-10,9);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
   bpy.ops.wm.save_as_mainfile(filepath=str(A/f'Berber_Tlemcen_Age{age}.blend'));sc.render.filepath=str(O/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
   sc.cycles.samples=2;sc.render.resolution_x=384;sc.render.resolution_y=384
   for name,loc in [('front',(0,-12,1.5)),('back',(0,12,1.5)),('left',(-12,0,1.5)),('right',(12,0,1.5)),('top',(0,0,12)),('bottom',(0,0,-12))]:
    cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
   for o in meshes:
    if 'roof' in o.name or 'parapet' in o.name:o.hide_render=True
   cam.location=(8,-10,11);cam.rotation_euler=(Vector((0,1,.7))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'age{age}_interior.png');bpy.ops.render.render(write_still=True)
   print('GALLERY_REPAIRED',age,flush=True)
 (O/'gallery_repair.json').write_text(json.dumps({'fault':'front gallery roof ended .085 behind entry enclosure; rear originally overlapped main roof','repair':'rear exact y=.385, front exact enclosure face y=-3.61','source_recipe_updated':True,'preview_samples':8,'six_side_samples':2},indent=2))
except Exception:
 (O/'REPAIR_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
