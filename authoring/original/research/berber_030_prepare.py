"""Prepare the twelve scoped native stock-model remixes in one Garrison project.

This stage creates editable palette sources and Garrison variant recipes only.
It never edits the 0.2.7.1 package or binds a civilization actor.
"""

import hashlib
import json
import os
import subprocess
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_0"
OUT = ROOT / "output/berber_update_0_3_0"
CACHE = ROOT / "output/shared_stock_cache/buildings_030"
PROJECT = OUT / "garrison-library-clean/Mods/berber_buildings_030"
CORE = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/core/garrison-core.exe"
DONORS = {
    "market": {2: "1ab6b9d2f7f10490f630", 3: "443d0fc1dd5ea4fd7ec1", 4: "aafbb12f25726ee3a0fb"},
    "blacksmith": {2: "4c1509af618cf11f44b9", 3: "1576a23e73464882d1ea", 4: "55a846a8b9e27ede22a6"},
    "archery_range": {2: "742bd610c37a22451656", 3: "404ea1e33574511e59af", 4: "69426240ccaab9ef6713"},
    "stable": {2: "cbc4024cabddca84fb1b", 3: "b0f38a2bd213553984a0", 4: "3d58842fdcc1f6f985e8"},
}
PALETTE = {
    2: {"brick": (158, 111, 76), "plaster": (180, 140, 100), "stone": (165, 143, 109), "trim": (145, 109, 70), "wood": (88, 56, 35), "fabric": (149, 116, 77), "shingle": (143, 103, 67), "building_kits": (146, 107, 75)},
    3: {"brick": (173, 139, 104), "plaster": (206, 183, 151), "stone": (185, 166, 134), "trim": (172, 136, 91), "wood": (93, 65, 42), "fabric": (157, 130, 93), "shingle": (165, 132, 90), "building_kits": (175, 143, 107)},
    4: {"brick": (192, 163, 125), "plaster": (226, 210, 181), "stone": (206, 190, 160), "trim": (199, 168, 112), "wood": (82, 59, 42), "fabric": (126, 137, 112), "shingle": (177, 148, 105), "building_kits": (200, 177, 139)},
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(label, args):
    result = subprocess.run([str(CORE), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{label}: {result.returncode}\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")


def tone(source, color, destination):
    image = Image.open(source).convert("RGBA")
    pixels = []
    for red, green, blue, alpha in image.getdata():
        luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
        detail = 0.68 + 0.40 * luminance
        pixels.append(tuple(min(255, round(channel * detail)) for channel in color) + (alpha,))
    image.putdata(pixels)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


def main():
    assert (PROJECT / "mod-project.json").is_file(), "Create the clean scoped Garrison project first"
    record = json.loads((PROJECT / "mod-project.json").read_text(encoding="utf-8"))
    assert not record.get("game_mode", {}).get("enabled", False)
    known = {item["name"] for item in record.get("model_variants", [])}
    first = json.loads((CACHE / DONORS["market"][2] / "decoded-static.json").read_text(encoding="utf-8"))
    carrier_source = first["request"]["logical_path"].removesuffix(".rgm")
    carriers = {}
    models = []
    for family, ages in DONORS.items():
        for age, key in ages.items():
            manifest = CACHE / key / "decoded-static.json"
            d = json.loads(manifest.read_text(encoding="utf-8"))
            source = d["request"]["logical_path"]
            name = f"{family}_age{age:02}"
            if name not in known:
                run("variant " + name, ["mod-project", "variant", "--project", PROJECT, "--source", source.removesuffix(".rgm"), "--name", name])
                known.add(name)
            materials = []
            for mat in d["material"]["materials"]:
                if mat["name"].endswith("_collection"):
                    continue
                slots = []
                preserved = []
                for block in mat["blocks"]:
                    for tex in block.get("textures", []):
                        slot = tex["name"]
                        semantic = tex.get("texture_name", "").lower()
                        if not slot.startswith("albedoTex") or slot == "albedoTexCharred":
                            continue
                        if "team" in semantic or "owner" in semantic or "debug" in semantic:
                            preserved.append({"slot": slot, "stock_texture": semantic})
                            continue
                        role = next((role for role in PALETTE[age] if "/" + role + "/" in semantic), None)
                        if not role:
                            continue
                        entry = next((x for x in d["textures"] if x.get("texture_name") == tex.get("texture_name")), None)
                        assert entry is not None, (name, semantic)
                        original = Path(entry["projection"]["path"])
                        identity = (sha(original), age, role)
                        if identity not in carriers:
                            carrier_name = "tone_" + hashlib.sha256(":".join(map(str, identity)).encode()).hexdigest()[:16]
                            image = ART / "textures" / f"{carrier_name}_{role}.png"
                            tone(original, PALETTE[age][role], image)
                            if carrier_name not in known:
                                run("carrier " + carrier_name, ["mod-project", "variant", "--project", PROJECT, "--source", carrier_source, "--name", carrier_name])
                                known.add(carrier_name)
                            run("carrier texture " + carrier_name, ["mod-project", "variant-set", "--project", PROJECT, "--name", carrier_name, "--slot", "albedoTex", "--image", image])
                            carriers[identity] = {"name": carrier_name, "source": str(original), "source_sha256": identity[0], "image": str(image), "image_sha256": sha(image), "role": role, "age": age}
                        slots.append({"slot": slot, "carrier": carriers[identity]["name"], "role": role, "source": semantic})
                materials.append({"name": mat["name"], "repaint": slots, "owner_colour_slots_preserved": preserved})
            assert any(m["repaint"] for m in materials), name
            models.append({"name": name, "family": family, "age": age, "source": source, "decoded": str(manifest), "decoded_sha256": sha(manifest), "stock_geometry": d["geometry"]["source"]["path"], "stock_material": d["material"]["source"]["path"], "materials": materials})
            print("PREPARED", name, flush=True)
    recipe = {"schema": "berber.native-building-remix/v2", "status": "variants and palette carriers prepared; no cooked or bound release", "project": str(PROJECT), "baseline_version": "0.2.7.1", "models": models, "texture_carriers": list(carriers.values()), "native_colour_policy": "Do not change stock debug/team/owner mask and shader slots"}
    target = ART / "recipe.json"
    target.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    print("BERBER_030_PREPARED", len(models), "models", len(carriers), "carriers")


if __name__ == "__main__":
    main()
