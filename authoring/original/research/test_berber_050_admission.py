"""Release guards against incomplete art and stale or unqualified cook evidence."""
import copy
import unittest
from berber_050_admission import EXPECTED, admit_coverage, admit_cook, changed_members


def complete_coverage():
    return {'rows': [{'family': family, 'age': age,
                       'status': 'preserved_accepted' if family == 'tuareg' else 'export_verified',
                       'geometry_modified': family != 'tuareg',
                       'donor_sha256': 'a' * 64,
                       'owner_colour_contract': 'native_dynamic',
                       'resources': [f'art/scenario/garrison/berber_units_050/{family}/age{age}/model.rrgeom']}
                      for family, ages in EXPECTED.items() for age in ages]}


class ReleaseAdmissionTests(unittest.TestCase):
    def test_complete_roster_admits_all_39_age_entries_including_regicide(self):
        self.assertEqual(len(admit_coverage(complete_coverage())), 39)

    def test_regicide_king_age_variants_cannot_be_silently_omitted(self):
        report = complete_coverage()
        report['rows'] = [r for r in report['rows'] if r['family'] != 'king']
        with self.assertRaisesRegex(ValueError, 'Missing coverage'):
            admit_coverage(report)

    def test_missing_imperial_imam_cannot_ship(self):
        report = complete_coverage()
        report['rows'] = [r for r in report['rows'] if (r['family'], r['age']) != ('imam', 4)]
        with self.assertRaisesRegex(ValueError, 'Missing coverage'):
            admit_coverage(report)

    def test_static_pose_or_stock_fallback_cannot_count_as_new_art(self):
        for changes in ({'status': 'stock_fallback'}, {'geometry_modified': False},
                        {'owner_colour_contract': 'baked_palette'}):
            report = complete_coverage()
            report['rows'][0].update(changes)
            with self.assertRaises(ValueError):
                admit_coverage(report)

    def test_duplicate_rows_cannot_conceal_a_missing_variant(self):
        report = complete_coverage()
        report['rows'][-1] = copy.deepcopy(report['rows'][0])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            admit_coverage(report)

    def test_stale_cook_or_live_reload_is_rejected(self):
        good = {'status': 'passed', 'live_reload': False, 'source_hashes': {'model.fbx': 'a' * 64}}
        self.assertTrue(admit_cook(good, good['source_hashes']))
        for changes in ({'status': 'failed'}, {'live_reload': True}, {'source_hashes': {}}):
            with self.assertRaises(ValueError):
                admit_cook(good | changes, good['source_hashes'])

    def test_unrelated_building_change_or_member_removal_is_rejected(self):
        base = {'art/buildings/keep.bin': 'a', 'attrib/unit.rgd': 'b'}
        candidate = {'art/buildings/keep.bin': 'a', 'attrib/unit.rgd': 'c', 'art/new.rrgeom': 'd'}
        self.assertEqual(changed_members(base, candidate, {'attrib/unit.rgd', 'art/new.rrgeom'}),
                         {'changed': ['attrib/unit.rgd'], 'new': ['art/new.rrgeom'], 'unchanged': 1})
        with self.assertRaisesRegex(ValueError, 'outside allowlist'):
            changed_members(base, candidate | {'art/buildings/keep.bin': 'x'}, {'attrib/unit.rgd', 'art/new.rrgeom'})
        with self.assertRaisesRegex(ValueError, 'removed'):
            changed_members(base, {'attrib/unit.rgd': 'b'}, set())


if __name__ == '__main__':
    unittest.main()
