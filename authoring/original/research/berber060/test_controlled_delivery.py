"""Offline controlled-delivery fixtures; never compile or mutate production."""
import copy
import tempfile
import unittest
import wave
from pathlib import Path
import numpy as np
import controlled_delivery as controlled
from jobs import apply_performance_overrides,PERFORMANCE_SEED_STEP
from batch_generation import job_key,single_identity
from generation import pcm_quality
from common import write,read,sha


class ControlledDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.out=self.root/'out';self.art=self.root/'art';self.receipts=self.out/'receipts'
        self.receipts.mkdir(parents=True);self.art.mkdir()
        self.job={'id':'stable-semantic-job','family':'zenata','event':'stop','age':'low',
            'delivery':'high','take':2,'voice_id':'same-actor','seed':800050,
            'model_id':'eleven_v3','generation_text':'[shouting] قفوا',
            'script':{'text':'قفوا','semantic':'stop','nonverbal':False},
            'credential_retry_epoch':1,'network_retry_epoch':2}
        self.plan={'jobs':[self.job],'estimate':{'conservative_usd_with_20_percent_retry':10}}
        self.key=job_key(self.job);self.source=self.root/'source.wav'
        samples=np.full(4800,1000,dtype='<i2');samples[100]=32767;self.pcm=samples.tobytes()
        self.save_source(self.pcm)
        self.receipt={'request_id':self.key,'identity':single_identity(self.job),'job_id':self.job['id'],
            'family':self.job['family'],'status':'review_required','source':str(self.source),
            'source_sha256':sha(self.source),'quality':pcm_quality(self.pcm,24000)}
        self.budget={'cap_usd':100,'reservations':{self.key:{'reserved_usd':.1,'status':'response_received'}}}
        self.save()
    def tearDown(self):self.temp.cleanup()
    def save_source(self,pcm):
        with wave.open(str(self.source),'wb') as stream:
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(24000);stream.writeframes(pcm)
    def save(self):
        write(self.receipts/f'{self.key}.json',self.receipt)
        write(self.art/'recording-plan.json',self.plan);write(self.out/'budget.json',self.budget)
    def preview(self,overrides=None):return controlled.preview(self.plan,self.budget,overrides or {},self.receipts)

    def test_exact_clipped_high_prompt_changes_only_leading_tag_seed_and_metadata(self):
        report=self.preview();self.assertEqual(len(report['decisions']),1)
        decision=report['decisions'][0];override=decision['override'];job=copy.deepcopy(self.job)
        original=copy.deepcopy(job)
        apply_performance_overrides({job['id']:job},{job['id']:override})
        self.assertEqual(job['generation_text'],'[angry] قفوا')
        self.assertEqual(job['seed'],(original['seed']+PERFORMANCE_SEED_STEP)%(2**32))
        for field in ('id','family','event','age','delivery','take','voice_id','script',
                      'credential_retry_epoch','network_retry_epoch'):
            self.assertEqual(job[field],original[field])
        self.assertTrue(job['force_single']);self.assertEqual(job_key(job),override['replacement_request_id'])
        self.assertEqual(override['source_pcm_quality']['clipped_samples'],1)
        self.assertEqual(override['documentation'],controlled.TAG_DOCUMENTATION)

    def test_accepted_unknown_missing_nonverbal_and_normal_not_eligible(self):
        for change in ({'status':'accepted_acoustic'},
                       {'status':'failed_or_unknown','error':'ElevenLabs transport error; outcome unknown'},
                       {'status':'not_generated'}):
            with self.subTest(change=change):
                original=copy.deepcopy(self.receipt);self.receipt.update(change);self.save()
                self.assertEqual(self.preview()['decisions'],[]);self.receipt=original
        self.save();(self.receipts/f'{self.key}.json').unlink()
        self.assertEqual(self.preview()['decisions'],[])
        for change in ({'delivery':'norm'},{'event':'effortpain'},
                       {'script':{'nonverbal':True}},{'generation_text':'قفوا'}):
            old=copy.deepcopy(self.job);self.job.update(change)
            self.assertEqual(self.preview()['decisions'],[]);self.job.clear();self.job.update(old)

    def test_source_hash_and_actual_clipping_required(self):
        self.source.write_bytes(b'corrupt')
        self.assertEqual(self.preview()['decisions'],[])
        self.save_source(np.full(4800,1000,dtype='<i2').tobytes())
        self.receipt['source_sha256']=sha(self.source);self.save()
        report=self.preview();self.assertEqual(report['decisions'],[])
        self.assertIn('not actually clipped',report['held'][0]['reason'])

    def test_preview_is_readonly_apply_once_and_preserves_budget_receipt_plan(self):
        paths=[self.out/'budget.json',self.receipts/f'{self.key}.json',self.art/'recording-plan.json',self.source]
        before={path:path.read_bytes() for path in paths}
        report=controlled.prepare(out=self.out,art=self.art)
        self.assertTrue(report['preview_only']);self.assertFalse((self.art/'performance-overrides.json').exists())
        applied=controlled.prepare(True,out=self.out,art=self.art)
        self.assertFalse(applied['preview_only'])
        overrides=read(self.art/'performance-overrides.json')
        self.assertEqual(overrides[self.job['id']]['epoch'],1)
        proof=Path(overrides[self.job['id']]['decision_file'])
        self.assertEqual(sha(proof),overrides[self.job['id']]['decision_sha256'])
        self.assertEqual(controlled.prepare(True,out=self.out,art=self.art)['decisions'],[])
        for path in paths:self.assertEqual(path.read_bytes(),before[path])

    def test_collision_budget_ceiling_and_active_lock_fail_closed(self):
        override=self.preview()['decisions'][0]['override']
        self.budget['reservations'][override['replacement_request_id']]={'reserved_usd':.2,'status':'failed_or_unknown'}
        self.assertEqual(self.preview()['decisions'],[])
        del self.budget['reservations'][override['replacement_request_id']]
        self.budget['reservations'][self.key]['reserved_usd']=95;self.save()
        self.assertFalse(self.preview()['headroom_ok'])
        with self.assertRaisesRegex(ValueError,'headroom'):controlled.prepare(True,out=self.out,art=self.art)
        self.assertFalse((self.art/'performance-overrides.json').exists())
        lock=self.out/'generation.lock';lock.write_text('active')
        for apply in (False,True):
            with self.assertRaisesRegex(ValueError,'active generation'):controlled.prepare(apply,out=self.out,art=self.art)
        self.assertEqual(lock.read_text(),'active')

    def test_compiler_refuses_changed_actor_context_epoch_or_prompt(self):
        override=self.preview()['decisions'][0]['override']
        for change in ({'voice_id':'other'},{'age':'high'},{'seed':self.job['seed']+1},
                       {'generation_text':'[shouting] Different meaning'}):
            changed={**copy.deepcopy(self.job),**change}
            with self.assertRaises(ValueError):apply_performance_overrides({changed['id']:changed},{changed['id']:override})
        invalid={**override,'epoch':2}
        with self.assertRaises(ValueError):apply_performance_overrides({self.job['id']:copy.deepcopy(self.job)},{self.job['id']:invalid})


if __name__=='__main__':unittest.main()
