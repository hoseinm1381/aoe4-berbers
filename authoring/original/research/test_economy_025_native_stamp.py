"""Real native stamp fixtures guard assembly and selector preservation."""
import struct,tempfile,unittest
from pathlib import Path
from build_berber_update_0_2_5 import INT,validate_stamp
from economy_025_native_stamp import NativeTree,relic_chunky

class NativeStampRegression(unittest.TestCase):
 def setUp(self):self.stock=INT/'stock/art/stamps/civ_common/com_lumber_camp.bin'
 def mutate(self,address,data):
  t=NativeTree(self.stock);payload=bytearray(t.memory.payload);offset=address-t.memory.payload_offset;payload[offset:offset+len(data)]=data
  raw=relic_chunky.rebuild(t.document,lambda c:bytes(payload) if c.tag==b'RFCI' else None)
  folder=tempfile.TemporaryDirectory(dir=INT);self.addCleanup(folder.cleanup);p=Path(folder.name)/'mutated.bin';p.write_bytes(raw);return p
 def test_all_three_native_assemblies_compare(self):
  for p in (INT/'stock').rglob('*.bin'):self.assertEqual(validate_stamp(p,p,{})['status'],'passed')
 def test_accidental_scale_change_is_rejected(self):
  t=NativeTree(self.stock);obj=next(o for o in t.objects.values() if o['type']=='Transform');f=obj['fields']['m_scale']
  p=self.mutate(obj['offset']+int(f.get('Offset')),struct.pack('<fff',.46,.46,.46))
  with self.assertRaises(AssertionError):validate_stamp(self.stock,p,{})
 def test_missing_assembly_component_is_rejected(self):
  t=NativeTree(self.stock);obj=next(o for o in t.objects.values() if o['type']=='StampBlueprint');f=obj['fields']['m_blueprints']
  p=self.mutate(obj['offset']+int(f.get('Offset'))+8,struct.pack('<I',1))
  with self.assertRaises(AssertionError):validate_stamp(self.stock,p,{})
 def test_selection_state_change_is_rejected(self):
  t=NativeTree(self.stock);obj=next(o for o in t.objects.values() if o['type']=='VisualStampBlueprint');f=obj['fields']['m_isSelectable']
  address=obj['offset']+int(f.get('Offset'));p=self.mutate(address,bytes([not t.bytes(address,1)[0]]))
  with self.assertRaises(AssertionError):validate_stamp(self.stock,p,{})

if __name__=='__main__':unittest.main()
