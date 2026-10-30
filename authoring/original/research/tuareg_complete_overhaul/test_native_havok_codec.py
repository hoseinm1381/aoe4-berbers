"""Independent native-tagfile adapter proof, not in-game acceptance."""
from pathlib import Path
import os
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_force_trial"
sys.path.insert(0, str(WORK / "codec_runtime"))
SOURCE = ROOT / "output/tuareg_shield_test/evidence/source/art/civilizations/common/humans/archetypes/base_spearshield/base_spearshield.rhka"

class CodecTests(unittest.TestCase):
    def test_actual_native_container_and_skeleton_parse(self):
        if os.environ.get("TUAREG_CODEC_BASELINE") == "1":
            from soulstruct.havok import HKX
            obj = HKX.from_path(SOURCE)
        else:
            from native_havok_codec import read_native
            obj = read_native(SOURCE)
        self.assertEqual(obj.hk_version, "20180200")
        self.assertGreater(len(obj.root.animations), 100)
        # Soulstruct's Shift-JIS reader represents native ASCII0x5c as U+00A5.
        self.assertIn("navigation\\idle_calm_basic_01", {x.name.replace("\u00a5", "\\") for x in obj.root.animations})
        self.assertTrue(any(len(x.skeleton.bones) == 48 for x in obj.root.animations))

    def test_native_roundtrip_preserves_clip_headers_and_predictive_payloads(self):
        from native_havok_codec import read_native
        obj = read_native(SOURCE)
        data = bytes(obj.to_writer())
        target = WORK / "codec-roundtrip.rhka"
        target.write_bytes(data)
        decoded = read_native(target)
        self.assertEqual(obj.root.name, decoded.root.name)
        self.assertEqual(len(obj.root.animations), len(decoded.root.animations))
        for left, right in zip(obj.root.animations, decoded.root.animations):
            self.assertEqual(left.name, right.name)
            a, b = left.animationBinding.animation, right.animationBinding.animation
            self.assertEqual(a.duration, b.duration)
            self.assertEqual(a.numberOfTransformTracks, b.numberOfTransformTracks)
            self.assertEqual(a.compressedData, b.compressedData)
            self.assertEqual(a.intData, b.intData)
            self.assertEqual(a.floatData, b.floatData)
            self.assertEqual(left.animationBinding.transformTrackToBoneIndices,
                             right.animationBinding.transformTrackToBoneIndices)

if __name__ == "__main__": unittest.main(verbosity=2)
