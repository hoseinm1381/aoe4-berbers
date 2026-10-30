"""Prepare scoped 0.3.1 private attachment identities and inspect stock stamps.

This does not change a civilization actor or the release SGA. The two Age IV
tiers absent from the baseline Keep and Marrakech actors are marked explicitly
for later visual-only tier wiring.
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_1"
BASE = ROOT / "output/berber_update_0_3_0/package/Berber_future_kingdom.sga"
OFFICIAL = Path("E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga")
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
ARCH = EXT / "bin/sga-archiver.exe"
CORE = EXT / "bin/core/garrison-core.exe"
PROJECT = OUT / "garrison-library/Mods/berber_buildings_031"
sys.path.insert(0, str(EXT))
from garrison_shared import rgd


FAMILIES = {
    "market": ("building_econ_market_mal", "civilizations/malian/buildings/econ_market_mal/tier{age}_econ_market_control_mal", (2, 3, 4)),
    "mosque": ("building_unit_religious_mal", "civilizations/malian/buildings/unit_religious_mal/tier{age}_unit_religious_control_mal", (3, 4)),
    "siege": ("building_unit_siege_mal", "civilizations/malian/buildings/unit_siege_mal/tier{age}_unit_siege_control_mal", (3, 4)),
    "keep": ("building_defense_keep_mal", "civilizations/malian/buildings/defense_keep_mal/tier3_keep_control_mal", (3, 4)),
    "tlemcen": ("landmarks/great_mosque_of_tlemcen/building_landmark_age2_landmarkc_control_mal", "civilizations/sultanate/buildings/unit_religious_sul/tier{age}_unit_religious_control_sul", (3, 4)),
    "marrakech": ("landmarks/marrakech/building_landmark_age2_landmarkd_control_mal", "civilizations/malian/buildings/mal_landmark_b_03", (3, 4)),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    r = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"{r.returncode} {args}\n{r.stdout[-1000:]}\n{r.stderr[-2000:]}")
    return r.stdout


def extract(archive, member):
    target = OUT / "scoped-inputs" / member
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        run(ARCH, "extract-member", archive, member, target)
    return target


def values(path, key):
    return [(p, n.value) for p, n in rgd.flatten(rgd.read(path.read_bytes()).nodes) if n.key == key]


def main():
    assert sha(BASE) == "33cbb2d3d60914da49e893fe0f19c37dc6cb9aaaa120c0d00613a26a2ebbe5af"
    assert PROJECT.joinpath("mod-project.json").is_file()
    existing = {x["name"] for x in json.loads(PROJECT.joinpath("mod-project.json").read_text(encoding="utf-8")).get("derived_blueprints", [])}
    specs = []
    for family, (actor, tier_template, ages) in FAMILIES.items():
        actor_member = f"attrib/ebps/races/malian/buildings/{actor}.rgd"
        actor_file = extract(BASE, actor_member)
        actor_refs = values(actor_file, "$PBGNAME")
        for age in ages:
            source = "attachments/attachment_lists/" + tier_template.format(age=age)
            member = f"attrib/{source}.rgd"
            tier_file = extract(OFFICIAL, member)
            stamps = values(tier_file, "stamp")
            # The 0.3.0 archive already contains market_ageNN_tier names. Use
            # release-qualified identities so both releases can coexist while
            # the superseded 0.3.0 media remains recoverable in the archive.
            name = f"v031_{family}_age{age:02}_tier"
            if name not in existing:
                run(CORE, "mod-project", "derive", "--project", PROJECT, "--source", source, "--name", name)
                existing.add(name)
            current_refs = [(p, v) for p, v in actor_refs if v == Path(source).name]
            if family == "market":
                old = f"market_age{age:02}_tier"
                current_refs = [(p, v) for p, v in actor_refs if v == "1d3145e8f1b2427f8bb0067851fcf0f1:" + old]
            specs.append({
                "family": family, "age": age, "actor": actor_member,
                "actor_sha256": sha(actor_file), "source_tier": member,
                "source_tier_sha256": sha(tier_file), "derived_name": name,
                "private_tier": f"attrib/attachments/attachment_lists/garrison/berber_buildings_031/{name}.rgd",
                "private_stamp": f"art/stamps/garrison/berber_buildings_031/{family}_age{age:02}",
                "stock_stamp_fields": stamps, "baseline_actor_references": current_refs,
                "age4_tier_needs_new_actor_group": family in ("keep", "marrakech") and age == 4,
            })
            print("PREPARED", family, age, "stamps", stamps, "refs", len(current_refs), flush=True)
    assert len(specs) == 13
    output = OUT / "binding-specs.json"
    output.write_text(json.dumps({"baseline_sha256": sha(BASE), "specs": specs}, indent=2) + "\n", encoding="utf-8")
    print("BERBER_031_BINDING_RECIPES", len(specs))


if __name__ == "__main__":
    main()
