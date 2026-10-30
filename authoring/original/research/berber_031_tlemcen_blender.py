"""Editable Tlemcen III/IV donor remixes and one-piece static aisle export.

The stock-derived native GEOB body is imported from decoded Garrison geometry,
then matched vertex-for-vertex to the validated native projection. Additions
form one exportable static part and do not replace stock owner-colour materials.
"""

import importlib.util
import json
import math
import os
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/tlemcen"
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
from garrison.material_adoption import adopt_material


def box(name, lo, hi, mat, collection):
    center = tuple((a + b) / 2 for a, b in zip(lo, hi))
    dims = tuple(b - a for a, b in zip(lo, hi))
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    for old in list(ob.users_collection): old.objects.unlink(ob)
    collection.objects.link(ob)
    return ob


def profile_roof(name, profile, y0, y1, mat, collection):
    # A thick, connected extrusion of a measured wall/eave/ridge profile.
    vertices = [(x, y, z) for y in (y0, y1) for x, z in profile]
    n = len(profile)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    mesh.materials.append(mat)
    return ob


def arch(name, axis, center, radius, spring, rise, thickness, mat, collection):
    # One real half-round voussoir mesh. It seats into two piers and the roof.
    zc = spring
    points = []
    for i in range(13):
        a = math.pi * i / 12
        points.append((-radius * math.cos(a), zc + rise * math.sin(a)))
    for i in range(12, -1, -1):
        a = math.pi * i / 12
        points.append((-(radius + 0.105) * math.cos(a), zc + (rise + 0.105) * math.sin(a)))
    verts = []
    for side in (-thickness / 2, thickness / 2):
        for u, z in points:
            x, y = (center[0] + side, center[1] + u) if axis == "Y" else (center[0] + u, center[1] + side)
            verts.append((x, y, z))
    n = len(points)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, n * 2))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    mesh.materials.append(mat)
    return ob


def setup_atlas(age):
    colors = [(0.78, 0.68, 0.52, 1), (0.51, 0.40, 0.28, 1), (0.18, 0.32, 0.31, 1), (0.34, 0.23, 0.15, 1)]
    if age == 4:
        colors = [(0.88, 0.82, 0.69, 1), (0.65, 0.55, 0.39, 1), (0.15, 0.35, 0.34, 1), (0.26, 0.18, 0.11, 1)]
    pixels = []
    for y in range(256):
        for x in range(256): pixels.extend(colors[(1 if x >= 128 else 0) + (2 if y >= 128 else 0)])
    img = bpy.data.images.new(f"Tlemcen age0{age} atlas", width=256, height=256, alpha=True)
    img.pixels = pixels
    img.filepath_raw = str(ART / f"tlemcen_age0{age}_albedo.png")
    img.file_format = "PNG"
    img.save()
    mat = bpy.data.materials.new(f"Tlemcen age0{age} supplement atlas")
    mat.diffuse_color = colors[0]
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    texture = mat.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = img
    mat.node_tree.links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    return mat, img


def uv_all(meshes):
    # One packed atlas with role-indexed quadrants. Every face has real UVs.
    for ob in meshes:
        idx = 0 if "plaster" in ob.name or "arch" in ob.name else 1 if "stone" in ob.name else 2 if "tile" in ob.name else 3
        cx = 0.25 if idx % 2 == 0 else 0.75
        cy = 0.25 if idx < 2 else 0.75
        uv = ob.data.uv_layers.active or ob.data.uv_layers.new(name="UVMap")
        for poly in ob.data.polygons:
            for j, loop_idx in enumerate(poly.loop_indices):
                # Local per-face mapping with nonzero area; safely inside cell.
                corners = [(cx - 0.19, cy - 0.19), (cx + 0.19, cy - 0.19), (cx + 0.19, cy + 0.19), (cx - 0.19, cy + 0.19)]
                uv.data[loop_idx].uv = corners[j % 4]


def stock(age, recipe):
    data = json.loads(Path(recipe["decoded"]).read_text(encoding="utf-8"))
    modified = json.loads(Path(recipe["remix_projection"]).read_text(encoding="utf-8"))
    proxy = bpy.data.objects.new("Donor provenance", None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"] = recipe["decoded"]
    proxy["donor_model"] = recipe["source_rgm"]
    root = _apply_decoded_static(proxy, data, create_controls=False)
    root.name = f"Tlemcen age0{age} native stock geometry"
    meshes = [ob for ob in root.children_recursive if ob.type == "MESH"]
    claimed = set()
    changed = 0
    for ob in meshes:
        matches = [(i, g) for i, g in enumerate(data["geometry"]["groups"]) if i not in claimed and len(g["positions"]) == len(ob.data.vertices) and tuple(g["positions"][0]) == tuple(ob.data.vertices[0].co)]
        assert len(matches) == 1, (age, ob.name, len(matches))
        idx, old = matches[0]
        claimed.add(idx)
        new = modified["geometry"]["groups"][idx]
        for vertex, before, after in zip(ob.data.vertices, old["positions"], new["positions"]):
            assert tuple(vertex.co) == tuple(before)
            vertex.co = after
            changed += tuple(before) != tuple(after)
        ob["native_owner_colour_preserved"] = True
        ob["native_geometry_source"] = recipe["native_geometry"]
    assert len(claimed) == len(meshes)
    return root, meshes, changed


def additions(age, mat):
    col = bpy.data.collections.new(f"Tlemcen age0{age} prayer courtyard and aisles")
    bpy.context.scene.collection.children.link(col)
    created = []
    contacts = []
    # Existing walled donor courtyard: interior x roughly +-2.55, y -2.65..0.
    for side in (-1, 1):
        xwall = side * 2.58
        xinner = side * 1.79
        outer, inner = (xwall + side * 0.05, xinner - side * 0.04)
        if side < 0:
            section = [(outer, 1.45), (outer, 1.83), (inner, 1.58), (inner, 1.45)]
        else:
            section = [(inner, 1.45), (inner, 1.58), (outer, 1.83), (outer, 1.45)]
        created.append(profile_roof(f"tile_{'west' if side < 0 else 'east'}_courtyard_lean_to", section, -2.44, 0.38, mat, col))
        contacts.append({"interface": "side aisle lean-to to donor outer wall and inner arcade", "side": side, "donor_wall_x": xwall, "roof_outer_x": outer, "wall_embed_xy": 0.05, "arcade_top": 1.61, "inner_roof_eave": 1.58, "arcade_overlap": 0.03})
        for k in range(4):
            y = -2.31 + k * 0.75
            created.append(box(f"stone_{'west' if side < 0 else 'east'}_pier_{k}", (xinner - 0.09, y - 0.08, 0.0), (xinner + 0.09, y + 0.08, 1.10), mat, col))
            contacts.append({"interface": "side pier ground", "side": side, "module": k, "gap": 0.0})
        for k in range(3):
            cy = -1.935 + k * 0.75
            created.append(arch(f"plaster_arch_{'west' if side < 0 else 'east'}_{k}", "Y", (xinner, cy), 0.375, 1.07, 0.43, 0.18, mat, col))
            contacts.append({"interface": "arch spring to adjacent pier tops", "side": side, "module": k, "vertical_overlap": 0.03})
    # A low courtyard-to-hall arcade traces the donor's existing north face.
    for k in range(5):
        x = -1.64 + k * 0.82
        created.append(box(f"stone_prayer_front_pier_{k}", (x - 0.09, 0.04, 0.0), (x + 0.09, 0.25, 1.33), mat, col))
    for k in range(4):
        x = -1.23 + k * 0.82
        created.append(arch(f"plaster_arch_prayer_front_{k}", "X", (x, 0.145), 0.41, 1.30, 0.48, 0.21, mat, col))
    created.append(box("wood_prayer_front_eave", (-2.04, 0.00, 1.77), (2.04, 0.63, 1.92), mat, col))
    contacts.append({"interface": "prayer-front eave over arch crowns", "arch_top": 1.78, "roof_bottom": 1.77, "overlap": 0.01})
    for side in (-1, 1):
        xlo, xhi = ((-3.08, -1.46) if side < 0 else (1.46, 3.08))
        ridge = (xlo + xhi) / 2
        eave_z = 2.11 if age == 3 else 2.16
        ridge_z = 2.75 if age == 3 else 2.88
        section = [(xlo, 1.58), (xlo, eave_z), (ridge, ridge_z), (xhi, eave_z), (xhi, 1.58)]
        created.append(profile_roof(f"tile_{'west' if side < 0 else 'east'}_double_sloped_prayer_aisle", section, 0.28, 3.04, mat, col))
        contacts.append({"interface": "thick gabled prayer aisle roof to donor wing", "side": side, "donor_side_domes_lowered_below_roof": True, "embedded_bottom": 1.58, "eave": eave_z, "ridge": ridge_z})
        if age == 4:
            created.append(box(f"tile_{'west' if side < 0 else 'east'}_ridge_cap", (ridge - 0.065, 0.26, ridge_z - 0.04), (ridge + 0.065, 3.06, ridge_z + 0.045), mat, col))
    # Offset tower casing converts the source minaret into a square Maghrebi
    # profile; panels overlap the remixed donor tower rather than floating.
    tower_x, tower_y = -2.675, -2.575
    created.append(box("plaster_minaret_south_wall", (tower_x - 0.30, tower_y - 0.34, 1.43), (tower_x + 0.30, tower_y - 0.27, 3.83), mat, col))
    created.append(box("plaster_minaret_north_wall", (tower_x - 0.30, tower_y + 0.27, 1.43), (tower_x + 0.30, tower_y + 0.34, 3.83), mat, col))
    created.append(box("plaster_minaret_west_wall", (tower_x - 0.34, tower_y - 0.30, 1.43), (tower_x - 0.27, tower_y + 0.30, 3.83), mat, col))
    created.append(box("plaster_minaret_east_wall", (tower_x + 0.27, tower_y - 0.30, 1.43), (tower_x + 0.34, tower_y + 0.30, 3.83), mat, col))
    for dx in (-0.31, 0.31):
        for dy in (-0.31, 0.31):
            created.append(box(f"stone_minaret_corner_{dx:+.2f}_{dy:+.2f}", (tower_x + dx - 0.065, tower_y + dy - 0.065, 1.43), (tower_x + dx + 0.065, tower_y + dy + 0.065, 4.55 if age == 3 else 5.02), mat, col))
    for z in (2.72, 3.84, 4.50 if age == 3 else 4.97):
        created.append(box(f"tile_minaret_band_{z:.2f}", (tower_x - 0.40, tower_y - 0.40, z), (tower_x + 0.40, tower_y + 0.40, z + 0.10), mat, col))
    contacts.append({"interface": "square minaret casing to stock tower", "center": [tower_x, tower_y], "foundation_z": 1.43, "core_radius_approx": 0.31})
    if age == 4:
        # Imperial refinement: restrained cedar screen and glazed tiles.
        for k in range(5):
            x = -1.64 + k * 0.82
            created.append(box(f"wood_cedar_screen_{k}", (x - 0.055, -0.03, 0.08), (x + 0.055, 0.04, 1.13), mat, col))
    uv_all(created)
    return col, created, contacts


def render(age, meshes, view, path):
    points = [ob.matrix_world @ Vector(v) for ob in meshes for v in ob.bound_box]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (lo + hi) / 2
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    cam_data = bpy.data.cameras.new("TEMP review camera")
    cam = bpy.data.objects.new("TEMP review camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(hi - lo) * (1.55 if view != "top" else 1.24)
    vec = {"iso": (1, -1, 0.8), "front": (0, -1, 0.25), "top": (0, 0, 1), "rear": (0, 1, 0.25), "west": (-1, 0, 0.25), "east": (1, 0, 0.25), "bottom": (0, 0, -1)}[view]
    cam.location = center + Vector(vec).normalized() * 30
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def export_one(age, added):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in added: ob.select_set(True)
    bpy.context.view_layer.objects.active = added[0]
    bpy.ops.object.duplicate()
    selected = list(bpy.context.selected_objects)
    bpy.context.view_layer.objects.active = selected[0]
    bpy.ops.object.join()
    joined = bpy.context.object
    joined.name = f"Tlemcen_age0{age}_aisles_static_export"
    fbx = ART / f"tlemcen_age0{age}_aisles.fbx"
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", mesh_smooth_type="FACE", path_mode="COPY", embed_textures=False)
    bpy.data.objects.remove(joined, do_unlink=True)
    return fbx


def flat_image(path, color):
    image = bpy.data.images.new(path.stem, width=256, height=256, alpha=True)
    image.generated_color = color
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def static_request(age, mat, added, fbx):
    contract = adopt_material(mat)
    textures = {"albedo": ART / f"tlemcen_age0{age}_albedo.png"}
    for key, colour in {"normal": (0.5, 0.5, 1, 1), "roughness": (0.83, 0.83, 0.83, 1), "metalness": (0, 0, 0, 1)}.items():
        textures[key] = ART / f"tlemcen_age0{age}_{key}.png"
        flat_image(textures[key], colour)
    asset_root = ROOT / f"output/berber_update_0_3_1/tlemcen-static-library/age0{age}/Assets/Custom/b031/tl{age}"
    source_dir = asset_root / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    canonical_fbx = source_dir / "model.fbx"
    shutil.copy2(fbx, canonical_fbx)
    canonical_textures = {}
    material_dir = source_dir / "materials" / contract["material_id"]
    material_dir.mkdir(parents=True, exist_ok=True)
    for key, original in textures.items():
        target = material_dir / (key + ".png")
        shutil.copy2(original, target)
        canonical_textures[key] = target
    request = {"schema": "garrison.custom-static-authoring-request/v2", "namespace": "b031", "asset_id": f"tl{age}", "catalog_folder": "Custom/Berber/Buildings", "build_id": f"20261015T03{age}000Z-b31t{age}", "source": {"fbx": str(canonical_fbx)}, "materials": [{"id": contract["material_id"], "source_name": mat.name, "mesh_name": f"Tlemcen_age0{age}_aisles_static_export", "textures": {k: str(v) for k, v in canonical_textures.items()}, "bindings": contract["semantics"], "usage": {"objects": [f"Tlemcen_age0{age}_aisles_static_export"], "faces": sum(len(ob.data.polygons) for ob in added)}}], "blender_executable": str(Path(bpy.app.binary_path).resolve(strict=True)), "template_project": "C:/Users/RS/AppData/Local/Garrison/Kit/template-project", "asset_root": str(asset_root), "cook_editor": "C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe"}
    path = ART / f"tlemcen-age0{age}-static-request.json"
    path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    return path


def run(age):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    report = json.loads((ART / "native-validation.json").read_text())
    recipe = next(r for r in report["models"] if r["age"] == age)
    root, native_meshes, changed = stock(age, recipe)
    mat, image = setup_atlas(age)
    col, added, contacts = additions(age, mat)
    OUT.mkdir(parents=True, exist_ok=True)
    for view in ("iso", "front", "top", "rear", "west", "east", "bottom"):
        render(age, native_meshes + added, view, OUT / f"tlemcen_age0{age}_{view}.png")
    fbx = export_one(age, added)
    request = static_request(age, mat, added, fbx)
    bpy.ops.file.pack_all()
    blend = ART / f"Berber_Tlemcen_age0{age}_0_3_1.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report_path = ART / f"age0{age}-source-validation.json"
    report_path.write_text(json.dumps({"age": age, "blend": str(blend), "fbx": str(fbx), "static_request": str(request), "albedo": image.filepath_raw, "donor_model": recipe["source_rgm"], "donor_geometry_sha256": recipe["stock_geometry_sha256"], "native_rrgeom": recipe["native_geometry"], "native_changed_vertices": changed, "added_meshes": len(added), "added_uv_all": all(bool(x.data.uv_layers) for x in added), "geometry_and_contact": contacts, "six_side_solid_previews": [str(OUT / f"tlemcen_age0{age}_{v}.png") for v in ("front", "top", "rear", "west", "east", "bottom")], "native_runtime": "pending"}, indent=2) + "\n")
    print("TLEMCEN_SOURCE_READY", age, blend, fbx, len(added), changed, flush=True)


if __name__ == "__main__":
    run(int(sys.argv[sys.argv.index("--") + 1]))
