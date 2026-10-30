import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import cleanup_author as ca

class AuthorCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.project=self.root/'wwise';self.research=self.root/'research';self.project.mkdir();self.research.mkdir()
        for path in ('BerberVoices.wproj','Originals/required.wav','Conversion Settings/required.wwu','SoundBanks/preserved.bnk','.cache/Windows/temp.wem','BerberVoices.RS.validationcache'):
            p=self.project/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'input or cache')
        (self.research/'example.py').write_text('pass');cache=self.research/'__pycache__';cache.mkdir();(cache/'example.cpython-313.pyc').write_bytes(b'bytecode')
    def test_explicit_cache_set_preserves_all_editable_inputs_and_soundbanks(self):
        plan=ca.author_inventory(self.project,self.research)
        selected={c['target'] for c in plan['candidates']}
        self.assertEqual(selected,{str(self.project/'.cache'),str(self.project/'BerberVoices.RS.validationcache'),str(self.research/'__pycache__')})
        protected={p['path'] for p in plan['protected']}
        for name in ('Originals/required.wav','Conversion Settings/required.wwu','SoundBanks/preserved.bnk','BerberVoices.wproj'):
            self.assertIn(str(self.project/name),protected)
    def test_bytecode_without_retained_python_source_is_not_disposable(self):
        (self.research/'example.py').unlink()
        with self.assertRaises(ValueError):ca.author_inventory(self.project,self.research)
    def test_wwise_project_is_required(self):
        (self.project/'BerberVoices.wproj').unlink()
        with self.assertRaises(ValueError):ca.author_inventory(self.project,self.research)

    def test_author_owner_junction_is_rejected_before_resolution(self):
        original=Path.is_junction
        def junction(path):return path==self.project or original(path)
        with patch.object(Path,'is_junction',junction):
            with self.assertRaisesRegex(ValueError,'reparse'):ca.author_inventory(self.project,self.research)

if __name__=='__main__':unittest.main()
