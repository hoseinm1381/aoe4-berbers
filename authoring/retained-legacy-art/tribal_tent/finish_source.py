"""Inspect the measured structure, furnish it, save iteration and render previews."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tribal_tent/iteration001'
print('FINISH_SCRIPT_STARTED',flush=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/tribal_tent/iterations/001/Berber_Tribal_Tent_Ages_I_IV_001.blend') if '--authored' in sys.argv else str(OUT/'structural_checkpoint.blend'))
print('STRUCTURE_LOADED',flush=True)
scene=bpy.context.scene
for o in scene.objects:
    if o.type in ('LIGHT','CAMERA'):o.hide_render=True
data=bpy.data.cameras.new('Source review camera');camera=bpy.data.objects.new('Source review camera',data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO'
def aim(center,offset,scale):
    target=Vector(center);camera.location=target+Vector(offset);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=scale
def only_age(age):
    for a in range(1,5):
        for o in bpy.data.collections[f'BER_Tent001_Age_{a}'].objects:o.hide_render=a!=age
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.62,.62);scene.display.shading.light='STUDIO';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.world.color=(.045,.045,.045)
scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100
only_age(4);aim((27,0,1.2),(6,-9,6),8.4)
scene.render.filepath=str(OUT/'structure-review.png');bpy.ops.render.render(write_still=True)
scope={'__file__':str(ROOT/'art/tribal_tent/build_source.py')};exec(compile(Path(scope['__file__']).read_text(),scope['__file__'],'exec'),scope)
scope['ROOTS']={age:bpy.data.objects[f'BER_Tent001_Age{age}_Origin'] for age in range(1,5)}
scope['MATS']={m.name.removeprefix('BER_Tent001 '):m for m in bpy.data.materials if m.name.startswith('BER_Tent001 ')}
scope['ensure_materials']()
scope['CONTACTS']=json.loads((OUT/'structural-contacts.json').read_text())
scope['PARTS']=[{'age':age,'object':o.name,'stage':o['ber_source_stage'],'material':o['ber_material_role']} for age in range(1,5) for o in bpy.data.collections[f'BER_Tent001_Age_{age}'].objects if o.type=='MESH']
if '--authored' not in sys.argv:scope['detailed']()
# Inspect all six sides of the finished largest variant in solid shading.
scene.render.resolution_x=600;scene.render.resolution_y=600
only_age(4)
for name,offset in [('front',(0,-9,0)),('back',(0,9,0)),('left',(-9,0,0)),('right',(9,0,0)),('top',(0,0,9)),('underside',(0,0,-9))]:
    aim((27,0,1.1),offset,7.2);scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
print('SOURCE_SIX_SIDES_READY',flush=True)
# Presentation cameras exist only after construction; remove them from saved authoring source.
bpy.data.objects.remove(camera,do_unlink=True)
for age in range(1,5):
    for o in bpy.data.collections[f'BER_Tent001_Age_{age}'].objects:o.hide_render=False
scope['validate_save']()
data=bpy.data.cameras.new('Final source preview camera');camera=bpy.data.objects.new('Final source preview camera',data);scene.collection.objects.link(camera);scene.camera=camera;data.type='ORTHO'
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.world.color=(.18,.18,.18)
scene.render.resolution_x=850;scene.render.resolution_y=750
groundmesh=bpy.data.meshes.new('Preview floor');groundmesh.from_pydata([(-8,-8,-.055),(36,-8,-.055),(36,8,-.055),(-8,8,-.055)],[],[(0,1,2,3)]);ground=bpy.data.objects.new('Preview floor',groundmesh);scene.collection.objects.link(ground)
m=bpy.data.materials.new('Preview sand');m.diffuse_color=(.21,.16,.10,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.21,.16,.10,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.96;groundmesh.materials.append(m)
lightdata=bpy.data.lights.new('Preview sun','SUN');lightdata.energy=2.5;lightdata.angle=.15;sun=bpy.data.objects.new('Preview sun',lightdata);scene.collection.objects.link(sun);sun.rotation_euler=(.42,-.48,-.5)
filldata=bpy.data.lights.new('Preview bounced daylight','AREA');filldata.energy=450;filldata.size=5;fill=bpy.data.objects.new('Preview bounced daylight',filldata);scene.collection.objects.link(fill)
for age in range(1,5):
    fill.location=((age-1)*9,-4,3.0);fill.rotation_euler=(Vector(((age-1)*9,0,.7))-fill.location).to_track_quat('-Z','Y').to_euler()
    only_age(age);aim(((age-1)*9,0,1.05),(7,-10,7),8.8);scene.render.filepath=str(OUT/f'age{age}.png');bpy.ops.render.render(write_still=True)
print('TRIBAL_TENT_FOUR_AGE_PREVIEWS_READY',flush=True)
