import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import landmarks as l
class LandmarkTests(unittest.TestCase):
 def source(self,family):
  member,scale=l.TARGETS[family]
  return (l.ROOT/'output/berber_update_0_6_0/integration/candidate-readback-6e4a4f3fcb00'/member).read_bytes(),scale
 def test_exact_scale_and_all_other_native_semantics_preserved(self):
  for family in l.TARGETS:
   raw,scale=self.source(family);encoded,changes=l.patch(raw,scale)
   self.assertEqual(changes,[{'field':l.FIELD,'kind':'Float','before':scale,'after':scale*1.25}])
   before=l.rgd.read(raw);after=l.rgd.read(encoded)
   lookup=dict(l.rgd.flatten(after.nodes));self.assertEqual(lookup[l.FIELD].value,scale*1.25)
   lookup[l.FIELD].value=scale;self.assertEqual(l.semantic(before.nodes),l.semantic(after.nodes))
 def test_wrong_existing_scale_rejected(self):
  raw,scale=self.source('tlemcen')
  with self.assertRaisesRegex(ValueError,'scale'):l.patch(raw,scale+1)
 def test_non_castle_landmark_rejected(self):
  path=l.ROOT/'output/berber_update_0_6_0/integration/candidate-readback-6e4a4f3fcb00/attrib/ebps/races/malian/buildings/landmarks/ribat_of_sanhaja/building_landmark_age1_landmarka_mal.rgd'
  with self.assertRaisesRegex(ValueError,'Castle'):l.patch(path.read_bytes(),100.0)
 def test_requirement_polarity_rejected(self):
  raw,scale=self.source('marrakech');doc=l.rgd.read(raw)
  path=next(p for p,n in l.rgd.flatten(doc.nodes) if p.endswith('upgrade_name/$PBGNAME') and n.value=='castle_age' and '/requirement_ext/' in p)
  dict(l.rgd.flatten(doc.nodes))[path.rsplit('/upgrade_name/',1)[0]+'/is_present'].value=True
  with self.assertRaisesRegex(ValueError,'polarity'):l.patch(l.rgd.write(doc),scale)
 def test_base_hash_guard_before_extraction(self):
  import tempfile
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'bad.sga';path.write_bytes(b'wrong')
   with self.assertRaisesRegex(ValueError,'immutable'):l.build(path,Path(tmp)/'out')
if __name__=='__main__':unittest.main()
