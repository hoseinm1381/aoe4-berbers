"""Regression gate for the importable 0.2.7.1-content test package."""

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/berber_update_0_2_7_1/berber_future_kingdom-0.2.7.1.zip"
TARGET = ROOT / "output/berber_update_0_2_7_1_manifest_repair/berber_future_kingdom-0.2.8-test.zip"


class ManifestRepairTests(unittest.TestCase):
    def test_manifest_only_repair(self):
        self.assertTrue(TARGET.is_file(), "repaired ZIP has not been built")
        with zipfile.ZipFile(SOURCE) as old, zipfile.ZipFile(TARGET) as new:
            self.assertIsNone(old.testzip())
            self.assertIsNone(new.testzip())
            self.assertEqual(set(old.namelist()), set(new.namelist()))
            old_manifest = json.loads(old.read("garrison.json"))
            new_manifest = json.loads(new.read("garrison.json"))
            self.assertRegex(new_manifest["details"]["version"], r"^\d+\.\d+\.\d+$")
            self.assertEqual(new_manifest["details"]["version"], "0.2.8")
            old_manifest["details"]["version"] = "0.2.8"
            self.assertEqual(new_manifest, old_manifest)
            for name in old.namelist():
                if name != "garrison.json":
                    self.assertEqual(
                        hashlib.sha256(new.read(name)).digest(),
                        hashlib.sha256(old.read(name)).digest(),
                        name,
                    )
            sga = new.read("Berber_future_kingdom.sga")
            self.assertEqual(hashlib.sha256(sga).hexdigest(), new_manifest["members"][0]["sha256"])


if __name__ == "__main__":
    unittest.main()
