"""Compose 13 cooked private donor models with verified 0.3.1 geometry/materials.

The Garrison cook supplies native RGM/RGO identities and texture carriers.
Only healthy GEOB geometry and age-scoped albedo references are substituted;
stock UV, topology, damage shader fields and native owner colour remain.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1"
OUT = ROOT / "output/berber_update_0_3_1"
READBACK = OUT / "garrison-cook-readback"
PAYLOAD = OUT / "native-art-payload"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path[:0] = [str(EXT), str(EXT.parent), str(ROOT / "art/economy_remix_0_2_5/mill")]
from garrison_shared import model_variants as mv, relic_chunky as rc
import garrison_shared

sys.modules["garrison.garrison_shared"] = garrison_shared
from native_materials import rewrite_scoped


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(member, raw, entries):
    target = PAYLOAD / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    digest = sha(raw)
    if member in entries:
        assert entries[member]["sha256"] == digest
    else:
        entries[member] = {"member": member, "file": str(target), "sha256": digest, "bytes": len(raw)}


def one_chunk(chunk):
    return rc.pack_document([rc.pack_chunk(chunk.kind, chunk.tag, chunk.payload, name=chunk.name, version=chunk.version)])


def main():
    recipe = json.loads((ART / "recipe.json").read_text(encoding="utf-8"))
    assert len(recipe["models"]) == 13
    project = Path(recipe["project"])
    record = json.loads((project / "mod-project.json").read_text(encoding="utf-8"))
    cook = record["cooks"][-1]
    assert not cook["live_reload"]
    assert sha(Path(cook["archive"]).read_bytes()) == cook["sha256"]
    key = project.name
    entries, models = {}, []
    for model in recipe["models"]:
        decoded = json.loads(Path(model["decoded"]).read_text(encoding="utf-8"))
        assert sha(Path(model["decoded"]).read_bytes()) == model["decoded_sha256"]
        stock_geometry = Path(model["stock_geometry"]).read_bytes()
        assert sha(stock_geometry) == decoded["resources"]["geometry"]["sha256"]
        raw_material = Path(model["stock_material"]).read_bytes()
        edits, changed_slots = {}, {}
        for mat in model["materials"]:
            texture_edits = {}
            for edit in mat["repaint"]:
                member = mv.texture_member(key, edit["carrier"], "albedoTex").replace("\\", "/") + ".rrtex"
                data = (READBACK / member).read_bytes()
                save(member, data, entries)
                texture_edits[edit["slot"]] = member
            edits[mat["name"]] = {"textures": texture_edits, "parameters": {}}
            changed_slots[mat["name"]] = sorted(texture_edits)
        remixed_material = rewrite_scoped(raw_material, edits)
        before_roots = {c.decoded_name: c for c in rc.parse(raw_material).roots}
        after_roots = {c.decoded_name: c for c in rc.parse(remixed_material).roots}
        assert set(before_roots) == set(after_roots)
        for name, original in before_roots.items():
            bare = name.removesuffix("_collection")
            old = mv.material_slots(one_chunk(original))
            new = mv.material_slots(one_chunk(after_roots[name]))
            for slot, value in old["textures"].items():
                if slot not in edits.get(bare, {}).get("textures", {}):
                    assert new["textures"][slot] == value, (model["name"], name, slot)
            for parameter, value in old["parameters"].items():
                assert new["parameters"][parameter] == value
        stem = mv.art_stem(key, model["name"]).replace("\\", "/")
        for suffix in (".rgm", ".rgo"):
            save(stem + suffix, (READBACK / (stem + suffix)).read_bytes(), entries)
        cooked_geometry = (READBACK / (stem + ".rrgeom")).read_bytes()
        assert sha(cooked_geometry) == sha(stock_geometry)
        native_geometry = Path(model["native_geometry"]).read_bytes()
        assert native_geometry != stock_geometry, model["name"]
        save(stem + ".rrgeom", native_geometry, entries)
        save(stem + ".rrmaterial", remixed_material, entries)
        models.append({"name": model["name"], "family": model["family"], "age": model["age"],
                       "source": model["source"], "private": stem,
                       "geometry_modified": True, "material_changed_slots": changed_slots,
                       "stock_owner_colour_nonrepaint_slots_preserved": True,
                       "stock_geometry_sha256": sha(stock_geometry), "native_geometry_sha256": sha(native_geometry)})
        print("NATIVE_ART_COMPOSED", model["name"], flush=True)
    report = {"status": "passed; art payload only, not bound", "cook": cook, "models": models,
              "model_mapping_by_variant": {x["name"]: x["private"] for x in models},
              "payloads": list(entries.values()), "native_runtime": "pending user test"}
    (OUT / "native-art-payload-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("BERBER_031_NATIVE_ART_READY", len(models), len(entries))


if __name__ == "__main__":
    main()
