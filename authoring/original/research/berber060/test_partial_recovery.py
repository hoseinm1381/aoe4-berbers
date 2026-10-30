"""Partial recovery apply tests use temporary local batches and forbid API."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import batch_generation as bg
import partial_recovery as pr
from common import read,write,sha
from test_batch_generation import fixture,job

class PartialApplyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.out=self.root/'out';self.art=self.root/'art'
        self.patches=[patch.object(pr,'OUT',self.out),patch.object(pr,'ART',self.art),patch.object(bg,'OUT',self.out),patch.object(bg,'ART',self.art),patch.object(bg,'request',side_effect=AssertionError('No API'))]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.jobs=[job(i) for i in range(4)];pcm,alignment=fixture(self.jobs);a=np.frombuffer(pcm,dtype='<i2').copy();a[int(.22*bg.RATE)]=32767
        self.key=bg.request_id(bg.batch_identity(self.jobs));folder=self.out/'batches'/self.key;folder.mkdir(parents=True)
        self.master=self.art/'batch-masters'/(self.key+'.wav');bg.wave_bytes(self.master,a.tobytes(),bg.RATE)
        self.alignment=folder/'alignment.json';write(self.alignment,alignment)
        self.record={'status':'rejected_or_unknown','batch_id':self.key,'identity':bg.batch_identity(self.jobs),'jobs':self.jobs,
            'master':str(self.master),'master_sha256':sha(self.master),'alignment':str(self.alignment),'alignment_sha256':sha(self.alignment),'error':'Clip contains clipped samples'}
        self.path=folder/'receipt.json';write(self.path,self.record)
        for j in self.jobs:write(self.out/'receipts'/(bg.job_key(j)+'.json'),dict(bg._receipt(j,self.key),status='rejected_or_unknown'))
        write(self.art/'recording-plan.json',{'jobs':self.jobs})
    def test_apply_recovers_only_safe_current_members_and_saves_prior_receipts(self):
        report=pr.apply();self.assertEqual(report['recovered_current_members'],3)
        self.assertEqual(read(self.path)['status'],'partially_accepted_acoustic')
        for index,j in enumerate(self.jobs):
            receipt=read(self.out/'receipts'/(bg.job_key(j)+'.json'))
            self.assertEqual(receipt['status'],'rejected_or_unknown' if index==0 else 'accepted_acoustic')
            if index:
                self.assertEqual(sha(receipt['source']),receipt['source_sha256']);self.assertTrue(Path(receipt['partial_recovery_proof']).is_file())
        self.assertEqual(len([p for p in (self.out/'partial-recovery').rglob('*.old-receipt.json') if p.name!='batch.old-receipt.json']),3)
        self.assertFalse((self.out/'generation.lock').exists())
    def test_active_queue_blocks_before_writes(self):
        (self.out/'generation.lock').write_text('active')
        with self.assertRaises(ValueError):pr.apply()
        self.assertEqual(read(self.path)['status'],'rejected_or_unknown')
    def test_different_existing_source_is_preserved_and_batch_not_promoted(self):
        target=self.art/'masters'/(bg.job_key(self.jobs[1])+'.wav');target.parent.mkdir(parents=True);target.write_bytes(b'different bytes')
        result=pr.apply();self.assertEqual(result['recovered_current_members'],0)
        self.assertEqual(target.read_bytes(),b'different bytes');self.assertEqual(read(self.path)['status'],'rejected_or_unknown')
    def test_stale_current_job_identity_is_not_reassigned(self):
        changed=[dict(j,seed=j['seed']+1000) for j in self.jobs];write(self.art/'recording-plan.json',{'jobs':changed})
        report=pr.apply();self.assertEqual(report['recovered_current_members'],0)
        self.assertFalse((self.art/'masters').exists())
    def test_existing_accepted_receipt_is_not_replaced(self):
        key=bg.job_key(self.jobs[1]);rp=self.out/'receipts'/(key+'.json');old=read(rp);old['status']='accepted_acoustic';old['keep']='existing acceptance';write(rp,old)
        digest=sha(rp);result=pr.apply()
        self.assertEqual(result['recovered_current_members'],2);self.assertEqual(sha(rp),digest)
    def test_started_batch_never_promoted(self):
        self.record['status']='response_saved';write(self.path,self.record)
        report=pr.apply();self.assertEqual(report['recovered_current_members'],0)
        self.assertEqual(read(self.path)['status'],'response_saved')
    def test_changed_source_hash_global_failure_never_recovers(self):
        self.master.write_bytes(b'changed')
        report=pr.apply();self.assertEqual(report['recovered_current_members'],0)
        self.assertEqual(read(self.path)['status'],'rejected_or_unknown')

if __name__=='__main__':unittest.main()
