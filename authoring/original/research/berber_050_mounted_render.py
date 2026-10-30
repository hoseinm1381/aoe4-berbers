"""Render whole combined unit and rider close-up from a packed review Blend."""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def main():
    source = Path(sys.argv[sys.argv.index('--')+1]).resolve()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 850
    scene.render.resolution_y = 850
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.world.color = (.65,.65,.65)
    camera_data = bpy.data.cameras.new('Temporary mounted review camera')
    camera = bpy.data.objects.new('Temporary mounted review camera', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'
    light_data = bpy.data.lights.new('Temporary mounted review light','AREA')
    light_data.energy = 1000
    light_data.shape = 'DISK'
    light_data.size = 5
    light = bpy.data.objects.new('Temporary mounted review light', light_data)
    scene.collection.objects.link(light)
    donor = bpy.data.objects['Official donor textured']
    candidate = bpy.data.objects['Berber candidate textured']
    views = [('donor',donor,candidate,-1.4,None,False),
             ('candidate',candidate,donor,1.4,None,False),
             ('rider-close',candidate,donor,1.4,None,True),
             ('team-red',candidate,donor,1.4,(.7,.045,.035,1),False),
             ('team-blue',candidate,donor,1.4,(.025,.18,.8,1),False)]
    for label, visible, hidden, offset, team, close in views:
        for obj in [visible,*visible.children_recursive]:
            obj.hide_render = obj.type == 'MESH' and obj.get('garrison_lod_level') != 1
        for obj in [hidden,*hidden.children_recursive]:
            obj.hide_render = True
        if team:
            for obj in visible.children_recursive:
                if obj.type != 'MESH':
                    continue
                for slot in obj.material_slots:
                    material = slot.material
                    if not material or not material.use_nodes:
                        continue
                    colour = material.node_tree.nodes.get('GARRISON Team Colour Preview')
                    strength = material.node_tree.nodes.get('GARRISON Team Colour Preview Strength')
                    if colour and strength:
                        colour.outputs['Color'].default_value = team
                        strength.outputs['Value'].default_value = 1.0
        camera_data.ortho_scale = 1.85 if close else 4.15
        camera.location = (offset+2.8,-5.2,2.6) if close else (offset+4.1,-7.0,3.1)
        target = (offset,0,1.28)
        aim(camera,target)
        light.location = (offset+1.6,-2.5,4.3)
        aim(light,target)
        scene.render.filepath = str(source.parent / f'textured-{label}.png')
        bpy.ops.render.render(write_still=True)
        print('BERBER_MOUNTED_RENDER',scene.render.filepath,flush=True)


if __name__ == '__main__':
    main()
