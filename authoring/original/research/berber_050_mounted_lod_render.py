"""Render private LOD2/LOD3 and isolated camel rider comparisons.

Only visibility and temporary camera/light change. The saved packed Blend and
native geometry/rest coordinates remain untouched.
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def set_visible(root,lod,rider_only=False):
    for mesh in root.children_recursive:
        if mesh.type!='MESH':
            continue
        # Native group names are not reliable LOD labels (one camel LOD3
        # group is named camel_lod1). The imported Garrison property is.
        is_lod=mesh.get('garrison_lod_level') == lod
        is_rider='rider' in mesh.name.lower()
        mesh.hide_render=not (is_lod and (not rider_only or is_rider))


def main():
    source=Path(sys.argv[sys.argv.index('--')+1]).resolve()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=850
    scene.render.resolution_y=850
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.world.color=(.65,.65,.65)
    camera_data=bpy.data.cameras.new('Temporary mounted LOD camera')
    camera=bpy.data.objects.new('Temporary mounted LOD camera',camera_data)
    scene.collection.objects.link(camera)
    scene.camera=camera
    camera_data.type='ORTHO'
    light_data=bpy.data.lights.new('Temporary mounted LOD light','AREA')
    light_data.energy=1000
    light_data.shape='DISK'
    light_data.size=5
    light=bpy.data.objects.new('Temporary mounted LOD light',light_data)
    scene.collection.objects.link(light)
    donor=bpy.data.objects['Official donor textured']
    candidate=bpy.data.objects['Berber candidate textured']
    for lod in (2,3):
        set_visible(donor,lod)
        set_visible(candidate,lod)
        for label,visible,hidden,offset in [('donor',donor,candidate,-1.4),('candidate',candidate,donor,1.4)]:
            set_visible(hidden,0)
            camera_data.ortho_scale=4.15
            camera.location=(offset+4.1,-7.0,3.1)
            aim(camera,(offset,0,1.28))
            light.location=(offset+1.6,-2.5,4.3)
            aim(light,(offset,0,1.28))
            scene.render.filepath=str(source.parent/f'textured-{label}-lod{lod}.png')
            bpy.ops.render.render(write_still=True)
            print('BERBER_MOUNTED_LOD_RENDER',scene.render.filepath,flush=True)
            set_visible(hidden,lod)
    if source.stem.startswith(('mehari','sanhaja','zenata_age04')):
        for label,visible,hidden,offset in [('donor',donor,candidate,-1.4),('candidate',candidate,donor,1.4)]:
            set_visible(visible,1,rider_only=True)
            set_visible(hidden,0)
            camera_data.ortho_scale=2.4
            camera.location=(offset+2.4,-4.2,2.6)
            aim(camera,(offset,0,1.04))
            light.location=(offset+1.3,-2.1,3.6)
            aim(light,(offset,0,1.04))
            scene.render.filepath=str(source.parent/f'textured-{label}-rider-only.png')
            bpy.ops.render.render(write_still=True)
            print('BERBER_MOUNTED_RIDER_RENDER',scene.render.filepath,flush=True)


if __name__=='__main__':
    main()
