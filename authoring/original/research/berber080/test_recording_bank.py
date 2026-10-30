from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime
from inspect_inputs import SOURCE, HERE


def load(path):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(path.read_text(encoding="utf-8"))
    return lua.globals().BerberVoiceBank


def plain(value):
    return {k: plain(v) for k, v in value.items()} if hasattr(value, "items") else value


class RecordingBankTests(unittest.TestCase):
    def test_existing_families_and_identity_maps_are_unchanged(self):
        before = plain(load(SOURCE / "mod-source/scar/berber_voice_bank.scar"))
        after = plain(load(HERE / "berber_voice_bank.scar"))
        self.assertEqual(before["pbgids"], after["pbgids"])
        self.assertEqual(before["blueprints"], after["blueprints"])
        self.assertEqual(len(after["clips"]), 26)
        for family, clips in before["clips"].items():
            self.assertEqual(clips, after["clips"][family], family)

    def test_villager_single_take_and_tuareg_four_ages(self):
        after = plain(load(HERE / "berber_voice_bank.scar"))
        self.assertEqual(len(after["clips"]["villager"]), 14)
        self.assertTrue(all(len(clips) == 1 for clips in after["clips"]["villager"].values()))
        self.assertEqual(set(after["age_clips"]["tuareg"]), {1, 2, 3, 4})
        selections = []
        for age in range(1, 5):
            bank = after["age_clips"]["tuareg"][age]
            self.assertEqual(len(bank), 11)
            selections.append(bank["select"][1][1])
        self.assertEqual(len(set(selections)), 4)


if __name__ == "__main__":
    unittest.main()
