"""Matched lighting/camera, actual actor visual scales; presentation only."""
import bpy,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'art/building_remix_0_9_0'
bpy.ops.wm.read_factory_settings(use_empty=True)
for name,file,col,scale,offset in [
 ('Fez',ART/'fez/Madrasa_of_Fez_090.blend','090_Marinid_College',1.3,-13),
 ('Wonder',ART/'wonder/Berber_Koutoubia_Wonder_090.blend','090_Koutoubia_monumental_mosque',1.5,13)]:
    with bpy.data.libraries.load(str(file),link=False) as (data,loaded):loaded.collections=[col]
    collection=loaded.collections[0];bpy.context.scene.collection.children.link(collection)
    bpy.context.view_layer.update()
    for ob in collection.all_objects:
        ob.matrix_world=Matrix.Translation((offset,0,0))@Matrix.Scale(scale,4)@ob.matrix_world
        ob.select_set(False)
scene=bpy.context.scene;scene.world=bpy.data.worlds.new('matched_daylight');scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.68,.74,.82,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.65
sun=bpy.data.lights.new('matched_sun','SUN');sun.energy=2.2;ob=bpy.data.objects.new('matched_sun',sun)
scene.collection.objects.link(ob);ob.rotation_euler=(.4,-.3,-.6)
camera=bpy.data.cameras.new('presentation_only');cam=bpy.data.objects.new('presentation_only',camera)
scene.collection.objects.link(cam);scene.camera=cam;camera.type='ORTHO';camera.ortho_scale=66
center=Vector((0,0,13));cam.location=center+Vector((.25,-1,1.05))*75
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.device='CPU'
scene.view_settings.view_transform='Standard';scene.view_settings.exposure=-.15
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ART/'matched_game_view.png')
bpy.ops.render.render(write_still=True)
print('090_PAIR_REVIEW_DONE',flush=True)
