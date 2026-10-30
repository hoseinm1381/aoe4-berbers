"""Prepare private donor variants and age palettes for the two 0.3.1 landmarks."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

from berber_030_prepare import PALETTE, tone

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1"
OUT = ROOT / "output/berber_update_0_3_1"
PROJECT = OUT / "garrison-library/Mods/berber_buildings_031"
CORE = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/core/garrison-core.exe"
CARRIER_SOURCE = "art/civilizations/abbasids/structures/market/abb_market_control_age02/abb_market_control_age02"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    r = subprocess.run([str(CORE), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"{args}: {r.returncode}\n{r.stdout[-800:]}\n{r.stderr[-2000:]}")


def family_models(family):
    record = json.loads((ART / family / "recipe.json").read_text(encoding="utf-8"))
    if family == "tlemcen":
        return record["models"]
    donor = ROOT / record["shared_decode"]
    decoded = json.loads(donor.read_text(encoding="utf-8"))
    result = []
    for variant in record["variants"]:
        result.append({
            "name": variant["name"], "family": family, "age": variant["age"],
            "source": record["new_main_donor"] + ".rgm", "decoded": str(donor),
            "decoded_sha256": sha(donor),
            "stock_geometry": decoded["geometry"]["source"]["path"],
            "stock_material": decoded["material"]["source"]["path"],
            "native_geometry": str(ROOT / variant["native_geometry"]),
            "remix_projection": str(ROOT / variant["projection"]),
        })
    return result


def main():
    recipe_path = ART / "recipe.json"
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    variants = json.loads((PROJECT / "mod-project.json").read_text(encoding="utf-8"))
    existing = {v["name"] for v in variants.get("model_variants", [])}
    carrier_map = {(c["source_sha256"], c["age"], c["role"]): c for c in recipe["texture_carriers"]}
    for family in ("marrakech", "tlemcen"):
        for model in family_models(family):
            name, age = model["name"], model["age"]
            if name not in existing:
                run("mod-project", "variant", "--project", PROJECT, "--source", model["source"].removesuffix(".rgm"), "--name", name)
                existing.add(name)
            decoded = json.loads(Path(model["decoded"]).read_text(encoding="utf-8"))
            materials = []
            for mat in decoded["material"]["materials"]:
                if mat["name"].endswith("_collection"):
                    continue
                repaint, preserved = [], []
                for block in mat["blocks"]:
                    for tex in block.get("textures", []):
                        slot = tex["name"]
                        semantic = tex.get("texture_name", "").lower()
                        if not slot.startswith("albedoTex") or slot == "albedoTexCharred":
                            continue
                        if any(x in semantic for x in ("team", "owner", "debug")):
                            preserved.append({"slot": slot, "stock_texture": semantic})
                            continue
                        role = next((r for r in PALETTE[age] if "/" + r + "/" in semantic), None)
                        if role is None and "/grout/" in semantic:
                            role = "plaster"
                        if role is None:
                            continue
                        tex_row = next((x for x in decoded["textures"] if x.get("texture_name") == tex.get("texture_name")), None)
                        assert tex_row, (name, semantic)
                        original = Path(tex_row["projection"]["path"])
                        identity = (sha(original), age, role)
                        if identity not in carrier_map:
                            carrier_name = "tone_" + hashlib.sha256(":".join(map(str, identity)).encode()).hexdigest()[:16]
                            image = ART / "textures" / f"{carrier_name}_{role}.png"
                            tone(original, PALETTE[age][role], image)
                            if carrier_name not in existing:
                                run("mod-project", "variant", "--project", PROJECT, "--source", CARRIER_SOURCE, "--name", carrier_name)
                                existing.add(carrier_name)
                            run("mod-project", "variant-set", "--project", PROJECT, "--name", carrier_name, "--slot", "albedoTex", "--image", image)
                            carrier_map[identity] = {"name": carrier_name, "source": str(original), "source_sha256": identity[0], "image": str(image), "image_sha256": sha(image), "role": role, "age": age}
                        repaint.append({"slot": slot, "carrier": carrier_map[identity]["name"], "role": role, "source": semantic})
                materials.append({"name": mat["name"], "repaint": repaint, "owner_colour_slots_preserved": preserved})
            assert any(m["repaint"] for m in materials)
            model["materials"] = materials
            recipe["models"].append(model)
            print("LANDMARK_VARIANT", name, "materials", len(materials), flush=True)
    assert len(recipe["models"]) == 7
    recipe["texture_carriers"] = list(carrier_map.values())
    recipe_path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
