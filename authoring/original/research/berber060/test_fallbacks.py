"""Offline same-context fallback preview fixtures; no production files or calls."""
import tempfile
import unittest
from pathlib import Path
import fallbacks
from common import write,sha
from coverage import key_for,identity
from batch_generation import batch_identity
from generation import request_id


class FallbackPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.receipts=self.root/'receipts';self.receipts.mkdir()
    def tearDown(self):self.temp.cleanup()
    def job(self,jid,take=1,**changes):
        return {'id':jid,'family':'archer','event':'select','age':'low','delivery':'norm','take':take,
            'voice_id':'moha','seed':take,'generation_text':'Example '+str(take),
            'script':{'semantic':'select','nonverbal':False},**changes}
    def receipt(self,job,status='accepted_acoustic',**changes):
        key=key_for(job);source=self.root/(key+'-source.wav');native=self.root/(key+'-native.wav')
        source.write_bytes(('source '+key).encode());native.write_bytes(('native '+key).encode())
        record={'status':status,'request_id':key,'identity':identity(job),'job_id':job['id'],'family':job['family'],
            'source':str(source),'native_path':str(native),'source_sha256':sha(source),
            'native_wav':{'sha256':sha(native)},'quality':{'duration_seconds':1,'clipped_samples':0},**changes}
        write(self.receipts/(key+'.json'),record);return record
    def quality_failure(self,job):
        return self.receipt(job,'review_required',quality={'duration_seconds':1,'clipped_samples':1})

    def test_suitable_take_reused_but_never_counted_as_new_or_distinct_variation(self):
        target=self.job('failed',2);donor=self.job('accepted',1)
        self.quality_failure(target);self.receipt(donor)
        report=fallbacks.preview({'jobs':[target,donor]},self.receipts)
        self.assertEqual(len(report['fallbacks']),1)
        self.assertEqual(report['fallbacks'][0]['replacement_job_id'],'accepted')
        self.assertEqual(report['summary']['accepted_request_records'],1)
        self.assertEqual(report['summary']['documented_fallback_jobs'],1)
        self.assertEqual(report['summary']['new_recordings_from_fallbacks'],0)
        self.assertEqual(report['contexts'][0]['planned_take_count'],2)
        self.assertEqual(report['contexts'][0]['distinct_native_waveforms'],1)
        self.assertEqual(report['contexts'][0]['missing_distinct_variation'],1)
        self.assertEqual(report['gaps'],[])

    def test_different_actor_or_context_or_semantics_never_substituted(self):
        changes=[{'voice_id':'previous-archer'},{'family':'scout'},{'event':'attack'},
                 {'age':'high'},{'delivery':'stealth'},
                 {'script':{'semantic':'select','nonverbal':True}},
                 {'script':{'semantic':'heal','nonverbal':False}}]
        target=self.job('failed',2);self.quality_failure(target)
        for index,change in enumerate(changes):
            with self.subTest(change=change):
                donor=self.job('other-'+str(index),1,**change);self.receipt(donor)
                report=fallbacks.preview({'jobs':[target,donor]},self.receipts)
                self.assertEqual(report['fallbacks'],[])
                self.assertIn('no_suitable_accepted_take',[g['status'] for g in report['gaps']])

    def test_corrupt_source_or_native_is_excluded(self):
        target=self.job('failed',2);donor=self.job('accepted',1);self.quality_failure(target)
        for field in ('source','native_path'):
            with self.subTest(field=field):
                receipt=self.receipt(donor);Path(receipt[field]).write_bytes(b'changed')
                report=fallbacks.preview({'jobs':[target,donor]},self.receipts)
                self.assertEqual(report['fallbacks'],[])
                self.assertEqual(report['summary']['accepted_request_records'],0)

    def test_missing_and_not_generated_remain_pending_even_with_explicit_decision(self):
        donor=self.job('accepted',1);self.receipt(donor)
        target=self.job('pending',2)
        decision={'decisions':[{'job_id':target['id'],'request_id':key_for(target),
            'action':'allow_existing_take_fallback','reason':'Reviewed unknown outcome'}]}
        for has_receipt in (False,True):
            with self.subTest(has_receipt=has_receipt):
                if has_receipt:self.receipt(target,'not_generated')
                report=fallbacks.preview({'jobs':[target,donor]},self.receipts,decision)
                self.assertEqual(report['fallbacks'],[])
                self.assertEqual(report['summary']['pending_unattempted_jobs'],1)

    def test_unknown_requires_exact_explicit_root_decision(self):
        target=self.job('unknown',2);donor=self.job('accepted',1);self.receipt(donor)
        self.receipt(target,'failed_or_unknown',error='IncompleteRead(10 bytes read, 20 more expected)')
        report=fallbacks.preview({'jobs':[target,donor]},self.receipts)
        self.assertEqual(report['fallbacks'],[])
        self.assertEqual(report['gaps'][0]['status'],'held_unknown_requires_explicit_decision')
        decision={'decisions':[{'job_id':target['id'],'request_id':key_for(target),
            'action':'allow_existing_take_fallback','reason':'Explicitly reviewed uncertain original; reservation retained'}]}
        approved=fallbacks.preview({'jobs':[target,donor]},self.receipts,decision)
        self.assertEqual(len(approved['fallbacks']),1)
        self.assertEqual(approved['fallbacks'][0]['basis'],'explicit_unknown_decision')
        decision['decisions'][0]['request_id']='stale'
        with self.assertRaises(ValueError):fallbacks.preview({'jobs':[target,donor]},self.receipts,decision)

    def test_batch_quality_needs_exact_saved_master_and_alignment(self):
        target=self.job('failed',2);donor=self.job('accepted',1);self.receipt(donor)
        batch_input=batch_identity([target,donor]);batch=request_id(batch_input)
        error='Interphrase boundary is not quiet'
        self.receipt(target,'rejected_or_unknown',error=error,batch_id=batch)
        folder=self.root/'batches'/batch;folder.mkdir(parents=True)
        master=folder/'master.wav';alignment=folder/'alignment.json'
        master.write_bytes(b'returned PCM fixture');alignment.write_bytes(b'{}')
        write(folder/'receipt.json',{'identity':batch_input,'jobs':[target,donor],'error':error,
            'master':str(master),'master_sha256':sha(master),
            'alignment':str(alignment),'alignment_sha256':sha(alignment)})
        report=fallbacks.preview({'jobs':[target,donor]},self.receipts)
        self.assertEqual(len(report['fallbacks']),1)
        master.write_bytes(b'changed')
        rejected=fallbacks.preview({'jobs':[target,donor]},self.receipts)
        self.assertEqual(rejected['fallbacks'],[])
        self.assertEqual(rejected['gaps'][0]['status'],'held_quality_evidence_unverified')


if __name__=='__main__':unittest.main()
