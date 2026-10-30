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
ART = ROOT / "art/building_remix_0_4_0/university"
CACHE = ROOT / "output/shared_stock_cache/buildings_031"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc


def sha(path):
    path=Path(path)
    if not path.exists() and path.name=='decoded-static.json':
        from berber_040_integrate_cache import read_cached_json
        read_cached_json(path)
        return json.loads((path.parent/'rebuild-cache.json').read_text())['members'][path.name]['sha256']
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
    x,y,z=p
    # Dome-to-pyramidal study-roof remap. Drum base and all lower arcades retain
    # their exact native positions. Each complete ring maps continuously onto
    # a square perimeter, so four sloping planes seat on the original drum.
    roofs=[(-3.78,-5.15,6.36,1.08,7.453125),(-3.75,2.35,6.36,1.08,7.453125),(1.995,4.585,7.86,1.39,9.2734375)]
    for cx,cy,base,radius,height in roofs:
        dx,dy=x-cx,y-cy;rr=math.hypot(dx,dy)
        if z>=base and rr<radius*1.12:
            if rr>0.0001:
                t=max(0,min(1,(z-base)/(height-base)))
                square=rr/max(abs(dx),abs(dy))
                x=cx+dx*square;y=cy+dy*square
            t=max(0,min(1,(z-base)/(height-base)))
            z=base+.82*(height-base)*(1-math.sqrt(max(0,1-t*t)))
            return x,y,z
    # Maghrebi broad portal: gently draw the upper central entrance risalit
    # toward the court; lower doorway sill and footprint remain exact.
    if -1.2<x<1.25 and -1.5<y<2.8 and z>4.7:
        y-=.18*min(1,(z-4.7)/.6)
    return x,y,z

def find(age):
    from berber_040_university_donors import ensure
    p=ensure()
    from berber_040_integrate_cache import read_cached_json
    return p,read_cached_json(p)

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
                if dest==tuple(p):continue
                old = struct.unpack_from("<3b", buf, at + offset)
                v = project(tuple(t / 127.0 for t in old))
                eps=.001
                basep=shape(p,age)
                cols=[]
                for axis in range(3):
                    q=list(p);q[axis]+=eps;sp=shape(q,age);cols.append(tuple((sp[j]-basep[j])/eps for j in range(3)))
                def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
                if offset==8:
                    co=[cross(cols[1],cols[2]),cross(cols[2],cols[0]),cross(cols[0],cols[1])]
                    scaled=unit(tuple(sum(v[k]*co[k][j] for k in range(3)) for j in range(3)))
                else:scaled=unit(tuple(sum(v[k]*cols[k][j] for k in range(3)) for j in range(3)))
                buf[at + offset:at + offset + 3] = struct.pack("<3b", *(max(-127, min(127, round(t * 127))) for t in native(scaled)))
            group["normals"][i]=list(project(tuple(t/127 for t in struct.unpack_from("<3b",buf,at+8))))
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
    target = ART / "university_age04.rrgeom"
    projection = ART / "university_age04-projection.json"
    target.write_bytes(result)
    projection.write_text(json.dumps(d), encoding="utf-8")
    native_colour = [m["name"] for m in d["material"]["materials"] if any("team" in (t.get("texture_name") or "").lower() or "owner" in (t.get("texture_name") or "").lower() for t in m.get("textures", []))]
    return {"age": age, "source_rgm": d["request"]["logical_path"], "decoded": str(manifest), "decoded_sha256": sha(manifest), "stock_geometry": str(source), "stock_geometry_sha256": hashlib.sha256(original).hexdigest(), "stock_material": d["material"]["source"]["path"], "native_geometry": str(target), "native_geometry_sha256": sha(target), "remix_projection": str(projection), "donor_bounds": [orig_lo, orig_hi], "source_bounds": [next_lo, next_hi], "world_bounds_at_animator_150": [[round(v * 1.5, 3) for v in next_lo], [round(v * 1.5, 3) for v in next_hi]], "groups": edited_groups, "native_owner_colour_materials": native_colour, "unchanged": "topology, UVs, collection/stage/damage metadata, opaque chunks, material shader and owner masks", "native_runtime": "pending"}


if __name__ == "__main__":
    reports = [remix(4)]
    (ART / "native-validation.json").write_text(json.dumps({"status": "passed", "models": reports}, indent=2) + "\n", encoding="utf-8")
    for report in reports:
        print("TLEMCEN_NATIVE", report["age"], report["source_bounds"], flush=True)
