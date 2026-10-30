"""Source checks for one editable Berber siege workshop Blender scene."""

import hashlib
import json
import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/siege"
age = int(os.environ["BERBER_SIEGE_AGE"])
stem = f"siege_age0{age}"
projection = json.loads((ART/f"{stem}-remix-projection.json").read_text(encoding="utf-8"))
donor = bpy.data.collections[f"STOCK_DERIVED_ABBASID_AGE_{age}"]
kit_collection = bpy.data.collections[f"BERBER_SIEGE_YARD_KIT_AGE_{age}"]
kit = next(iter(kit_collection.objects))
assert len(donor.objects) == len(projection["geometry"]["groups"])
assert len(kit_collection.objects) == 1
assert len(kit.data.materials) == 1
assert len(kit.data.uv_layers) == 1
assert all(abs(v) < 1e-8 for v in kit.location)
assert all(abs(v-1) < 1e-8 for v in kit.scale)
assert all(abs(v) < 1e-8 for v in kit.rotation_euler)
assert kit.data.materials[0].node_tree.nodes.get("Image Texture").image.packed_file
assert len({o.data.as_pointer() for o in list(donor.objects)+[kit]}) == len(donor.objects)+1

checked = []
for group in projection["geometry"]["groups"]:
    obj = donor.objects[group["name"]]
    assert len(obj.data.vertices) == group["vertex_count"]
    assert len(obj.data.polygons) == group["triangle_count"]
    assert len(obj.data.uv_layers) == 1
    assert obj.data.uv_layers[0].name == "UVMap"
    assert obj.get("stock_donor") == projection["request"]["logical_path"]
    checked.append({"name":obj.name,"vertices":len(obj.data.vertices),"triangles":len(obj.data.polygons)})

uv = kit.data.uv_layers.active
minimum_uv_area=float("inf")
for poly in kit.data.polygons:
    assert len(poly.loop_indices) >= 3
    uvs=[uv.data[i].uv for i in poly.loop_indices]
    area=abs(sum(uvs[i][0]*uvs[(i+1)%len(uvs)][1]-uvs[(i+1)%len(uvs)][0]*uvs[i][1] for i in range(len(uvs))))/2
    minimum_uv_area=min(minimum_uv_area,area)
assert minimum_uv_area > 1e-5, minimum_uv_area
assert all(-0.001 <= coordinate <= 1.001 for item in uv.data for coordinate in item.uv)
verts=[v.co for v in kit.data.vertices]
assert min(v.z for v in verts) >= -1e-5
assert not any(v.x < -1.2 and v.y < -2.0 for v in verts)
assert all(math.isfinite(c) for v in verts for c in v)

previews=ART/f"previews/age0{age}"
expected=("front","rear","left","right","top","bottom","default_zoom")
assert all((previews/f"{name}.png").is_file() for name in expected)
report={
    "status":"passed","age":age,"source_scene":bpy.data.filepath,
    "source_scene_sha256":hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
    "donor_model":projection["request"]["logical_path"],
    "donor_groups":checked,"kit_vertices":len(kit.data.vertices),
    "kit_faces":len(kit.data.polygons),"kit_materials":len(kit.data.materials),
    "kit_minimum_uv_polygon_area":minimum_uv_area,
    "kit_ground_contact_m":min(v.z for v in verts),
    "kit_exit_envelope_unblocked":True,
    "previews":{name:str(previews/f"{name}.png") for name in expected},
    "native_geometry_sha256":hashlib.sha256((ART/f"{stem}.rrgeom").read_bytes()).hexdigest(),
    "Garrison_static_prepare":"pending serialized coordinator native cook",
    "native_runtime":"pending user test",
}
(ART/f"{stem}-source-validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print("SIEGE_SOURCE_VALIDATED",age,len(checked),len(kit.data.polygons),minimum_uv_area)
