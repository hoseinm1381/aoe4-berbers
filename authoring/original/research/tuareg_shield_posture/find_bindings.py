"""Locate verified shield-wall key/clip consumers in the reflected native tree."""
import json
from pathlib import Path
from read_native_tree import NativeTree, ROOT, WORK

tree = NativeTree(ROOT / "output/tuareg_ability_pose_test/simulation-statetree.bin")
hits = []
for obj in tree.objects.values():
    fields = {}
    for name, field in obj["fields"].items():
        kind = field.get("FieldTypeName")
        if kind == "Reflect::ReflectStringHash" or kind == "util::ReflectString<StdTraits>" or kind.startswith("FamilyManagerEnum<"):
            value = tree.field(obj, field)
            text = value.get("text") or ""
            if "shieldwall" in text or "spearman_shield_wall_byz" in text or "spearman_defensive" in text:
                fields[name] = value
    if fields:
        ancestors = []
        parent = obj
        seen = set()
        for _ in range(15):
            if parent["id"] in seen:
                break
            seen.add(parent["id"])
            ancestors.append(tree.describe(parent))
            parent = tree.objects.get(parent["owner"])
            if parent is None:
                break
        hits.append({"id": obj["id"], "type": obj["type"], "fields": fields, "ancestors": ancestors})
(WORK / "shield-key-and-clip-consumers.json").write_text(json.dumps(hits, indent=2))
print(json.dumps([{"id": x["id"], "type": x["type"], "fields": x["fields"],
                   "ancestors": [(a["type"], a["fields"].get("m_name", {}).get("text")) for a in x["ancestors"]]}
                  for x in hits], indent=2))
