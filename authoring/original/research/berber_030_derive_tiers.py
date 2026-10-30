"""Derive only the twelve Malian Age II-IV visual tier controls.

No actor or gameplay field changes occur here. Fresh private PBG identities
are allocated by the Garrison/Content Editor cook, then bound later.
"""

import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_0"
PROJECT = OUT / "garrison-library-clean/Mods/berber_buildings_030"
BASE = ROOT / "output/berber_update_0_2_7_1/package/Berber_future_kingdom.sga"
OFFICIAL = Path("E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga")
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
CORE = EXT / "bin/core/garrison-core.exe"
ARCH = EXT / "bin/sga-archiver.exe"
FAMILIES = {
    "market": ("building_econ_market_mal", "econ_market_mal", "econ_market", "abb_market"),
    "blacksmith": ("building_tech_unit_infantry_mal", "tech_unit_melee_mal", "tech_unit_melee", "abb_blacksmith"),
    "archery_range": ("building_unit_ranged_mal", "unit_ranged_mal", "unit_ranged", "abb_archery_range"),
    "stable": ("building_unit_cavalry_mal", "unit_cavalry_mal", "unit_cavalry", "abb_stable"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"command failed {result.returncode}: {args}\n{result.stderr[-1500:]}")


def extract(archive, member):
    destination = OUT / "scoped-inputs" / member
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        run([ARCH, "extract-member", archive, member, destination])
    return destination


def main():
    assert sha(BASE) == "6f2d9844e2a932bd4ae9e440d2e07720dfd6e0fe1c60e9b53b23cc0549cb8faf"
    record = json.loads((PROJECT / "mod-project.json").read_text(encoding="utf-8"))
    existing = {x["name"] for x in record.get("derived_blueprints", [])}
    specs = []
    for family, (actor, folder, prefix, donor) in FAMILIES.items():
        actor_member = f"attrib/ebps/races/malian/buildings/{actor}.rgd"
        baseline_actor = extract(BASE, actor_member)
        for age in (2, 3, 4):
            source = f"attachments/attachment_lists/civilizations/malian/buildings/{folder}/tier{age}_{prefix}_control_mal"
            member = "attrib/" + source + ".rgd"
            original = extract(OFFICIAL, member)
            name = f"{family}_age{age:02}_tier"
            if name not in existing:
                run([CORE, "mod-project", "derive", "--project", PROJECT, "--source", source, "--name", name])
                existing.add(name)
            specs.append({"family": family, "age": age, "actor": actor_member, "actor_file": str(baseline_actor), "actor_sha256": sha(baseline_actor), "source_tier": member, "source_tier_file": str(original), "source_tier_sha256": sha(original), "derived_name": name, "private_tier": f"attrib/attachments/attachment_lists/garrison/berber_buildings_030/{name}.rgd", "stock_stamp": f"art/stamps/civ_abbasid/{donor}_age_{age:02}", "private_stamp": f"art/stamps/garrison/berber_buildings_030/{family}_age{age:02}"})
            print("DERIVED_TIER", name, flush=True)
    assert len(specs) == 12
    (OUT / "binding-specs.json").write_text(json.dumps({"status": "source and private recipes prepared; cook required", "baseline_sha256": sha(BASE), "specs": specs}, indent=2) + "\n", encoding="utf-8")
    print("BERBER_030_TIER_RECIPES_READY", len(specs))


if __name__ == "__main__":
    main()
