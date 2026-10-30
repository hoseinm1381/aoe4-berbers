"""Read-only native stamp auxiliary AABB audit for the kasbah art source."""

import itertools
import json
import os
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/marrakech"
STAMP = ROOT / "output/shared_stock_cache/buildings_031/stamps/art/stamps/civ_mal/mal_landmark_b_age_03.bin"
CACHE = ROOT / "output/shared_stock_cache/buildings_031"
sys.path.insert(0, str(ROOT / "research"))
from economy_025_native_stamp import NativeTree


DONORS = {
    "mal_fl3b_gate": "6b2f77523a3e36c6257f",
    "mal_fl3b_stall_01": "4b2071214919b98d561f",
    "mal_fl3b_stall_02": "7a327b7ae34aac15f256",
    "mal_fl3b_tent": "92a2139df7228470687b",
}


def bounds(manifest):
    doc = json.loads((CACHE / manifest / "decoded-static.json").read_text(encoding="utf-8"))
    groups = doc["geometry"]["groups"]
    return [[min(g["bounds"]["minimum"][i] for g in groups) for i in range(3)], [max(g["bounds"]["maximum"][i] for g in groups) for i in range(3)]]


def rotate(v, q):
    x, y, z, w = q
    qv = (x, y, z)
    cross = lambda a, b: (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    t = tuple(2 * n for n in cross(qv, v))
    c = cross(qv, t)
    return tuple(v[i] + w * t[i] + c[i] for i in range(3))


def world_box(box, transform):
    q, translation, scale = transform[:4], transform[4:7], transform[7:10]
    vertices = []
    for xb, yb, zb in itertools.product(*zip(box[0], box[1])):
        native = (-xb, zb, -yb)
        transformed = rotate(tuple(native[i] * scale[i] for i in range(3)), q)
        native_world = tuple(transformed[i] + translation[i] for i in range(3))
        vertices.append((-native_world[0], -native_world[2], native_world[1]))
    return [[min(p[i] for p in vertices) for i in range(3)], [max(p[i] for p in vertices) for i in range(3)]]


def intersect(a, b):
    lengths = [max(0.0, min(a[1][i], b[1][i]) - max(a[0][i], b[0][i])) for i in range(3)]
    return {"overlap_lengths": lengths, "horizontal_area": lengths[0] * lengths[1], "volume": lengths[0] * lengths[1] * lengths[2]}


def main():
    tree = NativeTree(STAMP)
    base = {name: bounds(key) for name, key in DONORS.items()}
    main = json.loads((ART / "native-geometry-validation.json").read_text(encoding="utf-8"))["remixes"]
    rows = []
    for obj in tree.objects.values():
        if obj["type"] != "VisualStampBlueprint":
            continue
        fields = obj["fields"]
        model = tree.field(obj, fields["m_blueprint"])["text"].replace("\\", "/")
        basename = model.split("/")[-1]
        if basename not in DONORS and obj["id"] != 5362244697167843257:
            continue
        raw = tree.field(obj, fields["m_transform"])["raw"]
        transform = struct.unpack("<10f", bytes.fromhex(raw))
        local = base.get(basename)
        item = {"id": str(obj["id"]), "model": model, "transform": transform}
        if local:
            item["local_bounds"] = local
            item["world_bounds"] = world_box(local, transform)
        rows.append(item)
    assert len(rows) == 13, len(rows)  # 1 main, 1 gate, 8 stalls, 3 tents
    source_main = next(r for r in rows if r["id"] == "5362244697167843257")
    report = {"status": "source_transform_aabb_only", "stock_stamp": str(STAMP), "main_transform": source_main["transform"], "ages": []}
    for variant in main:
        main_world = world_box(variant["bounds"], source_main["transform"])
        checks = []
        for row in rows:
            if row is source_main:
                continue
            checks.append({"id": row["id"], "model": row["model"], "world_bounds": row["world_bounds"], "against_main": intersect(main_world, row["world_bounds"])})
        stalls = [r for r in checks if "stall" in r["model"]]
        gate = next(r for r in checks if "fl3b_gate" in r["model"])
        tents = [r for r in checks if "tent" in r["model"]]
        report["ages"].append({"age": variant["age"], "main_world_bounds": main_world, "auxiliaries": checks,
            "risk_summary": {"stall_aabb_intersections": sum(r["against_main"]["horizontal_area"] > 0 for r in stalls),
                "stall_total_xy_aabb_overlap_m2": sum(r["against_main"]["horizontal_area"] for r in stalls),
                "gate_to_main_y_gap_m": gate["world_bounds"][0][1] - main_world[1][1],
                "tent_aabb_intersections": sum(r["against_main"]["horizontal_area"] > 0 for r in tents),
                "recommended_art_only_offsets": "Shift east-side stalls about +1.85m X and west-side stalls about -2.45m X to clear the main AABB by 0.25m; preserve identity and inspect paths/outskirts. Keep outer gate as parade-yard gate only if a disconnected 2.75m approach is intentional; otherwise redesign gate/fort contact with a measured port, not an arbitrary move."}})
    (ART / "stamp-overlap-analysis.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for age in report["ages"]:
        print("AGE", age["age"], "MAIN", age["main_world_bounds"])
        for row in age["auxiliaries"]:
            print(row["model"].split("/")[-1], row["id"], "XY", round(row["against_main"]["horizontal_area"], 3), "VOLUME", round(row["against_main"]["volume"], 3), "BOUNDS", row["world_bounds"])


if __name__ == "__main__":
    main()
