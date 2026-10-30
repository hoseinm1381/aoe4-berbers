import copy, unittest
from pathlib import Path
from unittest.mock import patch as mock_patch
import bindings
from common import OUT, read

class SpeechBindingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=read(OUT/'binding-audit.json')

    def fixture(self, suffix):
        row=next(r for r in self.audit['rows'] if r['member'].endswith(suffix))
        return Path(row['file']).read_bytes()

    def test_both_owners_and_all_nested_speaker_fields(self):
        for row in self.audit['rows']:
            if row.get('owner'): continue
            source=Path(row['file']).read_bytes()
            original=bindings.rgd.read(source)
            expected={p for p,n in bindings.rgd.flatten(original.nodes) if p.endswith(bindings.SPEAKERS)}
            data,changes=bindings.patch(source,'longer_060_private_speaker','malian')
            actual={c['field'] for c in changes if c['field'].endswith(bindings.SPEAKERS)}
            self.assertEqual(expected,actual,row['member'])
            bindings.verify_undo(original,bindings.rgd.read(data),changes)

    def test_gender_and_age_mapping_preserved(self):
        source=self.fixture('sbps/races/malian/berbers/unit_handcannon_4_mal.rgd')
        original=dict(bindings.rgd.flatten(bindings.rgd.read(source).nodes))
        data,_=bindings.patch(source,'b12xxxxx','malian')
        after=dict(bindings.rgd.flatten(bindings.rgd.read(data).nodes))
        preserved={k for k in original if 'female_chance' in k or '/age_mapping/' in k}
        self.assertTrue(preserved)
        for key in preserved:self.assertEqual(original[key].value,after[key].value)
        self.assertTrue(any(n.value==1 for k,n in original.items() if 'female_chance' in k))

    def test_required_existing_race_only(self):
        source=self.fixture('sbps/races/malian/berbers/mehari_2_ber.rgd')
        data,changes=bindings.patch(source,'b05xxxxxxxx','abbasid')
        race=[c for c in changes if c['field'].endswith(bindings.RACE)]
        self.assertTrue(race)
        self.assertTrue(all(c['after']=='abbasid' for c in race))

    def test_masmuda_age_two_and_king_age_two_select_existing_forms(self):
        for suffix,mapping in [('berbers/unit_masmuda_cb_2_ber.rgd',[2,2,3,4]),('malian/unit_king_1_mal.rgd',[2,2,3,4])]:
            source=self.fixture(suffix)
            data,changes=bindings.patch(source,'private_actor','malian',age_mapping=mapping)
            after=dict(bindings.rgd.flatten(bindings.rgd.read(data).nodes))
            values=[n.value for p,n in after.items() if p.startswith('default/squad_speech_ext/age_mapping/')]
            self.assertEqual(values,mapping)
            bindings.verify_undo(bindings.rgd.read(source),bindings.rgd.read(data),changes)

    def test_unrelated_diff_rejected(self):
        source=self.fixture('ebps/races/malian/units/mehari_2_ber.rgd')
        data,changes=bindings.patch(source,'b05xxxxxxxx','abbasid')
        original=bindings.rgd.read(source);candidate=bindings.rgd.read(data)
        unrelated=next(n for k,n in bindings.rgd.flatten(candidate.nodes) if n.kind=='Int' and not 'speech' in k)
        unrelated.value+=1
        with self.assertRaisesRegex(ValueError,'Non-speech'):
            bindings.verify_undo(original,candidate,changes)

    def test_corruption_rejected(self):
        with self.assertRaises(Exception):bindings.patch(b'not a native RGD','private','malian')

    def test_wrong_base_rejected(self):
        with mock_patch.object(bindings,'sha',return_value='wrong'):
            with self.assertRaisesRegex(ValueError,'Wrong authoritative'):
                bindings.validate_base(Path('irrelevant'))

    def test_audit_excludes_dormant_combat(self):
        family=next(f for f in self.audit['families'] if f['family']=='combat_ship')
        self.assertTrue(family['owners'])
        self.assertTrue(all('_mal.rgd' not in m for m in family['owners']))

if __name__=='__main__':unittest.main()
