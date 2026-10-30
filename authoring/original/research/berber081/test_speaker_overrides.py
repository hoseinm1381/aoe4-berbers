import sys
import unittest
from pathlib import Path
from investigate import OUT, extract, rgd

MEMBERS = [f"attrib/attachments/attachment_lists/garrison/berber_units_050/bind_villager_a{age}_tier{age}_villager_mal.rgd" for age in range(1, 5)]


class AttachmentSpeakerTests(unittest.TestCase):
    def test_all_villager_attachment_speaker_overrides_are_empty(self):
        for member in MEMBERS:
            with self.subTest(member=member):
                patched = OUT / "payloads" / member
                path = patched if patched.exists() else extract(member)
                nodes = [n for _, n in rgd.flatten(rgd.read(path.read_bytes()).nodes) if n.key == "attachment_speaker_code"]
                self.assertEqual(len(nodes), 52)
                self.assertTrue(all(n.kind == "CString" and n.value == "" for n in nodes))


if __name__ == "__main__":
    unittest.main()
