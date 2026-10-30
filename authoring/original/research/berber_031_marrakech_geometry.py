"""Native-compatible Malian fort donor reshaping for Marrakech Ages III/IV.

The source is the official Age II Malian landmark fort model, used as a new
stamp main in place of the Age III skull tower. Only GEOB vertex positions,
normals and tangents change. Topology, UVs, material/owner mask slots, opaque
chunks, and all gameplay resources are untouched. This is art source, not a
cooked or native-tested resource.
"""

import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/marrakech"
MANIFEST = ROOT / "output/shared_stock_cache/buildings_031/aa9a46fa271304378d30/decoded-static.json"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc


def sha(data):
    return hashlib.sha256(data).hexdigest()


def game_to_blender(v):
    return (-v[0], -v[2], v[1])


def blender_to_game(v):
    return (-v[0], v[2], -v[1])


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def transform(point, age):
    x, y, z = point
    # Scale the existing battlements/court to the 8x8 landmark control. The
    # original long approach is intentionally drawn toward the entrance.
    front = smooth(1.5, 7.5, -y)
    x1 = x * (0.565 - 0.026 * front)
    y1 = y * 0.495 + 1.08

    # Shape the castle-age hierarchy: lower flanking tower crowns and a
    # taller, deeper gatehouse at the middle of the connected rampart.
    upper = smooth(1.7, 4.0, z)
    central = (1.0 - smooth(2.1, 4.4, abs(x))) * (1.0 - smooth(1.7, 5.2, abs(y + 2.0)))
    flank = smooth(3.2, 5.7, abs(x))
    rise = (0.58 if age == 3 else 1.72) * central * upper
    lower = (0.58 if age == 3 else 0.16) * flank * upper
    z1 = z * 0.68 + rise - lower
    return (x1, y1, z1)


def normalize(v):
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v) if length else (0.0, 0.0, 1.0)


def derivative(p, age):
    h = 0.02
    columns = []
    for axis in range(3):
        a = list(p)
        b = list(p)
        a[axis] -= h
        b[axis] += h
        lo = transform(a, age)
        hi = transform(b, age)
        columns.append(tuple((hi[i] - lo[i]) / (2 * h) for i in range(3)))
    return columns


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def normal_transform(n, columns):
    a, b, c = columns
    # Cofactor matrix acts as inverse transpose up to positive determinant.
    cofactors = (cross(b, c), cross(c, a), cross(a, b))
    v = tuple(sum(n[j] * cofactors[j][i] for j in range(3)) for i in range(3))
    return normalize(v)


def tangent_transform(t, columns):
    return normalize(tuple(sum(columns[j][i] * t[j] for j in range(3)) for i in range(3)))


def encode_snorm3(v):
    return struct.pack("<3b", *(max(-127, min(127, round(c * 127))) for c in v))


def build(age, source, decoded):
    doc = rc.parse(source)
    chunks = [c for c in rc.walk(doc.roots) if c.tag == b"GEOB"]
    changes = {}
    groups = decoded["geometry"]["groups"]
    used = set()
    evidence = []
    for group in groups:
        count = len(group["positions"])
        candidates = []
        for chunk in chunks:
            if len(chunk.payload) != 16 + count * 24:
                continue
            n, _, stride, _ = struct.unpack_from("<4I", chunk.payload)
            if n != count or stride != 24:
                continue
            if all(game_to_blender(struct.unpack_from("<4e", chunk.payload, 16 + 24 * i)) == tuple(group["positions"][i]) for i in (0, count // 2, count - 1)):
                candidates.append(chunk)
        assert len(candidates) == 1, (group["name"], len(candidates))
        chunk = candidates[0]
        assert chunk.offset not in used
        used.add(chunk.offset)
        data = bytearray(chunk.payload)
        moved = 0
        maximum = 0.0
        regional = 0
        max_regional = 0.0
        for i, point in enumerate(group["positions"]):
            at = 16 + i * 24
            original = struct.unpack_from("<4e", data, at)
            assert game_to_blender(original) == tuple(point)
            p = transform(point, age)
            data[at:at + 8] = struct.pack("<4e", *blender_to_game(p), original[3])
            quantized = game_to_blender(struct.unpack_from("<4e", data, at))
            group["positions"][i] = list(quantized)
            basis = derivative(point, age)
            old_n = game_to_blender(tuple(v / 127 for v in struct.unpack_from("<3b", chunk.payload, at + 8)))
            old_t = game_to_blender(tuple(v / 127 for v in struct.unpack_from("<3b", chunk.payload, at + 12)))
            new_n = normal_transform(old_n, basis)
            new_t = tangent_transform(old_t, basis)
            data[at + 8:at + 11] = encode_snorm3(blender_to_game(new_n))
            data[at + 12:at + 15] = encode_snorm3(blender_to_game(new_t))
            assert data[at + 11] == chunk.payload[at + 11]
            assert data[at + 15:at + 24] == chunk.payload[at + 15:at + 24]
            group["normals"][i] = list(new_n)
            if any(abs(a - b) > 0.005 for a, b in zip(point, quantized)):
                moved += 1
                maximum = max(maximum, math.dist(point, quantized))
            uniform = (point[0] * 0.565, point[1] * 0.495 + 1.08, point[2] * 0.68)
            residual = math.dist(quantized, uniform)
            if residual > 0.05:
                regional += 1
                max_regional = max(max_regional, residual)
        changes[chunk.offset] = bytes(data)
        evidence.append({"group": group["name"], "vertices": count, "moved": moved, "regionally_reshaped_beyond_uniform_fit": regional, "max_regional_reshaping_m": max_regional, "max_displacement_m": maximum, "uv_layers": len(group["uv_layers"]), "triangles": group["triangle_count"]})
    assert len(used) == len(groups) == 6
    output = rc.rebuild(doc, lambda c: changes.get(c.offset))
    assert len(output) == len(source)
    reread = rc.parse(output)
    for before, after in zip(rc.walk(doc.roots), rc.walk(reread.roots)):
        assert (before.tag, before.name, before.version) == (after.tag, after.name, after.version)
        if before.offset not in changes and not before.children:
            assert before.payload == after.payload
    target = ART / f"marrakech_age{age:02}_kasbah.rrgeom"
    projection = ART / f"marrakech_age{age:02}_projection.json"
    target.write_bytes(output)
    projection.write_text(json.dumps(decoded), encoding="utf-8")
    points = [p for g in groups for p in g["positions"]]
    bounds = [[min(p[i] for p in points) for i in range(3)], [max(p[i] for p in points) for i in range(3)]]
    assert bounds[0][0] > -4.0 and bounds[1][0] < 4.0, bounds
    assert bounds[0][1] > -4.0 and bounds[1][1] < 4.0, bounds
    return {"age": age, "source_sha256": sha(source), "native_geometry": str(target), "native_sha256": sha(output), "projection": str(projection), "bounds": bounds, "groups": evidence, "native_owner_slots_and_opaque_chunks_preserved": True}


def main():
    decoded = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = Path(decoded["geometry"]["source"]["path"]).read_bytes()
    ART.mkdir(parents=True, exist_ok=True)
    results = []
    for age in (3, 4):
        # A separate projection document is needed for each age.
        results.append(build(age, source, json.loads(MANIFEST.read_text(encoding="utf-8"))))
    report = {"status": "source_only", "donor": decoded["request"]["logical_path"], "main_replaces_active_age03_skull_tower": True, "age4_needs_new_visual_tier": True, "remixes": results, "runtime": "untested"}
    (ART / "native-geometry-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("MARRAKECH_NATIVE_GEOMETRY_READY", len(results), flush=True)


if __name__ == "__main__":
    main()
