"""Compose only six 031 visual families on the verified 030 archive."""

import copy
import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_1"
INT = OUT / "integration"
PAYLOAD = INT / "payload"
BASE = ROOT / "output/berber_update_0_3_0/package/Berber_future_kingdom.sga"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
ARCH = EXT / "bin/sga-archiver.exe"
GUID = "1d3145e8f1b2427f8bb0067851fcf0f1"
BASE_SHA = "33cbb2d3d60914da49e893fe0f19c37dc6cb9aaaa120c0d00613a26a2ebbe5af"
sys.path[:0] = [str(ROOT / "research"), str(EXT)]
from garrison_shared import rgd, relic_chunky as rc
from economy_025_native_stamp import NativeTree
from building_026_native_rebind import rebind
from build_berber_update_0_2_5 import encode, semantics, validate_stamp


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run(*args):
    p = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding="utf-8")
    if p.returncode:
        raise RuntimeError(f"{args}: {p.returncode}\n{p.stdout[-1000:]}\n{p.stderr[-2000:]}")
    return p.stdout


def save(member, raw, payloads):
    target = PAYLOAD / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    row = {"member": member, "file": str(target), "sha256": sha(raw), "bytes": len(raw)}
    if member in payloads:
        assert payloads[member] == row
    else:
        payloads[member] = row


def inject_static(encoded, family, age, parts):
    if not parts:
        return encoded, []
    path = INT / f"{family}_age{age:02}_main.bin"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    tree = NativeTree(path)
    marker = "mon_market_stall_med_c" if family == "market" else "sagebush_row"
    stock = sorted((o for o in tree.objects.values()
                    if o["type"] == "VisualStampBlueprint"
                    and marker in tree.field(o, o["fields"]["m_blueprint"])["text"]), key=lambda o: o["id"])
    assert len(stock) >= len(parts), (family, age, len(stock), len(parts))
    assert family in ("market", "tlemcen", "siege", "mosque", "keep"), family
    memory = bytearray(tree.memory.payload)
    changes = []
    for obj, model in zip(stock, parts):
        field = obj["fields"]["m_blueprint"]
        assert field.get("FieldTypeName") == "util::ReflectString<StdTraits>"
        at = obj["offset"] + int(field.get("Offset")) - tree.memory.payload_offset
        displacement, count = struct.unpack_from("<qQ", memory, at)
        old = tree.field(obj, field)["text"]
        new = model.replace("/", "\\")
        data = new.encode("utf-8")
        assert len(data) <= count, (family, age, old, new, count)
        start = at + displacement
        assert bytes(memory[start:start + count]).decode("utf-8") == old
        memory[start:start + count] = data + b"\0" * (count - len(data))
        struct.pack_into("<Q", memory, at + 8, len(data))
        transform = obj["fields"]["m_transform"]
        assert int(transform.get("BaseSize")) == 40
        t_at = obj["offset"] + int(transform.get("Offset")) - tree.memory.payload_offset
        old_transform = bytes(memory[t_at:t_at + 40]).hex()
        memory[t_at:t_at + 40] = struct.pack("<10f", 0, 0, 0, 1, 0, 0, 0, 1, 1, 1)
        changes.append({"object_id": obj["id"], "from": old, "to": new, "old_transform": old_transform})
    output = rc.rebuild(tree.document, lambda chunk: bytes(memory) if chunk.offset == tree.memory.offset else None)
    final_path = INT / f"{family}_age{age:02}_static.bin"
    final_path.write_bytes(output)
    final = NativeTree(final_path)
    assert len(final.objects) == len(tree.objects)
    for obj, model in zip(stock, parts):
        target = final.objects[obj["id"]]
        assert final.field(target, target["fields"]["m_blueprint"])["text"] == model.replace("/", "\\")
    for before, after in zip(rc.walk(tree.document.roots), rc.walk(final.document.roots)):
        if before.offset != tree.memory.offset and not before.children:
            assert before.payload == after.payload
    return output, changes


def clear_marrakech_stalls(encoded, age):
    """Move the eight inherited bazaar stalls outside the remodeled kasbah.

    The source AABB audit measures the east-side overlap clearing with +1.85m
    world X and the west side with -2.45m.  Native stamp X has the opposite
    sign after the model/stamp coordinate conversion, hence the deltas below.
    The outer tents, parade gate, object identities and every non-transform
    field remain untouched.
    """
    path = INT / f"marrakech_age{age:02}_preclear.bin"
    path.write_bytes(encoded)
    tree = NativeTree(path)
    east = {741798391448930604, 15543520507527987118, 16140867069943257980, 9264055861527722079}
    west = {7354401244879200629, 2636269912888673832, 15069090344078771042, 12935766383558563878}
    selected = {**{item: -1.85 for item in east}, **{item: 2.45 for item in west}}
    memory = bytearray(tree.memory.payload)
    changes = []
    for object_id, native_dx in selected.items():
        obj = tree.objects[object_id]
        assert obj["type"] == "VisualStampBlueprint"
        model = tree.field(obj, obj["fields"]["m_blueprint"])["text"]
        assert "mal_fl3b_stall_" in model, (object_id, model)
        transform = obj["fields"]["m_transform"]
        assert int(transform.get("BaseSize")) == 40
        at = obj["offset"] + int(transform.get("Offset")) - tree.memory.payload_offset
        before = struct.unpack_from("<10f", memory, at)
        after = list(before)
        after[4] += native_dx
        struct.pack_into("<10f", memory, at, *after)
        changes.append({"object_id": object_id, "model": model, "world_x_delta_m": -native_dx,
                        "old_transform": list(before), "new_transform": after})
    output = rc.rebuild(tree.document, lambda chunk: bytes(memory) if chunk.offset == tree.memory.offset else None)
    final_path = INT / f"marrakech_age{age:02}_cleared.bin"
    final_path.write_bytes(output)
    final = NativeTree(final_path)
    assert len(final.objects) == len(tree.objects)
    for row in changes:
        target = final.objects[row["object_id"]]
        actual = struct.unpack("<10f", bytes.fromhex(final.field(target, target["fields"]["m_transform"])["raw"]))
        assert list(actual) == row["new_transform"]
    for before_chunk, after_chunk in zip(rc.walk(tree.document.roots), rc.walk(final.document.roots)):
        if before_chunk.offset != tree.memory.offset and not before_chunk.children:
            assert before_chunk.payload == after_chunk.payload
    return output, changes


def main_model(family, age):
    rows = read(OUT / "stock-stamp-models.json")
    row = next(x for x in rows if x["family"] == family and x["age"] == age)
    models = [x["model"] for x in row["visual_models"]]
    if family == "marrakech":
        hits = [x for x in models if "/landmark_3b/" in x]
    else:
        hits = [x for x in models if "/structures/" in x and "/debris/" not in x]
    assert len(hits) == 1, (family, age, hits)
    return hits[0]


def compose():
    assert sha(BASE.read_bytes()) == BASE_SHA
    specs = read(OUT / "binding-specs.json")["specs"]
    art = read(OUT / "native-art-payload-report.json")
    keys = read(OUT / "stamp-probe/native-model-key-table.json")["keys"]
    tier_root = OUT / "garrison-cook-readback"
    static_root = tier_root / "art/scenario/b031"
    assert len(specs) == len(art["models"]) == 13
    static_parts = {}
    for family, ages in {"market": (2, 3, 4), "tlemcen": (3, 4), "siege": (3, 4), "keep": (3, 4)}.items():
        for age in ages:
            short = {"market": f"m{age}", "tlemcen": f"tl{age}", "siege": f"sg{age}", "keep": f"kp{age}"}[family]
            folder = static_root / short
            static_parts[(family, age)] = sorted(p.with_suffix("").relative_to(tier_root).as_posix() for p in folder.glob("*.rgm"))
    assert all(static_parts.values()), static_parts
    expected = {m["private"] for m in art["models"]} | {p for parts in static_parts.values() for p in parts}
    assert {x.replace("\\", "/") for x in keys} == expected
    payloads = {}
    for row in art["payloads"]:
        raw = Path(row["file"]).read_bytes()
        assert sha(raw) == row["sha256"]
        save(row["member"], raw, payloads)
    for item in static_root.rglob("*"):
        if item.is_file():
            save(item.relative_to(tier_root).as_posix(), item.read_bytes(), payloads)
    stamp_report, tier_report = [], []
    for spec in specs:
        family, age = spec["family"], spec["age"]
        stamp_values = [v for path, v in spec["stock_stamp_fields"] if path.startswith("default/") and path.endswith("stamp_attachment/stamp")]
        assert len(stamp_values) == 1, (family, age, stamp_values)
        stock_name = stamp_values[0].replace("\\", "/")
        stock = ROOT / "output/shared_stock_cache/buildings_031/stamps" / (stock_name + ".bin")
        assert stock.is_file()
        tree = NativeTree(stock)
        model = next(x for x in art["models"] if x["family"] == family and x["age"] == age)
        mapping = {main_model(family, age): model["private"]}
        encoded, report = rebind(tree, mapping, keys)
        pre = INT / f"{family}_age{age:02}_prestatic.bin"
        pre.write_bytes(encoded)
        validate_stamp(stock, pre, mapping)
        parts = static_parts.get((family, age), [])
        encoded, inserts = inject_static(encoded, family, age, parts)
        prop_moves = []
        if family == "marrakech":
            encoded, prop_moves = clear_marrakech_stalls(encoded, age)
        assert b"b030\\aa" not in encoded, (family, age)
        save(spec["private_stamp"] + ".bin", encoded, payloads)
        stamp_report.append({"family": family, "age": age, "stock_sha256": sha(stock.read_bytes()),
                             "private_stamp": spec["private_stamp"], "private_sha256": sha(encoded),
                             "main_mapping": mapping, "editor_owned_reference": report,
                             "static_replacements": inserts, "art_only_prop_moves": prop_moves,
                             "objects": len(tree.objects)})
        original = rgd.read((OUT / "scoped-inputs" / spec["source_tier"]).read_bytes())
        doc = copy.deepcopy(original)
        allocated = rgd.read((tier_root / spec["private_tier"]).read_bytes())
        identity = rgd.find(allocated.nodes, "default/pbgid").value
        changes = []
        source_stamp = stock_name.replace("/", "\\").lower()
        for path, node in rgd.flatten(doc.nodes):
            if node.key == "pbgid":
                node.value = identity
            elif node.kind == "CString" and node.key == "stamp" and node.value.lower() == source_stamp:
                old = node.value
                node.value = spec["private_stamp"].replace("/", "\\")
                changes.append((path, old))
        assert len(changes) in (1, 2), (family, age, changes)
        restored = copy.deepcopy(doc)
        for path, node in rgd.flatten(restored.nodes):
            if node.key == "pbgid":
                node.value = rgd.find(original.nodes, path).value
            elif path in dict(changes):
                node.value = dict(changes)[path]
        assert semantics(restored.nodes) == semantics(original.nodes)
        save(spec["private_tier"], encode(doc), payloads)
        tier_report.append({"family": family, "age": age, "member": spec["private_tier"],
                            "pbgid": identity, "stamp_paths_changed": [x[0] for x in changes],
                            "other_fields": "identical to official source"})
        print("031_STAMP_AND_TIER", family, age, flush=True)
    actors = {}
    actor_report = []
    for member in sorted({s["actor"] for s in specs}):
        family = next(s["family"] for s in specs if s["actor"] == member)
        source = OUT / "scoped-inputs" / member
        before = rgd.read(source.read_bytes())
        if family in ("keep", "marrakech"):
            probe = OUT / "integration/probes" / member
            doc = rgd.read(probe.read_bytes())
            modified = ["tier_ext:age3 reference", "tier_ext:age4 visual-only group"]
        else:
            doc = copy.deepcopy(before)
            modified = []
            for spec in (s for s in specs if s["actor"] == member):
                refs = spec["baseline_actor_references"]
                assert len(refs) == 1
                path, old = refs[0]
                node = rgd.find(doc.nodes, path)
                assert node and node.value == old, (family, spec["age"], path, node.value if node else None, old)
                node.value = GUID + ":" + spec["derived_name"]
                modified.append(path)
            restored = copy.deepcopy(doc)
            for spec in (s for s in specs if s["actor"] == member):
                path, old = spec["baseline_actor_references"][0]
                rgd.find(restored.nodes, path).value = old
            assert semantics(restored.nodes) == semantics(before.nodes)
        save(member, encode(doc), payloads)
        actor_report.append({"member": member, "family": family, "visual_changes": modified,
                             "nonvisual_fields": "identical to 0.3.0"})
    assert len(stamp_report) == len(tier_report) == 13 and len(actor_report) == 6
    write(INT / "composition-report.json", {"status": "passed", "baseline_sha256": BASE_SHA,
          "native_stamps": stamp_report, "private_tiers": tier_report, "actors": actor_report,
          "static_parts": {f"{k[0]}_{k[1]}": v for k, v in static_parts.items()},
          "payloads": list(payloads.values()), "native_runtime": "pending"})
    print("BERBER_031_COMPOSITION_READY", len(payloads), "members")


def archive():
    report = read(INT / "composition-report.json")
    assert report["status"] == "passed" and sha(BASE.read_bytes()) == BASE_SHA
    payloads = report["payloads"]
    allowed = {row["member"] for row in payloads}
    assert len(allowed) == len(payloads)
    for alias, prefix in (("data", "art/"), ("attrib", "attrib/")):
        rows = [r for r in payloads if r["member"].startswith(prefix)]
        assert rows
        (INT / f"{alias}-members.txt").write_text("\n".join(r["member"] + "=" + r["file"] for r in rows) + "\n", encoding="utf-8")
    middle = INT / "media-candidate.sga"
    candidate = INT / "candidate/Berber_future_kingdom.sga"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    run(ARCH, "set-members", BASE, INT / "data-members.txt", middle, "--alias", "data")
    run(ARCH, "set-members", middle, INT / "attrib-members.txt", candidate, "--alias", "attrib")
    before = json.loads(run(ARCH, "list", BASE, "--verify"))
    after = json.loads(run(ARCH, "list", candidate, "--verify"))
    assert before["archive"]["verification"]["verified"] and after["archive"]["verification"]["verified"]
    assert after["archive"]["name"].replace("-", "").lower() == GUID
    old = {x["path"]: x for x in before["members"]}
    new = {x["path"]: x for x in after["members"]}
    assert set(new) == set(old) | allowed
    for member in old:
        if member not in allowed:
            assert old[member]["toc"] == new[member]["toc"], member
    readback = INT / "candidate-readback"
    run(ARCH, "unpack", candidate, "--output", readback)
    for row in payloads:
        assert sha((readback / row["member"]).read_bytes()) == row["sha256"]
    write(INT / "candidate-report.json", {"status": "candidate SGA verified; editor/release gates pending",
          "archive": str(candidate), "archive_sha256": sha(candidate.read_bytes()),
          "baseline_sha256": BASE_SHA, "project_guid": GUID, "member_count": len(new),
          "new_members": sorted(set(new) - set(old)), "allowlist": sorted(allowed),
          "unrelated_members_byte_preserved": True, "crc_sha1_verified": True, "native_runtime": "pending"})
    print("BERBER_031_CANDIDATE_READY", len(new), "members")


if __name__ == "__main__":
    globals()[sys.argv[1]]()
