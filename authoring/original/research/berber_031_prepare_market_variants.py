"""Prepare scoped Market variant carriers in 0.3.1 Garrison project.

Reuses the retained 0.3.0 material source images and actual Abbasid donors;
the 0.3.1 geometry sources are supplied by the Market family author.
"""

import copy
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/building_remix_0_3_1"
OUT = ROOT / "output/berber_update_0_3_1"
PROJECT = OUT / "garrison-library/Mods/berber_buildings_031"
CORE = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/core/garrison-core.exe"


def run(*args):
    result = subprocess.run([str(CORE), *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{args}: {result.returncode}\n{result.stdout[-1000:]}\n{result.stderr[-2000:]}")


def main():
    prior = json.loads((ROOT / "art/building_remix_0_3_0/recipe.json").read_text(encoding="utf-8"))
    record = json.loads((PROJECT / "mod-project.json").read_text(encoding="utf-8"))
    existing = {x["name"] for x in record.get("model_variants", [])}
    original = [x for x in prior["models"] if x["family"] == "market"]
    assert len(original) == 3
    carrier_names = {edit["carrier"] for model in original for mat in model["materials"] for edit in mat["repaint"]}
    carriers = [c for c in prior["texture_carriers"] if c["name"] in carrier_names]
    assert set(c["name"] for c in carriers) == carrier_names
    carrier_source = original[0]["source"].removesuffix(".rgm")
    for c in carriers:
        if c["name"] not in existing:
            run("mod-project", "variant", "--project", PROJECT, "--source", carrier_source, "--name", c["name"])
            existing.add(c["name"])
        run("mod-project", "variant-set", "--project", PROJECT, "--name", c["name"], "--slot", "albedoTex", "--image", c["image"])
        print("CARRIER", c["name"], flush=True)
    models = []
    for old in original:
        model = copy.deepcopy(old)
        name = old["name"]
        if name not in existing:
            run("mod-project", "variant", "--project", PROJECT, "--source", model["source"].removesuffix(".rgm"), "--name", name)
            existing.add(name)
        model["native_geometry"] = str(ART / "market" / f"Berber_{name}_0_3_1.rrgeom")
        model["remix_projection"] = str(ART / "market" / f"Berber_{name}_0_3_1-projection.json")
        models.append(model)
        print("MARKET_VARIANT", name, flush=True)
    target = ART / "recipe.json"
    target.write_text(json.dumps({"schema": "berber.native-building-remix/v3", "status": "Market Garrison variants prepared; cook pending", "project": str(PROJECT), "baseline_version": "0.3.0", "models": models, "texture_carriers": carriers, "native_colour_policy": "Preserve stock dynamic owner colour slots"}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
