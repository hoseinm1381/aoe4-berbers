"""Offline wrapper tests. Every source, native WAV and receipt is temporary."""
import copy,shutil,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
import numpy as np
import normalize_all as n
from common import read,write,sha

def wav(path,samples,rate=48000):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(samples.astype('<i2').tobytes())

class NormalizeAllTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.patches=[patch.object(n,'OUT',self.root/'out'),patch.object(n,'ART',self.root/'art')]
        for p in self.patches:p.start()
        self.job={'id':'j1','family':'tuareg','voice_id':'actor','age':'none','delivery':'high','seed':1,
            'event':'effortpain','generation_text':'هُهْ','script':{'nonverbal':True}}
        self.key=n.job_key(self.job);self.receipt=n.OUT/'receipts'/f'{self.key}.json'
        self.master=n.ART/'masters'/f'{self.key}.wav';self.native=n.OUT/'wav'/f'{self.key}.wav'
        samples=(np.sin(np.arange(24000)*.1)*10000).astype('<i2')
        wav(self.master,samples[::2],24000);wav(self.native,samples)
        self.master_hash=sha(self.master);self.native_hash=sha(self.native)
        write(self.receipt,{'status':'accepted_acoustic','job_id':self.job['id'],'request_id':self.key,
            'identity':n.single_identity(self.job),'source':str(self.master),'source_sha256':self.master_hash,
            'native_path':str(self.native),'native_wav':{'sha256':self.native_hash,'duration_seconds':99,'rms':99}})
        self.proof_path=n.OUT/'loudness/normalization-provenance'/f'{self.key}.json'

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def fake_normalize(self,key,event,expected,nonverbal):
        self.assertEqual((key,event,expected,nonverbal),(self.key,'effortpain',self.native_hash,True))
        original=n.OUT/'loudness/native-pre-normalization'/f'{key}.wav';original.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(self.native,original)
        with wave.open(str(self.native),'rb') as w:samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
        wav(self.native,np.rint(samples*.5))
        proof={'request_id':key,'event':event,'source':{'sha256':sha(original)},
            'output':{'sha256':sha(self.native),'path':str(self.native),'integrated_lufs':None,
                'rms_dbfs':-22,'true_peak_dbtp':-16,'duration_seconds':.5},
            'decision':{'applied_gain_db':-6.020599913,'matching_metric':'rms_proxy'},
            'reference':{'target_rms_dbfs':-22,'basis':'short effort stock RMS proxy; no EBU match'},
            'recipe':{'retained_input':str(original),'retained_input_sha256':sha(original)}}
        write(self.proof_path,proof);return proof

    def test_source_preserved_native_stats_and_rms_gain_provenance_updated(self):
        with patch.object(n,'normalize_native',side_effect=self.fake_normalize) as helper:
            result=n.normalize_job(self.job)
        self.assertEqual(helper.call_count,1);self.assertEqual(result['status'],'normalized')
        receipt=read(self.receipt)
        self.assertEqual(sha(self.master),self.master_hash)
        self.assertEqual(receipt['source_sha256'],self.master_hash)
        self.assertEqual(receipt['native_wav']['sha256'],sha(self.native))
        self.assertAlmostEqual(receipt['native_wav']['duration_seconds'],.5)
        self.assertLess(receipt['native_wav']['rms'],1)
        self.assertEqual(receipt['native_wav']['clipped_samples'],0)
        self.assertAlmostEqual(receipt['native_wav']['normalization_gain_db'],-6.020599913)
        self.assertIsNone(receipt['native_wav']['integrated_lufs'])
        self.assertEqual(receipt['normalization']['provenance_sha256'],sha(self.proof_path))
        self.assertTrue(receipt['normalization']['source_untouched'])
        self.assertFalse((n.OUT/'budget.json').exists())

    def test_interrupted_after_audio_replacement_reconciles_without_reapplying_gain(self):
        proof=self.fake_normalize(self.key,'effortpain',self.native_hash,True)
        normalized_hash=sha(self.native)
        with patch.object(n,'normalize_native',side_effect=AssertionError('Must reuse local proof')),patch.object(n,'write',wraps=write) as writer:
            first=n.normalize_job(self.job);second=n.normalize_job(self.job)
        self.assertEqual(writer.call_count,1)  # Reconcile once; current second pass is read-only.
        self.assertEqual(first['native_sha256'],normalized_hash)
        self.assertEqual(second['native_sha256'],normalized_hash)
        self.assertEqual(sha(self.master),self.master_hash)

    def test_fully_current_receipt_still_verified_without_redundant_write(self):
        with patch.object(n,'normalize_native',side_effect=self.fake_normalize):n.normalize_job(self.job)
        before=sha(self.receipt);native=sha(self.native)
        real_quality=n.pcm_quality
        with patch.object(n,'normalize_native',side_effect=AssertionError('Gain must not reapply')),\
             patch.object(n,'write',side_effect=AssertionError('Current receipt must not be rewritten')),\
             patch.object(n,'pcm_quality',wraps=real_quality) as quality,patch.object(n,'sha',wraps=sha) as hashes:
            result=n.normalize_job(self.job)
        self.assertEqual(result['status'],'normalized');self.assertEqual(quality.call_count,1)
        checked={Path(call.args[0]) for call in hashes.call_args_list}
        self.assertTrue({self.master,self.native,self.proof_path}<=checked)
        self.assertIn(Path(read(self.proof_path)['recipe']['retained_input']),checked)
        self.assertEqual(sha(self.receipt),before);self.assertEqual(sha(self.native),native)

    def test_stale_normalized_metadata_is_repaired_and_written(self):
        with patch.object(n,'normalize_native',side_effect=self.fake_normalize):n.normalize_job(self.job)
        receipt=read(self.receipt);receipt['native_wav'].update(rms=99,duration_seconds=99,normalization_gain_db=0)
        write(self.receipt,receipt);native=sha(self.native)
        with patch.object(n,'normalize_native',side_effect=AssertionError('Use existing proof')),patch.object(n,'write',wraps=write) as writer:
            n.normalize_job(self.job)
        self.assertEqual(writer.call_count,1)
        corrected=read(self.receipt)
        self.assertEqual(corrected['native_wav']['duration_seconds'],.5)
        self.assertLess(corrected['native_wav']['rms'],1)
        self.assertAlmostEqual(corrected['native_wav']['normalization_gain_db'],-6.020599913)
        self.assertEqual(sha(self.native),native)

    def test_lossless_source_corruption_rejected_before_normalizing(self):
        raw=bytearray(self.master.read_bytes());raw[-1]^=1;self.master.write_bytes(raw)
        with patch.object(n,'normalize_native',side_effect=AssertionError('Must not normalize')):
            with self.assertRaisesRegex(ValueError,'Lossless source changed'):n.normalize_job(self.job)

    def test_retained_input_corruption_rejected(self):
        proof=self.fake_normalize(self.key,'effortpain',self.native_hash,True)
        retained=Path(proof['recipe']['retained_input']);raw=bytearray(retained.read_bytes());raw[-1]^=1;retained.write_bytes(raw)
        with self.assertRaisesRegex(ValueError,'Retained normalization input changed'):n.normalize_job(self.job)

    def test_cached_proof_identity_and_recipe_hash_corruption_rejected(self):
        proof=self.fake_normalize(self.key,'effortpain',self.native_hash,True)
        for field in ('request_id','event'):
            corrupt=copy.deepcopy(proof);corrupt[field]='different';write(self.proof_path,corrupt)
            with self.assertRaisesRegex(ValueError,'identity differs'):n.normalize_job(self.job)
        corrupt=copy.deepcopy(proof);corrupt['recipe']['retained_input_sha256']='f'*64;write(self.proof_path,corrupt)
        with self.assertRaisesRegex(ValueError,'recipe input hash'):n.normalize_job(self.job)

    def test_previously_recorded_proof_metadata_corruption_rejected(self):
        with patch.object(n,'normalize_native',side_effect=self.fake_normalize):n.normalize_job(self.job)
        proof=read(self.proof_path);proof['decision']['applied_gain_db']=0;write(self.proof_path,proof)
        with self.assertRaisesRegex(ValueError,'Recorded normalization provenance changed'):n.normalize_job(self.job)

    def test_unrelated_expected_native_hash_rejects_crash_reconciliation(self):
        self.fake_normalize(self.key,'effortpain',self.native_hash,True)
        receipt=read(self.receipt);receipt['native_wav']['sha256']='f'*64;write(self.receipt,receipt)
        with self.assertRaisesRegex(ValueError,'provenance differs from accepted receipt'):n.normalize_job(self.job)

    def test_missing_unaccepted_and_wrong_identity_receipts(self):
        receipt=read(self.receipt);receipt['status']='failed_or_unknown';write(self.receipt,receipt)
        self.assertEqual(n.normalize_job(self.job)['status'],'not_accepted')
        receipt['status']='accepted_acoustic';receipt['identity']['seed']=999;write(self.receipt,receipt)
        with self.assertRaisesRegex(ValueError,'current recording identity'):n.normalize_job(self.job)
        self.receipt.unlink();self.assertEqual(n.normalize_job(self.job)['status'],'not_accepted')

    def test_active_generation_lock_blocks_bulk_without_touching_audio(self):
        (n.OUT/'generation.lock').write_text('active')
        with patch.object(n,'normalize_native',side_effect=AssertionError('No production queue')):
            with self.assertRaisesRegex(ValueError,'Generation still active'):n.normalize_all()
        self.assertEqual(sha(self.native),self.native_hash)
        self.assertFalse((n.OUT/'normalization.lock').exists())

if __name__=='__main__':unittest.main()
