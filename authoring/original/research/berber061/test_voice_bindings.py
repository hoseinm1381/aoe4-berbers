import unittest
import voice_bindings as vb
class VoiceBindingsTests(unittest.TestCase):
 def test_bothfamilies_preserveallnonspeech_and_identity(self):
  for family in vb.FAMILIES:
   source=vb.source_bytes(family,'sbps');payload,changes=vb.patch(source,family,'sbps')
   original=vb.rgd.read(source);after=vb.rgd.read(payload);vb.verify_undo(original,after,changes)
   nodes=dict(vb.rgd.flatten(after.nodes))
   self.assertEqual(nodes['default/pbgid'].value,vb.FAMILIES[family]['pbgid'])
   self.assertEqual(nodes['default/squad_loadout_ext/squad_female_chance'].value,0)
   self.assertEqual([n.value for p,n in nodes.items() if '/squad_speech_ext/age_mapping/' in p],[1,1,1,1])
   self.assertEqual(nodes['default/squad_speech_ext/squad_speaker_code'].value,vb.FAMILIES[family]['speaker'])
 def test_ebps_private_speaker_only(self):
  for family in vb.FAMILIES:
   source=vb.source_bytes(family,'ebps');payload,changes=vb.patch(source,family,'ebps')
   self.assertEqual(len(changes),1);self.assertEqual(changes[0]['field'],'default/speech_ext/speaker_code')
   vb.verify_undo(vb.rgd.read(source),vb.rgd.read(payload),changes)
 def test_nonspeechmutationrejected(self):
  source=vb.source_bytes('villager','sbps');payload,changes=vb.patch(source,'villager','sbps');after=vb.rgd.read(payload)
  dict(vb.rgd.flatten(after.nodes))['default/squad_loadout_ext/squad_female_chance'].value=1
  with self.assertRaises(ValueError):vb.verify_undo(vb.rgd.read(source),after,changes)
if __name__=='__main__':unittest.main()
