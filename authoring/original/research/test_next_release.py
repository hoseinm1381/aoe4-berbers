import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import next_release as n
class PackagingTests(unittest.TestCase):
 def test_new_archive_metadata_and_unchanged_voice_payload(self):
  with tempfile.TemporaryDirectory(prefix='berber-next-release-') as folder:
   root=Path(folder);source=root/'source';source.mkdir();sga=root/'new.sga';sga.write_bytes(b'fixture revised archive')
   manifest={'details':{'version':'0.7.3'},'members':[{'path':'Berber_future_kingdom.sga','sha256':'old'}]}
   for kind in ('MAIN-GARRISON','VOICES-INSTALLER'):
    with zipfile.ZipFile(source/('Berber-0.7.3-'+kind+'.zip'),'w') as z:
     if kind=='MAIN-GARRISON':z.writestr('garrison.json',json.dumps(manifest));z.writestr('Berber_future_kingdom.sga',b'old')
     else:z.writestr('NativeAudio/blobs/test',b'fixture voice');z.writestr('Setup-BerberVoices.ps1',b'Import Berber-0.7.3-MAIN-GARRISON.zip')
   with patch.object(n,'SOURCE',source),patch.object(n,'check',return_value={'status':'fixture'}):
    report=n.build('0.8.0','Fixture update',sga,root/'build')
    with zipfile.ZipFile(report['packages'][0]['path']) as z:
     actual=json.loads(z.read('garrison.json'));self.assertEqual(actual['details']['version'],'0.8.0');self.assertEqual(actual['members'][0]['sha256'],hashlib.sha256(sga.read_bytes()).hexdigest());self.assertEqual(z.read('Berber_future_kingdom.sga'),sga.read_bytes())
    with zipfile.ZipFile(report['packages'][1]['path']) as z:
     self.assertEqual(z.read('NativeAudio/blobs/test'),b'fixture voice');self.assertIn(b'0.8.0',z.read('Setup-BerberVoices.ps1'))
    with self.assertRaises(FileExistsError):n.build('0.8.0','Again',sga,root/'build')
 def test_invalid_version_and_summary_rejected_before_dependencies(self):
  for version,summary in [('0.8.0.1','test'),('../escape','test'),('0.7.3','test'),('0.8.0',''),('0.8.0','x'*181)]:
   with self.subTest(version=version):
    with self.assertRaises(ValueError):n.build(version,summary,'missing.sga')
if __name__=='__main__':unittest.main()
