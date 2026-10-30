"""Market donor-graft visual pilot; source only, not a packaged game asset.

Uses the decoded official Abbasid market control and a clipped portion of the
official Byzantine mercenary barracks. The second donor is deliberately not a
new primitive. It remains separate so a later native integration can preserve
the market's own owner-colour and state machinery.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

import bmesh
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


CACHE = ROOT / "output/shared_stock_cache/buildings_030"
OUT = ROOT / "art/building_remix_0_3_0/market"
PREVIEW = ROOT / "output/berber_update_0_3_0/reference-previews"


def add_donor(key, name):
    manifest = CACHE / key / "decoded-static.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    proxy = bpy.data.objects.new(name + " donor metadata", None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"] = str(manifest)
    proxy["garrison_logical_path"] = data["request"]["logical_path"]
    proxy["garrison_display_name"] = name
    root = _apply_decoded_static(proxy, data, create_controls=False)
    root.name = name
    return root, data


def bounds(objects):
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    return [min(p[i] for p in points) for i in range(3)], [max(p[i] for p in points) for i in range(3)]


def clip_byzantine_tower(root):
    meshes = [o for o in root.children_recursive if o.type == "MESH"]
    assert meshes
    retained = 0
    for o in meshes:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        result = bmesh.ops.bisect_plane(
            bm,
            geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
            dist=0.0001,
            plane_co=(2.35, 0.0, 0.0),
            plane_no=(1.0, 0.0, 0.0),
            clear_inner=True,
            clear_outer=False,
        )
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
        retained += len(o.data.polygons)
        o["source_donor"] = "official Byzantine mercenary barracks Age II"
        o["graft_operation"] = "plane bisect at source x=2.35; retain corner tower/frontage"
    assert retained > 500, retained
    # Market core spans roughly x -4.4..3.0, y -2.9..2.9. The annex is
    # inset into the rear-right corner, not placed across its front arch.
    root.scale = (0.61, 0.61, 0.61)
    root.location = (-0.65, 1.9, -0.66)
    bpy.context.view_layer.update()
    return meshes, retained


def render(label, objects):
    scene = bpy.context.scene
    lo, hi = bounds(objects)
    center = Vector(tuple((a + b) / 2 for a, b in zip(lo, hi)))
    extent = max(b - a for a, b in zip(lo, hi))
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    cam_data = bpy.data.cameras.new("Temporary evidence camera")
    cam = bpy.data.objects.new("Temporary evidence camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = extent * 1.55
    for view, direction in (("isometric", Vector((1, -1, 0.8))), ("front", Vector((0, -1, 0.35))), ("top", Vector((0, 0, 1)))):
        cam.location = center + direction.normalized() * 30
        cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEW / f"{label}_{view}.png")
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    return {"min": lo, "max": hi}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    market, market_data = add_donor("1ab6b9d2f7f10490f630", "Abbasid functional market")
    core = [o for o in market.children_recursive if o.type == "MESH"]
    core_bounds = bounds(core)
    byz, byz_data = add_donor("4550424ff074a6ab50fd", "Byzantine clipped corner annex")
    annex, faces = clip_byzantine_tower(byz)
    graft_bounds = bounds(annex)
    assert all(graft_bounds[0][i] >= core_bounds[0][i] - 0.002 for i in range(3))
    assert all(graft_bounds[1][i] <= core_bounds[1][i] + 0.002 for i in range(3))
    composite_bounds = render("market_age02_graft_pilot", core + annex)
    market["role"] = "functional native control donor; original mesh and UV untouched"
    byz["role"] = "secondary stock-derived Byzantine architectural graft"
    byz["release_status"] = "source-only pilot; no runtime binding"
    bpy.ops.file.pack_all()
    target = OUT / "Berber_Tribal_Market_Age2_PILOT.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    report = {
        "status": "source-only pilot",
        "blend": str(target),
        "market_logical_path": market_data["request"]["logical_path"],
        "byzantine_logical_path": byz_data["request"]["logical_path"],
        "market_bounds": core_bounds,
        "graft_bounds": graft_bounds,
        "composite_bounds": composite_bounds,
        "byzantine_retained_faces": faces,
        "runtime_acceptance": "not yet tested",
    }
    (OUT / "pilot-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("MARKET_STOCK_GRAFT_PILOT", report, flush=True)


if __name__ == "__main__":
    main()
