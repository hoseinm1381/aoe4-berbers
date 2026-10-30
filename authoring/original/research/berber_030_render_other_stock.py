"""Focused solid-form references for the remaining Age II stock donors."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
spec = importlib.util.spec_from_file_location("garrison_shared", str(EXT / "garrison_shared.cp313-win_amd64.pyd"))
shared = importlib.util.module_from_spec(spec)
sys.modules["garrison_shared"] = shared
spec.loader.exec_module(shared)
sys.path.insert(0, str(EXT.parent))
import garrison

sys.modules["garrison.garrison_shared"] = shared
from garrison.decode_projection import _apply_decoded_static


sources = {
    "blacksmith": "4c1509af618cf11f44b9",
    "archery_range": "742bd610c37a22451656",
    "stable": "cbc4024cabddca84fb1b",
}
cache = ROOT / "output/shared_stock_cache/buildings_030"
out = ROOT / "output/berber_update_0_3_0/reference-previews"
out.mkdir(parents=True, exist_ok=True)
for family, key in sources.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    manifest = cache / key / "decoded-static.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    proxy = bpy.data.objects.new(family + " donor", None)
    scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"] = str(manifest)
    proxy["garrison_logical_path"] = data["request"]["logical_path"]
    proxy["garrison_display_name"] = family
    donor = _apply_decoded_static(proxy, data, create_controls=False)
    meshes = [obj for obj in donor.children_recursive if obj.type == "MESH"]
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (lo + hi) / 2
    extent = hi - lo
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    cam_data = bpy.data.cameras.new("Temporary reference camera")
    camera = bpy.data.objects.new("Temporary reference camera", cam_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(extent.x, extent.y, extent.z) * 1.55
    for view, direction in (("front", Vector((0, -1, 0.35))), ("isometric", Vector((1, -1, 0.8))), ("top", Vector((0, 0, 1)))):
        camera.location = center + direction.normalized() * 30
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(out / f"abbasid_{family}_age02_{view}.png")
        bpy.ops.render.render(write_still=True)
        print("REFERENCE_RENDER", scene.render.filepath)
