import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/palisade_bastion';O=R/'output/buildings_batch/palisade_bastion'
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_PalisadeBastion_Age{age}.blend'))
  ctx=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);ctx.__enter__()
  manifest=json.loads((A/f'age{age}_states.json').read_text());states=manifest['states']
  removed=set()
  for state,v in states.items():
   stays=[n for n in v['objects'] if n.startswith('terminal_diagonal_stay')]
   for n in stays[1::2]:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True);removed.add(n)
   v['objects']=[n for n in v['objects'] if n not in removed]
  (A/f'age{age}_states.json').write_text(json.dumps(manifest,indent=2))
  c=json.loads((A/f'age{age}_construction.json').read_text());c['parts']=[p for p in c['parts'] if p['object'] not in removed];(A/f'age{age}_construction.json').write_text(json.dumps(c,indent=2))
  validation=json.loads((O/f'age{age}_validation.json').read_text())
  for k in validation['states']:validation['states'][k]=[p for p in validation['states'][k] if p['object'] not in removed]
  (O/f'age{age}_validation.json').write_text(json.dumps(validation,indent=2))
  for ob in bpy.context.scene.objects:
   if ob.type=='MESH' and ob.name.startswith('terminal_diagonal_stay'):
    ax=max([0,1],key=lambda k:abs(ob.location[k]));assert abs(abs(ob.location[ax])-.305)<1e-6;ob['contact_face']='inner stay face on timber outer0.275m plane, signed gap0'
  bpy.context.view_layer.update()
  for name,s in states.items():
   bpy.ops.object.select_all(action='DESELECT')
   for n in s['objects']:
    ob=bpy.data.objects[n];ob.hide_set(False);ob.select_set(True)
   bpy.context.view_layer.objects.active=bpy.data.objects[s['objects'][0]]
   bpy.ops.export_scene.fbx(filepath=str(A/f'Berber_PalisadeBastion_Age{age}_{name}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
  for ob in bpy.context.scene.objects:
   if ob.type=='MESH':ob.hide_render=ob.name not in states['corner_90']['objects'];ob.hide_set(ob.hide_render)
  sc=bpy.context.scene;cam=sc.camera;sc.render.resolution_x=768;sc.render.resolution_y=768;sc.cycles.samples=8
  cam.location=(9,-13,10);cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.wm.save_as_mainfile(filepath=str(A/f'Berber_PalisadeBastion_Age{age}.blend'))
  sc.render.filepath=str(O/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
  sc.cycles.samples=4;sc.render.resolution_x=256;sc.render.resolution_y=256
  for name,loc in [('front',(0,-12,2)),('back',(0,12,2)),('left',(-12,0,2)),('right',(12,0,2)),('top',(0,0,15)),('bottom',(0,0,-12))]:
   cam.location=loc;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 (O/'STAY_CONTACT_REPAIR.json').write_text(json.dumps({'ages':[1,2,3,4],'radial_stay_shift_m':.04,'inner_face':.275,'timber_outer_face':.275,'gap':0,'source_recipe_updated':True}))
except Exception:
 import traceback;(O/'STAY_REPAIR_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender()
