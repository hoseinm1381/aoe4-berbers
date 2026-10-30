"""Build twelve editable Blender source scenes from the decoded stock donors.

The scenes are art/source validation, not native runtime proof. Model geometry is
the same verified native GEOB projection used by the package preparation.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_0"
OUT = ROOT / "output/berber_update_0_3_0/reference-previews"
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
sys.path.insert(0, str(ROOT / "research"))
from berber_030_market_pilot import CACHE, clip_byzantine_tower


def objects(root):
    return [o for o in root.children_recursive if o.type == "MESH"]


def bounds(meshes):
    points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    return ([min(p[i] for p in points) for i in range(3)], [max(p[i] for p in points) for i in range(3)])


def donor(model):
    d = json.loads(Path(model["decoded"]).read_text(encoding="utf-8"))
    proxy = bpy.data.objects.new(model["name"] + " metadata", None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"] = model["decoded"]
    proxy["garrison_logical_path"] = d["request"]["logical_path"]
    root = _apply_decoded_static(proxy, d, create_controls=False)
    root.name = "Stock-derived Berber " + model["name"]
    root["native_progenitor"] = model["source"]
    return root, d


def remix(root, original, model, carriers):
    modified = json.loads(Path(model["remix_projection"]).read_text(encoding="utf-8"))
    stock_groups = original["geometry"]["groups"]
    new_groups = modified["geometry"]["groups"]
    used = set()
    changed = 0
    for ob in objects(root):
        candidates = [(i, group) for i, group in enumerate(stock_groups) if i not in used and len(group["positions"]) == len(ob.data.vertices) and tuple(group["positions"][0]) == tuple(ob.data.vertices[0].co)]
        assert len(candidates) == 1, (model["name"], ob.name, len(candidates))
        index, before = candidates[0]
        used.add(index)
        after = new_groups[index]
        assert len(before["positions"]) == len(after["positions"])
        for vertex, old, new in zip(ob.data.vertices, before["positions"], after["positions"]):
            assert tuple(vertex.co) == tuple(old)
            if old != new:
                assert old[:2] == new[:2]
                vertex.co = new
                changed += 1
        if model["family"] in ("archery_range", "stable"):
            ob.data.normals_split_custom_set_from_vertices(new_groups[index]["normals"])
        slot = ob.get("garrison_material_slot")
        recipe = next((mat for mat in model["materials"] if mat["name"] == slot), None)
        if recipe:
            for mat in ob.data.materials:
                for edit in recipe["repaint"]:
                    node = mat.node_tree.nodes.get("Essence · " + edit["slot"])
                    if node is None:
                        continue
                    carrier = carriers[edit["carrier"]]
                    image = bpy.data.images.load(carrier["image"], check_existing=True)
                    image.colorspace_settings.name = "sRGB"
                    node.image = image
                mat["berber_native_owner_colour_preserved"] = True
        ob["source_donor"] = model["source"]
        ob["native_geometry_span_remix"] = model["family"] in ("archery_range", "stable")
    assert len(used) == len(stock_groups)
    return changed


def graft_market():
    manifest = CACHE / "4550424ff074a6ab50fd/decoded-static.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    proxy = bpy.data.objects.new("Byzantine mercenary barracks source metadata", None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"] = str(manifest)
    proxy["garrison_logical_path"] = data["request"]["logical_path"]
    root = _apply_decoded_static(proxy, data, create_controls=False)
    root.name = "Clipped Byzantine mercenary-barracks corner"
    meshes, faces = clip_byzantine_tower(root)
    root["retained_faces"] = faces
    root["native_binding_status"] = "source only; separate annex asset required"
    return meshes


def preview(model, meshes):
    scene = bpy.context.scene
    lo, hi = bounds(meshes)
    center = Vector(tuple((a + b) / 2 for a, b in zip(lo, hi)))
    extent = max(b - a for a, b in zip(lo, hi))
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    camera_data = bpy.data.cameras.new("Temporary source-review camera")
    camera = bpy.data.objects.new("Temporary source-review camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = extent * 1.55
    camera.location = center + Vector((1, -1, 0.8)).normalized() * 30
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(OUT / (model["name"] + "_source_isometric.png"))
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)


def main():
    recipe = json.loads((ART / "recipe.json").read_text(encoding="utf-8"))
    carriers = {x["name"]: x for x in recipe["texture_carriers"]}
    OUT.mkdir(parents=True, exist_ok=True)
    report_path = ART / "blender-source-validation.json"
    selected = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
    previous = json.loads(report_path.read_text(encoding="utf-8"))["models"] if selected is not None and report_path.exists() else []
    reports = {item["model"]: item for item in previous}
    models = [model for model in recipe["models"] if selected is None or model["name"] == selected]
    assert models, selected
    for model in models:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.preferences.filepaths.save_version = 0
        root, d = donor(model)
        original_bounds = bounds(objects(root))
        changed = remix(root, d, model, carriers)
        core_bounds = bounds(objects(root))
        assert all(abs(a - b) < 0.003 for a, b in zip(original_bounds[0][:2] + original_bounds[1][:2], core_bounds[0][:2] + core_bounds[1][:2]))
        assert abs(original_bounds[0][2] - core_bounds[0][2]) < 0.003
        all_meshes = objects(root)
        if model["family"] == "market":
            annex = graft_market()
            annex_bounds = bounds(annex)
            assert all(annex_bounds[0][i] >= core_bounds[0][i] - 0.003 for i in range(3))
            assert all(annex_bounds[1][i] <= core_bounds[1][i] + 0.003 for i in range(3))
            all_meshes += annex
        preview(model, all_meshes)
        bpy.ops.file.pack_all()
        folder = ART / model["family"]
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / ("Berber_" + model["name"] + "_0_3_0.blend")
        bpy.ops.wm.save_as_mainfile(filepath=str(target))
        reports[model["name"]] = {"model": model["name"], "blend": str(target), "original_bounds": original_bounds, "core_bounds": core_bounds, "changed_vertices": changed, "stock_uv_and_topology_preserved": True, "market_annex": model["family"] == "market", "status": "editable source; not cooked or bound"}
        report_path.write_text(json.dumps({"status": "running", "models": list(reports.values())}, indent=2) + "\n", encoding="utf-8")
        print("SOURCE_SAVED", model["name"], changed, flush=True)
    report_path.write_text(json.dumps({"status": "passed" if len(reports) == 12 else "partial", "models": list(reports.values()), "native_runtime": "pending"}, indent=2) + "\n", encoding="utf-8")
    print("BERBER_030_BLENDER_SOURCES_READY", len(reports), flush=True)


if __name__ == "__main__":
    main()
