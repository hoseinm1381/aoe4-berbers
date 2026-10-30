"""Tint official Byzantine masonry source textures for the market graft."""

import hashlib
import json
from pathlib import Path

from berber_030_prepare import PALETTE, tone


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "output/shared_stock_cache/buildings_030/4550424ff074a6ab50fd/decoded-static.json"
OUT = ROOT / "art/building_remix_0_3_0/market/annex_source"


def main():
    d = json.loads(CACHE.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for mat in d["material"]["materials"]:
        name = mat["name"]
        if name.endswith("_collection"):
            continue
        tex = next(t for block in mat["blocks"] for t in block.get("textures", []) if t["name"] == "albedoTex")
        source = next(x for x in d["textures"] if x.get("texture_name") == tex["texture_name"])
        path = Path(source["projection"]["path"])
        role = "stone" if name == "roof" else "brick"
        target = OUT / (name + "_byzantine_toned.png")
        tone(path, PALETTE[2][role], target)
        rows.append({"material": name, "stock_texture": tex["texture_name"], "stock_image": str(path), "stock_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "source_toned": str(target), "toned_sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    (OUT / "texture-provenance.json").write_text(json.dumps({"source_model": d["request"]["logical_path"], "materials": rows}, indent=2) + "\n", encoding="utf-8")
    print("ANNEX_TONED_STOCK_TEXTURES", len(rows))


if __name__ == "__main__":
    main()
