"""Export the clipped Byzantine market graft through Garrison static authoring.

The visible geometry is a bisected official mercenary-barracks donor. This
auxiliary static piece does not replace the market's native owner-colour core.
"""

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_0/market/annex_source"
OUT = ROOT / "output/berber_update_0_3_0/annex-library/Assets/Custom/b030/aa"
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
from garrison.material_adoption import adopt_material

sys.path.insert(0, str(ROOT / "research"))
from berber_030_market_pilot import CACHE, clip_byzantine_tower


def make_material(name):
    mat = bpy.data.materials.new("annex_" + name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    principled.inputs["Roughness"].default_value = 0.84
    principled.inputs["Metallic"].default_value = 0.0
    image = bpy.data.images.load(str(ART / (name + "_byzantine_toned.png")), check_existing=True)
    image.colorspace_settings.name = "sRGB"
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Official donor albedo, Berber earthen tone"
    texture.image = image
    mat.node_tree.links.new(texture.outputs["Color"], principled.inputs["Base Color"])
    adopt_material(mat)
    return mat


def constant_image(target, color, size):
    image = bpy.data.images.new(target.stem, width=size[0], height=size[1], alpha=True)
    image.generated_color = color
    image.filepath_raw = str(target)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def material_records(meshes, source):
    records = []
    for obj in meshes:
        mat = obj.data.materials[0]
        contract = adopt_material(mat)
        material_id = contract["material_id"]
        folder = source / "materials" / material_id
        folder.mkdir(parents=True, exist_ok=True)
        albedo = folder / "albedo.png"
        role = mat.name.removeprefix("annex_")
        shutil.copy2(ART / (role + "_byzantine_toned.png"), albedo)
        size = tuple(bpy.data.images.load(str(albedo), check_existing=False).size)
        constant_image(folder / "normal.png", (.5, .5, 1.0, 1.0), size)
        constant_image(folder / "roughness.png", (.84, .84, .84, 1.0), size)
        constant_image(folder / "metalness.png", (0.0, 0.0, 0.0, 1.0), size)
        records.append({"id": material_id, "source_name": mat.name, "mesh_name": obj.name, "textures": {s: str(folder / (s + ".png")) for s in ("albedo", "normal", "roughness", "metalness")}, "bindings": contract["semantics"], "usage": {"objects": [obj.name], "faces": len(obj.data.polygons)}})
    return records


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    manifest = CACHE / "4550424ff074a6ab50fd/decoded-static.json"
    d = json.loads(manifest.read_text(encoding="utf-8"))
    proxy = bpy.data.objects.new("Official Byzantine mercenary barracks provenance", None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"] = str(manifest)
    proxy["garrison_logical_path"] = d["request"]["logical_path"]
    root = _apply_decoded_static(proxy, d, create_controls=False)
    root.name = "Berber market Byzantine annex"
    meshes, faces = clip_byzantine_tower(root)
    mats = {name: make_material(name) for name in ("main", "extra", "roof")}
    for obj in meshes:
        slot = obj.get("garrison_material_slot")
        assert slot in mats, (obj.name, slot)
        obj.name = "geo_mat_annex_" + slot
        obj.data.materials.clear()
        obj.data.materials.append(mats[slot])
        for face in obj.data.polygons:
            face.material_index = 0
        if obj.data.uv_layers:
            obj.data.uv_layers.active_index = 0
            for layer in tuple(obj.data.uv_layers)[1:]:
                obj.data.uv_layers.remove(layer)
    result = {"ok": all(len(obj.data.polygons) > 0 and obj.data.uv_layers.active is not None and len(obj.data.materials) == 1 for obj in meshes), "note": "Blender structural precheck; Garrison static prepare is the authoritative model preflight"}
    assert result["ok"]
    print("ANNEX_STRUCTURAL_PRECHECK", result, flush=True)
    source = OUT / "source"
    source.mkdir(parents=True, exist_ok=True)
    materials = material_records(meshes, source)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    fbx = source / "model.fbx"
    exported = bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={"MESH"}, use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False, path_mode="AUTO", axis_forward="-Z", axis_up="Y", apply_unit_scale=True, use_space_transform=True)
    assert "FINISHED" in exported
    bpy.ops.file.pack_all()
    ART.mkdir(parents=True, exist_ok=True)
    blend = ART / "Berber_Market_Byzantine_Annex_Age2_0_3_0.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    request = {
        "schema": "garrison.custom-static-authoring-request/v2",
        "namespace": "b030",
        "asset_id": "aa",
        "catalog_folder": "Custom/Berber/Buildings",
        "build_id": "20261015T010000Z-b03a",
        "source": {"fbx": str(fbx)},
        "materials": materials,
        "blender_executable": str(Path(bpy.app.binary_path).resolve(strict=True)),
        "template_project": "C:/Users/RS/AppData/Local/Garrison/Kit/template-project",
        "asset_root": str(OUT),
        "cook_editor": "C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe",
    }
    request_path = OUT / ".garrison/requests/berber-030-market-annex-001.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    report = {"status": "prepared source and request; native static cook pending", "request": str(request_path), "report": str(OUT / ".garrison/reports/berber-030-market-annex-001.prepare.json"), "blend": str(blend), "faces": faces, "preflight_ok": result["ok"], "materials": materials}
    (ART / "annex-authoring.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("ANNEX_EXPORT_READY", request_path, flush=True)


if __name__ == "__main__":
    main()
