import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import source_bundle as b

class BundleTests(unittest.TestCase):
 def fixture(self,root,raw=b'original bytes',digest=None):
  target=root/'cache/input.json';bundle=root/'source.zip';index=root/'index.json'
  h=hashlib.sha256(raw).hexdigest()
  with zipfile.ZipFile(bundle,'w') as z:z.writestr(h,raw)
  index.write_text(json.dumps({'bundle':str(bundle),'bundle_sha256':b.sha(bundle),'files':[{'path':str(target),'sha256':digest or h,'member':h,'bytes':len(raw),'kind':'decoded'}]}))
  return target,index
 def test_missing_input_reads_without_expanding(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);target,index=self.fixture(root)
   with patch.object(b,'INDEX',index):self.assertEqual(b.read_bytes(target),b'original bytes')
   self.assertFalse(target.exists())
 def test_archived_glob_size_and_json_read(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);target,index=self.fixture(root,b'{"value":1}')
   with patch.object(b,'INDEX',index):
    self.assertEqual(b.cached_paths(root,'*/input.json'),[target])
    self.assertEqual(b.size(target),11)
    self.assertEqual(b.read_json(target),{'value':1})
 def test_restore_is_scoped_and_preserves_user_edits(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);target,index=self.fixture(root)
   with patch.object(b,'INDEX',index),patch.object(b,'ROOTS',[root]):
    self.assertEqual(b.restore(root/'other'),0)
    self.assertEqual(b.restore(target.parent),1)
    target.write_bytes(b'edited')
    self.assertEqual(b.restore(target.parent),0)
    self.assertEqual(target.read_bytes(),b'edited')
 def test_corrupt_payload_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);target,index=self.fixture(root,digest='0'*64)
   with patch.object(b,'INDEX',index),patch.object(b,'ROOTS',[root]):
    with self.assertRaises(ValueError):b.restore(root)
   self.assertFalse(target.exists())
 def test_outside_destination_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);target,index=self.fixture(root)
   with patch.object(b,'INDEX',index),patch.object(b,'ROOTS',[root/'different']):
    with self.assertRaises(ValueError):b.restore(root)
 def test_portable_export_and_traversal_rejection(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);target,index=self.fixture(root);record=json.loads(index.read_text());record['files'][0].update(scope='project',relative='art/old/input.json');index.write_text(json.dumps(record))
   with patch.object(b,'INDEX',index):
    self.assertEqual(b.export(root/'exported'),1)
    self.assertEqual((root/'exported/project/art/old/input.json').read_bytes(),b'original bytes')
    record['files'][0]['relative']='../escape';index.write_text(json.dumps(record))
    with self.assertRaises(ValueError):b.export(root/'bad-export')
 def test_symlink_parent_refused(self):
  project_output=b.ROOT/'output'
  if project_output.exists() and project_output.is_junction():
   # Exercise the real existing junction without creating or changing it.
   with self.assertRaises(ValueError):b.safe_target(project_output/'source-restore-guard-probe')
   return
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);target,index=self.fixture(root);outside=root/'outside';outside.mkdir()
   try:target.parent.symlink_to(outside,target_is_directory=True)
   except OSError:self.skipTest('symlinks unavailable')
   with patch.object(b,'INDEX',index),patch.object(b,'ROOTS',[root]):
    with self.assertRaises(ValueError):b.restore(root)
   self.assertFalse((outside/target.name).exists())

if __name__=='__main__':unittest.main()
