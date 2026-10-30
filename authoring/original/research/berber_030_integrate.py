"""Integrate the four Age II-IV families over the tested 0.2.7.1 SGA.

Explicit allowlist only: twelve private native stamps, twelve private tier
attachments, four visual actor references, twelve remixed native control
models and one three-part stock-derived Byzantine annex. No gameplay edits.
"""

import copy
import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_0"
INT = OUT / "integration"
PAYLOAD = INT / "payload"
BASE = ROOT / "output/berber_update_0_2_7_1/package/Berber_future_kingdom.sga"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
ARCH = EXT / "bin/sga-archiver.exe"
GUID = "1d3145e8f1b2427f8bb0067851fcf0f1"
sys.path[:0] = [str(ROOT / "research"), str(EXT)]
from garrison_shared import rgd, relic_chunky as rc
from economy_025_native_stamp import NativeTree
from building_026_native_rebind import rebind
from build_berber_update_0_2_5 import encode, semantics, validate_stamp


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run(args):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"failed {result.returncode}: {args}\n{result.stdout[-1000:]}\n{result.stderr[-2000:]}")
    return result.stdout


def save(member, raw, payloads):
    target = PAYLOAD / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    digest = sha(target)
    if member in payloads:
        assert payloads[member]["sha256"] == digest
    else:
        payloads[member] = {"member": member, "file": str(target), "sha256": digest, "bytes": len(raw)}


def inject_annex(encoded, age, annex_models):
    path = INT / f"market_age{age:02}_main-rebind.bin"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    tree = NativeTree(path)
    stalls = sorted((o for o in tree.objects.values() if o["type"] == "VisualStampBlueprint" and "mon_market_stall" in tree.field(o, o["fields"]["m_blueprint"])["text"]), key=lambda o: o["id"])
    assert len(stalls) >= 3, (age, len(stalls))
    selected = stalls[:3]
    memory = bytearray(tree.memory.payload)
    changes = []
    for obj, model in zip(selected, annex_models):
        field = obj["fields"]["m_blueprint"]
        assert field.get("FieldTypeName") == "util::ReflectString<StdTraits>"
        at = obj["offset"] + int(field.get("Offset")) - tree.memory.payload_offset
        displacement, count = struct.unpack_from("<qQ", memory, at)
        old = tree.field(obj, field)["text"]
        new = model.replace("/", "\\")
        data = new.encode("utf-8")
        assert len(data) <= count, (age, old, new, count)
        start = at + displacement
        assert bytes(memory[start:start + count]).decode("utf-8") == old
        memory[start:start + count] = data + b"\0" * (count - len(data))
        struct.pack_into("<Q", memory, at + 8, len(data))
        transform = obj["fields"]["m_transform"]
        assert int(transform.get("BaseSize")) == 40
        t_at = obj["offset"] + int(transform.get("Offset")) - tree.memory.payload_offset
        previous_transform = bytes(memory[t_at:t_at + 40]).hex()
        memory[t_at:t_at + 40] = struct.pack("<10f", 0, 0, 0, 1, 0, 0, 0, 1, 1, 1)
        changes.append({"object_id": obj["id"], "from": old, "to": new, "old_transform": previous_transform, "new_transform": "identity; geometry exported at final local placement"})
    output = rc.rebuild(tree.document, lambda chunk: bytes(memory) if chunk.offset == tree.memory.offset else None)
    final_path = INT / f"market_age{age:02}_annex-rebind.bin"
    final_path.write_bytes(output)
    final = NativeTree(final_path)
    assert len(final.objects) == len(tree.objects)
    for obj, model in zip(selected, annex_models):
        target = final.objects[obj["id"]]
        assert final.field(target, target["fields"]["m_blueprint"])["text"] == model.replace("/", "\\")
        assert final.field(target, target["fields"]["m_transform"])["raw"] == struct.pack("<10f", 0, 0, 0, 1, 0, 0, 0, 1, 1, 1).hex()
    for before, after in zip(rc.walk(tree.document.roots), rc.walk(final.document.roots)):
        if before.offset != tree.memory.offset and not before.children:
            assert before.payload == after.payload
    return output, changes


def compose():
    assert sha(BASE) == "6f2d9844e2a932bd4ae9e440d2e07720dfd6e0fe1c60e9b53b23cc0549cb8faf"
    specs = read(OUT / "binding-specs.json")["specs"]
    art = read(OUT / "native-art-payload-report.json")
    keys = read(OUT / "stamp-probe/native-model-key-table.json")["keys"]
    tier = OUT / "garrison-tier-cook-readback"
    annex_root = OUT / "annex-short-readback/art/scenario/b030/aa"
    annex_models = sorted(p.with_suffix("").relative_to(OUT / "annex-short-readback").as_posix() for p in annex_root.glob("*.rgm"))
    assert len(annex_models) == 3
    assert set(art["model_mapping"].values()) | set(annex_models) == {key.replace("\\", "/") for key in keys}
    payloads = {}
    for row in art["payloads"]:
        file = Path(row["file"])
        assert sha(file) == row["sha256"]
        save(row["member"], file.read_bytes(), payloads)
    for file in annex_root.iterdir():
        if file.is_file():
            member = file.relative_to(OUT / "annex-short-readback").as_posix()
            save(member, file.read_bytes(), payloads)
    reports = []
    for spec in specs:
        family, age = spec["family"], spec["age"]
        stock = ROOT / "output/shared_stock_cache/buildings_030/stamps" / (spec["stock_stamp"] + ".bin")
        tree = NativeTree(stock)
        model = next(x for x in art["models"] if x["family"] == family and x["age"] == age)
        mapping = {model["source"].removesuffix(".rgm"): model["private"]}
        encoded, native_report = rebind(tree, mapping, keys)
        before_extra = INT / f"{family}_age{age:02}_pre-annex.bin"
        before_extra.write_bytes(encoded)
        validate_stamp(stock, before_extra, mapping)
        annex_changes = []
        if family == "market":
            encoded, annex_changes = inject_annex(encoded, age, annex_models)
        save(spec["private_stamp"] + ".bin", encoded, payloads)
        reports.append({"family": family, "age": age, "stock_stamp": spec["stock_stamp"], "stock_sha256": sha(stock), "private_stamp": spec["private_stamp"], "private_sha256": hashlib.sha256(encoded).hexdigest(), "objects": len(tree.objects), "main_mapping": mapping, "editor_owned_reference": native_report, "byzantine_annex_parts": annex_changes})
        print("NATIVE_STAMP", family, age, flush=True)
    actors = {}
    actor_originals = {}
    attachment_report = []
    for spec in specs:
        family, age = spec["family"], spec["age"]
        original = rgd.read(Path(spec["source_tier_file"]).read_bytes())
        doc = copy.deepcopy(original)
        allocated = rgd.read((tier / spec["private_tier"]).read_bytes())
        identity = rgd.find(allocated.nodes, "default/pbgid").value
        changes = []
        for path, node in rgd.flatten(doc.nodes):
            if node.key == "pbgid":
                node.value = identity
            elif node.kind == "CString" and node.key == "stamp" and node.value.lower().replace("\\", "/") == f"art/stamps/civ_mal/mal_{family}_age_{age:02}".lower():
                old = node.value
                node.value = spec["private_stamp"].replace("/", "\\")
                changes.append({"path": path, "old": old, "new": node.value})
        assert len(changes) == 1, (family, age, changes)
        restored = copy.deepcopy(doc)
        for path, node in rgd.flatten(restored.nodes):
            if node.key == "pbgid":
                node.value = rgd.find(original.nodes, path).value
            elif path == changes[0]["path"]:
                node.value = changes[0]["old"]
        assert semantics(restored.nodes) == semantics(original.nodes)
        save(spec["private_tier"], encode(doc), payloads)
        attachment_report.append({"family": family, "age": age, "member": spec["private_tier"], "pbgid": identity, "changes": changes, "all_other_fields": "identical to official source"})
        member = spec["actor"]
        if member not in actors:
            actors[member] = rgd.read(Path(spec["actor_file"]).read_bytes())
            actor_originals[member] = copy.deepcopy(actors[member])
        old_name = Path(spec["source_tier"]).stem
        count = 0
        for path, node in rgd.flatten(actors[member].nodes):
            if node.kind == "CString" and node.key == "$PBGNAME" and node.value == old_name and "attachments" in path:
                node.value = GUID + ":" + spec["derived_name"]
                count += 1
        assert count > 0, (member, old_name)
    actor_report = []
    for member, doc in actors.items():
        original = actor_originals[member]
        restored = copy.deepcopy(doc)
        modified = []
        for path, node in rgd.flatten(restored.nodes):
            if node.kind == "CString" and node.key == "$PBGNAME" and node.value.startswith(GUID + ":"):
                match = next((s for s in specs if s["actor"] == member and node.value == GUID + ":" + s["derived_name"]), None)
                if match:
                    node.value = Path(match["source_tier"]).stem
                    modified.append(path)
        assert semantics(restored.nodes) == semantics(original.nodes)
        save(member, encode(doc), payloads)
        actor_report.append({"member": member, "visual_references_changed": modified, "all_other_fields": "identical to 0.2.7.1"})
    assert len(reports) == len(attachment_report) == 12 and len(actor_report) == 4
    write(INT / "composition-report.json", {"status": "passed", "baseline_sha256": sha(BASE), "native_stamps": reports, "private_tiers": attachment_report, "actors": actor_report, "annex_models": annex_models, "payloads": list(payloads.values()), "native_runtime": "pending"})
    print("BERBER_030_COMPOSITION_READY", len(payloads), "members")


def archive():
    report = read(INT / "composition-report.json")
    assert report["status"] == "passed"
    payloads = report["payloads"]
    allowed = {row["member"] for row in payloads}
    assert len(allowed) == len(payloads)
    for alias, prefix in (("data", "art/"), ("attrib", "attrib/")):
        rows = [r for r in payloads if r["member"].startswith(prefix)]
        assert rows
        path = INT / (alias + "-members.txt")
        path.write_text("\n".join(r["member"] + "=" + r["file"] for r in rows) + "\n", encoding="utf-8")
    intermediate = INT / "media-candidate.sga"
    candidate = INT / "candidate/Berber_future_kingdom.sga"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    run([ARCH, "set-members", BASE, INT / "data-members.txt", intermediate, "--alias", "data"])
    run([ARCH, "set-members", intermediate, INT / "attrib-members.txt", candidate, "--alias", "attrib"])
    old = json.loads(run([ARCH, "list", BASE, "--verify"]))
    new = json.loads(run([ARCH, "list", candidate, "--verify"]))
    assert old["archive"]["verification"]["verified"] and new["archive"]["verification"]["verified"]
    assert new["archive"]["name"].replace("-", "").lower() == GUID
    before = {x["path"]: x for x in old["members"]}
    after = {x["path"]: x for x in new["members"]}
    assert set(after) == set(before) | allowed
    for member in before:
        assert before[member]["toc"] == after[member]["toc"]
    run([ARCH, "unpack", candidate, "--output", INT / "candidate-readback"])
    for row in payloads:
        assert sha(INT / "candidate-readback" / row["member"]) == row["sha256"]
    write(INT / "candidate-report.json", {"status": "candidate SGA verified; editor and release gates pending", "archive": str(candidate), "archive_sha256": sha(candidate), "baseline_sha256": sha(BASE), "project_guid": GUID, "member_count": len(after), "new_members": sorted(set(after) - set(before)), "allowlist": sorted(allowed), "crc_sha1_verified": True, "native_runtime": "pending"})
    print("BERBER_030_CANDIDATE_READY", len(after), "members")


if __name__ == "__main__":
    globals()[sys.argv[1]]()
