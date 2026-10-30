import importlib.util
from pathlib import Path
import tempfile, unittest, zipfile

class WorkspaceSafety(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('workspace',Path(__file__).with_name('workspace.py'))
        self.w=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.w)
    def test_rejects_escape_and_protected_targets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for p in (root, root/'.git/objects/x', root/'../outside'):
                with self.assertRaises(ValueError): self.w.safe_target(p,[root])
            self.assertEqual(self.w.safe_target(root/'cache/x',[root]),root/'cache/x')
    def test_restore_refuses_overwriting_user_edit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); bundle=root/'bundle.zip';dest=root/'source.txt'
            with zipfile.ZipFile(bundle,'w') as z:z.writestr('blob',b'original')
            dest.write_bytes(b'user edit')
            with zipfile.ZipFile(bundle) as z:
                with self.assertRaises(FileExistsError):self.w.restore_one(z,'blob',dest,self.w.digest(b'original'))
            self.assertEqual(dest.read_bytes(),b'user edit')
    def test_member_override_cannot_escape_or_replace_without_explicit_selection(self):
        for key in ('../bad','/bad','art/../../bad','C:/bad'):
            with self.assertRaises(ValueError):self.w.member_name(key)
        self.assertEqual(self.w.member_name('art/test.rrgeom'),'art/test.rrgeom')
    def test_failed_hash_never_installs_restored_input(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);bundle=root/'bundle.zip';dest=root/'source'
            with zipfile.ZipFile(bundle,'w') as z:z.writestr('blob',b'corrupt')
            with zipfile.ZipFile(bundle) as z:
                with self.assertRaises(ValueError):self.w.restore_one(z,'blob',dest,self.w.digest(b'expected'))
            self.assertFalse(dest.exists())
    def test_cleanup_rejects_changed_input(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'input';p.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                self.w.verify_cleanup_candidate({'path':str(p),'bytes':7,'sha256':self.w.digest(b'earlier')},[root])
    def test_directory_restore_preserves_edits_and_limits_scope(self):
        with tempfile.TemporaryDirectory() as d:
            w=self.w;root=Path(d);w.ROOT=root/'project';w.EXTERNAL=root/'external';w.HERE=w.ROOT/'tools';w.INPUTS=w.EXTERNAL/'inputs'
            w.INPUTS.mkdir(parents=True);bundle=w.INPUTS/'source-blobs.zip';rows=[]
            with zipfile.ZipFile(bundle,'w') as z:
                for relative,raw in [('voices/a',b'a'),('voices/b',b'b'),('other/c',b'c')]:
                    h=w.digest(raw);z.writestr(h,raw);rows.append({'scope':'external','relative':relative,'path':str(w.EXTERNAL/relative),'sha256':h,'member':h})
            w.save(w.HERE/'source-index.json.gz',{'bundle':str(bundle),'bundle_sha256':w.sha(bundle),'files':rows})
            (w.EXTERNAL/'voices').mkdir();(w.EXTERNAL/'voices/a').write_bytes(b'a')
            self.assertEqual(w.restore_inputs(w.EXTERNAL/'voices'),1)
            self.assertEqual((w.EXTERNAL/'voices/b').read_bytes(),b'b');self.assertFalse((w.EXTERNAL/'other').exists())
            (w.EXTERNAL/'voices/a').write_bytes(b'edited')
            with self.assertRaises(FileExistsError):w.restore_inputs(w.EXTERNAL/'voices')
            self.assertEqual((w.EXTERNAL/'voices/a').read_bytes(),b'edited')

if __name__=='__main__':unittest.main()
