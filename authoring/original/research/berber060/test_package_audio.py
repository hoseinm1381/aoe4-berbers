"""Offline package integrity tests; no game paths or provider calls."""
import copy, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import package_audio as package
from common import OUT, read, write, sha
from profiles import parse_profile
from batch_generation import job_key, single_identity

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.profile=copy.deepcopy(read(OUT/'profiles/manifest.json')['families'][2])
        self.profiles={'families':[self.profile]}
        self.job={'id':'test','family':self.profile['family'],'event':'select','age':'low','delivery':'norm',
                  'generation_text':'test','voice_id':'test','seed':1}
        self.key=job_key(self.job)
        self.plan={'jobs':[self.job],'assignments':[{'family':self.profile['family'],'path':m['path'].replace('\\','/').lower(),'job_id':'test'} for m in self.profile['media']]}
        self.wav=self.root/'source.wav';self.wav.write_bytes(b'validated wav fixture')
        self.wem=self.root/'source.wem';self.wem.write_bytes(b'qualified WEM fixture')
        self.receipts=self.root/'receipts';self.receipts.mkdir()
        self.receipt={'status':'accepted_acoustic','request_id':self.key,'identity':single_identity(self.job),
            'job_id':'test','family':self.job['family'],'native_path':str(self.wav),'native_wav':{'sha256':sha(self.wav)}}
        self.encoding={self.key:{'source':str(self.wav),'source_sha256':sha(self.wav),'wem':str(self.wem),
             'sha256':sha(self.wem),'bytes':self.wem.stat().st_size}}
        self.save()
        self.inspect=patch.object(package,'inspect_wem',return_value={'sha256':sha(self.wem),'bytes':self.wem.stat().st_size})
        self.inspect.start();self.addCleanup(self.inspect.stop)
    def save(self):write(self.receipts/(self.key+'.json'),self.receipt)
    def prepare(self):return package.prepare(self.plan,self.profiles,self.receipts,self.encoding)
    def test_all_aliases_covered_and_single_content_blob(self):
        result=self.prepare();media=[r for r in result['files'] if r['path'].endswith('.wem')]
        self.assertEqual(len(media),len(self.plan['assignments']))
        self.assertEqual(len({r['payload'] for r in media}),1)
        self.assertEqual(len(result['profiles']),1)
    def test_missing_or_old_receipt_fails_closed(self):
        for change in ({'status':'review_required'},{'request_id':'old'},{'identity':{}},{'job_id':'old'}):
            original=copy.deepcopy(self.receipt);self.receipt.update(change);self.save()
            with self.assertRaises(ValueError):self.prepare()
            self.receipt=original
    def test_changed_wav_or_wem_rejected(self):
        self.wav.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):self.prepare()
        self.wav.write_bytes(b'validated wav fixture');self.wem.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):self.prepare()
    def test_alias_collision_and_missing_spd_reference_rejected(self):
        self.plan['assignments'].append(dict(self.plan['assignments'][0],path=self.plan['assignments'][0]['path'].upper()))
        with self.assertRaises(ValueError):self.prepare()
        self.plan['assignments']=self.plan['assignments'][:-2]
        with self.assertRaises(ValueError):self.prepare()
    def test_changed_profile_hash_rejected(self):
        self.profile['profile_sha256']='0'*64
        with self.assertRaises(ValueError):self.prepare()
    def test_fallback_requires_same_contract_and_reason(self):
        second=dict(self.job,id='replacement',seed=2)
        self.plan['jobs'].append(second)
        for fallback in ({'job_id':'test','replacement_job_id':'replacement','reason':''},
                         {'job_id':'test','replacement_job_id':'unknown','reason':'same event replacement'}):
            with self.assertRaises(ValueError):package.prepare(self.plan,self.profiles,self.receipts,self.encoding,{'fallbacks':[fallback]})
        second['age']='high'
        with self.assertRaises(ValueError):package.prepare(self.plan,self.profiles,self.receipts,self.encoding,{'fallbacks':[{'job_id':'test','replacement_job_id':'replacement','reason':'rejected take'}]})
    def test_documented_same_contract_fallback_is_audited(self):
        second=dict(self.job,id='replacement',seed=2)
        self.plan['jobs'].append(second)
        key=job_key(second)
        replacement=dict(self.receipt,request_id=key,job_id='replacement',identity=single_identity(second))
        write(self.receipts/(key+'.json'),replacement)
        self.encoding[key]=dict(self.encoding[self.key])
        (self.receipts/(self.key+'.json')).unlink()
        fallback={'fallbacks':[{'job_id':'test','replacement_job_id':'replacement','reason':'rejected first take; same event/age/delivery'}]}
        result=package.prepare(self.plan,self.profiles,self.receipts,self.encoding,fallback)
        self.assertEqual(result['fallbacks'],fallback['fallbacks'])
        self.assertEqual(result['coverage']['accepted_recordings'],1)
    def test_wrong_family_media_identity_rejected(self):
        self.profile['private_media_identity']='malian_b99xx'
        with self.assertRaises(ValueError):self.prepare()
    def test_medium_manifest_cannot_point_at_other_quality(self):
        folder=self.root/'Medium';folder.mkdir()
        manifest=folder/'encoding-manifest.json'
        write(manifest,self.encoding)
        with self.assertRaises(ValueError):package.load_medium(manifest)
        windows=folder/'Windows';windows.mkdir()
        import shutil
        target=windows/(self.key+'.wem');shutil.copyfile(self.wem,target)
        self.encoding[self.key]['wem']=str(target);write(manifest,self.encoding)
        self.assertIn(self.key,package.load_medium(manifest))
    def test_unsafe_path_rejected(self):
        self.plan['assignments'][0]['path']='../stock.wem'
        with self.assertRaises(ValueError):self.prepare()
    def test_package_validator_detects_corrupt_payload(self):
        result=self.prepare();destination=self.root/'package'
        package.stage(result,destination)
        package.validate(destination)
        next((destination/'payloads').glob('*.wem')).write_bytes(b'corrupt')
        with self.assertRaises(ValueError):package.validate(destination)

if __name__=='__main__':unittest.main()
