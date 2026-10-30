"""Native upgrade merge meshes must preserve their intentional no-RGO contract."""
import unittest
from berber_050_build import MANIFESTS
from berber_050_common import read
from berber_050_model_payloads import (ATTACHMENT_CARRIERS, absolute, collect,
                                      cook_source, mv, native_stock)


class NativeUpgradeAttachmentRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = collect(MANIFESTS)
        cls.attachments = {n:r for n,r in cls.models.items()
                           if cook_source(r) != r['official_donor_rgm'].removesuffix('.rgm')}

    def test_only_six_known_official_skinned_merge_resources_are_exempt(self):
        self.assertEqual(len(ATTACHMENT_CARRIERS), 2)
        self.assertEqual(set(self.attachments), {
            'mehari_age02_upgrade', 'mehari_age03_upgrade',
            'sanhaja_age02_upgrade', 'sanhaja_age03_upgrade',
            'sanhaja_age03_upgrade_part02', 'sanhaja_age04_upgrade_part02'})
        self.assertEqual(cook_source({'official_donor_rgm':'art/unknown/full_unit.rgm'}),
                         'art/unknown/full_unit')

    def test_native_skin_and_rgo_absence_are_preserved(self):
        for name, row in self.attachments.items():
            with self.subTest(variant=name):
                stock, proof = native_stock(row)
                self.assertNotIn('.rgo', stock)
                self.assertGreater(proof['normalized_weight_vertices'], 0)
                self.assertGreater(proof['skinned_lod_groups'], 0)
                self.assertIn('no own RGO', proof['native_rgo_contract'])
                report = read(absolute(row['geometry_report']))
                self.assertEqual(report['source_sha256'], row['native_source_rrgeom_sha256'])
                self.assertEqual(report['output_sha256'], row['authored_rrgeom_sha256'])

    def test_private_native_rgm_rewrite_is_exactly_reversible(self):
        for name, row in self.attachments.items():
            with self.subTest(variant=name):
                stock, _ = native_stock(row)
                before = row['official_donor_rgm'].removesuffix('.rgm')
                after = 'art/scenario/garrison/berber_units_050/' + name + '/' + name
                changed = mv.rewrite_model_path(stock['.rgm'], before, after)
                self.assertNotEqual(changed, stock['.rgm'])
                self.assertEqual(mv.rewrite_model_path(changed, after, before), stock['.rgm'])


if __name__ == '__main__':
    unittest.main()
