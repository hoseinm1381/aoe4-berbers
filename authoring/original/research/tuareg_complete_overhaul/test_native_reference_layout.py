"""Verify decoded node references against native reflected member offsets."""
from pathlib import Path
import sys
import unittest
import json

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/tuareg_shield_posture"))
from read_native_tree import NativeTree

class NativeReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = NativeTree(ROOT / "output/tuareg_ability_pose_test/simulation-statetree.bin")

    def test_reflect_object_ref_uses_declared_object_id_member(self):
        checked = 0
        for obj in self.tree.objects.values():
            for field in obj["fields"].values():
                if field.get("FieldTypeName", "").startswith("util::ReflectObjectRef<StateTree::StateNode"):
                    address = obj["offset"] + int(field.get("Offset"))
                    schema = self.tree.types[int(field.get("FieldTypeId"))]
                    member = schema.find('Fields/ReflectField[@Name="m_objectID"]')
                    expected = self.tree.u64(address + int(member.get("Offset")))
                    actual = self.tree.field(obj, field)["object_ref"]
                    self.assertEqual(actual, expected, (obj["type"], address))
                    if expected: self.assertIn(expected, self.tree.objects)
                    checked += 1
        self.assertGreater(checked, 1000)

    def test_tree_reader_and_addon_contracts_share_one_compiled_namespace(self):
        from garrison.addon_common import core_module
        self.assertEqual(len(core_module("unit_prototypes").catalog()), 2)

    def test_inventory_includes_native_strafing_matrix_separately(self):
        data = json.loads((ROOT / "output/tuareg_complete_overhaul/motion-coverage-candidates.json").read_text())
        rows = {x["track_id"]: x for x in data["motion_candidates"]}
        self.assertIn(4176028309801556714, rows)
        row = rows[4176028309801556714]
        self.assertEqual(row["reference_kind"], "animation_matrix")
        self.assertEqual(row["animation_names"], ["strafe_tense_jog"])
        self.assertEqual(row["clip_names"], [])
        self.assertEqual(data["animation_tracks"], 206)

if __name__ == "__main__": unittest.main(verbosity=2)
