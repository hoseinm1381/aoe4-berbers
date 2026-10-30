"""Trace incoming native state-node references and retain owner ancestry."""
import json
from read_native_tree import NativeTree, ROOT, WORK

tree = NativeTree(ROOT / "output/tuareg_ability_pose_test/simulation-statetree.bin")
targets = {14144259852053327193}
rows = []
for obj in tree.objects.values():
    for name, field in obj["fields"].items():
        if field.get("FieldTypeName", "").startswith("util::ReflectObjectRef<StateTree::StateNode"):
            if tree.field(obj, field)["object_ref"] in targets:
                ancestors = []
                parent = obj
                for _ in range(15):
                    ancestors.append(tree.describe(parent))
                    parent = tree.objects.get(parent["owner"])
                    if parent is None:
                        break
                rows.append({"reference": tree.describe(obj), "ancestors": ancestors})
(WORK / "defensive-entry-references.json").write_text(json.dumps(rows, indent=2))
print(json.dumps([{"reference": x["reference"]["type"],
                   "ancestors": [(a["type"], a["fields"].get("m_name", {}).get("text")) for a in x["ancestors"]]}
                  for x in rows], indent=2))
