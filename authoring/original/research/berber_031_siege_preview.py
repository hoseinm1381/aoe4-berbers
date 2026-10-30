"""Render an isolated Blender building source with a temporary Workbench camera."""

import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


output = Path(os.environ["BERBER_SIEGE_PREVIEW"])
output.mkdir(parents=True, exist_ok=True)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes
group = os.environ.get("BERBER_SIEGE_GROUP")
if group:
    for obj in meshes:
        obj.hide_render = obj.name != group
    meshes = [obj for obj in meshes if obj.name == group]
for obj in bpy.context.scene.objects:
    obj.select_set(False)
mins = [min((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)]
maxs = [max((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)]
center = Vector(((mins[0]+maxs[0])/2, (mins[1]+maxs[1])/2, (mins[2]+maxs[2])/2))
radius = max(maxs[i]-mins[i] for i in range(3))
camera = bpy.data.cameras.new("TEMP_PREVIEW_CAMERA")
camera.type = "ORTHO"
camera.ortho_scale = radius * 1.9
camera_obj = bpy.data.objects.new("TEMP_PREVIEW_CAMERA", camera)
bpy.context.scene.collection.objects.link(camera_obj)
bpy.context.scene.camera = camera_obj
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.render.resolution_x = 900
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = {
    "front": (0, -1, 0.38),
    "rear": (0, 1, 0.38),
    "left": (-1, 0, 0.38),
    "right": (1, 0, 0.38),
    "top": (0, 0, 1),
    "bottom": (0, 0, -1),
    "default_zoom": (1.25, -1.6, 1.55),
}
for name, direction in views.items():
    d = Vector(direction).normalized()
    camera_obj.location = center + d * radius * 2.2
    camera_obj.rotation_euler = (center - camera_obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(output / f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("SIEGE_PREVIEWS", output, len(views), "BOUNDS", mins, maxs)
