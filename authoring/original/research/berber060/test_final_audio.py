"""Offline final decode currency and normalization guard tests."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import final_audio as fa
from common import read,write,sha
from batch_generation import job_key,single_identity

class FinalAudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.out=self.root/'out';self.art=self.root/'art';self.out.mkdir();self.art.mkdir()
        self.patchers=[patch.object(fa,'OUT',self.out),patch.object(fa,'ART',self.art)]
        for p in self.patchers:p.start();self.addCleanup(p.stop)
        self.job={'id':'j','family':'scout','voice_id':'actor','event':'select','age':'low','delivery':'norm','seed':1,'generation_text':'text'}
        self.key=job_key(self.job);self.plan={'jobs':[self.job]}
        self.source=self.root/'master.wav';self.source.write_bytes(b'master');self.native=self.root/'native.wav';self.native.write_bytes(b'normalized')
        retained=self.root/'pre.wav';retained.write_bytes(b'prenormalized')
        self.proof={'request_id':self.key,'event':'select','output':{'sha256':sha(self.native)},'source':{'sha256':sha(retained)},'recipe':{'retained_input':str(retained),'retained_input_sha256':sha(retained)}}
        self.pp=self.root/'normalization.json';write(self.pp,self.proof)
        self.receipt={'status':'accepted_acoustic','job_id':'j','family':'scout','request_id':self.key,'identity':single_identity(self.job),
            'source':str(self.source),'source_sha256':sha(self.source),'native_path':str(self.native),'native_wav':{'sha256':sha(self.native)},
            'normalization':{'provenance':str(self.pp),'provenance_sha256':sha(self.pp)}}
        self.rp=self.out/'receipts'/(self.key+'.json');write(self.rp,self.receipt)
    def test_normalized_source_identity_and_provenance_required(self):
        self.assertIn(self.key,fa.normalized_receipts(self.plan))
        del self.receipt['normalization'];write(self.rp,self.receipt)
        with self.assertRaises(ValueError):fa.normalized_receipts(self.plan)
    def test_stale_normalization_and_corrupt_native_fail(self):
        self.pp.write_bytes(b'changed')
        with self.assertRaises(ValueError):fa.normalized_receipts(self.plan)
        write(self.pp,self.proof);self.native.write_bytes(b'changed')
        with self.assertRaises(ValueError):fa.normalized_receipts(self.plan)
    def test_corrupt_lossless_source_and_old_receipt_identity_fail(self):
        self.receipt['identity']={};write(self.rp,self.receipt)
        with self.assertRaises(ValueError):fa.normalized_receipts(self.plan)
        self.receipt['identity']=single_identity(self.job);write(self.rp,self.receipt);self.source.write_bytes(b'changed')
        with self.assertRaises(ValueError):fa.normalized_receipts(self.plan)
    def test_parallel_and_serial_preserve_all_results_and_plan_order(self):
        from batch_generation import single_identity,job_key
        jobs=[]
        for seed in (4,2,3):
            j=dict(self.job,id='j'+str(seed),seed=seed);key=job_key(j);jobs.append(j)
            proof=dict(self.proof,request_id=key);path=self.root/(key+'.normalization.json');write(path,proof)
            receipt=copy.deepcopy(self.receipt);receipt.update(request_id=key,job_id=j['id'],identity=single_identity(j),
                normalization={'provenance':str(path),'provenance_sha256':sha(path)})
            write(self.out/'receipts'/(key+'.json'),receipt)
        plan={'jobs':jobs}
        serial=fa.normalized_receipts(plan,workers=1);parallel=fa.normalized_receipts(plan,workers=6)
        self.assertEqual(serial,parallel);self.assertEqual(list(parallel),[job_key(j) for j in jobs])
        path=self.root/(job_key(jobs[1])+'.normalization.json');path.write_bytes(b'corrupt')
        for workers in (1,6):
            with self.assertRaisesRegex(ValueError,'provenance missing or changed'):fa.normalized_receipts(plan,workers=workers)
    def test_worker_bound_does_not_allow_unbounded_validation(self):
        for workers in (0,7):
            with self.assertRaises(ValueError):fa.normalized_receipts(self.plan,workers=workers)

    def test_cached_clipping_silence_and_nonfinite_proof_refused(self):
        good={'status':'passed','decode':{'clipped_samples':0,'duration_seconds':1,'peak':.2,'rms':.05,'snr_db':30}}
        self.assertTrue(fa.valid_decode(good))
        for k,v in [('clipped_samples',1),('rms',0),('snr_db',float('nan')),('duration_seconds',0)]:
            bad=copy.deepcopy(good);bad['decode'][k]=v;self.assertFalse(fa.valid_decode(bad))
    def test_exact_report_coverage_hashes_and_normalization_currency(self):
        expected=[{'source':str(self.native),'source_sha256':sha(self.native),'sha256':'a'*64,'bytes':100,'request_id':self.key,'normalization_provenance_sha256':sha(self.pp)}]
        report={'status':'passed','quality':'Medium','rows':[dict(expected[0],status='passed',decode={'clipped_samples':0,'duration_seconds':1,'peak':.2,'rms':.05,'snr_db':30})]}
        fa.validate_rows(report,expected)
        for field in ('source_sha256','sha256','normalization_provenance_sha256'):
            stale=copy.deepcopy(report);stale['rows'][0][field]='b'*64
            with self.assertRaises(ValueError):fa.validate_rows(stale,expected)
        missing=copy.deepcopy(report);missing['rows']=[]
        with self.assertRaises(ValueError):fa.validate_rows(missing,expected)
        duplicate=copy.deepcopy(report);duplicate['rows']*=2
        with self.assertRaises(ValueError):fa.validate_rows(duplicate,expected)

if __name__=='__main__':unittest.main()
