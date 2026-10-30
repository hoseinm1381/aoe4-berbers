"""Deterministic native-mesh remix of the active Sultanate monastery donors.

Only GEOB vertex positions/normals/tangents change. Topology, UVs, native
material masks, damage/construction collections and opaque metadata survive.
The separate Blender additions are static art and require their own cook.
"""

import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/tlemcen"
CACHE = ROOT / "output/shared_stock_cache/buildings_031"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit(v):
    length = math.sqrt(sum(x * x for x in v))
    return tuple(x / length for x in v) if length else (0.0, 0.0, 1.0)


def project(v):
    return (-v[0], -v[2], v[1])


def native(v):
    return (-v[0], v[2], -v[1])


def smooth(a, b, v):
    t = max(0.0, min(1.0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def shape(p, age):
    x, y, z = p
    # The donor has two Indian-style minarets. Keep one as an offset square
    # Maghrebi tower and reduce the other to the courtyard wall's height.
    if z > 2.5 and x > 4.45 and y < -4.15:
        z = 2.5 + (z - 2.5) * (1.0 - 0.82 * smooth(2.5, 4.5, z))
    if age == 4 and z > 3.4 and abs(x) > 4.45 and y > -4.15:
        # The stock Imperial donor grows additional Indo-Islamic spires.
        # Lower them into parapet-height corner masses for Maghrebi coherence.
        z = 3.4 + (z - 3.4) * (1.0 - 0.84 * smooth(3.4, 5.2, z))
    if z > 2.0 and x < -4.45 and y < -4.15:
        cx, cy = -5.35, -5.15
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        if 0.06 < r < 1.0:
            theta = math.atan2(dy, dx)
            square = 1.0 / max(abs(math.cos(theta)), abs(math.sin(theta)))
            influence = smooth(2.0, 3.2, z)
            x = cx + dx * (1.0 + (square - 1.0) * 0.67 * influence)
            y = cy + dy * (1.0 + (square - 1.0) * 0.67 * influence)
    # Roofed side aisles replace four dominant domes, leaving a clear central
    # liturgical aisle. This alters stock roof masses, not just a material.
    if abs(x) > 2.7 and y > 0.0 and z > 2.50:
        z = 2.50 + (z - 2.50) * (1.0 - 0.95 * smooth(2.50, 3.30, z))
    # Compact ribbed dome above the central prayer bay / mihrab.
    if abs(x) < 2.55 and 0.65 < y < 4.7 and z > 3.45:
        cx, cy = 0.0, 2.85
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        if r > 0.10:
            rib = math.cos(16.0 * math.atan2(dy, dx))
            envelope = smooth(3.45, 4.2, z) * (1.0 - smooth(2.0, 2.55, r))
            strength = 0.065 if age == 3 else 0.080
            x += dx * strength * rib * envelope
            y += dy * strength * rib * envelope
        if age == 4:
            z = 3.45 + (z - 3.45) * 0.83
    # Preserve the actor's 150% animator_scale; shrink donor-space geometry.
    return (x * 0.50, y * 0.50, z * 0.74 if z >= 0 else z * 0.50)


def find(age):
    for p in CACHE.glob("*/decoded-static.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        if f"sul_monastery_control_age0{age}" in d["request"]["logical_path"]:
            return p, d
    raise FileNotFoundError(age)


def remix(age):
    manifest, d = find(age)
    source = Path(d["geometry"]["source"]["path"])
    original = source.read_bytes()
    doc = rc.parse(original)
    chunks = [c for c in rc.walk(doc.roots) if c.tag == b"GEOB"]
    changed = {}
    used = set()
    edited_groups = []
    orig_lo = [float("inf")] * 3
    orig_hi = [float("-inf")] * 3
    next_lo = [float("inf")] * 3
    next_hi = [float("-inf")] * 3
    for group in d["geometry"]["groups"]:
        count = len(group["positions"])
        candidates = []
        for c in chunks:
            if c.offset in used or len(c.payload) != 16 + 24 * count:
                continue
            n, _, stride, _ = struct.unpack_from("<4I", c.payload)
            if n == count and stride == 24 and all(project(struct.unpack_from("<4e", c.payload, 16 + i * 24)) == tuple(group["positions"][i]) for i in (0, count // 2, count - 1)):
                candidates.append(c)
        assert len(candidates) == 1, (age, group["name"], len(candidates))
        c = candidates[0]
        used.add(c.offset)
        buf = bytearray(c.payload)
        vertex_edits = 0
        for i, p in enumerate(group["positions"]):
            at = 16 + 24 * i
            raw = struct.unpack_from("<4e", buf, at)
            assert project(raw) == tuple(p)
            dest = shape(p, age)
            buf[at:at + 8] = struct.pack("<4e", *native(dest), raw[3])
            quant = project(struct.unpack_from("<4e", buf, at))
            group["positions"][i] = list(quant)
            for k in range(3):
                orig_lo[k] = min(orig_lo[k], p[k]); orig_hi[k] = max(orig_hi[k], p[k])
                next_lo[k] = min(next_lo[k], quant[k]); next_hi[k] = max(next_hi[k], quant[k])
            for offset in (8, 12):
                old = struct.unpack_from("<3b", buf, at + offset)
                v = project(tuple(t / 127.0 for t in old))
                scaled = unit((v[0] / 0.5, v[1] / 0.5, v[2] / 0.74)) if offset == 8 else unit((v[0] * 0.5, v[1] * 0.5, v[2] * 0.74))
                buf[at + offset:at + offset + 3] = struct.pack("<3b", *(max(-127, min(127, round(t * 127))) for t in native(scaled)))
            assert buf[at + 11] == c.payload[at + 11]
            assert buf[at + 15:at + 24] == c.payload[at + 15:at + 24]
            vertex_edits += dest != tuple(p)
        changed[c.offset] = bytes(buf)
        edited_groups.append({"name": group["name"], "vertices": count, "changed_positions": vertex_edits})
    assert len(used) == len(d["geometry"]["groups"])
    result = rc.rebuild(doc, lambda c: changed.get(c.offset))
    assert len(result) == len(original)
    back = rc.parse(result)
    for before, after in zip(rc.walk(doc.roots), rc.walk(back.roots)):
        assert (before.tag, before.name, before.version) == (after.tag, after.name, after.version)
        if before.offset not in changed and not before.children:
            assert before.payload == after.payload
    ART.mkdir(parents=True, exist_ok=True)
    target = ART / f"tlemcen_age0{age}.rrgeom"
    projection = ART / f"tlemcen_age0{age}-projection.json"
    target.write_bytes(result)
    projection.write_text(json.dumps(d), encoding="utf-8")
    native_colour = [m["name"] for m in d["material"]["materials"] if any("team" in (t.get("texture_name") or "").lower() or "owner" in (t.get("texture_name") or "").lower() for t in m.get("textures", []))]
    return {"age": age, "source_rgm": d["request"]["logical_path"], "decoded": str(manifest), "decoded_sha256": sha(manifest), "stock_geometry": str(source), "stock_geometry_sha256": hashlib.sha256(original).hexdigest(), "stock_material": d["material"]["source"]["path"], "native_geometry": str(target), "native_geometry_sha256": sha(target), "remix_projection": str(projection), "donor_bounds": [orig_lo, orig_hi], "source_bounds": [next_lo, next_hi], "world_bounds_at_animator_150": [[round(v * 1.5, 3) for v in next_lo], [round(v * 1.5, 3) for v in next_hi]], "groups": edited_groups, "native_owner_colour_materials": native_colour, "unchanged": "topology, UVs, collection/stage/damage metadata, opaque chunks, material shader and owner masks", "native_runtime": "pending"}


if __name__ == "__main__":
    reports = [remix(3), remix(4)]
    (ART / "native-validation.json").write_text(json.dumps({"status": "passed", "models": reports}, indent=2) + "\n", encoding="utf-8")
    for report in reports:
        print("TLEMCEN_NATIVE", report["age"], report["source_bounds"], flush=True)
