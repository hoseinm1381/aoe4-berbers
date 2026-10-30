"""Native 081 fixtures: exact proportional resize, semantic preservation, fail closed."""
import unittest
import integrate as i
class ScaleTests(unittest.TestCase):
 def test_both_actual_castle_landmarks_only_scale_changes(self):
  rows=i.read(i.OUT/'baseline-audit.json')['targets']
  for kind,expected in [('tlemcen',262.5),('marrakech',175.0)]:
   row=next(r for r in rows if r['kind']==kind and 'actor' in r)
   raw,after=i.patch_scale(i.extract(row['actor']).read_bytes(),row['scale'])
   self.assertEqual(after,expected)
 def test_rejects_stale_scale(self):
  raw=i.extract(i.ACTORS['tlemcen']).read_bytes()
  with self.assertRaises(AssertionError):i.patch_scale(raw,150.0)
if __name__=='__main__':unittest.main()
