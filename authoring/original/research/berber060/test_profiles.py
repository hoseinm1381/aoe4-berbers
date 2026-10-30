"""Offline native-layout tests against extracted official fixtures."""
import unittest, struct, hashlib
from profiles import *

class ProfilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=OUT/'inventory/stock/malian_donso.spd'
        cls.data=cls.path.read_bytes();cls.q=qualify(cls.data)

    def test_all_39_observed_stock_fixtures_parse(self):
        fixtures=read(OUT/'inventory/stock-profiles.json')
        self.assertEqual(len(fixtures),39)
        for f in fixtures:
            data=Path(f['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),f['sha256'])
            self.assertTrue(parse_profile(data))

    def test_private_clone_preserves_every_pointer_and_nonidentity_byte(self):
        result,allowed=clone_private(self.data,self.q,'b03xx','malian_b03xx')
        self.assertEqual(len(result),len(self.data))
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(self.data,result))))
        a,b=parse_profile(self.data),parse_profile(result)
        for old,new in zip(a,b):
            self.assertEqual(old['context'],new['context']);self.assertEqual(old['race'],new['race'])
            for key in ('speaker','media'):
                x,y=old[key],new[key]
                if key=='speaker':x,y=[x],[y]
                self.assertEqual([(m['offset'],m['size']) for m in x],[(m['offset'],m['size']) for m in y])

    def test_donor_hash_guard(self):
        corrupt=bytearray(self.data);corrupt[-1]^=1
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            clone_private(bytes(corrupt),self.q,'b03xx','malian_b03xx')

    def test_qualification_identity_guard(self):
        q=dict(self.q,speakers=['other'])
        with self.assertRaisesRegex(ValueError,'qualification mismatch'):
            clone_private(self.data,q,'b03xx','malian_b03xx')

    def test_private_collision_and_unsafe_identifiers(self):
        for speaker in ('donso','b03xx','../xx'):
            with self.assertRaises(ValueError):
                clone_private(self.data,self.q,speaker,'malian_b03xx',occupied=['b03xx'])

    def test_length_change_rejected(self):
        for speaker,media in [('longer','malian_b03xx'),('b03xx','malian_longer')]:
            with self.assertRaisesRegex(ValueError,'relocate pointers'):
                clone_private(self.data,self.q,speaker,media)

    def test_truncation_and_offset_corruption_rejected(self):
        for data in (self.data[:23],self.data[:-1]):
            with self.assertRaises(ValueError): parse_profile(data)
        _,start,_,_=chunks(self.data)[0]
        corrupt=bytearray(self.data)
        struct.pack_into('<i',corrupt,start+16+52,-2147483648)
        with self.assertRaisesRegex(ValueError,'media list'): parse_profile(corrupt)
        corrupt=bytearray(self.data)
        struct.pack_into('<i',corrupt,start+16+4,-2147483648)
        with self.assertRaisesRegex(ValueError,'String reference'): parse_profile(corrupt)

    def test_media_parser_retains_alternates_and_efforts(self):
        a=parse_media(r'Civ_Malian\malian_donso\malian_donso_effortDeath_iHigh_cNone_02_ALT07.wem')
        self.assertEqual((a['event'],a['delivery'],a['era'],a['take'],a['alternate']),('effortdeath','ihigh','cnone',2,7))
        self.assertTrue(a['effort']);self.assertIsNone(a['age'])
        b=parse_media(r'Civ_Malian\malian_donso\malian_donso_celebrate_cnone_cLowest_01.wem')
        self.assertEqual(b['delivery'],'cnone')
        self.assertFalse(parse_media('unknown.wem')['parsed'])

    def test_all_families_private_and_complete(self):
        manifest=read(OUT/'profiles/manifest.json');speakers=[];paths=[]
        self.assertEqual(len(manifest['families']),26)
        for family in manifest['families']:
            self.assertFalse(family['unparsed'])
            speakers.append((family['race'],family['speaker'].lower()))
            data=Path(family['profile_path']).read_bytes()
            self.assertEqual(sha(family['profile_path']),family['profile_sha256'])
            rows=parse_profile(data)
            self.assertEqual(len(rows),family['record_count'])
            actual={m['text'] for row in rows for m in row['media']}
            self.assertEqual(actual,{m['path'] for m in family['media']})
            paths.extend(p.lower() for p in actual)
        self.assertEqual(len(speakers),len(set(speakers)))
        self.assertEqual(len(paths),len(set(paths)))

    def test_handgunner_distinct_speaker_and_media_identity_lengths(self):
        rows=read(OUT/'profiles/manifest.json')['families']
        row=next(r for r in rows if r['family']=='handgunner')
        self.assertEqual(row['donor_speaker'],'handcannon')
        self.assertEqual(len(row['speaker']),10)
        self.assertEqual(len(row['private_media_identity'].split('_')[1]),14)

    def test_masmuda_approved_archer_is_complete_native_context_superset(self):
        def contexts(name):
            data=(OUT/'inventory/stock'/(name+'.spd')).read_bytes()
            return {r['context']['text'].lower() for r in parse_profile(data)}
        original=contexts('abbasid_crossbowman'); chosen=contexts('malian_archer')
        self.assertTrue(original<=chosen)
        for context in original:
            if context.endswith('_cmed'):
                self.assertIn(context[:-5]+'_clow',chosen)
        row=next(r for r in read(OUT/'profiles/manifest.json')['families'] if r['family']=='masmuda')
        self.assertEqual((row['donor'],row['speaker'],row['race']),('malian_archer','b09xxx','malian'))
        self.assertFalse(row['coverage_gaps'])

    def test_conditional_donor_switches_reject_native_context_losses(self):
        decisions={r['family']:r for r in read(OUT/'profiles/donor-decisions.json')}
        for family in ('fishing_boat','transport_ship'):
            self.assertFalse(decisions[family]['accepted'])
            self.assertIn('reactproud_ihigh_chigh',decisions[family]['missing_original_native_contexts'])
        self.assertFalse(decisions['king']['accepted'])
        self.assertIn('charge_ihigh_cnone',decisions['king']['missing_original_native_contexts'])
        self.assertTrue(decisions['masmuda']['accepted'])

if __name__=='__main__': unittest.main()
