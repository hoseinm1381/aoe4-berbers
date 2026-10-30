"""Source-preserving native geometry remixes for the Berber siege workshop.

Only verified position, normal, and tangent bytes in stock GEOB vertex streams
change. Topology, UV, material indices, collections and opaque chunks remain.
The model still needs the coordinator's private Garrison cook and stamp binding.
"""

import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/siege"
SHARED = ROOT / "output/shared_stock_cache/buildings_031"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc

DONORS = {3: "028f0735c6a97dbf180a", 4: "2aab62547dae0b6332ab"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def project(v):
    return (-v[0], -v[2], v[1])


def native(v):
    return (-v[0], v[2], -v[1])


def norm(v):
    length = math.sqrt(sum(c*c for c in v))
    return tuple(c/length for c in v) if length else (0.0, 0.0, 1.0)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t*t*(3.0-2.0*t)


def shape(v, age):
    x, y, z = v
    # The ground-contact band and siege exit arches remain at exact donor
    # coordinates. Above 2.15 m, the tall flat roof and flues compress into
    # lower artisan sheds. Their exterior edges rise to broad asymmetric
    # pitches, so the existing wall/roof/chimney groups deform coherently.
    if z <= 2.15:
        return (x, y, z)
    ratio = 0.60 if age == 3 else 0.66
    upper = z - 2.15
    ramp = smooth(upper/0.65)
    roof_pitch = 0.43 if age == 3 else 0.60
    rear = smooth((y-0.4)/3.1)
    west = smooth((-x-0.65)/2.8)
    pitch = roof_pitch * (0.52*rear + 0.48*west) * ramp
    # Set the wide inner north roof deck below its outer parapet. This turns
    # the stock high roof into an open-looking, sheltered work terrace from
    # the gameplay camera while leaving every native face and UV in place.
    recess_x = smooth((x+0.15)/0.75) * smooth((3.45-x)/0.75)
    recess_y = smooth((y-0.65)/0.65) * smooth((4.25-y)/0.65)
    roof_recess = -(0.66 if age == 3 else 0.78) * recess_x * recess_y * ramp
    gate = smooth((-x-1.15)/1.2) * smooth((-y-1.55)/1.2)
    gate_lift = (0.67 if age == 3 else 1.08) * gate * ramp
    shrink = 0.045 if age == 3 else 0.032
    inset = shrink * ramp
    return (x*(1.0-inset), y*(1.0-inset), 2.15 + upper*ratio + pitch + gate_lift + roof_recess)


def jacobian(v, age):
    epsilon = 0.01
    cols = []
    for axis in range(3):
        hi = list(v)
        lo = list(v)
        hi[axis] += epsilon
        lo[axis] -= epsilon
        a, b = shape(hi, age), shape(lo, age)
        cols.append(tuple((a[i]-b[i])/(2*epsilon) for i in range(3)))
    return cols


def new_frame(n, t, v, age):
    # Recompute a tangent frame by inverse transpose of the local warp.
    # The X/Y inset terms are small; evaluating finite differences avoids
    # approximating pitched roof normals with their old flat orientations.
    c = jacobian(v, age)
    tx = tuple(sum(c[j][i]*t[j] for j in range(3)) for i in range(3))
    bx = norm((n[1]*t[2]-n[2]*t[1], n[2]*t[0]-n[0]*t[2], n[0]*t[1]-n[1]*t[0]))
    b2 = tuple(sum(c[j][i]*bx[j] for j in range(3)) for i in range(3))
    n2 = norm((tx[1]*b2[2]-tx[2]*b2[1], tx[2]*b2[0]-tx[0]*b2[2], tx[0]*b2[1]-tx[1]*b2[0]))
    tx = norm(tuple(tx[i]-n2[i]*sum(tx[j]*n2[j] for j in range(3)) for i in range(3)))
    return n2, tx


def byte_vector(v):
    return struct.pack("<3b", *(max(-127, min(127, round(c*127))) for c in native(v)))


def remix(age):
    cache = SHARED / DONORS[age]
    projection = json.loads((cache / "decoded-static.json").read_text(encoding="utf-8"))
    stock_path = Path(projection["resources"]["geometry"]["cache_path"])
    original = stock_path.read_bytes()
    assert digest(original) == projection["resources"]["geometry"]["sha256"]
    doc = rc.parse(original)
    chunks = [c for c in rc.walk(doc.roots) if c.tag == b"GEOB"]
    changed = {}
    claimed = set()
    group_report = []
    minimum_clearance = float("inf")
    for gi, group in enumerate(projection["geometry"]["groups"]):
        assert group["stream"] == "StructureCollectionPositionDataStream"
        count = len(group["positions"])
        matches = []
        for chunk in chunks:
            if len(chunk.payload) != 16+24*count:
                continue
            n, _, stride, _ = struct.unpack_from("<4I", chunk.payload)
            if n != count or stride != 24:
                continue
            if all(project(struct.unpack_from("<4e", chunk.payload, 16+i*24)) == tuple(group["positions"][i]) for i in (0, count//2, count-1)):
                matches.append(chunk)
        assert len(matches) == 1, (age, gi, len(matches))
        chunk = matches[0]
        assert chunk.offset not in claimed
        claimed.add(chunk.offset)
        data = bytearray(chunk.payload)
        edits = 0
        major = 0
        max_displacement = 0.0
        for i, p in enumerate(group["positions"]):
            p = tuple(p)
            if p[2] <= 2.15:
                continue
            at = 16+i*24
            raw = struct.unpack_from("<4e", data, at)
            assert project(raw) == p
            mapped = shape(p, age)
            data[at:at+8] = struct.pack("<4e", *native(mapped), raw[3])
            q = project(struct.unpack_from("<4e", data, at))
            old_n = project(tuple(c/127 for c in struct.unpack_from("<3b", data, at+8)))
            old_t = project(tuple(c/127 for c in struct.unpack_from("<3b", data, at+12)))
            n2, t2 = new_frame(norm(old_n), norm(old_t), p, age)
            data[at+8:at+11] = byte_vector(n2)
            data[at+12:at+15] = byte_vector(t2)
            assert data[at+11] == chunk.payload[at+11]
            assert data[at+15:at+24] == chunk.payload[at+15:at+24]
            group["positions"][i] = list(q)
            group["normals"][i] = list(n2)
            displacement = math.dist(p, q)
            max_displacement = max(max_displacement, displacement)
            if displacement > 0.01:
                edits += 1
            if displacement > 0.15:
                major += 1
            minimum_clearance = min(minimum_clearance, q[2] if p[2] > 2.15 else float("inf"))
        changed[chunk.offset] = bytes(data)
        group_report.append({"name": group["name"], "vertices": count, "edited_over_1cm": edits, "edited_over_15cm": major, "max_displacement_m": round(max_displacement, 4)})
    result = rc.rebuild(doc, lambda chunk: changed.get(chunk.offset))
    assert len(result) == len(original)
    reread = rc.parse(result)
    for before, after in zip(rc.walk(doc.roots), rc.walk(reread.roots)):
        assert (before.tag, before.name, before.version) == (after.tag, after.name, after.version)
        if before.offset not in changed and not before.children:
            assert before.payload == after.payload
    assert sum(g["edited_over_15cm"] for g in group_report) > 12000
    ART.mkdir(parents=True, exist_ok=True)
    stem = f"siege_age0{age}"
    geom = ART / f"{stem}.rrgeom"
    projected = ART / f"{stem}-remix-projection.json"
    geom.write_bytes(result)
    projected.write_text(json.dumps(projection, separators=(",", ":")), encoding="utf-8")
    return {
        "name": stem, "age": age,
        "stock_logical_model": projection["request"]["logical_path"],
        "stock_model_sha256": projection["resources"]["model"]["sha256"],
        "stock_geometry_sha256": digest(original),
        "native_geometry": str(geom), "native_geometry_sha256": digest(result),
        "remix_projection": str(projected),
        "native_geometry_size_unchanged": len(original) == len(result),
        "lower_band_and_exit_untouched_below_m": 2.15,
        "uv_topology_collection_and_opaque_chunks_preserved": True,
        "groups": group_report,
    }


def main():
    reports = [remix(age) for age in (3, 4)]
    (ART / "native-geometry-validation.json").write_text(json.dumps({"status": "passed", "models": reports, "runtime": "pending"}, indent=2)+"\n", encoding="utf-8")
    print("SIEGE_NATIVE_GEOMETRY_READY", [(r["age"], sum(g["edited_over_15cm"] for g in r["groups"])) for r in reports])


if __name__ == "__main__":
    main()
