"""Focused, non-packaged solid inspection of the two live Sultanate monastery donors."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "output/shared_stock_cache/buildings_031"
OUT = ROOT / "output/berber_update_0_3_1/tlemcen-inspection"
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


def draw(age):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = next(p for p in CACHE.glob("*/decoded-static.json") if f"sul_monastery_control_age0{age}" in json.loads(p.read_text())["request"]["logical_path"])
    data = json.loads(path.read_text())
    proxy = bpy.data.objects.new("DONOR metadata", None)
    bpy.context.scene.collection.objects.link(proxy)
    root = _apply_decoded_static(proxy, data, create_controls=False)
    meshes = [ob for ob in root.children_recursive if ob.type == "MESH"]
    points = [ob.matrix_world @ Vector(v) for ob in meshes for v in ob.bound_box]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (lo + hi) / 2
    extent = max(hi - lo)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    cam_data = bpy.data.cameras.new("TEMP review")
    cam = bpy.data.objects.new("TEMP review", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = extent * 1.65
    OUT.mkdir(parents=True, exist_ok=True)
    for name, vec in {"iso": (1, -1, 0.8), "front": (0, -1, 0.25), "top": (0, 0, 1)}.items():
        cam.location = center + Vector(vec).normalized() * 30
        cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / f"tlemcen_donor_age0{age}_{name}.png")
        bpy.ops.render.render(write_still=True)
    print("TLEMCEN_DONOR", age, str(path), tuple(lo), tuple(hi), len(meshes), flush=True)


if __name__ == "__main__":
    draw(int(sys.argv[sys.argv.index("--") + 1]))
