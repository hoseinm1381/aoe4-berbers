"""Offline DNS transport and reconciliation tests; all network access is mocked."""
import copy
import http.client
import json
import socket
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import Mock, patch
import account
import generation
import batch_generation as bg
import reset_dns_failures as reset
from common import read, write


def job(index):
    return {'id':str(index),'family':'scout','event':'select','age':'low','delivery':'norm',
            'take':index,'voice_id':'actor','seed':index,'generation_text':'Phrase '+str(index)}


class DNSAccountTests(unittest.TestCase):
    def test_only_socket_gaierror_during_initial_open_is_typed_and_sanitized(self):
        opener=Mock();opener.open.side_effect=urllib.error.URLError(socket.gaierror(11001,'private hostname text'))
        with patch.object(account,'credential',return_value='test-placeholder'),patch.object(account.urllib.request,'build_opener',return_value=opener) as build:
            with self.assertRaises(account.PreconnectDNSError) as caught:account.request('/v1/text-to-speech/fake',{'text':'example'})
        self.assertEqual(str(caught.exception),account.DNS_ERROR)
        self.assertIsInstance(build.call_args.args[0],account.NoRedirect)
        self.assertEqual(opener.open.call_count,1)

    def test_string_dns_reason_and_partial_reads_are_never_safe_preconnect(self):
        for reason in ('[Errno 11001] getaddrinfo failed',TimeoutError('timeout')):
            opener=Mock();opener.open.side_effect=urllib.error.URLError(reason)
            with patch.object(account,'credential',return_value='test-placeholder'),patch.object(account.urllib.request,'build_opener',return_value=opener):
                with self.assertRaisesRegex(RuntimeError,'outcome unknown') as caught:account.request('/fake',{})
            self.assertNotIsInstance(caught.exception,account.PreconnectDNSError)
        for error in (http.client.IncompleteRead(b'partial',5),urllib.error.URLError(socket.gaierror(11001,'late DNS'))):
            from unittest.mock import MagicMock
            opener=Mock();response=MagicMock();response.__enter__.return_value.read.side_effect=error;opener.open.return_value=response
            with patch.object(account,'credential',return_value='test-placeholder'),patch.object(account.urllib.request,'build_opener',return_value=opener):
                with self.assertRaisesRegex(RuntimeError,'response read error') as caught:account.request('/fake',{})
            self.assertNotIsInstance(caught.exception,account.PreconnectDNSError)

    def test_redirect_is_rejected_before_any_second_host_open(self):
        with self.assertRaises(urllib.error.HTTPError):
            account.NoRedirect().redirect_request(urllib.request.Request('https://api.elevenlabs.io/fake',data=b'body'),None,302,'redirect',{},'https://other.invalid')


class DNSQueueTests(unittest.TestCase):
    def test_dns_stops_single_and_batch_before_other_pending_calls(self):
        for mode in ('single','batch'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                jobs=[job(i) for i in range(16)] if mode=='batch' else [dict(job(i),voice_id='actor'+str(i)) for i in range(2)]
                route=bg if mode=='batch' else generation
                with patch.object(bg,'OUT',root),patch.object(bg,'ART',root/'art'),patch.object(generation,'OUT',root),patch.object(generation,'ART',root/'art'),patch.object(route,'request',side_effect=account.PreconnectDNSError()) as post:
                    results=bg.generate_batches(jobs,workers=1)
                self.assertEqual(post.call_count,1)
                first=read(root/'receipts'/f'{bg.job_key(jobs[0])}.json')
                self.assertEqual(first['transport_proof'],account.DNS_PROOF)
                self.assertEqual(first['failure_kind'],'preconnect_dns')
                self.assertTrue(any(r['status']=='not_generated' for r in results))
                self.assertTrue(all(r['reason']=='API preconnect DNS failure' for r in results if r['status']=='not_generated'))

    def test_unknown_transport_stops_but_is_never_dns_safe_or_released(self):
        for mode in ('single','batch'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                jobs=[job(i) for i in range(16)] if mode=='batch' else [dict(job(i),voice_id='actor'+str(i)) for i in range(2)]
                route=bg if mode=='batch' else generation
                with patch.object(bg,'OUT',root),patch.object(bg,'ART',root/'art'),patch.object(generation,'OUT',root),patch.object(generation,'ART',root/'art'),patch.object(route,'request',side_effect=account.TransportOutcomeUnknown()) as post:
                    result=bg.generate_batches(jobs,workers=1)
                self.assertEqual(post.call_count,1)
                record=read(root/'receipts'/f'{bg.job_key(jobs[0])}.json')
                self.assertNotIn('transport_proof',record)
                self.assertIsNone(reset.classification(record,True))
                budget=read(root/'budget.json');original=copy.deepcopy(budget)
                updated,epochs,proof=reset.reconcile({'jobs':jobs},budget,{},root,True)
                self.assertEqual(updated,original);self.assertEqual(epochs,{})
                self.assertEqual(proof['released_unbilled_estimate_usd'],0)
                self.assertTrue(any(r['status']=='not_generated' for r in result))
        self.assertIn('outcome unknown',generation.provider_stop_reason(http.client.IncompleteRead(b'x',2)))


class DNSResetTests(unittest.TestCase):
    def receipt(self,root,j,**extra):
        key=bg.job_key(j)
        record={'request_id':key,'identity':bg.single_identity(j),'status':'failed_or_unknown',
                'error':account.DNS_ERROR,'failure_kind':'preconnect_dns','transport_proof':dict(account.DNS_PROOF),**extra}
        write(root/'receipts'/f'{key}.json',record);return record

    def test_only_exact_typed_attempt_released_legacy_retained_and_epochs_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);jobs=[job(i) for i in (1,2,3)];keys=[bg.job_key(j) for j in jobs]
            self.receipt(root,jobs[0],attempt_key=keys[0]+':retry1')
            self.receipt(root,jobs[1],error='IncompleteRead(100 bytes read)')
            self.receipt(root,jobs[2],error=reset.LEGACY_DNS,failure_kind=None,transport_proof=None)
            budget={'cap_usd':100,'reservations':{keys[0]:{'reserved_usd':.1,'status':'failed_or_unknown'},
                keys[0]+':retry1':{'reserved_usd':.2,'status':'failed_or_unknown'},
                keys[1]:{'reserved_usd':.3,'status':'failed_or_unknown'},keys[2]:{'reserved_usd':.4,'status':'failed_or_unknown'}}}
            original=copy.deepcopy(budget)
            updated,epochs,proof=reset.reconcile({'jobs':jobs},budget,{},root,True)
            self.assertEqual(budget,original)
            self.assertEqual(proof['released_unbilled_estimate_usd'],.2)
            self.assertEqual(updated['reservations'][keys[0]]['reserved_usd'],.1)
            self.assertEqual(updated['reservations'][keys[1]]['reserved_usd'],.3)
            self.assertEqual(updated['reservations'][keys[2]]['reserved_usd'],.4)
            self.assertEqual(epochs,{'1':1,'3':1});self.assertEqual(proof['reviewed_legacy_jobs'],1)
            again,next_epochs,again_proof=reset.reconcile({'jobs':jobs},updated,epochs,root,True)
            self.assertEqual(next_epochs,epochs);self.assertEqual(again_proof['released_unbilled_estimate_usd'],0)
            self.assertEqual(again,updated)

    def test_batch_members_release_one_attempt_once_and_response_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);jobs=[job(1),job(2)];identity=bg.batch_identity(jobs);key=generation.request_id(identity)
            for j in jobs:self.receipt(root,j,batch_id=key,status='rejected_or_unknown')
            batch={'batch_id':key,'identity':identity,'jobs':jobs,'status':'rejected_or_unknown',
                   'error':account.DNS_ERROR,'failure_kind':'preconnect_dns','transport_proof':dict(account.DNS_PROOF)}
            path=root/'batches'/key/'receipt.json';write(path,batch)
            budget={'cap_usd':100,'reservations':{key:{'reserved_usd':.7,'status':'rejected_or_unknown'}}}
            updated,epochs,proof=reset.reconcile({'jobs':jobs},budget,{},root)
            self.assertEqual(len(proof['selected']),2);self.assertEqual(proof['released_unbilled_estimate_usd'],.7)
            self.assertEqual(len(proof['released_attempts']),1)
            batch['provider_receipt']={'request-id':'connected'};write(path,batch)
            updated,epochs,proof=reset.reconcile({'jobs':jobs},budget,{},root)
            self.assertEqual(proof['selected'],[]);self.assertEqual(updated,budget)

    def test_idle_lock_and_successful_probe_required_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);art=root/'art';art.mkdir();lock=root/'generation.lock'
            lock.write_text('active')
            probe=Mock()
            with self.assertRaises(FileExistsError):reset.reset(out=root,art=art,probe=probe)
            probe.assert_not_called();self.assertEqual(lock.read_text(),'active')
            lock.unlink();probe.side_effect=RuntimeError('Auth/network still unavailable')
            with self.assertRaises(RuntimeError):reset.reset(out=root,art=art,probe=probe)
            self.assertFalse(lock.exists());self.assertFalse((art/'network-retries.json').exists())


if __name__=='__main__':unittest.main()
