"""Temporary Workbench renders of the two decoded market donors."""

from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art/building_remix_0_3_0/reference/market_stock_donors.blend"
OUT = ROOT / "output/berber_update_0_3_0/reference-previews"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 900
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
camera_data = bpy.data.cameras.new("Temporary reference camera")
camera = bpy.data.objects.new("Temporary reference camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = "ORTHO"

for label, root_name in (("abbasid_market_age02", "Abbasid Market Age II"), ("byzantine_mercenary_barracks_age02", "Byzantine Mercenary Barracks Age II")):
    donor = bpy.data.objects[root_name]
    meshes = [obj for obj in donor.children_recursive if obj.type == "MESH"]
    for obj in scene.objects:
        if obj.type == "MESH":
            obj.hide_render = obj not in meshes
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (lo + hi) / 2
    extent = hi - lo
    camera_data.ortho_scale = max(extent.x, extent.y, extent.z) * 1.55
    for view, direction in (("front", Vector((0, -1, 0.35))), ("isometric", Vector((1, -1, 0.8))), ("top", Vector((0, 0, 1)))):
        camera.location = center + direction.normalized() * 30
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / f"{label}_{view}.png")
        bpy.ops.render.render(write_still=True)
        print("REFERENCE_RENDER", scene.render.filepath)
