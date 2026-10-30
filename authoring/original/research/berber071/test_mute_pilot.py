import unittest,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from mute_pilot import patch,verify,rgd,explicit_candidate
ROOT=Path(__file__).absolute().parents[2]
class MuteTests(unittest.TestCase):
 def test_explicit_mute_retains_extension_and_changes_speaker_only(self):
  member='attrib/sbps/races/malian/unit_villager_1_mal.rgd'
  data=(ROOT/'output/berber_update_0_6_1/readback'/member).read_bytes()
  payload,proof=explicit_candidate(data,member)
  self.assertEqual(proof['speaker'],'b71vmute')
  self.assertTrue(all(c['field'].endswith('speaker_code') for c in proof['changes']))
  self.assertIn('default/squad_speech_ext',dict(rgd.flatten(rgd.read(payload).nodes)))
 def test_roundtrip_restores_entire_native_owner(self):
  for kind,member,extension in [('ebps','attrib/ebps/races/malian/units/unit_villager_1_mal.rgd','speech_ext'),('sbps','attrib/sbps/races/malian/unit_villager_1_mal.rgd','squad_speech_ext')]:
   data=(ROOT/'output/berber_update_0_6_1/readback'/member).read_bytes();payload,proof=patch(data,extension)
   self.assertNotIn('default/'+extension,dict(rgd.flatten(rgd.read(payload).nodes)))
   self.assertEqual(proof['native_mute'],'UNVERIFIED until audible pilot')
 def test_mutated_gameplay_rejected(self):
  p=ROOT/'output/berber_update_0_6_1/readback/attrib/sbps/races/malian/unit_villager_1_mal.rgd'
  original=rgd.read(p.read_bytes());payload,proof=patch(p.read_bytes(),'squad_speech_ext');candidate=rgd.read(payload)
  default=dict(rgd.flatten(original.nodes))['default'];removed=copy.deepcopy(default.value[proof['sibling_index']])
  dict(rgd.flatten(candidate.nodes))['default/pbgid'].value+=1
  with self.assertRaises(ValueError):verify(original,candidate,proof['sibling_index'],removed)
if __name__=='__main__':unittest.main()
