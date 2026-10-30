"""Read-only stock donor scene and isolated orthographic silhouette previews."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/marrakech"
MANIFEST = ROOT / "output/shared_stock_cache/buildings_031/b2f086bad44adad77491/decoded-static.json"
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


def render(scene, meshes, label, direction):
    lo = [min((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)]
    hi = [max((o.matrix_world @ Vector(c))[i] for o in meshes for c in o.bound_box) for i in range(3)]
    center = Vector(tuple((a + b) / 2 for a, b in zip(lo, hi)))
    camera_data = bpy.data.cameras.new("Temporary review camera")
    camera = bpy.data.objects.new("Temporary review camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = center + Vector(direction).normalized() * 20
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(b - a for a, b in zip(lo, hi)) * 1.35
    scene.camera = camera
    scene.render.filepath = str(ART / "references" / f"stock_{label}.png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    return lo, hi


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    proxy = bpy.data.objects.new("Malian landmark donor metadata", None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"] = str(MANIFEST)
    proxy["garrison_logical_path"] = data["request"]["logical_path"]
    root = _apply_decoded_static(proxy, data, create_controls=False)
    meshes = [o for o in root.children_recursive if o.type == "MESH"]
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.display.shading.color_type = "SINGLE"
    scene.display.shading.show_cavity = True
    (ART / "references").mkdir(parents=True, exist_ok=True)
    report = {}
    for label, direction in {"front": (0, -1, 0.35), "back": (0, 1, 0.35), "left": (-1, 0, 0.35), "right": (1, 0, 0.35), "top": (0, 0, 1), "iso": (1, -1, 0.8)}.items():
        lo, hi = render(scene, meshes, label, direction)
        report[label] = {"bounds_min": lo, "bounds_max": hi}
    (ART / "references" / "stock-bounds.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("MARRAKECH_STOCK_PREVIEW_READY", len(meshes), flush=True)


if __name__ == "__main__":
    main()
