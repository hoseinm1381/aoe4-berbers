import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
import restore_cleanup_cache as r
class RestoreTests(unittest.TestCase):
 def test_sources_scope_and_existing_edits(self):
  with tempfile.TemporaryDirectory(prefix='berber-cleanup-test-') as scratch:
   root=Path(scratch);report=root/'report';report.mkdir();cache=root/'cache';cache.mkdir()
   source=root/'source';source.write_bytes(b'kept source');h=hashlib.sha256(source.read_bytes()).hexdigest()
   z=root/'source.zip'
   with zipfile.ZipFile(z,'w') as f:f.writestr('file',source.read_bytes())
   rows=[{'path':str(cache/'copy'),'sha256':h,'restore':{'file':str(source)}},{'path':str(cache/'fromzip'),'sha256':h,'restore':{'zip':str(z),'member':'file'}},{'path':str(root/'outside'),'sha256':h,'restore':{'file':str(source)}}]
   (report/'deletion-plan.json').write_text(json.dumps({'files':rows}));old=r.REPORT;r.REPORT=report
   try:
    self.assertEqual(r.restore(cache),2);self.assertFalse((root/'outside').exists())
    (cache/'copy').write_bytes(b'user edit');self.assertEqual(r.restore(cache),0)
    self.assertEqual((cache/'copy').read_bytes(),b'user edit')
   finally:r.REPORT=old
 def test_corrupt_restore_rejected_without_destination(self):
  with tempfile.TemporaryDirectory(prefix='berber-cleanup-test-') as scratch:
   root=Path(scratch);source=root/'source';source.write_bytes(b'bad')
   dest=root/'cache'/'copy';old=r.REPORT;r.REPORT=root
   (root/'deletion-plan.json').write_text(json.dumps({'files':[{'path':str(dest),'sha256':'0'*64,'restore':{'file':str(source)}}]}))
   try:
    with self.assertRaises(ValueError):r.restore(dest.parent)
    self.assertFalse(dest.exists());self.assertFalse(dest.with_name('copy.cleanup-restore.tmp').exists())
   finally:r.REPORT=old
 def test_existing_temporary_work_is_preserved(self):
  with tempfile.TemporaryDirectory(prefix='berber-cleanup-test-') as scratch:
   root=Path(scratch);source=root/'source';source.write_bytes(b'data');dest=root/'cache/copy';dest.parent.mkdir()
   temp=dest.with_name('copy.cleanup-restore.tmp');temp.write_bytes(b'preexisting work');old=r.REPORT;r.REPORT=root
   (root/'deletion-plan.json').write_text(json.dumps({'files':[{'path':str(dest),'sha256':hashlib.sha256(b'data').hexdigest(),'restore':{'file':str(source)}}]}))
   try:
    with self.assertRaises(FileExistsError):r.restore(dest.parent)
    self.assertEqual(temp.read_bytes(),b'preexisting work')
   finally:r.REPORT=old
if __name__=='__main__':unittest.main()
