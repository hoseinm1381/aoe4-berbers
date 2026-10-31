import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/marrakech';O=R/'output/buildings_batch/marrakech'
try:
 for age in [3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Marrakech_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
   for ob in obs:
    if ob.name.startswith('walk_access_stair_'):ob.location.x=2.625
   for ob in obs:
    if ob.name.startswith('outer_walk_parapet'):
     ob.dimensions.y=6.88;bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.select_set(False)
    if ob.name.startswith('lime_stone_rampart_repair'):
     ob.location.x=3.55 if ob.location.x>0 else -3.55;ob.dimensions.x=.14;bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.select_set(False)
   bpy.context.view_layer.update()
   ob=bpy.data.objects['walk_access_stair_9'];wall=bpy.data.objects['side_wall_walk_3.25'];a=max((ob.matrix_world@Vector(v)).x for v in ob.bound_box);b=min((wall.matrix_world@Vector(v)).x for v in wall.bound_box);gap=b-a;assert abs(gap)<1e-5
   val=json.loads((O/f'age{age}_validation.json').read_text());val['void_guards'].append({'access_stair_to_east_walk_signed_gap':gap,'pass':True});(O/f'age{age}_validation.json').write_text(json.dumps(val,indent=2))
   bpy.ops.object.select_all(action='DESELECT')
   for ob in obs:ob.select_set(True)
   bpy.context.view_layer.objects.active=obs[0];bpy.ops.export_scene.fbx(filepath=str(A/f'Berber_Marrakech_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
   bpy.ops.wm.save_as_mainfile(filepath=str(A/f'Berber_Marrakech_Age{age}.blend'))
   bpy.context.scene.render.filepath=str(O/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
finally:bpy.ops.wm.quit_blender()
