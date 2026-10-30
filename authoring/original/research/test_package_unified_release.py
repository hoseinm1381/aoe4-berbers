import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import package_unified_release as p


class UnifiedPackagingTests(unittest.TestCase):
    def fixture(self, folder, duplicate=False):
        root = Path(folder)
        source = root / "source"
        source.mkdir()
        with zipfile.ZipFile(source / p.ZIP_NAME, "w") as z:
            z.writestr("garrison.json", json.dumps({"details": {"version": "0.8.1"}, "members": [{"path": "Berber_future_kingdom.sga", "sha256": "old"}]}))
            z.writestr("VOICE_COVERAGE.json", "{}")
            z.writestr("VOICE_GAPS.md", "fixture baseline")
            if duplicate:
                z.writestr("documentation/garrison.json", "{}")
        sga = root / "candidate.sga"
        sga.write_bytes(b"fixture validated archive with embedded voices")
        return root, source, sga

    def test_single_zip_metadata_hashes_and_collision(self):
        with tempfile.TemporaryDirectory(prefix="berber-unified-") as folder:
            root, source, sga = self.fixture(folder)
            with patch.object(p, "SOURCE", source), patch.object(p, "check", return_value={}):
                report = p.build("0.8.2", "Fixture changes", sga, root / "out")
                with zipfile.ZipFile(report["zip"]) as z:
                    self.assertEqual(sum(Path(n).name == "garrison.json" for n in z.namelist()), 1)
                    self.assertFalse(any(n.endswith((".exe", ".dll", ".ps1", ".cmd")) for n in z.namelist()))
                    self.assertEqual(z.read("Berber_future_kingdom.sga"), sga.read_bytes())
                    m = json.loads(z.read("garrison.json"))
                    self.assertEqual(m["details"]["version"], "0.8.2")
                    self.assertEqual(m["members"][0]["sha256"], hashlib.sha256(sga.read_bytes()).hexdigest())
                with self.assertRaises(FileExistsError):
                    p.build("0.8.2", "Again", sga, root / "out")

    def test_duplicate_source_manifest_rejected_before_output(self):
        with tempfile.TemporaryDirectory(prefix="berber-unified-") as folder:
            root, source, sga = self.fixture(folder, duplicate=True)
            with patch.object(p, "SOURCE", source), patch.object(p, "check", return_value={}):
                with self.assertRaises(ValueError):
                    p.build("0.8.2", "Fixture", sga, root / "out")
            self.assertFalse((root / "out").exists())

    def test_bad_version_and_empty_summary_rejected(self):
        for version, summary in (("../escape", "test"), ("0.8.1", "test"), ("0.8.2.1", "test"), ("0.8.2", "")):
            with self.subTest(version=version), self.assertRaises(ValueError):
                p.build(version, summary, "missing.sga")


if __name__ == "__main__":
    unittest.main()
