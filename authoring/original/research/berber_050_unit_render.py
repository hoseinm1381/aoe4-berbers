"""Render a saved private unit review file for textured authoring QA only."""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def aim(obj,target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()


def main():
    args=sys.argv[sys.argv.index('--')+1:]
    source=Path(args[0]).resolve()
    palette=next((arg for arg in args[1:] if arg in ('red','blue')),None)
    rider_only='rider' in args[1:]
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=650
    scene.render.resolution_y=850
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.world.color=(0.65,0.65,0.65)
    camera_data=bpy.data.cameras.new('Temporary QA orthographic camera')
    camera=bpy.data.objects.new('Temporary QA orthographic camera',camera_data)
    scene.collection.objects.link(camera)
    scene.camera=camera
    camera_data.type='ORTHO'
    mounted=not rider_only and any(tag in source.stem.lower() for tag in
                ('horse','camel','mehari','sanhaja','scout','zenata','lancer','trader'))
    camera_data.ortho_scale=4.0 if mounted else 2.5
    light_data=bpy.data.lights.new('Temporary QA area light','AREA')
    light_data.energy=900
    light_data.shape='DISK'
    light_data.size=5
    light=bpy.data.objects.new('Temporary QA area light',light_data)
    scene.collection.objects.link(light)
    donor=bpy.data.objects['Official donor textured']
    candidate=bpy.data.objects['Berber candidate textured']
    if palette:
        colours={'blue':(.025,.18,.8,1),'red':(.7,.045,.035,1)}
        if palette not in colours:
            raise ValueError(f'Unknown preview palette {palette}')
        for obj in candidate.children_recursive:
            if obj.type!='MESH':
                continue
            for slot in obj.material_slots:
                material=slot.material
                if not material or not material.use_nodes:
                    continue
                colour=material.node_tree.nodes.get('GARRISON Team Colour Preview')
                strength=material.node_tree.nodes.get('GARRISON Team Colour Preview Strength')
                if colour and strength:
                    colour.outputs['Color'].default_value=colours[palette]
                    strength.outputs['Value'].default_value=1.0
    suffix='-rider' if rider_only else ''
    views=[(f'team-{palette}{suffix}',candidate,donor,1.4)] if palette else [(f'donor{suffix}',donor,candidate,-1.4),(f'candidate{suffix}',candidate,donor,1.4)]
    for label,visible,hidden,offset in views:
        for obj in [visible,*visible.children_recursive]:
            obj.hide_render=(obj.type=='MESH' and
                (re.search(r'lod[ _]?1(?:\.|$)',obj.name,re.IGNORECASE) is None
                 or (rider_only and 'rider' not in obj.name.lower())))
        for obj in [hidden,*hidden.children_recursive]:
            obj.hide_render=True
        camera.location=(offset+4.0,-7.0,3.0) if mounted else (offset+3.0,-5.0,2.5)
        aim(camera,(offset,0,1.25 if mounted else 1.0))
        light.location=(offset+1.5,-2.5,4)
        aim(light,(offset,0,1.25 if mounted else 1.0))
        scene.render.filepath=str(source.parent/(f'textured-{label}.png'))
        bpy.ops.render.render(write_still=True)
        print('BERBER_050_TEXTURED_RENDER',scene.render.filepath,flush=True)


if __name__=='__main__':
    main()
