"""Inventory native motion candidates and immediate-transition checks."""
import collections
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_complete_overhaul"
sys.path.insert(0, str(ROOT / "research/tuareg_shield_posture"))
from read_native_tree import NativeTree
tree = NativeTree(ROOT / "output/tuareg_ability_pose_test/simulation-statetree.bin")
owners = collections.defaultdict(list)
for obj in tree.objects.values(): owners[obj["owner"]].append(obj["id"])

def descendants(oid):
    found = {oid}; queue = [oid]
    while queue:
        for child in owners[queue.pop()]:
            if child not in found: found.add(child); queue.append(child)
    return found

def node_name(obj):
    field = obj["fields"].get("m_name")
    return tree.field(obj, field).get("text") if field is not None else None

def ancestry(obj):
    path = []; seen = set()
    while obj is not None and obj["id"] not in seen:
        seen.add(obj["id"])
        name = node_name(obj)
        if name: path.append(name)
        obj = tree.objects.get(obj["owner"])
    return list(reversed(path))

root = next(obj for obj in tree.objects.values() if obj["type"] == "StateTree::StateNodeRoot" and node_name(obj) == "anims_spearshield")
scope = descendants(root["id"])
motions = []; opportunities = []
for oid in sorted(scope):
    obj = tree.objects[oid]
    if ("Animation" in obj["type"] and "Track" in obj["type"]
        and "m_timeBegin" in obj["fields"] and "m_timeEnd" in obj["fields"]):
        inner = descendants(oid)
        clips = []
        providers = []
        for child_id in inner:
            child = tree.objects[child_id]
            if "Animation" in child["type"] and "Provider" in child["type"]:
                providers.append(child["type"])
            if child["type"] == "StateTree::Provider_ConstAnimationName":
                clips.append(tree.field(child, child["fields"]["m_animationName"])["text"])
        path = ancestry(obj)
        family = "other"
        if "Locomotion" in path: family = "locomotion"
        if "Transitions" in path: family = "transitions"
        lowered = "/".join(path).lower()
        for word, label in (("attack", "attack"), ("brace", "brace"), ("charge", "charge"),
                            ("torch", "torch"), ("death", "death"), ("reaction", "reaction"),
                            ("sync", "synchronized_action")):
            if word in lowered: family = label
        is_matrix = "Matrix" in obj["type"]
        motions.append({"track_id": oid, "type": obj["type"], "state_path": path,
                        "family": family, "animation_names": sorted(set(clips)),
                        "reference_kind": "animation_matrix" if is_matrix else "clip",
                        "clip_names": [] if is_matrix else sorted(set(clips)),
                        "matrix_expansion": "pending_constituent_clip_and_unit_reachability_resolution" if is_matrix else None,
                        "provider_types": sorted(set(providers)),
                        "timing_fields": {name: tree.field(obj, field) for name, field in obj["fields"].items()
                                          if name in ("m_timeBegin", "m_timeEnd", "m_master")},
                        "status": "native_graph_candidate_not_yet_unit_reachability_proven",
                        "custom_implementation": "not_authored_export_gate_unqualified"})
    if obj["type"] == "StateTree::OpportunityTrack":
        target = tree.field(obj, obj["fields"]["m_referenceNode"])["object_ref"]
        opportunities.append({"track_id": oid, "state_path": ancestry(obj),
                              "target_id": target, "target_path": ancestry(tree.objects[target]) if target else [],
                              "fields": {name: tree.field(obj, field) for name, field in obj["fields"].items()
                                         if name in ("m_timeBegin", "m_timeEnd", "m_latchTime", "m_reenterState")}})

clips = sorted({name for motion in motions for name in motion["clip_names"]})
report = {"schema": "tuareg-complete-motion-qualification/v1", "native_root": "anims_spearshield",
          "objects_in_root": len(scope), "animation_tracks": len(motions), "clip_names": clips,
          "matrix_references": sorted({name for motion in motions if motion["reference_kind"] == "animation_matrix" for name in motion["animation_names"]}),
          "named_animation_references": sorted({name for motion in motions for name in motion["animation_names"]}),
          "motion_candidates": motions, "immediate_transition_checks": opportunities,
          "reachability_boundary": "Graph contains shared-archetype candidates; equipment/condition/native action validation is still required"}
(WORK / "motion-coverage-candidates.json").write_text(json.dumps(report, indent=2))
# Resolve every native clip through the actual installed timing contracts.
sys.path.insert(0, str(Path.home() / "AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com"))
from garrison.addon_common import core_module
prototype = core_module("unit_prototypes")
probes = []
for name in clips:
    row = {"prototype": "english-spearman-2", "clip": name}
    try: row.update(status="admitted_timing", timing=prototype.clip_timing("english-spearman-2", {"name": name}))
    except ValueError as error: row.update(status="refused", reason=str(error))
    probes.append(row)
(WORK / "native-slot-export-probes.json").write_text(json.dumps(probes, indent=2))
print(json.dumps({"objects_in_root": len(scope), "animation_tracks": len(motions), "distinct_named_clips": len(clips),
                  "matrix_references": report["matrix_references"],
                  "distinct_named_animation_references": len(report["named_animation_references"]),
                  "admitted_timing": [x["clip"] for x in probes if x["status"] == "admitted_timing"],
                  "refused_clips": sum(x["status"] == "refused" for x in probes),
                  "immediate_checks": opportunities}, indent=2))
