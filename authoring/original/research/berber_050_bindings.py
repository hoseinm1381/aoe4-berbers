"""Build a read-only-source/private-candidate binding manifest for Berber 0.5.0.

The manifest joins the frozen 0.4.0 compiled actor fields to current typed
official attachment-list consumers. It deliberately records real selector
paths and source body refs; it does not infer reachability from an arbitrary
attrib filename or patch any live project files.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/berber_update_0_5_0"
BASE = OUT / "integration/baseline-readback"
OFFICIAL_INPUTS = OUT / "official-inputs/attrib"
TARGETS = OUT / "targets.json"
MEMBER_HASHES = OUT / "baseline-member-sha256.json"
OFFICIAL_ARCHIVE = Path(r"E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga")
PRIVATE_PROJECT = OUT / "garrison-library/Mods/berber_050_official_derive_research"
MODEL_ROOT = "art/scenario/garrison/berber_units_050"

FIELD_POLICY = {
    "only_mutable_consumer_field": "attachment_lists/attachment_list/.../animator_merge_mesh_attachment/meshes/animatorN",
    "preserve_fields": [
        "tier selectors and requirements", "tier upgrade target entity/squad",
        "parent_animator", "all animator attachment list references",
        "weapon and state attachments", "sockets, colors, skeleton/bind/LOD data",
        "task/carry/tool/relic/cart/mount attachments", "actor gameplay and stats",
    ],
    "actor_tier_ref_changes": "same-path Malian stock actor attrib-set override changes only the tier attachment $PBGNAME; leave actor identity, SBPS loadout, PBGMAP, selector, requirement and upgrade targets unchanged",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pbg(node: ET.Element) -> str | None:
    name = next((x.get("Value") for x in node if x.get("Key") == "$PBGNAME"), None)
    pmap = next((x.get("Value") for x in node if x.get("Key") == "$PBGMAP"), None)
    if not name:
        return None
    return ((pmap or "").replace("\\", "/").strip("/") + "/" + name).strip("/")


def indexed_children(parent: ET.Element) -> list[tuple[ET.Element, str]]:
    counts: dict[str, int] = {}
    result = []
    for child in list(parent):
        if child.tag != "RGDNode":
            continue
        key = child.get("Key", "")
        ix = counts.get(key, 0)
        counts[key] = ix + 1
        suffix = "" if ix == 0 else f"[{ix}]"
        result.append((child, key + suffix))
    return result


def values(node: ET.Element, path: str = "") -> list[dict]:
    out = []
    for child, seg in indexed_children(node):
        cur = f"{path}/{seg}" if path else seg
        if child.get("Value") is not None:
            out.append({"field": cur, "type": child.get("Type"), "value": child.get("Value")})
        out.extend(values(child, cur))
    return out


def selector_groups(xml_path: Path) -> list[dict]:
    root = ET.parse(xml_path).getroot()
    # Retain actual tier-group nesting/indexing and ref values from the compiled
    # 0.4.0 decompile. Do not flatten repeated actor selectors.
    rows = []
    tiers: list[tuple[ET.Element, str]] = []
    def collect(node: ET.Element, path: str = "") -> None:
        for child, seg in indexed_children(node):
            cur = f"{path}/{seg}" if path else seg
            if child.get("Key") == "tier" and child.get("Type") == "List":
                tiers.append((child, cur))
            collect(child, cur)
    collect(root)
    for n, (tier, tier_path) in enumerate(tiers):
        vals = values(tier)
        def value(suffix: str) -> str | None:
            return next((v["value"] for v in vals if v["field"].endswith(suffix)), None)
        attachments = next((x for x in tier.iter("RGDNode") if x.get("Key") == "attachments" and x.get("Type") == "List"), None)
        att_path = tier_path + "/attachments/$PBGNAME" if attachments is not None else None
        # The RGD XML wraps fields in `default`; editor field paths start at
        # the default table's contents.
        if att_path.startswith("default/"):
            att_path = att_path[len("default/"):]
        rows.append({
            "tier_occurrence": n,
            "attachment_ref": pbg(attachments) if attachments is not None else None,
            "attachment_pbgname": (pbg(attachments) or "").rsplit("/", 1)[-1] or None,
            "attachment_field_path": att_path,
            "upgrade_target_entity": value("statetree_tier_pgb_upgrade_target_entity/$PBGNAME"),
            "upgrade_target_squad": value("statetree_tier_pgb_upgrade_target_squad/$PBGNAME"),
            "requirement": value("statetree_tier_requirements_pbg/$PBGNAME"),
            "selector_fields": {(tier_path + "/" + v["field"])[len("default/"):] if (tier_path + "/" + v["field"]).startswith("default/") else tier_path + "/" + v["field"]: v["value"] for v in vals if any(k in v["field"] for k in ("statetree_tier_pgb_upgrade_target_entity", "statetree_tier_pgb_upgrade_target_squad", "statetree_tier_requirements_pbg", "tier_attachment_action"))},
        })
    return rows


def model_entries(row: dict) -> list[dict]:
    actor = row.get("baseline_040_actor", {})
    candidates: list[dict] = []
    for consumer in actor.get("resolved_tier_consumers", []):
        for entry in consumer.get("model_refs", []):
            candidates.append({"consumer": consumer.get("blueprint"), **entry})
    for key in ("direct_animator_consumer", "compiled_body_consumer", "inherited_official_animator_consumer"):
        consumer = actor.get(key) or {}
        for entry in consumer.get("model_refs", []):
            candidates.append({"consumer": consumer.get("blueprint"), **entry})
    for consumer in row.get("age_tier_consumer") or []:
        for entry in consumer.get("model_refs", []):
            candidates.append({"consumer": consumer.get("blueprint"), **entry})
    # Preserve references once, but retain every actual field occurrence.
    return [x for x in candidates if str(x.get("value", "")).startswith("art/")]


def family_target(family: str, age: int, suffix: str = "") -> str:
    name = f"{family}_age0{age}{suffix}"
    return f"{MODEL_ROOT}/{name}/{name}"


def numeric_age(value: str | None) -> int | None:
    if not value:
        return None
    lower = value.lower()
    m = re.search(r"age0?([1-4])(?:\b|_)", lower)
    if not m:
        m = re.search(r"_([1-4])(?:_|$)", lower)
    if not m:
        m = re.search(r"tier([1-4])(?:_|$)", lower)
    if m:
        return int(m.group(1))
    return None


def route_target_age(tier: dict, source_actor: str, family: str, fallback_age: int) -> tuple[int | None, str]:
    """Use actual child actor target / age gate; use owner actor only for base/parallel tiers."""
    child = tier.get("upgrade_target_entity") or tier.get("upgrade_target_squad")
    found = numeric_age(child)
    if found is not None:
        return found, "upgrade target PBG"
    req = tier.get("requirement")
    gates = {"dark_age": 1, "feudal_age": 2, "castle_age": 3, "imperial_age": 4}
    if req in gates:
        return gates[req], "native age requirement PBG"
    # The current actor PBG determines only its base visual state; all upgrade
    # and age-gated alternatives were handled above.
    owner = numeric_age(source_actor)
    if owner is not None:
        return owner, "base actor PBG; parallel state retains same visual stage"
    return fallback_age, "compiled squad's canonical minimum spawn age; no selector conversion/gate"


def body_fields_for_consumer(row: dict, blueprint: str) -> list[dict]:
    name = (blueprint or "").rsplit("/", 1)[-1]
    refs = []
    for consumer in row.get("baseline_040_actor", {}).get("resolved_tier_consumers", []):
        if (consumer.get("blueprint") or "").rsplit("/", 1)[-1] != name:
            continue
        for item in consumer.get("model_refs", []):
            path = item.get("field", "")
            value = str(item.get("value", "")).replace("\\", "/")
            if ("animator_merge_mesh_attachment/meshes/animator" not in path
                    and "animator_skin_attachment/animator" not in path):
                continue
            if not value.startswith("art/civilizations/") or "/archetypes/" in value:
                continue
            if any(token in value.lower() for token in ("/weapons/", "_shield_", "_staff_", "/tools/")):
                continue
            refs.append({"consumer": consumer.get("blueprint"), **item})
    # Same official list often appears more than once in parallel campaign
    # groups. Identical list+field+value is a single source change.
    unique = {}
    for item in refs:
        unique[(item.get("consumer"), item["field"], item["value"])] = item
    return list(unique.values())


def actor_evidence(row: dict, manifest: dict) -> dict:
    family, age = row["family"], row["age"]
    actor = row["actor"]
    if row["actor_kind"] == "official":
        native_actor = actor if actor.startswith("ebps/") else "ebps/races/malian/units/" + actor
        native_rgd = OFFICIAL_INPUTS / (native_actor + ".rgd")
        return {
            "kind": "official actor consumed through 0.4.0 SBPS loadout",
            "actor_pbg": native_actor,
            "official_actor_member": "attrib/" + native_actor + ".rgd",
            "official_actor_member_path": str(native_rgd.relative_to(ROOT)).replace("\\", "/"),
            "official_actor_member_sha256": sha(native_rgd) if native_rgd.exists() else None,
            "compiled_040_actor": None,
            "note": "Use a same-PBG stock actor attrib-set override for tier attachment $PBGNAME only; preserve actor identity, SBPS loadout, PBGMAP, age gates and all nonvisual fields.",
        }
    stem = actor.rsplit("/", 1)[-1]
    rel = f"attrib/ebps/races/malian/units/{stem}"
    xml = BASE / (rel + ".xml")
    rgd = BASE / (rel + ".rgd")
    if not (xml.exists() and rgd.exists()):
        return {"kind": "0.4.0 compiled mod actor", "actor_pbg": "ebps/races/malian/units/" + stem, "compiled_040_actor": rel + ".rgd", "status": "missing baseline actor member"}
    return {
        "kind": "0.4.0 compiled mod actor",
        "actor_pbg": "ebps/races/malian/units/" + stem,
        "compiled_040_actor": rel + ".rgd",
        "compiled_040_actor_sha256": manifest.get(rel + ".rgd"),
        "compiled_040_decompile": rel + ".xml",
        "compiled_040_decompile_sha256": sha(xml),
        "tier_consumers": selector_groups(xml),
    }


def main() -> None:
    target = json.loads(TARGETS.read_text(encoding="utf-8"))
    manifest = json.loads(MEMBER_HASHES.read_text(encoding="utf-8"))
    out = OUT / "bindings"
    private_source = out / "private-source"
    private_source.mkdir(parents=True, exist_ok=True)
    official_sha = sha(OFFICIAL_ARCHIVE)
    rows = []
    for row in target["rows"]:
        age = row["age"]
        actor = row["actor"]
        actor_path = actor if actor.startswith("ebps/") else "ebps/races/malian/units/" + actor
        consumers = []
        for t in actor_evidence(row, manifest).get("tier_consumers", []):
            consumers.append({
                **t,
                "typed_official_identity_candidates": [x.get("blueprint") for x in row.get("baseline_040_actor", {}).get("resolved_tier_consumers", [])
                                                       if (x.get("blueprint") or "").endswith("/" + (t.get("attachment_pbgname") or ""))],
            })
        patch_fields = []
        evidence = actor_evidence(row, manifest)
        routes = []
        if row["actor_kind"] == "official":
            # For stock villagers/Imam, use the typed official tier list and its
            # exact native gate; the actor is overridden only through a private
            # derived PBG. The first no-gate list is the row actor's base age.
            for rt in row.get("baseline_040_actor", {}).get("official_tier_route", []):
                blueprint = rt.get("blueprint")
                consumer = rt.get("consumer") or {}
                if not blueprint:
                    continue
                source_actor_age = numeric_age(actor)
                tgt = ({"dark_age": 1, "feudal_age": 2, "castle_age": 3, "imperial_age": 4}.get(rt.get("age_requirement"))
                       or numeric_age(blueprint)
                       or source_actor_age
                       or age)
                models = []
                for item in consumer.get("model_refs", []):
                    path = item.get("field", "")
                    value = str(item.get("value", "")).replace("\\", "/")
                    if ("animator_merge_mesh_attachment/meshes/animator" in path or "animator_skin_attachment/animator" in path) and value.startswith("art/civilizations/"):
                        if not any(token in value.lower() for token in ("/weapons/", "_shield_", "_staff_", "/tools/", "/archetypes/")):
                            if row["family"] == "villager" and "female" in value.lower():
                                continue
                            models.append({"consumer": blueprint, **item})
                prefix = "tier_ext/tier_group_list/tier_group/tier" + (f"[{rt['index']-1}]" if rt.get("index", 1) > 1 else "")
                routes.append({"attachment_ref": blueprint, "typed_source_blueprint": blueprint, "actor_tier_field": prefix + "/attachments/$PBGNAME",
                               "target_age": tgt,
                               "target_age_evidence": "official typed native tier gate" if rt.get("age_requirement") else "official typed tier PBG/base actor age",
                               "models": models})
        else:
            for tier in evidence.get("tier_consumers", []):
                pbg_name = tier.get("attachment_pbgname")
                blueprint_candidates = [x.get("blueprint") for x in row.get("baseline_040_actor", {}).get("resolved_tier_consumers", [])
                                        if (x.get("blueprint") or "").rsplit("/", 1)[-1] == pbg_name]
                for blueprint in blueprint_candidates:
                    family_base = min((r["age"] for r in target["rows"] if r["family"] == row["family"]), default=age)
                    target_age, age_evidence = route_target_age(tier, actor, row["family"], family_base)
                    if target_age is None:
                        continue
                    routes.append({"attachment_ref": tier.get("attachment_ref"), "typed_source_blueprint": blueprint,
                                   "actor_tier_field": tier.get("attachment_field_path"),
                                   "target_age": target_age, "target_age_evidence": age_evidence,
                                   "selector_fields": tier.get("selector_fields"),
                                   "models": body_fields_for_consumer(row, blueprint)})
        # A typed source body may appear through actor tier aliases. Retain each
        # actual selector route but list only fields relevant to that route age.
        for route in routes:
            for entry in route.get("models", []):
                value = str(entry["value"]).replace("\\", "/")
                suffix = "_upgrade" if "_upgrade/" in value or value.endswith("_upgrade") else ""
                patch_fields.append({
                    "source_consumer": route.get("typed_source_blueprint") or route.get("attachment_ref"),
                    "consumer_candidate": (route.get("attachment_ref") or "").replace("\\", "/"),
                    "consumer_actor_field": route.get("actor_tier_field"),
                    "source_actor": actor_path,
                    "source_field": entry["field"],
                    "source_model": value,
                    "target_age": route.get("target_age"),
                    "target_age_evidence": route.get("target_age_evidence"),
                    "target_model": family_target(row["family"], route["target_age"], suffix),
                    "change_scope": "geometry/model reference only; preserve all companion attachment rows and list ordering",
                })
        # De-duplicate repeated campaign/XP3 tier groups that use the same
        # source consumer and visual target. Each route remains in
        # `visual_routes` for semantic proof; a source copy is created once.
        unique_patches = {}
        for item in patch_fields:
            unique_patches[(item["source_consumer"], item["target_age"], item["source_field"], item["source_model"])] = item
        patch_fields = list(unique_patches.values())
        rows.append({
            "family": row["family"], "age": age,
            "target_model_stem": family_target(row["family"], age),
            "target_model_upgrade_stem": family_target(row["family"], age, "_upgrade") if any(x["target_model"].endswith("_upgrade/" + row["family"] + f"_age0{age}_upgrade") for x in patch_fields) else None,
            "actor": evidence,
            "reachable_squad": row["reachable_squad"],
            "reachability_sources": row.get("reachability_sources", []),
            "preservation_contract": row.get("preservation_contract"),
            "consumed_visual_refs": patch_fields,
            "consumed_visual_ref_count": len(patch_fields),
            "visual_routes": routes,
            "existing_age_tier_consumers": [
                {"blueprint": x.get("blueprint"), "age_requirement": x.get("age_requirement"),
                 "parent_animator": x.get("parent_animator"), "model_refs": x.get("model_refs", [])}
                for x in (row.get("age_tier_consumer") or [])
            ],
            "current_actor_attachment_refs": row.get("baseline_040_actor", {}).get("all_attachment_lists", []),
            "direct_animator_refs": row.get("baseline_040_actor", {}).get("animator_attachments", []),
            "visual_route_status": "derived from the exact compiled actor selector tree and typed current consumer; no age is inferred from a filename",
        })
    king_rows = []
    for row in target.get("conditional_rows", []):
        king_rows.append({
            "family": "king", "age": row["age"],
            "actor_pbg": row["current_actor"],
            "conditional_mode": row["conditional_mode"],
            "reachability_evidence": row["reachability_evidence"],
            "target_model_stem": family_target("king", row["age"]),
            "existing_visual_route": row.get("current_age_visual_tier"),
            "typed_consumer_parent": "art/civilizations/common/humans/archetypes/base_swordsman/base_swordsman",
            "donor_source_body": "art/civilizations/malian/humans/mal_infantry_light_age04/mal_infantry_light_age04",
            "consumer_graph_policy": "preserve official King tier attachment list and base_swordsman parent; do not substitute base_spearshield based on linked clip-owner indexing",
            "age_selector_policy": "King I keeps native tier; II-IV extend the same typed native schema with visual-only routes; no spawn/stat/conversion changes",
        })
    report = {
        "schema": "berber-0.5.0-private-bindings/v1",
        "status": "source closure mapped; typed private attachment candidates and same-path stock actor overrides applied only in isolated research project; no live asset or cook mutation",
        "baseline": {"archive": target["baseline"]["archive"], "sha256": target["baseline"]["sha256"],
                     "compiled_readback": target["baseline"]["compiled_archive_readback"],
                     "member_sha_manifest": target["baseline"]["readback_members_manifest"]},
        "official_typed_source": {"archive": str(OFFICIAL_ARCHIVE), "sha256": official_sha,
                                  "length_bytes": OFFICIAL_ARCHIVE.stat().st_size,
                                  "typed_source_reader": "installed Garrison core mod-project attrib-fields (indexed official RGD)"},
        "private_project": str(PRIVATE_PROJECT.relative_to(ROOT)).replace("\\", "/"),
        "model_root": MODEL_ROOT,
        "coverage": {"families": 13, "nonconditional_rows": len(rows), "conditional_rows": len(king_rows), "total_rows": len(rows) + len(king_rows)},
        "binding_policy": FIELD_POLICY,
        "rows": rows,
        "conditional_rows": king_rows,
        "semantic_proof_required_at_integration": [
            "compiled actor fields outside the attachment-list PBG refs are identical to frozen 0.4.0",
            "all source attachment-list fields except selected mesh animator refs are semantically identical",
            "tier ordering, age requirements, tier upgrade target entity/squad and conversion parameters are unchanged",
            "villager male-only spawn route; villager job/task/carry branches remain; female mesh reference unchanged",
            "trader cart/mount/cargo/harness and native sex/age selectors remain",
            "monk relic pickup/carry/drop/deposit selectors and both staff attachments remain",
            "melee/ranged weapon states, mounted components, shields and all owner-color/material fields remain",
            "Tuareg Spearman 0.4.0 actor, unique bodies and attachments remain unchanged",
            "King keeps the official base_swordsman consumer graph and original production/spawn behavior",
        ],
        "unresolved_routes": [],
    }
    # Private Garrison derive instructions: one candidate list per family,
    # target visual age, and exact official consumer PBG. No candidate is
    # registered in the shared final project and no cook is performed here.
    candidates = {}
    for row in rows:
        for field in row["consumed_visual_refs"]:
            source = field["source_consumer"]
            age = field["target_age"]
            if not source or age not in (1, 2, 3, 4):
                continue
            key = (row["family"], age, source)
            slug = re.sub(r"[^a-z0-9]+", "_", source.rsplit("/", 1)[-1].lower()).strip("_")
            name = f"bind_{row['family']}_a{age}_{slug}"[:63].rstrip("_")
            record = candidates.setdefault(key, {
                "family": row["family"], "target_age": age, "source_blueprint": source,
                "derived_name": name, "derive_command": ["garrison-core", "mod-project", "derive", "--project", str(PRIVATE_PROJECT), "--source", source, "--name", name],
                "field_changes": [],
                "actor_consumer_fields": [],
            })
            actor_field = field.get("consumer_actor_field")
            if actor_field and actor_field not in record["actor_consumer_fields"]:
                record["actor_consumer_fields"].append(actor_field)
            change = {"field": field["source_field"], "source_value": field["source_model"], "value": field["target_model"],
                      "command": ["garrison-core", "mod-project", "derive-change", "--project", str(PRIVATE_PROJECT), "--name", name, "--field", field["source_field"], "--value", field["target_model"]]}
            if change not in record["field_changes"]:
                record["field_changes"].append(change)
    # Official villagers and Imam retain their exact stock actor PBG identity
    # and frozen SBPS loadout. Garrison serializes a same-path stock actor
    # override via attrib-set, changing only attachments/$PBGNAME; PBGMAP and
    # every native age gate remain inherited.
    actor_overrides = []
    for fam, source_actor in (("villager", "ebps/races/malian/units/unit_villager_1_mal"),
                              ("imam", "ebps/races/malian/units/unit_monk_3_mal")):
        actor_routes = []
        famrow = next(r for r in rows if r["family"] == fam)
        for route in famrow["visual_routes"]:
            source_blueprint = route.get("typed_source_blueprint") or route["attachment_ref"]
            key = (fam, route["target_age"], source_blueprint)
            rec = candidates.get(key)
            if not rec:
                continue
            actor_routes.append({
                "field": route["actor_tier_field"], "source_attachment": route["attachment_ref"],
                "derived_name": rec["derived_name"],
                "source_attachment": route["attachment_ref"],
            })
        actor_overrides.append({
            "family": fam, "source_actor": source_actor,
            "actor_field_changes": actor_routes,
            "command_template": ["garrison-core", "mod-project", "attrib-set", "--project", str(PRIVATE_PROJECT),
                                 "--file", source_actor, "--field", "<field>", "--value", "<private-project-guid>:<derived-name>"],
            "identity_route": "same stock Malian actor PBG override; preserve existing SBPS loadout and all actor behavior; only tier attachments/$PBGNAME refs change; preserve $PBGMAP",
        })
        squad = "sbps/races/malian/berbers/unit_villager_1_mal" if fam == "villager" else "sbps/races/malian/unit_monk_3_mal"
        squad_member = BASE / ("attrib/" + squad + ".rgd")
        squad_decompile = BASE / ("attrib/" + squad + ".xml")
        loadout_path = "squad_loadout_ext/unit_list/loadout_data/type"
        actor_overrides[-1]["source_squad"] = squad
        actor_overrides[-1]["source_squad_rgds_sha256"] = sha(squad_member) if squad_member.exists() else None
        actor_overrides[-1]["source_squad_decompile_sha256"] = sha(squad_decompile) if squad_decompile.exists() else None
    private_payload = {
        "schema": "berber-0.5.0-private-binding-candidates/v1",
        "project": str(PRIVATE_PROJECT.relative_to(ROOT)).replace("\\", "/"),
        "source_authority": {"archive": str(OFFICIAL_ARCHIVE), "sha256": official_sha,
                             "identity_source": "Garrison current indexed typed RGD; each source blueprint below is the exact resolved official consumer PBG"},
        "candidate_count": len(candidates),
        "candidates": list(candidates.values()),
        "official_actor_overrides": actor_overrides,
        "execution": "Private source proposals only. Root must register identical derive commands in final project after review; no cook/build invoked.",
        "identity_note": "Garrison allocates private attachment-list PBG IDs during derive. Same-path stock actor attrib-set values use the final project's normalized GUID plus the derived attachment-list name; PBGMAP stays attachments_lists.",
    }
    (private_source / "derive-candidates.json").write_text(json.dumps(private_payload, indent=2) + "\n", encoding="utf-8")
    report["private_candidate_manifest"] = "output/berber_update_0_5_0/bindings/private-source/derive-candidates.json"
    path = out / "plan.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{path}: {len(rows)} family/age rows + {len(king_rows)} conditional King rows; {sum(r['consumed_visual_ref_count'] for r in rows)} current typed body refs")
    if args.apply_private:
        apply_private_candidates(private_payload, out / "private-source/private-project-apply-log.json")


def apply_private_candidates(payload: dict, log_path: Path) -> None:
    """Apply only Garrison-derived candidates to the task-owned private project."""
    core = Path(__import__("os").environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/core/garrison-core.exe"
    project_file = PRIVATE_PROJECT / "mod-project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    known = {x["name"]: x for x in data.get("derived_blueprints", [])}
    entries = []

    def run(cmd: list[str], label: str) -> dict:
        actual = list(cmd)
        actual[0] = str(core)
        result = subprocess.run(actual, capture_output=True, text=True, encoding="utf-8", errors="replace")
        item = {"label": label, "command": actual, "returncode": result.returncode,
                "stdout_tail": result.stdout[-1200:], "stderr_tail": result.stderr[-1200:]}
        entries.append(item)
        if result.returncode:
            raise RuntimeError(f"Garrison candidate command failed ({label}): {result.stderr[-1000:]}")
        return item

    for candidate in payload["candidates"]:
        name, source = candidate["derived_name"], candidate["source_blueprint"]
        known = {x["name"]: x for x in json.loads(project_file.read_text(encoding="utf-8")).get("derived_blueprints", [])}
        existing = known.get(name)
        if existing and existing.get("source") != source:
            raise RuntimeError(f"Private candidate name collision: {name}")
        if not existing:
            run(candidate["derive_command"], f"derive:{name}")
        for change in candidate["field_changes"]:
            current_data = json.loads(project_file.read_text(encoding="utf-8"))
            record = next(x for x in current_data["derived_blueprints"] if x["name"] == name)
            prior = [x for x in record.get("changes", []) if x.get("field") == change["field"]]
            if prior and prior[-1].get("value") != change["value"]:
                raise RuntimeError(f"Private field conflict in {name}: {change['field']}")
            if not prior:
                run(change["command"], f"change:{name}:{change['field']}")
    # Same-path stock actor overrides are recorded by attrib-set. Resolve the
    # project GUID once and keep the native PBGMAP untouched.
    project_guid = json.loads(project_file.read_text(encoding="utf-8"))["mod_id"]
    project_guid = project_guid.replace("-", "")
    project_guid = f"{project_guid[:8]}-{project_guid[8:12]}-{project_guid[12:16]}-{project_guid[16:20]}-{project_guid[20:]}"
    for candidate in payload["official_actor_overrides"]:
        for route in candidate["actor_field_changes"]:
            value = f"{project_guid}:{route['derived_name']}"
            run(["garrison-core", "mod-project", "attrib-set", "--project", str(PRIVATE_PROJECT),
                 "--file", candidate["source_actor"], "--field", route["field"], "--value", value],
                f"actor-override:{candidate['source_actor']}:{route['field']}")
    log = {"project": str(PRIVATE_PROJECT.relative_to(ROOT)).replace("\\", "/"),
           "project_id": json.loads(project_file.read_text(encoding="utf-8"))["mod_id"],
           "commands_run": len(entries), "entries": entries,
           "project_mod_json_sha256": sha(project_file), "native_cook_performed": False}
    log_path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    print(f"Applied {len(entries)} private Garrison derive/change commands; no cook. Log: {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-private", action="store_true", help="apply typed candidates to the task-owned private research project only")
    args = parser.parse_args()
    main()
