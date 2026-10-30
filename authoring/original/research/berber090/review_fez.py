"""Presentation-only views and fresh source export, after geometry validation."""
import bpy, sys, json, os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research'))
ART=ROOT/'art/building_remix_0_9_0/fez'
old='--old' in sys.argv
source=ROOT/'art/building_remix_0_4_0/fez/fez_040_original.blend' if old else ART/'Madrasa_of_Fez_090.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
col=bpy.data.collections['040_original_fez' if old else '090_Marinid_College']
scene=bpy.context.scene
for ob in bpy.context.selected_objects:ob.select_set(False)
if '--export' in sys.argv:
    sys.path.insert(0,str(Path(__file__).parent))
    from export_source import export
    export(source,col.name,ART/'export_lod0')
else:
    # Cameras are temporary presentation helpers; never saved into editable source.
    for ob in list(bpy.data.objects):
        if ob.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(ob,do_unlink=True)
    ca=bpy.data.cameras.new('090_temporary_review');cam=bpy.data.objects.new('090_temporary_review',ca)
    scene.collection.objects.link(cam);scene.camera=cam;ca.type='ORTHO';ca.ortho_scale=24
    scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    center=Vector((0,0,6.8))
    views={'front':(0,-1,0),'back':(0,1,0),'left':(-1,0,0),'right':(1,0,0),'top':(0,0,1),'bottom':(0,0,-1),'game':(1,-1,1.05),'court':(-1,-1,1.5)}
    scene.world=scene.world or bpy.data.worlds.new('090_review_world');scene.world.use_nodes=True
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.68,.74,.82,1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.65
    ld=bpy.data.lights.new('090_sun','SUN');ld.energy=2.2;sun=bpy.data.objects.new('090_sun',ld)
    scene.collection.objects.link(sun);sun.rotation_euler=(.4,-.3,-.6)
    scene.view_settings.view_transform='Standard';scene.view_settings.exposure=-.15
    for name,d in views.items():
        if old and name not in {'game','court'}:continue
        cam.location=center+Vector(d)*40;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.engine='BLENDER_WORKBENCH'
        scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.show_cavity=True
        if name in {'game','court'}:
            scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.cycles.device='CPU'
        scene.render.filepath=str(ART/(('before_' if old else '')+name+'.png'))
        bpy.ops.render.render(write_still=True)
        print('REVIEW_DONE',name,flush=True)
