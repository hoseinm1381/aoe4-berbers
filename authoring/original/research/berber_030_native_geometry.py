"""Native roof-mass reduction for range/stable, retaining lower contact and XY.

This edits only verified GEOB position/normal/tangent vertex spans. Opaque
selection, topology, UV, construction/damage and collection chunks are retained.
The result is an art source; packaging still requires native cook/readback.
"""

import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_0"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc

POLICY = {
    "archery_range": {"threshold": 1.25, "transition": 0.70, "upper_scale": 0.30},
    "stable": {"threshold": 1.45, "transition": 0.60, "upper_scale": 0.34},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def project(v):
    return (-v[0], -v[2], v[1])


def native(v):
    return (-v[0], v[2], -v[1])


def normal(v):
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v) if length else (0, 0, 1)


def deform(z, policy):
    threshold = policy["threshold"]
    transition = policy["transition"]
    scale = policy["upper_scale"]
    t = z - threshold
    if t <= 0:
        return z, 1.0
    if t < transition:
        return threshold + t - (1 - scale) * t * t / (2 * transition), 1 - (1 - scale) * t / transition
    return threshold + transition * (1 + scale) / 2 + scale * (t - transition), scale


def mutate(model):
    manifest = Path(model["decoded"])
    projection = json.loads(manifest.read_text(encoding="utf-8"))
    source = Path(model["stock_geometry"])
    original = source.read_bytes()
    doc = rc.parse(original)
    chunks = [c for c in rc.walk(doc.roots) if c.tag == b"GEOB"]
    changed = {}
    claimed = set()
    detail = []
    for index, group in enumerate(projection["geometry"]["groups"]):
        assert group["stream"] == "StructureCollectionPositionDataStream"
        count = len(group["positions"])
        candidates = []
        for chunk in chunks:
            if len(chunk.payload) != 16 + 24 * count:
                continue
            n, _, stride, _ = struct.unpack_from("<4I", chunk.payload)
            if n != count or stride != 24:
                continue
            if all(project(struct.unpack_from("<4e", chunk.payload, 16 + i * 24)) == tuple(group["positions"][i]) for i in (0, count // 2, count - 1)):
                candidates.append(chunk)
        assert len(candidates) == 1, (model["name"], index, len(candidates))
        chunk = candidates[0]
        assert chunk.offset not in claimed
        claimed.add(chunk.offset)
        data = bytearray(chunk.payload)
        edits = 0
        maximum = 0.0
        for i, p in enumerate(group["positions"]):
            at = 16 + 24 * i
            raw_position = struct.unpack_from("<4e", data, at)
            assert project(raw_position) == tuple(p)
            new_z, jacobian = deform(p[2], POLICY[model["family"]])
            if new_z == p[2]:
                continue
            data[at:at + 8] = struct.pack("<4e", *native((p[0], p[1], new_z)), raw_position[3])
            quantized = project(struct.unpack_from("<4e", data, at))
            assert quantized[:2] == tuple(p[:2])
            assert quantized[2] <= p[2] + 0.003
            old_n = struct.unpack_from("<4b", data, at + 8)
            old_t = struct.unpack_from("<4b", data, at + 12)
            n = project(tuple(max(-1, c / 127) for c in old_n[:3]))
            n = normal((n[0], n[1], n[2] / jacobian))
            t = project(tuple(max(-1, c / 127) for c in old_t[:3]))
            t = (t[0], t[1], t[2] * jacobian)
            dot = sum(a * b for a, b in zip(n, t))
            t = normal(tuple(a - b * dot for a, b in zip(t, n)))
            for offset, vector in ((8, n), (12, t)):
                data[at + offset:at + offset + 3] = struct.pack("<3b", *(max(-127, min(127, round(v * 127))) for v in native(vector)))
            assert data[at + 11] == chunk.payload[at + 11]
            assert data[at + 15:at + 24] == chunk.payload[at + 15:at + 24]
            group["positions"][i] = list(quantized)
            group["normals"][i] = list(normal(project(tuple(max(-1, c / 127) for c in struct.unpack_from("<3b", data, at + 8)))))
            edits += 1
            maximum = max(maximum, p[2] - quantized[2])
        if edits:
            changed[chunk.offset] = bytes(data)
        detail.append({"group": index, "vertices": count, "edited": edits, "max_vertical_reduction": maximum})
    assert any(x["edited"] for x in detail), model["name"]
    output = rc.rebuild(doc, lambda c: changed.get(c.offset))
    assert len(output) == len(original)
    reread = rc.parse(output)
    for before, after in zip(rc.walk(doc.roots), rc.walk(reread.roots)):
        assert (before.tag, before.name, before.version) == (after.tag, after.name, after.version)
        if before.offset not in changed and not before.children:
            assert before.payload == after.payload
    location = ART / model["family"]
    location.mkdir(parents=True, exist_ok=True)
    geometry_path = location / (model["name"] + ".rrgeom")
    projection_path = location / (model["name"] + "-remix-projection.json")
    geometry_path.write_bytes(output)
    projection_path.write_text(json.dumps(projection), encoding="utf-8")
    model["native_geometry"] = str(geometry_path)
    model["remix_projection"] = str(projection_path)
    return {"name": model["name"], "source_sha256": sha(original), "remix_sha256": sha(output), "groups": detail, "xy_unchanged": True, "lower_contact_unchanged": True, "uv_index_layout_and_opaque_chunks_unchanged": True}


def main():
    recipe_path = ART / "recipe.json"
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    reports = []
    for model in recipe["models"]:
        if model["family"] in POLICY:
            reports.append(mutate(model))
            print("GEOMETRY_REMIX", model["name"], flush=True)
        else:
            model["native_geometry"] = model["stock_geometry"]
            model["remix_projection"] = model["decoded"]
    recipe_path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    report_path = ART / "native-geometry-validation.json"
    report_path.write_text(json.dumps({"status": "passed", "models": reports, "native_runtime": "pending"}, indent=2) + "\n", encoding="utf-8")
    print("BERBER_030_NATIVE_GEOMETRY_READY", len(reports))


if __name__ == "__main__":
    main()
