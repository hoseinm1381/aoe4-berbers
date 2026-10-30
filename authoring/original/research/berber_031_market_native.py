"""Deterministic native GEOB remix of the three Abbasid market donors.

Only the position/normal/tangent stream is touched. UV, indices, opaque
resource chunks, origin, and low contact vertices remain from the donor.
This is an authoring source; the coordinator owns cook and archive binding.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/market"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project(v):
    return (-v[0], -v[2], v[1])


def native(v):
    return (-v[0], v[2], -v[1])


def norm(v):
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v) if length else (0.0, 0.0, 1.0)


def smooth(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def deform(p, age: int):
    x, y, z = p
    # No mutation below the contact/door threshold. Existing low geometry
    # remains an exact native anchor for construction and traffic clearance.
    a = smooth((z - 0.45) / 0.95)
    if a == 0:
        return x, y, z
    # Make the inherited upper block broader and lower, favoring a horizontal
    # courtyard/arcade read rather than the stock two-storey tower read.
    x2 = x
    y2 = y
    # Collapse the stock high roof mass into a compact courtyard hall. This
    # changes the donor's own roof silhouette while preserving its XY contact
    # and footprint exactly; the gatehouse becomes the new height hierarchy.
    roof = 1.15
    upper = 0.30 if age == 2 else (0.38 if age == 3 else 0.45)
    z2 = z if z <= roof else roof + upper * (z - roof)
    # Preserve a slight central entrance lift in the front facade while
    # keeping the stock topology continuous. The sculpted gateway in the
    # Blender source is seated against this wall, not floating beside it.
    gate = math.exp(-((x + 0.25) / 0.95) ** 2 - ((y + 1.76) / 0.53) ** 2)
    z2 += a * gate * (0.25 if age == 2 else 0.34 if age == 3 else 0.42)
    return x2, y2, z2


def mutate(model):
    name = model["name"]
    age = int(name[-2:])
    decoded = json.loads(Path(model["decoded"]).read_text(encoding="utf-8"))
    stock_bytes = Path(model["stock_geometry"]).read_bytes()
    document = rc.parse(stock_bytes)
    chunks = [c for c in rc.walk(document.roots) if c.tag == b"GEOB"]
    changed = {}
    claimed = set()
    group_stats = []
    for group_index, group in enumerate(decoded["geometry"]["groups"]):
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
        assert len(candidates) == 1, (name, group_index, len(candidates))
        chunk = candidates[0]
        assert chunk.offset not in claimed
        claimed.add(chunk.offset)
        data = bytearray(chunk.payload)
        edits = 0
        max_displacement = 0.0
        for i, original in enumerate(group["positions"]):
            at = 16 + 24 * i
            raw = struct.unpack_from("<4e", data, at)
            assert project(raw) == tuple(original)
            wanted = deform(original, age)
            if all(abs(a-b) < 0.001 for a,b in zip(wanted, original)):
                continue
            data[at:at+8] = struct.pack("<4e", *native(wanted), raw[3])
            actual = project(struct.unpack_from("<4e", data, at))
            assert all(math.isfinite(c) for c in actual)
            if original[2] <= 0.45:
                assert actual == tuple(original)
            # Transform the direction vectors by the local finite-difference
            # deformation Jacobian, then re-orthogonalize the tangent.
            eps = 0.003
            jac = [tuple((deform((original[0] + (eps if axis == 0 else 0), original[1] + (eps if axis == 1 else 0), original[2] + (eps if axis == 2 else 0)), age)[j] - wanted[j]) / eps for j in range(3)) for axis in range(3)]
            old_n = project(tuple(v / 127 for v in struct.unpack_from("<3b", data, at+8)))
            old_t = project(tuple(v / 127 for v in struct.unpack_from("<3b", data, at+12)))
            # For this predominantly axis-aligned deformation, inverse
            # transpose of the diagonal is sufficient for a stable normal.
            diag = [max(0.1, jac[j][j]) for j in range(3)]
            nvec = norm(tuple(old_n[j] / diag[j] for j in range(3)))
            tvec = tuple(sum(jac[k][j] * old_t[k] for k in range(3)) for j in range(3))
            dot = sum(a*b for a,b in zip(nvec,tvec))
            tvec = norm(tuple(tvec[j] - dot*nvec[j] for j in range(3)))
            for offset, vector in ((8,nvec),(12,tvec)):
                data[at+offset:at+offset+3] = struct.pack("<3b", *(max(-127,min(127,round(v*127))) for v in native(vector)))
            assert data[at+11] == chunk.payload[at+11]
            assert data[at+15:at+24] == chunk.payload[at+15:at+24]
            group["positions"][i] = list(actual)
            group["normals"][i] = list(nvec)
            edits += 1
            max_displacement = max(max_displacement, math.dist(original,actual))
        if edits:
            changed[chunk.offset] = bytes(data)
        group_stats.append({"group":group_index,"vertices":count,"changed_vertices":edits,"max_displacement_m":round(max_displacement,4)})
    assert sum(s["changed_vertices"] for s in group_stats) > 10000
    remix = rc.rebuild(document, lambda chunk: changed.get(chunk.offset))
    assert len(remix) == len(stock_bytes)
    reread = rc.parse(remix)
    for before, after in zip(rc.walk(document.roots),rc.walk(reread.roots)):
        assert (before.tag,before.name,before.version) == (after.tag,after.name,after.version)
        if before.offset not in changed and not before.children:
            assert before.payload == after.payload
    ART.mkdir(parents=True,exist_ok=True)
    target = ART / f"Berber_{name}_0_3_1.rrgeom"
    projection = ART / f"Berber_{name}_0_3_1-projection.json"
    target.write_bytes(remix)
    projection.write_text(json.dumps(decoded),encoding="utf-8")
    return {"name":name,"stock_model":model["source"],"stock_geometry":model["stock_geometry"],"stock_sha256":sha(stock_bytes),"native_geometry":str(target),"native_sha256":sha(remix),"projection":str(projection),"groups":group_stats,"contact_vertices_unchanged_below_z":0.45,"uv_indices_opaque_chunks_unchanged":True}


def main():
    recipe = json.loads((ROOT/"art/building_remix_0_3_0/recipe.json").read_text(encoding="utf-8"))
    models = [m for m in recipe["models"] if m["family"] == "market"]
    reports = [mutate(model) for model in models]
    (ART/"native-geometry-validation.json").write_text(json.dumps({"status":"passed","models":reports,"cook":"pending","native_runtime":"pending"},indent=2)+"\n",encoding="utf-8")
    print("BERBER_031_MARKET_NATIVE_READY",len(reports),flush=True)


if __name__ == "__main__":
    main()
