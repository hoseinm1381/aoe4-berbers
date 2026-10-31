"""Pin native archive TOC namespaces against real working and broken archives."""
import json,unittest
from pathlib import Path
from archive_contract import validate_house_namespaces
ROOT=Path(__file__).resolve().parents[2]
def fixture(name):return json.loads((ROOT/'output'/name/'final-inventory.log').read_text())
class HouseNamespaceTest(unittest.TestCase):
    def test_broken_022_private_tiers_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'house_age1_tier.*attrib'):
            validate_house_namespaces(fixture('berber_update_0_2_2'))
    def test_corrected_native_namespaces_are_accepted(self):
        d=fixture('berber_update_0_2_2')
        for m in d['members']:
            if m['path'].startswith('attrib/attachments/attachment_lists/garrison/berber_house_022/'):m['toc']='attrib'
        validate_house_namespaces(d)
    def test_one_wrong_age_is_not_hidden_by_other_correct_ages(self):
        d=fixture('berber_update_0_2_2')
        for m in d['members']:
            if m['path'].startswith('attrib/attachments/attachment_lists/garrison/berber_house_022/'):m['toc']='attrib'
        bad=next(m for m in d['members'] if m['path'].endswith('house_age4_tier.rgd'));bad['toc']='data'
        with self.assertRaisesRegex(ValueError,'house_age4_tier'):validate_house_namespaces(d)
    def test_missing_age_is_rejected(self):
        d=fixture('berber_update_0_2_2');d['members']=[m for m in d['members'] if not m['path'].endswith('house_age2_tier.rgd')]
        with self.assertRaisesRegex(ValueError,'missing.*house_age2'):validate_house_namespaces(d)
    def test_working_tent_and_actor_use_attrib(self):
        members={m['path']:m for m in fixture('berber_update_0_2_2')['members']}
        self.assertEqual(members['attrib/attachments/attachment_lists/garrison/berber_tent_art_020/berber_tent_age1_tier.rgd']['toc'],'attrib')
        self.assertEqual(members['attrib/ebps/races/malian/buildings/building_house_mal.rgd']['toc'],'attrib')
    def test_actual_023_release_has_correct_native_namespaces(self):
        validate_house_namespaces(fixture('berber_update_0_2_3'))
if __name__=='__main__':unittest.main()
