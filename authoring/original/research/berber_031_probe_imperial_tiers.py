"""Probe art-only Age IV tier groups missing from Keep and Marrakech.

Creates isolated actor RGDs for semantic inspection. These are not release
payloads until the private tier identities, native cook, and full checks pass.
"""

import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_3_1"
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import rgd

GUID = "1d3145e8f1b2427f8bb0067851fcf0f1"


def sem(nodes):
    return [(n.key, n.hash, n.kind, sem(n.value) if isinstance(n.value, list) else n.value) for n in nodes]


def value(nodes, path):
    item = rgd.find(nodes, path)
    assert item is not None, path
    return item


def mutate(member, family):
    source = OUT / "scoped-inputs" / member
    doc = rgd.read(source.read_bytes())
    before = copy.deepcopy(doc)
    group_list = value(doc.nodes, "default/tier_ext/tier_group_list")
    main_group = group_list.value[0]
    assert len(main_group.value) == 1, (family, len(main_group.value))
    castle = main_group.value[0]
    existing = value(castle.value, "attachments/$PBGNAME").value
    assert existing in ("tier3_keep_control_mal", "mal_landmark_b_03"), existing
    value(castle.value, "attachments/$PBGNAME").value = GUID + f":v031_{family}_age03_tier"
    imperial = copy.deepcopy(castle)
    value(imperial.value, "attachments/$PBGNAME").value = GUID + f":v031_{family}_age04_tier"
    value(imperial.value, "statetree_tier_requirements_pbg/$PBGNAME").value = "imperial_age"
    value(imperial.value, "statetree_tier_requirements_pbg/$PBGMAP").value = "upgrade"
    main_group.value.append(imperial)
    assert len(group_list.value) == len(value(before.nodes, "default/tier_ext/tier_group_list").value)
    for candidate in (doc, before):
        value(candidate.nodes, "default/tier_ext/tier_group_list").value = []
    assert sem(doc.nodes) == sem(before.nodes), family
    # Restore the modified group for serialization after proving other fields.
    doc = rgd.read(source.read_bytes())
    group_list = value(doc.nodes, "default/tier_ext/tier_group_list")
    castle = group_list.value[0].value[0]
    value(castle.value, "attachments/$PBGNAME").value = GUID + f":v031_{family}_age03_tier"
    imperial = copy.deepcopy(castle)
    value(imperial.value, "attachments/$PBGNAME").value = GUID + f":v031_{family}_age04_tier"
    value(imperial.value, "statetree_tier_requirements_pbg/$PBGNAME").value = "imperial_age"
    value(imperial.value, "statetree_tier_requirements_pbg/$PBGMAP").value = "upgrade"
    group_list.value[0].value.append(imperial)
    raw = rgd.write(doc)
    reread = rgd.read(raw)
    assert sem(reread.nodes) == sem(doc.nodes)
    target = OUT / "integration/probes" / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {"family": family, "member": member, "baseline_ref": existing,
            "age3_ref": GUID + f":v031_{family}_age03_tier",
            "age4_ref": GUID + f":v031_{family}_age04_tier",
            "age4_requirement": "upgrade:imperial_age", "nonvisual_actor_fields": "identical",
            "roundtrip": "passed", "file": str(target)}


def main():
    specs = json.loads((OUT / "binding-specs.json").read_text(encoding="utf-8"))["specs"]
    results = []
    for family in ("keep", "marrakech"):
        member = next(s["actor"] for s in specs if s["family"] == family)
        results.append(mutate(member, family))
        print("IMPERIAL_TIER_PROBE", family, flush=True)
    (OUT / "imperial-tier-probe.json").write_text(json.dumps({"status": "probe only", "results": results}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
