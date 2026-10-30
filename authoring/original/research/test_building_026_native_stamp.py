"""Actual native terrain spline graph preservation in the rebind route."""
import unittest,json,struct
from pathlib import Path
from economy_025_native_stamp import NativeTree,clone_id
from build_berber_update_0_2_5 import validate_stamp
ROOT=Path(__file__).resolve().parents[1];INT=ROOT/'output/berber_update_0_2_6/integration'
class StockSplineGraph(unittest.TestCase):
 def setUp(self):
  self.row=next(r for r in json.loads((INT/'stamp-source.json').read_text()) if r['name']=='barracks_abb_barracks_age_01')
  self.old=NativeTree(self.row['stock']);self.new=NativeTree(INT/'encoded-stamps'/(self.row['private']+'.bin'))
 def test_all_fields_and_arrays_preserved(self):
  self.assertEqual(validate_stamp(self.old.path,self.new.path,self.row['mapping'])['status'],'passed')
 def test_four_byte_spline_modes_retained_exact(self):
  count=0
  for oid,o in self.old.objects.items():
   n=self.new.objects[clone_id(self.old,oid)]
   for name,f in o['fields'].items():
    if f.get('FieldTypeName')=='MathPrim::SplineMode':
     a=self.old.bytes(o['offset']+int(f.get('Offset')),4);b=self.new.bytes(n['offset']+int(f.get('Offset')),4)
     self.assertEqual(a,b);self.assertEqual(struct.unpack('<I',a)[0],0);count+=1
  self.assertEqual(count,12)
 def test_creation_table_and_pointer_fixups_valid(self):
  raw=self.new.chunks[b'RNEW'].payload;count=struct.unpack_from('<Q',raw)[0]
  self.assertEqual(len(raw),8+29*count)
  for i in range(count):
   oid,tid,offset,checksum,flags=struct.unpack_from('<QQQIB',raw,8+29*i)
   self.assertIn(oid,self.new.objects);o=self.new.objects[oid];self.assertEqual((tid,offset),(o['type_id'],o['offset']))
  self.assertEqual(self.old.chunks[b'RFUP'].payload,self.new.chunks[b'RFUP'].payload)
if __name__=='__main__':unittest.main()
