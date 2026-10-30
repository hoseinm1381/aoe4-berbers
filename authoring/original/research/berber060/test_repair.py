"""Temporary-fixture quality retake tests; never call providers or production."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import repair
from batch_generation import job_key,single_identity,batch_identity
from generation import request_id
from common import read,write,sha


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.out=self.root/'out';self.art=self.root/'art';self.out.mkdir();self.art.mkdir()
        self.patches=[patch.object(repair,'OUT',self.out),patch.object(repair,'ART',self.art)]
        for p in self.patches:p.start()
        self.job={'id':'rare-pain','family':'zenata','event':'effortpain','age':'low','delivery':'high',
            'take':2,'voice_id':'actor','seed':700050,'generation_text':'[grunts]',
            'script':{'nonverbal':True},'network_retry_epoch':2,'credential_retry_epoch':1}
        self.key=job_key(self.job);self.source=self.root/'returned.wav';self.source.write_bytes(b'returned source')
        self.receipt={'request_id':self.key,'identity':single_identity(self.job),'job_id':self.job['id'],
            'family':'zenata','status':'review_required','source':str(self.source),'source_sha256':sha(self.source),
            'quality':{'duration_seconds':1,'clipped_samples':3}}
        self.budget={'cap_usd':100,'reservations':{self.key:{'reserved_usd':.5,'status':'response_received'}}}
        write(self.out/'budget.json',self.budget);write(self.art/'recording-plan.json',{'jobs':[self.job]})
        self.save()
    def save(self):write(self.out/'receipts'/f'{self.key}.json',self.receipt)
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def test_verified_rare_effort_preserves_manual_epochs_budget_and_source(self):
        old={'seed_offset':700000,'attempt':1,'manual_outcome_replacement':True,
             'prior_request_id':'original-uncertain','reason':'Explicit manual decision','custom':'preserved'}
        write(self.art/'retake-overrides.json',{self.job['id']:old})
        budget=(self.out/'budget.json').read_bytes();receipt=(self.out/'receipts'/f'{self.key}.json').read_bytes()
        result=repair.prepare_retakes();self.assertEqual(len(result['retakes']),1)
        override=read(self.art/'retake-overrides.json')[self.job['id']]
        self.assertEqual(override['seed_offset'],800000);self.assertEqual(override['attempt'],2)
        self.assertTrue(override['manual_outcome_replacement']);self.assertTrue(override['force_single'])
        self.assertEqual(override['custom'],'preserved')
        self.assertEqual(override['replacement_request_id'],job_key(dict(self.job,seed=800050)))
        self.assertEqual(override['retake_history'][0]['network_retry_epoch'],2)
        self.assertEqual(override['retake_history'][0]['previous_reason'],'Explicit manual decision')
        self.assertEqual((self.out/'budget.json').read_bytes(),budget)
        self.assertEqual((self.out/'receipts'/f'{self.key}.json').read_bytes(),receipt)

    def test_wrong_current_identity_and_corrupt_or_absent_source_are_held(self):
        original=copy.deepcopy(self.receipt)
        for change in ({'identity':{}},{'job_id':'other'},{'source_sha256':'0'*64},{'source':str(self.root/'absent.wav')}):
            self.receipt={**original,**change};self.save()
            result=repair.prepare_retakes();self.assertEqual(result['retakes'],[])
            self.assertEqual(result['unresolved'][0]['status'],'held_invalid_evidence')
            self.assertFalse((self.art/'retake-overrides.json').exists())

    def test_unknown_transport_never_automatically_retried_even_with_source(self):
        self.receipt.update(status='failed_or_unknown',error='ElevenLabs transport error; outcome unknown');self.save()
        result=repair.prepare_retakes()
        self.assertEqual(result['retakes'],[]);self.assertEqual(len(result['unresolved']),1)

    def test_max_two_and_idempotent_same_original_then_avoid_identity_collision(self):
        collision=job_key(dict(self.job,seed=self.job['seed']+100000))
        self.budget['reservations'][collision]={'reserved_usd':.1,'status':'failed_or_unknown'}
        write(self.out/'budget.json',self.budget)
        first=repair.prepare_retakes();override=read(self.art/'retake-overrides.json')[self.job['id']]
        self.assertEqual(override['seed_offset'],200000)
        self.assertNotEqual(override['replacement_request_id'],collision)
        before=(self.art/'retake-overrides.json').read_bytes()
        self.assertEqual(repair.prepare_retakes()['retakes'],[])
        self.assertEqual((self.art/'retake-overrides.json').read_bytes(),before)
        write(self.art/'retake-overrides.json',{self.job['id']:{'attempt':2,'seed_offset':200000}})
        limited=repair.prepare_retakes();self.assertEqual(limited['retakes'],[])
        self.assertEqual(limited['unresolved'][0]['status'],'retake_limit')

    def test_batch_needs_exact_identity_and_both_returned_hashes(self):
        other=dict(self.job,id='other',seed=2,take=1,script={'nonverbal':False},event='select')
        # Quality batches contain spoken jobs, never rare efforts.
        self.job.update(event='select',script={'nonverbal':False})
        self.key=job_key(self.job);self.receipt.update(request_id=self.key,identity=single_identity(self.job),
            status='rejected_or_unknown',error='Interphrase boundary is not quiet',quality={})
        identity=batch_identity([self.job,other]);batch=request_id(identity);self.receipt['batch_id']=batch
        master=self.root/'master.wav';alignment=self.root/'alignment.json';master.write_bytes(b'raw');alignment.write_bytes(b'{}')
        record={'identity':identity,'jobs':[self.job,other],'error':'Interphrase boundary is not quiet',
            'master':str(master),'master_sha256':sha(master),'alignment':str(alignment),'alignment_sha256':sha(alignment)}
        write(self.out/'batches'/batch/'receipt.json',record)
        write(self.out/'budget.json',{'cap_usd':100,'reservations':{batch:{'reserved_usd':.5,'status':'rejected_or_unknown'}}})
        write(self.art/'recording-plan.json',{'jobs':[self.job]});self.save()
        alignment.write_bytes(b'changed')
        self.assertEqual(repair.prepare_retakes()['retakes'],[])
        alignment.write_bytes(b'{}')
        self.assertEqual(len(repair.prepare_retakes()['retakes']),1)

    def test_active_lock_is_preserved(self):
        lock=self.out/'generation.lock';lock.write_text('active')
        with self.assertRaisesRegex(ValueError,'active generation'):repair.prepare_retakes()
        self.assertEqual(lock.read_text(),'active')
        self.assertFalse((self.art/'retake-overrides.json').exists())


if __name__=='__main__':unittest.main()
