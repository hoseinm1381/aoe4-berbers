"""Collect the isolated Tlemcen donor remixes for serialized integration."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1/tlemcen"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


native = json.loads((ART / "native-validation.json").read_text())["models"]
stamps = [r for r in json.loads((ROOT / "output/berber_update_0_3_1/stock-stamp-models.json").read_text()) if r["family"] == "tlemcen"]
specs = [r for r in json.loads((ROOT / "output/berber_update_0_3_1/binding-specs.json").read_text())["specs"] if r["family"] == "tlemcen"]
models = []
for item in native:
    age = item["age"]
    source = json.loads((ART / f"age0{age}-source-validation.json").read_text())
    stamp = next(r for r in stamps if r["age"] == age)
    spec = next(r for r in specs if r["age"] == age)
    principal = [v for v in stamp["visual_models"] if v["model"] == item["source_rgm"].removesuffix(".rgm")]
    assert len(principal) == 1
    request = Path(source["static_request"])
    assert request.exists()
    prep = ART / f"tlemcen-age0{age}-static-prepare.json"
    prepared = json.loads(prep.read_text()) if prep.exists() else None
    if prepared is not None: assert prepared["success"]
    models.append({"name": f"tlemcen_age0{age}", "family": "tlemcen", "age": age, "source": item["source_rgm"], "decoded": item["decoded"], "decoded_sha256": item["decoded_sha256"], "stock_geometry": item["stock_geometry"], "stock_geometry_sha256": item["stock_geometry_sha256"], "stock_material": item["stock_material"], "native_geometry": item["native_geometry"], "native_geometry_sha256": item["native_geometry_sha256"], "remix_projection": item["remix_projection"], "blend": source["blend"], "fbx_supplement": source["fbx"], "fbx_supplement_sha256": sha(source["fbx"]), "garrison_static_request": str(request), "garrison_static_request_sha256": sha(request), "garrison_static_prepare": str(prep) if prepared is not None else None, "garrison_static_workspace_manifest": prepared["manifest"] if prepared is not None else None, "static_model_logical_base": prepared["validation"]["asset"]["logical_base"] if prepared is not None else None, "stock_stamp": stamp["stamp"], "principal_visual_object_id": principal[0]["id"], "actor": spec["actor"], "private_tier": spec["private_tier"], "private_stamp": spec["private_stamp"], "animator_scale": 150, "world_bounds_at_animator_150": item["world_bounds_at_animator_150"], "native_owner_colour_materials": item["native_owner_colour_materials"], "native_contact": "source z=0 stays z=0; actor scale unchanged; lower embedded donor z remains below ground", "static_supplement": "One piece placed at healthy main visual's origin with identity transform; must Garrison-cook then wire ALL resulting model parts into the private stamp", "validation": source})
recipe = {"schema": "berber.native-building-remix/v3", "baseline_version": "0.3.0", "name": "Great Mosque of Tlemcen", "models": models, "isolated_garrison_mod_project_add_check": str(ROOT / "output/berber_update_0_3_1/tlemcen-static-compat/Mods/tlemcen_static_compat_031/mod-project.json"), "integration": "Use only verified native GEOB surgery and separately Garrison-cooked static supplement; do not bind raw FBX. Clone source tier/stamp privately; replace only healthy principal visual model, append cooked supplement part(s) at identical origin. Leave construction/damage/ruin/selector auxiliary refs and gameplay actor fields unchanged.", "status": "Blender/native source and static prepare/add validated; Garrison cook, tier binding, native game acceptance pending"}
(ART / "recipe.json").write_text(json.dumps(recipe, indent=2) + "\n")
print("TLEMCEN_RECIPE_READY", len(models))
