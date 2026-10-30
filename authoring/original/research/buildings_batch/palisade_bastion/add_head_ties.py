import bpy,json,math,traceback,bmesh
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/palisade_bastion';O=R/'output/buildings_batch/palisade_bastion'
src=(A/'build_palisade_bastion.py').read_text();exec(src[:src.index('def donor():')]);exec(src[src.index('def audit(objs):'):src.index('def build(age):')])
try:
 for age in [2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_PalisadeBastion_Age{age}.blend'))
  ctx=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);ctx.__enter__();PARTS=[];MATS.clear()
  for i,(name,c,owner) in enumerate(COLORS):
   m=bpy.data.materials.get('BerberPalisadeBastion_'+name)
   if m:MATS[name]=(m,i)
  manifest=json.loads((A/f'age{age}_states.json').read_text());states=manifest['states'];construction=json.loads((A/f'age{age}_construction.json').read_text());validation=json.loads((O/f'age{age}_validation.json').read_text())
  for name,state in states.items():
   old=set(bpy.context.scene.objects)
   for y in [-.165,.165]:box('locking_head_tie_x',(0,y,4.08),(.682861328125,.09,.14),'straw',80)
   for x in [-.165,.165]:box('locking_head_tie_y',(x,0,4.08),(.09,.682861328125,.14),'straw',80)
   new=[ob for ob in bpy.context.scene.objects if ob not in old];coll=bpy.data.collections[name]
   for ob in new:
    for c in list(ob.users_collection):c.objects.unlink(ob)
    coll.objects.link(ob)
   state['objects'] += [ob.name for ob in new];validation['states'][name]+=audit(new)
   bpy.ops.object.select_all(action='DESELECT')
   for n in state['objects']:ob=bpy.data.objects[n];ob.hide_set(False);ob.select_set(True)
   bpy.context.view_layer.objects.active=bpy.data.objects[state['objects'][0]]
   bpy.ops.export_scene.fbx(filepath=str(A/f'Berber_PalisadeBastion_Age{age}_{name}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
  construction['parts']+=PARTS
  (A/f'age{age}_states.json').write_text(json.dumps(manifest,indent=2));(A/f'age{age}_construction.json').write_text(json.dumps(construction,indent=2));(O/f'age{age}_validation.json').write_text(json.dumps(validation,indent=2))
  for ob in bpy.context.scene.objects:
   if ob.type=='MESH':ob.hide_render=ob.name not in states['corner_90']['objects'];ob.hide_set(ob.hide_render)
  sc=bpy.context.scene;cam=sc.camera;cam.data.ortho_scale=6.5;cam.location=(9,-13,10);cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=768;sc.render.resolution_y=768;sc.cycles.samples=8
  bpy.ops.wm.save_as_mainfile(filepath=str(A/f'Berber_PalisadeBastion_Age{age}.blend'));sc.render.filepath=str(O/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
  sc.cycles.samples=4;sc.render.resolution_x=256;sc.render.resolution_y=256
  for name,loc in [('front',(0,-12,2)),('back',(0,12,2)),('left',(-12,0,2)),('right',(12,0,2)),('top',(0,0,15)),('bottom',(0,0,-12))]:
   cam.location=loc;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
  for i,(name,state) in enumerate(states.items()):
   for n in state['objects']:ob=bpy.data.objects[n];ob.hide_render=False;ob.hide_set(False);ob.location.x+=(i-2)*1.5
  sc.render.resolution_x=1280;sc.render.resolution_y=768;cam.data.ortho_scale=9;cam.location=(5,-14,9);cam.rotation_euler=(Vector((0,0,2.3))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'age{age}_state_gallery_final.png');bpy.ops.render.render(write_still=True)
except Exception:
 (O/'HEAD_TIE_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender()
