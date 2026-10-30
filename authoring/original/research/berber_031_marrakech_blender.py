"""Editable donor-derived Marrakech kasbah scenes and six-view evidence."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/marrakech"
MANIFEST = ROOT / "output/shared_stock_cache/buildings_031/aa9a46fa271304378d30/decoded-static.json"
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


def world_bounds(meshes):
    points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    return [[min(p[i] for p in points) for i in range(3)], [max(p[i] for p in points) for i in range(3)]]


def render(scene, meshes, age, view, direction):
    low, high = world_bounds(meshes)
    center = Vector(tuple((a + b) / 2 for a, b in zip(low, high)))
    camera_data = bpy.data.cameras.new("Temporary review camera")
    camera = bpy.data.objects.new("Temporary review camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = center + Vector(direction).normalized() * 25
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(b - a for a, b in zip(low, high)) * 1.45
    scene.camera = camera
    scene.render.filepath = str(ART / "previews" / f"marrakech_age{age:02}_{view}.png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)


def main():
    bpy.context.preferences.filepaths.save_version = 0
    original = json.loads(MANIFEST.read_text(encoding="utf-8"))
    reports = []
    (ART / "previews").mkdir(parents=True, exist_ok=True)
    for age in (3, 4):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        projection = json.loads((ART / f"marrakech_age{age:02}_projection.json").read_text(encoding="utf-8"))
        proxy = bpy.data.objects.new(f"Malian fort donor metadata Age {age}", None)
        bpy.context.scene.collection.objects.link(proxy)
        proxy["garrison_decode_manifest"] = str(MANIFEST)
        proxy["garrison_logical_path"] = original["request"]["logical_path"]
        root = _apply_decoded_static(proxy, original, create_controls=False)
        root.name = f"Dar al-Jihad kasbah Age {age} stock-derived core"
        root["donor"] = original["request"]["logical_path"]
        root["native_geometry"] = str(ART / f"marrakech_age{age:02}_kasbah.rrgeom")
        root["native_source_note"] = "Model uses native GEOB patch, not a Garrison static FBX; owner-colour materials remain stock."
        meshes = [o for o in root.children_recursive if o.type == "MESH"]
        used = set()
        changed = 0
        uv_records = []
        for ob in meshes:
            choices = [(i, g) for i, g in enumerate(original["geometry"]["groups"]) if i not in used and len(g["positions"]) == len(ob.data.vertices) and tuple(g["positions"][0]) == tuple(ob.data.vertices[0].co)]
            assert len(choices) == 1, (ob.name, len(choices))
            index, before = choices[0]
            used.add(index)
            after = projection["geometry"]["groups"][index]
            for vertex, old, new in zip(ob.data.vertices, before["positions"], after["positions"]):
                assert tuple(vertex.co) == tuple(old)
                if old != new:
                    vertex.co = new
                    changed += 1
            ob.data.normals_split_custom_set_from_vertices(after["normals"])
            ob["source_group"] = before["name"]
            ob["source_donor"] = original["request"]["logical_path"]
            uv_records.append({"name": ob.name, "vertices": len(ob.data.vertices), "triangles": len(ob.data.polygons), "uv_layers": [layer.name for layer in ob.data.uv_layers], "materials": [mat.name for mat in ob.data.materials if mat], "positive_scale": all(v > 0 for v in ob.scale)})
        assert len(used) == len(original["geometry"]["groups"]) == 6
        bounds = world_bounds(meshes)
        assert bounds[0][0] > -4 and bounds[1][0] < 4
        assert bounds[0][1] > -4 and bounds[1][1] < 4
        assert all(x["uv_layers"] and x["materials"] and x["positive_scale"] for x in uv_records)
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = 900
        scene.render.resolution_y = 750
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_cavity = True
        for name, direction in {"front": (0, -1, 0.35), "back": (0, 1, 0.35), "left": (-1, 0, 0.35), "right": (1, 0, 0.35), "top": (0, 0, 1), "bottom": (0, 0, -1), "isometric": (1, -1, 0.8)}.items():
            render(scene, meshes, age, name, direction)
        bpy.ops.file.pack_all()
        target = ART / f"Dar_al_Jihad_Marrakech_Age{age}_0_3_1.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(target))
        reports.append({"age": age, "blend": str(target), "bounds": bounds, "changed_vertices": changed, "mesh_evidence": uv_records, "native_owner_colour": "stock material slots retained, game test pending", "contact": "continuous source topology; 8x8 horizontal envelope verified", "runtime": "pending"})
        print("MARRAKECH_SOURCE_SAVED", age, changed, flush=True)
    (ART / "blender-source-validation.json").write_text(json.dumps({"status": "source_passed", "models": reports}, indent=2) + "\n", encoding="utf-8")
    print("MARRAKECH_BLENDERS_READY", len(reports), flush=True)


if __name__ == "__main__":
    main()
