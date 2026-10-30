"""Explicit replacement planning fixtures; never use real production directories."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import manual_outcomes as manual
from batch_generation import job_key,single_identity,batch_identity
from generation import request_id
from common import read,write,sha


class ManualOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.out=self.root/'out';self.art=self.root/'art';self.out.mkdir();self.art.mkdir()
        self.patches=[patch.object(manual,'OUT',self.out),patch.object(manual,'ART',self.art)]
        for p in self.patches:p.start()
        self.job={'id':'scout-a','family':'scout','generation_text':'Example','voice_id':'actor','seed':50}
        self.key=job_key(self.job)
        self.plan={'jobs':[self.job],'estimate':{'conservative_usd_with_20_percent_retry':10}}
        self.history={'status':'completed_readonly','results':[{'status':'held_no_unique_settings_and_time_match',
            'exact_matches':0,'kind':'single','id':self.key,'job_ids':[self.job['id']]}]}
        self.receipt={'request_id':self.key,'identity':single_identity(self.job),'job_id':self.job['id'],'status':'started'}
        self.budget={'cap_usd':100,'reservations':{self.key:{'reserved_usd':.5,'status':'reserved_before_request'}}}
        write(self.art/'recording-plan.json',self.plan)
        write(self.out/'history-reconciliation/report.json',self.history)
        write(self.out/'receipts'/f'{self.key}.json',self.receipt)
        write(self.out/'budget.json',self.budget)
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def test_new_performance_preserves_budget_and_original_receipt(self):
        budget=(self.out/'budget.json').read_bytes();receipt=(self.out/'receipts'/f'{self.key}.json').read_bytes()
        result=manual.prepare();override=read(self.art/'retake-overrides.json')[self.job['id']]
        self.assertEqual(len(result['decisions']),1)
        self.assertEqual(override['seed_offset'],700000);self.assertTrue(override['force_single'])
        self.assertEqual(result['decisions'][0]['replacement_request_id'],job_key(dict(self.job,seed=700050)))
        self.assertEqual((self.out/'budget.json').read_bytes(),budget)
        self.assertEqual((self.out/'receipts'/f'{self.key}.json').read_bytes(),receipt)
        self.assertFalse((self.out/'generation.lock').exists())

    def test_ceiling_rejection_writes_no_decisions_or_budget(self):
        self.budget['reservations'][self.key]['reserved_usd']=91
        write(self.out/'budget.json',self.budget);before=(self.out/'budget.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'headroom'):manual.prepare()
        self.assertFalse((self.art/'retake-overrides.json').exists())
        self.assertFalse((self.art/'manual-retake-decisions.json').exists())
        self.assertEqual((self.out/'budget.json').read_bytes(),before)
        self.budget['cap_usd']=200;write(self.out/'budget.json',self.budget)
        with self.assertRaisesRegex(ValueError,'ceiling'):manual.prepare()

    def test_history_and_receipt_identity_must_match_current_unknown(self):
        self.history['results'][0]['id']='different-original';write(self.out/'history-reconciliation/report.json',self.history)
        with self.assertRaisesRegex(ValueError,'History investigation'):manual.prepare()
        self.history['results'][0]['id']=self.key;write(self.out/'history-reconciliation/report.json',self.history)
        self.receipt['identity']['seed']=999;write(self.out/'receipts'/f'{self.key}.json',self.receipt)
        with self.assertRaisesRegex(ValueError,'identity changed'):manual.prepare()
        self.assertFalse((self.art/'retake-overrides.json').exists())

    def test_idempotent_after_recompile_even_when_new_receipt_absent(self):
        first=manual.prepare();before=(self.art/'manual-retake-decisions.json').read_bytes()
        self.plan['jobs'][0]['seed']+=700000;write(self.art/'recording-plan.json',self.plan)
        # Already commissioned: a later depleted budget cannot trigger another decision.
        self.budget['reservations'][self.key]['reserved_usd']=99;write(self.out/'budget.json',self.budget)
        second=manual.prepare()
        self.assertEqual(second,first)
        self.assertEqual((self.art/'manual-retake-decisions.json').read_bytes(),before)

    def test_existing_override_is_extended_and_active_lock_blocks_writes(self):
        write(self.art/'retake-overrides.json',{self.job['id']:{'seed_offset':10,'attempt':2,'custom':'retain'}})
        # Current seed already includes the original offset.
        result=manual.prepare();override=read(self.art/'retake-overrides.json')[self.job['id']]
        self.assertEqual(override['seed_offset'],700010);self.assertEqual(override['attempt'],3)
        self.assertEqual(override['custom'],'retain')
        (self.out/'generation.lock').write_text('active')
        with self.assertRaisesRegex(ValueError,'stop'):manual.prepare()
        self.assertEqual((self.out/'generation.lock').read_text(),'active')

    def transport_fixture(self):
        error='IncompleteRead(100 bytes read, 20 more expected)'
        self.receipt.update(status='failed_or_unknown',error=error)
        write(self.out/'receipts'/f'{self.key}.json',self.receipt)
        evidence={'bulk_results_sha256':manual.CAPTURED_BULK_SHA256,
            'non_dns_transport_unknown_records':[{'job_id':self.job['id'],'request_id':self.key,
                'batch_id':None,'status':'failed_or_unknown','error':error}]}
        path=self.out/'manual-outcomes-review-evidence.json';write(path,evidence)
        return patch.object(manual,'TRANSPORT_EVIDENCE_SHA256',sha(path))

    def test_reviewed_transport_is_new_performance_without_history_claim_or_refund(self):
        with self.transport_fixture():
            before=(self.out/'budget.json').read_bytes();receipt=(self.out/'receipts'/f'{self.key}.json').read_bytes()
            report=manual.prepare(True);decision=report['decisions'][0]
            self.assertFalse(decision['provider_history_checked'])
            self.assertEqual(decision['basis'],'explicit_reviewed_transport')
            self.assertNotIn('investigated_history_target',decision)
            self.assertEqual((self.out/'budget.json').read_bytes(),before)
            self.assertEqual((self.out/'receipts'/f'{self.key}.json').read_bytes(),receipt)
            # Recover the same committed decision after an interrupted override write.
            (self.art/'retake-overrides.json').unlink()
            again=manual.prepare(True)
            self.assertEqual(again,report)
            self.assertEqual(read(self.art/'retake-overrides.json')[self.job['id']]['seed_offset'],700000)
            # Subsequent compiled plan has no replacement receipt yet; still exactly once.
            self.plan['jobs'][0]['seed']+=700000;write(self.art/'recording-plan.json',self.plan)
            self.assertEqual(manual.prepare(True),report)

    def test_reviewed_transport_rejects_local_audio_and_changed_evidence(self):
        with self.transport_fixture():
            source=self.art/'masters'/f'{self.key}.wav';source.parent.mkdir();source.write_bytes(b'local evidence')
            with self.assertRaisesRegex(ValueError,'recovery review'):manual.prepare(True)
            self.assertFalse((self.art/'retake-overrides.json').exists())
            source.unlink()
            evidence_path=self.out/'manual-outcomes-review-evidence.json'
            evidence_path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'fingerprint'):manual.prepare(True)

    def test_reviewed_transport_requires_same_current_request_identity(self):
        with self.transport_fixture():
            self.plan['jobs'][0]['seed']+=1;write(self.art/'recording-plan.json',self.plan)
            with self.assertRaisesRegex(ValueError,'current request identity'):manual.prepare(True)
            self.assertFalse((self.art/'retake-overrides.json').exists())

    def test_reviewed_batch_members_keep_one_original_reservation_and_check_master(self):
        jobs=[dict(self.job,age='low',delivery='norm'),dict(self.job,id='scout-b',seed=51,
            generation_text='Other',age='low',delivery='norm')]
        identity=batch_identity(jobs);batch=request_id(identity);error='IncompleteRead(100 bytes read, 20 more expected)'
        rows=[]
        for job in jobs:
            key=job_key(job);receipt={'request_id':key,'identity':single_identity(job),'job_id':job['id'],
                'batch_id':batch,'status':'rejected_or_unknown','error':error}
            write(self.out/'receipts'/f'{key}.json',receipt)
            rows.append({'job_id':job['id'],'request_id':key,'batch_id':batch,'error':error})
        write(self.out/'batches'/batch/'receipt.json',{'identity':identity,'jobs':jobs,'error':error})
        write(self.art/'recording-plan.json',{'jobs':jobs,'estimate':{'conservative_usd_with_20_percent_retry':10}})
        write(self.out/'budget.json',{'cap_usd':100,'reservations':{batch:{'reserved_usd':.6,'status':'rejected_or_unknown'}}})
        evidence=self.out/'manual-outcomes-review-evidence.json'
        write(evidence,{'bulk_results_sha256':manual.CAPTURED_BULK_SHA256,'non_dns_transport_unknown_records':rows})
        before=(self.out/'budget.json').read_bytes()
        with patch.object(manual,'TRANSPORT_EVIDENCE_SHA256',sha(evidence)):
            master=self.art/'batch-masters'/f'{batch}.wav';master.parent.mkdir();master.write_bytes(b'partial proof')
            with self.assertRaisesRegex(ValueError,'recovery review'):manual.prepare(True)
            master.unlink();report=manual.prepare(True)
        self.assertEqual(len(report['decisions']),2)
        self.assertEqual({r['original_attempt_key'] for r in report['decisions']},{batch})
        self.assertEqual((self.out/'budget.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
