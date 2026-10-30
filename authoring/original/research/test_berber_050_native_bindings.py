"""Native fixtures: reject gameplay drift and entity replacement during visual aging."""
import copy
import unittest
from berber_050_native_bindings import (
    KING, TIER, PBG_GUID, field, source_actor, patch_actor, verify_actor, rgd,
)


class NativeActorSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.source = source_actor(KING)
        cls.original = rgd.read(cls.source.read_bytes())

    def king_candidate(self):
        data, applied = patch_actor(self.source,
            {TIER + '/attachments/$PBGNAME': PBG_GUID + ':bind_king_a1_unit_king_1_mal'}, True)
        return rgd.read(data), applied

    def test_king_ages_without_entity_conversion(self):
        candidate, applied = self.king_candidate()
        verify_actor(self.original, candidate, applied, True)
        for path, node in rgd.flatten(candidate.nodes):
            if '/tier_ext/' in path and '_upgrade_target_' in path and path.endswith('/$PBGNAME'):
                self.assertEqual(node.value, '')

    def test_reject_gameplay_drift(self):
        candidate, applied = self.king_candidate()
        _, identity = field(candidate, 'default/pbgid')
        identity.value += 1
        with self.assertRaisesRegex(ValueError, 'gameplay/identity'):
            verify_actor(self.original, candidate, applied, True)

    def test_reject_age_gate_that_replaces_entity(self):
        candidate, applied = self.king_candidate()
        _, target = field(candidate, TIER + '[1]/statetree_tier_pgb_upgrade_target_entity/$PBGNAME')
        target.value = 'replacement_entity'
        with self.assertRaisesRegex(ValueError, 'added tier modifies behavior'):
            verify_actor(self.original, candidate, applied, True)


if __name__ == '__main__':
    unittest.main()
