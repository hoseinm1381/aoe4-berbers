"""Pure receipt selection and aggregation tests; no generator/provider calls."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run_queue as queue
from batch_generation import job_key,single_identity
from common import write


class QueueSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.receipts=self.root/'receipts';self.receipts.mkdir()
        self.a={'id':'a','family':'scout','voice_id':'actor','generation_text':'Example','seed':1}
        self.b=dict(self.a,id='b',seed=2)
    def tearDown(self):self.temp.cleanup()
    def save(self,job,status='accepted_acoustic',**extra):
        record={'request_id':job_key(job),'identity':single_identity(job),'job_id':job['id'],
                'family':job['family'],'status':status,**extra}
        path=self.receipts/(job_key(job)+'.json');write(path,record);return path

    def test_only_absent_current_identity_selected_and_existing_unknown_untouched(self):
        path=self.save(self.a,'failed_or_unknown',error='outcome uncertain');before=path.read_bytes()
        selected=queue.select_missing([self.a,self.b],self.receipts)
        self.assertEqual(selected['pending'],[self.b])
        self.assertEqual(selected['existing'][0]['status'],'failed_or_unknown')
        self.assertEqual(path.read_bytes(),before)
        # An old seeded receipt never masks a deliberately changed current identity.
        changed=dict(self.a,seed=999)
        self.assertEqual(queue.select_missing([changed],self.receipts)['pending'],[changed])

    def test_existing_wrong_identity_or_malformed_file_is_held_not_dispatched(self):
        path=self.save(self.a,identity={})
        selected=queue.select_missing([self.a],self.receipts)
        self.assertEqual(selected['pending'],[]);self.assertEqual(len(selected['held_existing']),1)
        path.write_text('{')
        self.assertEqual(queue.select_missing([self.a],self.receipts)['pending'],[])

    def test_identical_duplicates_skipped_but_conflicting_plan_refused(self):
        selected=queue.select_missing([self.a,copy.deepcopy(self.a)],self.receipts)
        self.assertEqual(selected['pending'],[self.a]);self.assertEqual(len(selected['duplicates_skipped']),1)
        with self.assertRaises(ValueError):queue.select_missing([self.a,dict(self.a,seed=4)],self.receipts)
        with self.assertRaises(ValueError):queue.select_missing([self.a,dict(self.a,id='other')],self.receipts)

    def test_aggregate_verifies_current_identity_and_preserves_pending_stop_reason(self):
        path=self.save(self.a,'accepted_acoustic',source_sha256='unchanged',source='not-read-by-coordinator')
        before=path.read_bytes()
        report=queue.aggregate([self.a,self.b],self.receipts,[{'request_id':job_key(self.b),
            'status':'not_generated','reason':'API transport outcome unknown'}])
        self.assertEqual(report['receipt_status_counts'],{'accepted_acoustic':1,'not_generated':1})
        self.assertEqual(report['results'][1]['reason'],'API transport outcome unknown')
        self.assertFalse(report['source_hashes_verified']);self.assertEqual(path.read_bytes(),before)
        self.save(self.a,family='wrong')
        self.assertEqual(queue.aggregate([self.a],self.receipts)['results'][0]['status'],'held_invalid_receipt')

    def test_active_entry_lock_refused_before_selection_or_dispatch(self):
        (self.root/'generation.lock').write_text('active')
        with patch.object(queue,'OUT',self.root),patch.object(queue,'generate_batches') as dispatch:
            with self.assertRaisesRegex(ValueError,'active'):queue.run()
        dispatch.assert_not_called()

    def test_no_pending_never_calls_generator_or_rebuilds_cached_source(self):
        self.save(self.a);plan=self.root/'plan.json';write(plan,{'jobs':[self.a]})
        with patch.object(queue,'OUT',self.root),patch.object(queue,'generate_batches',side_effect=AssertionError('No dispatch')) as dispatch:
            report=queue.run(plan)
        dispatch.assert_not_called();self.assertEqual(report['initial_pending_requests'],0)
        self.assertFalse(report['plan_changed_during_run'])

    def test_dispatch_gets_only_missing_and_final_snapshot_uses_latest_plan(self):
        cached=self.save(self.a,'failed_or_unknown');before=cached.read_bytes()
        plan=self.root/'plan.json';write(plan,{'jobs':[self.a,self.b]})
        extra=dict(self.a,id='later-plan',seed=99)
        def dispatch(pending,workers):
            self.assertEqual(pending,[self.b]);self.assertEqual(workers,2)
            self.save(self.b)
            write(plan,{'jobs':[self.a,self.b,extra]})
            return []
        with patch.object(queue,'OUT',self.root),patch.object(queue,'generate_batches',side_effect=dispatch) as called:
            report=queue.run(plan,workers=2)
        called.assert_called_once()
        self.assertEqual(cached.read_bytes(),before)
        self.assertTrue(report['plan_changed_during_run'])
        self.assertEqual(report['receipt_status_counts'],{'failed_or_unknown':1,'accepted_acoustic':1,'not_generated':1})
        self.assertFalse(report['plan_changed_during_final_snapshot'])

    def test_dispatch_only_holds_even_bad_existing_paths_without_reading_them(self):
        path=self.save(self.a);path.write_text('{invalid JSON')
        with patch.object(queue,'current_record',side_effect=AssertionError('Existing receipt read')):
            selected=queue.select_absent_paths([self.a,self.b,copy.deepcopy(self.b)],self.receipts)
        self.assertEqual(selected['pending'],[self.b])
        self.assertEqual(len(selected['existing']),1)
        self.assertEqual(len(selected['duplicates_skipped']),1)
        with self.assertRaises(ValueError):queue.select_absent_paths([self.a,dict(self.a,seed=4)],self.receipts)

    def test_dispatch_only_passes_missing_only_never_aggregates_and_flags_changed_plan(self):
        existing=self.save(self.a,'failed_or_unknown');existing.write_text('{bad existing')
        before=existing.read_bytes();plan=self.root/'plan.json';write(plan,{'jobs':[self.a,self.b]})
        original_read=Path.read_bytes
        def read(path):
            if path.parent==self.receipts:raise AssertionError('Receipt bytes must remain unread')
            return original_read(path)
        def dispatch(pending,workers):
            self.assertEqual(pending,[self.b]);self.assertEqual(workers,2)
            write(plan,{'jobs':[self.a,self.b,dict(self.a,id='later',seed=44)]})
            return [{'request_id':job_key(self.b),'job_id':self.b['id'],'status':'not_generated','reason':'stop gate'}]
        with patch.object(queue,'OUT',self.root),patch.object(queue,'generate_batches',side_effect=dispatch) as called,patch.object(queue,'aggregate',side_effect=AssertionError('No aggregate')),patch.object(Path,'read_bytes',read):
            report=queue.run(plan,workers=2,dispatch_only=True)
        called.assert_called_once();self.assertEqual(existing.read_bytes(),before)
        self.assertTrue(report['plan_changed_during_run']);self.assertFalse(report['existing_receipts_read'])
        self.assertEqual(report['initial_existing_paths_held_unread'],1)
        self.assertEqual(report['dispatch_status_counts'],{'not_generated':1})
        self.assertNotIn('receipt_status_counts',report)
        self.assertNotIn('results',report)

    def test_dispatch_only_refuses_active_generation_before_any_selection(self):
        (self.root/'generation.lock').write_text('active')
        with patch.object(queue,'OUT',self.root),patch.object(queue,'select_absent_paths') as select,patch.object(queue,'generate_batches') as dispatch:
            with self.assertRaisesRegex(ValueError,'active'):queue.run(dispatch_only=True)
        select.assert_not_called();dispatch.assert_not_called()


if __name__=='__main__':unittest.main()
