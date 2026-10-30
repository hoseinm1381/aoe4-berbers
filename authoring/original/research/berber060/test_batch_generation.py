"""Deterministic fake timestamp/audio tests. No provider requests permitted."""
import base64, copy, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import batch_generation as bg
import generation as singles
from common import read, write

def job(index,text=None,**extra):
    return {'id':f'j{index}','family':'scout','voice_id':'actor-a','age':'low','delivery':'norm',
        'seed':index,'event':'select','generation_text':text or f'Phrase {index}',
        'model_id':'eleven_v3','script':{'nonverbal':False},**extra}

def fixture(jobs,gap=.4,overlap=False):
    chars=[];starts=[];ends=[];spoken=[];cursor=.2
    for index,j in enumerate(jobs):
        if index:
            chars.extend(['\n','\n']);starts.extend([cursor,cursor]);ends.extend([cursor,cursor])
            cursor+=gap
        for ch in j['generation_text']:
            chars.append(ch);starts.append(cursor);ends.append(cursor+.045)
            if ch.isalnum():spoken.append((cursor,cursor+.045))
            cursor+=.05
    if overlap:
        # First speech character of phrase two starts before preceding phrase ends.
        at=len(jobs[0]['generation_text'])+2
        starts[at]=ends[at-3]-.01
    a=np.zeros(int((cursor+.2)*bg.RATE),dtype='<i2')
    for start,end in spoken:
        first=int(start*bg.RATE);last=int(end*bg.RATE)
        a[first:last]=(np.sin(np.arange(last-first)*.19)*5000).astype('<i2')
    return a.tobytes(),{'characters':chars,'character_start_times_seconds':starts,'character_end_times_seconds':ends}

class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.patches=[patch.object(bg,'OUT',self.root/'out'),patch.object(bg,'ART',self.root/'art'),
            patch.object(singles,'OUT',self.root/'out'),patch.object(singles,'ART',self.root/'art'),
            patch.object(bg,'request',side_effect=AssertionError('Real provider request prohibited')),
            patch.object(singles,'request',side_effect=AssertionError('Real provider request prohibited'))]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def budget(self): return bg.Budget(bg.OUT/'budget.json',100)
    def fake_response(self,jobs):
        pcm,alignment=fixture(jobs)
        return json.dumps({'audio_base64':base64.b64encode(pcm).decode(),'alignment':alignment}).encode(),{'request-id':'fake'}

    def test_partial_bad_boundary_refuses_both_neighbors_only(self):
        jobs=[job(i,'Phrase '+str(i)) for i in range(5)]
        pcm,alignment=fixture(jobs);signal=np.frombuffer(pcm,dtype='<i2').copy()
        strict=bg.aligned_splits(jobs,alignment,pcm)
        boundary=strict[1]['right_boundary']
        first=int(boundary['gap_start_seconds']*bg.RATE);last=int(boundary['gap_end_seconds']*bg.RATE)
        signal[first:last]=4000
        with self.assertRaisesRegex(ValueError,'not quiet'):bg.aligned_splits(jobs,alignment,signal.tobytes())
        result=bg.aligned_splits(jobs,alignment,signal.tobytes(),allow_partial=True)
        self.assertEqual({r['request_id'] for r in result['rejected']},{bg.job_key(jobs[1]),bg.job_key(jobs[2])})
        self.assertEqual([r['request_id'] for r in result['splits']],[bg.job_key(jobs[i]) for i in (0,3,4)])
        for accepted in result['splits']:
            original=next(r for r in strict if r['request_id']==accepted['request_id'])
            self.assertEqual(accepted,original)
        self.assertLess(result['splits'][0]['end_sample'],result['splits'][1]['start_sample'])
    def test_partial_clipped_member_refuses_only_it(self):
        jobs=[job(i) for i in range(4)];pcm,alignment=fixture(jobs)
        strict=bg.aligned_splits(jobs,alignment,pcm);signal=np.frombuffer(pcm,dtype='<i2').copy()
        signal[int(strict[1]['speech_start_seconds']*bg.RATE)+20]=32767
        with self.assertRaisesRegex(ValueError,'clipped'):bg.aligned_splits(jobs,alignment,signal.tobytes())
        result=bg.aligned_splits(jobs,alignment,signal.tobytes(),allow_partial=True)
        self.assertEqual([r['request_id'] for r in result['rejected']],[bg.job_key(jobs[1])])
        self.assertEqual(result['splits'],[strict[i] for i in (0,2,3)])
    def test_partial_clean_is_exactly_strict_and_no_overlap(self):
        jobs=[job(i) for i in range(8)];pcm,alignment=fixture(jobs)
        strict=bg.aligned_splits(jobs,alignment,pcm)
        result=bg.aligned_splits(jobs,alignment,pcm,allow_partial=True)
        self.assertEqual(result['splits'],strict);self.assertFalse(result['rejected'])
        self.assertTrue(all(a['end_sample']<b['start_sample'] for a,b in zip(result['splits'],result['splits'][1:])))
    def test_partial_malformed_global_input_still_rejects_all(self):
        jobs=[job(1),job(2)];pcm,alignment=fixture(jobs)
        bad=copy.deepcopy(alignment);bad['characters'][0]='Z'
        with self.assertRaisesRegex(ValueError,'exactly cover'):bg.aligned_splits(jobs,bad,pcm,allow_partial=True)
        bad=copy.deepcopy(alignment);bad['character_end_times_seconds'].pop()
        with self.assertRaisesRegex(ValueError,'timing arrays'):bg.aligned_splits(jobs,bad,pcm,allow_partial=True)
        bad=copy.deepcopy(alignment);bad['character_start_times_seconds'][1]=-.1
        with self.assertRaises(ValueError):bg.aligned_splits(jobs,bad,pcm,allow_partial=True)
        bad=copy.deepcopy(alignment);bad['character_start_times_seconds'][1]=0
        with self.assertRaisesRegex(ValueError,'Nonmonotonic'):bg.aligned_splits(jobs,bad,pcm,allow_partial=True)

    def test_grouping_limits_and_nonverbal_singles(self):
        jobs=[job(i) for i in range(19)]+[job(30,event='effortpain',script={'nonverbal':True}),job(31,delivery='high')]
        groups=bg.plan_batches(jobs)
        self.assertEqual([len(g) for g in groups],[8,8,3,1,1])
        with self.assertRaises(ValueError):bg.batch_identity([jobs[0],jobs[-1]])

    def test_single_request_identity_exact_parity(self):
        j=job(1);pcm,_=fixture([j])
        with patch.object(singles,'request',return_value=(pcm,{})):
            result=singles.synthesize(j,self.budget())
        self.assertEqual(result['request_id'],bg.job_key(j))
        self.assertEqual(result['identity'],bg.single_identity(j))

    def test_normalized_tags_spacing_and_punctuation(self):
        jobs=[job(1,'[shouting] Alpha!'),job(2,'Beta?')]
        spoken=[dict(j,generation_text=j['generation_text'].replace('[shouting] ','')) for j in jobs]
        pcm,alignment=fixture(spoken)
        proof=bg.aligned_splits(jobs,alignment,pcm)
        self.assertEqual(len(proof),2)
        self.assertLess(proof[0]['end_sample'],proof[1]['start_sample'])
        self.assertEqual(proof[0]['normalized_text'],'alpha')

    def test_alignment_mismatch_and_missing_timings_rejected(self):
        jobs=[job(1),job(2)];pcm,alignment=fixture(jobs)
        mismatch=copy.deepcopy(alignment);mismatch['characters'][0]='Z'
        with self.assertRaisesRegex(ValueError,'exactly cover'):bg.aligned_splits(jobs,mismatch,pcm)
        mismatch=copy.deepcopy(alignment);mismatch['character_end_times_seconds'].pop()
        with self.assertRaisesRegex(ValueError,'timing arrays'):bg.aligned_splits(jobs,mismatch,pcm)

    def test_unicode_canonical_composition_retains_timing_spans(self):
        jobs=[job(1,'ألف'),job(2,'Café')]
        aligned_jobs=[job(1,'ا\u0654لف'),job(2,'Cafe\u0301')]
        pcm,alignment=fixture(aligned_jobs)
        result=bg.aligned_splits(jobs,alignment,pcm)
        self.assertEqual([p['normalized_text'] for p in result],['ألف','café'])

    def test_realistic_tail_rounding_six_and_twentyone_ms_clamped(self):
        jobs=[job(1,'Alpha'),job(2,'Beta')]
        pcm,alignment=fixture(jobs)
        for overrun in (.006,.021,.040):
            duration=alignment['character_end_times_seconds'][-1]-overrun
            shortened=pcm[:round(duration*bg.RATE)*2]
            original=copy.deepcopy(alignment)
            result=bg.aligned_splits(jobs,alignment,shortened)
            self.assertEqual(result[-1]['end_sample'],len(shortened)//2)
            self.assertAlmostEqual(result[-1]['speech_end_seconds'],len(shortened)/2/bg.RATE)
            self.assertEqual(result[-1]['raw_speech_end_seconds'],alignment['character_end_times_seconds'][-1])
            self.assertTrue(result[-1]['timing_clamps'])
            self.assertEqual(alignment,original)

    def test_tail_beyond_forty_ms_and_invalid_times_rejected(self):
        jobs=[job(1,'Alpha'),job(2,'Beta')];pcm,alignment=fixture(jobs)
        duration=alignment['character_end_times_seconds'][-1]-.041
        with self.assertRaisesRegex(ValueError,'Invalid alignment time'):
            bg.aligned_splits(jobs,alignment,pcm[:round(duration*bg.RATE)*2])
        for value in (-.041,float('nan'),float('inf'),True):
            bad=copy.deepcopy(alignment);bad['character_start_times_seconds'][0]=value
            with self.assertRaisesRegex(ValueError,'Invalid alignment time'):bg.aligned_splits(jobs,bad,pcm)

    def test_auth_failure_stops_actor_before_next_group(self):
        import threading
        budget=self.budget();budget.stopped=threading.Event();budget.stop_reason=None
        def abort(reason):budget.stop_reason=reason;budget.stopped.set()
        budget.abort=abort
        with patch.object(bg,'Budget',return_value=budget),patch.object(bg,'request',side_effect=RuntimeError('ElevenLabs HTTP 401; status=invalid_api_key')) as fake:
            result=bg.generate_batches([job(i) for i in range(16)],workers=1)
        self.assertEqual(fake.call_count,1)
        self.assertTrue(budget.stopped.is_set())
        self.assertEqual(sum(r['status']=='not_generated' for r in result),8)
        self.assertTrue(all(r.get('reason')=='API authentication rejected' for r in result if r['status']=='not_generated'))

    def test_overlap_short_gap_and_nonquiet_gap_rejected(self):
        jobs=[job(1),job(2)]
        for gap in (0,.05):
            pcm,alignment=fixture(jobs,gap=gap)
            with self.assertRaisesRegex(ValueError,'gap'):bg.aligned_splits(jobs,alignment,pcm)
        pcm,alignment=fixture(jobs,overlap=True)
        with self.assertRaises(ValueError):bg.aligned_splits(jobs,alignment,pcm)
        pcm,alignment=fixture(jobs);a=np.frombuffer(pcm,dtype='<i2').copy()
        a[:]=4000
        with self.assertRaisesRegex(ValueError,'not quiet'):bg.aligned_splits(jobs,alignment,a.tobytes())

    def test_clipped_silent_and_long_rejected(self):
        jobs=[job(1),job(2)];pcm,alignment=fixture(jobs)
        with self.assertRaisesRegex(ValueError,'silent'):bg.aligned_splits(jobs,alignment,bytes(len(pcm)))
        a=np.frombuffer(pcm,dtype='<i2').copy();a[int(.22*bg.RATE)]=32767
        with self.assertRaisesRegex(ValueError,'clipped'):bg.aligned_splits(jobs,alignment,a.tobytes())
        longjob=[job(1,'A'*200),job(2)]
        pcm,alignment=fixture(longjob)
        with self.assertRaisesRegex(ValueError,'too long'):bg.aligned_splits(longjob,alignment,pcm)

    def test_bounded_quiet_search_moves_actual_cuts_inside_verified_window(self):
        jobs=[job(1),job(2)];pcm,alignment=fixture(jobs)
        signal=np.frombuffer(pcm,dtype='<i2').copy()
        left=alignment['character_end_times_seconds'][len(jobs[0]['generation_text'])-1]
        right=alignment['character_start_times_seconds'][len(jobs[0]['generation_text'])+2]
        midpoint=(left+right)/2
        signal[int((midpoint-.025)*bg.RATE):int((midpoint+.025)*bg.RATE)]=800
        original=signal.tobytes();proof=bg.aligned_splits(jobs,alignment,original)
        boundary=proof[0]['right_boundary']
        self.assertNotEqual(boundary['offset_seconds'],0)
        self.assertLessEqual(abs(boundary['offset_seconds']),min(.1,(right-left)/6))
        self.assertEqual(boundary,proof[1]['left_boundary'])
        self.assertLess(proof[0]['end_sample'],proof[1]['start_sample'])
        for cut in (proof[0]['end_sample'],proof[1]['start_sample']):
            self.assertGreaterEqual(cut,boundary['window_start_sample'])
            self.assertLessEqual(cut,boundary['window_end_sample'])
        self.assertEqual(signal.tobytes(),original)

    def test_quiet_window_must_be_full_width_and_within_bound(self):
        signal=np.full(bg.RATE,.02)
        # A 30ms hole cannot fit a 40ms verified window.
        signal[int(.485*bg.RATE):int(.515*bg.RATE)]=0
        with self.assertRaisesRegex(ValueError,'not quiet'):bg.quiet_boundary(signal,.2,.8,bg.RATE)
        signal[:]=.02
        # A valid 50ms hole exists, but beyond the allowed midpoint +/-100ms.
        signal[int(.655*bg.RATE):int(.705*bg.RATE)]=0
        with self.assertRaisesRegex(ValueError,'not quiet'):bg.quiet_boundary(signal,.2,.8,bg.RATE)

    def test_accepted_batch_lossless_restore_and_exact_job_receipts(self):
        jobs=[job(1),job(2)];budget=self.budget()
        with patch.object(bg,'request',return_value=self.fake_response(jobs)) as fake:
            first=bg.synthesize_batch(jobs,budget)
            self.assertEqual(fake.call_count,1)
        self.assertTrue(all(r['status']=='accepted_acoustic' for r in first))
        self.assertEqual([r['request_id'] for r in first],[bg.job_key(j) for j in jobs])
        self.assertEqual(len(budget.data['reservations']),1)
        identity=bg.batch_identity(jobs)
        self.assertAlmostEqual(budget.spent,len(identity['text'])*.30/1000)
        for result in first:Path(result['source']).unlink();Path(result['native_path']).unlink()
        restored=bg.synthesize_batch(jobs,budget)
        self.assertEqual([r['source_sha256'] for r in restored],[r['source_sha256'] for r in first])

    def test_rejected_alignment_never_accepts_jobs_or_retries(self):
        jobs=[job(1),job(2)];body,headers=self.fake_response(jobs)
        value=json.loads(body);value['alignment']['characters'][0]='X'
        with patch.object(bg,'request',return_value=(json.dumps(value).encode(),headers)) as fake:
            first=bg.synthesize_batch(jobs,self.budget())
            second=bg.synthesize_batch(jobs,self.budget())
            self.assertEqual(fake.call_count,1)
        self.assertTrue(all(r['status']=='rejected_or_unknown' for r in first+second))
        self.assertFalse(any((bg.OUT/'wav').glob('*.wav')))

    def test_started_unknown_and_orphan_reservation_never_retry(self):
        jobs=[job(1),job(2)];budget=self.budget();key=bg.request_id(bg.batch_identity(jobs))
        budget.reserve(key,.1)
        result=bg.synthesize_batch(jobs,budget)
        self.assertTrue(all(r['status']=='failed_or_unknown' for r in result))
        with patch.object(bg,'request',side_effect=TimeoutError('fake timeout')) as fake:
            # Distinct clean identities for simulated provider timeout.
            other=[job(3),job(4)]
            first=bg.synthesize_batch(other,budget);second=bg.synthesize_batch(other,budget)
            self.assertEqual(fake.call_count,1)
            self.assertTrue(all(r['status']=='rejected_or_unknown' for r in first+second))

    def test_interrupted_batch_before_member_receipts_does_not_retry(self):
        jobs=[job(1),job(2)];identity=bg.batch_identity(jobs);key=bg.request_id(identity)
        budget=self.budget();budget.reserve(key,.1)
        write(bg.OUT/'batches'/key/'receipt.json',{'identity':identity,'status':'started'})
        result=bg.synthesize_batch(jobs,budget)
        self.assertTrue(all(r['status']=='failed_or_unknown' for r in result))

    def test_resume_identity_and_saved_alignment_hash_guard(self):
        jobs=[job(1),job(2)];budget=self.budget()
        with patch.object(bg,'request',return_value=self.fake_response(jobs)):
            result=bg.synthesize_batch(jobs,budget)
        key=result[0]['batch_id'];path=bg.OUT/'batches'/key/'receipt.json';record=read(path)
        record['identity']['seed']=999;write(path,record)
        with self.assertRaisesRegex(ValueError,'identity changed'):bg.synthesize_batch(jobs,budget)
        record['identity']=bg.batch_identity(jobs);write(path,record)
        Path(record['alignment']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'source or alignment changed'):bg.synthesize_batch(jobs,budget)

    def test_scheduler_serializes_same_actor(self):
        import threading,time
        active=set();guard=threading.Lock();calls=[]
        jobs=[job(i) for i in range(18)]+[job(30+i,voice_id='actor-b',family='archer') for i in range(2)]
        def fake_batch(group,budget):
            actor=group[0]['voice_id']
            with guard:
                self.assertNotIn(actor,active);active.add(actor);calls.append(actor)
            time.sleep(.01)
            with guard:active.remove(actor)
            return [dict(bg._receipt(j,'fake'),status='fake') for j in group]
        with patch.object(bg,'synthesize_batch',side_effect=fake_batch):
            result=bg.generate_batches(jobs,workers=4)
        self.assertEqual(len(result),len(jobs));self.assertEqual(calls.count('actor-a'),3)

    def failed_quality_response(self,group):
        pcm,alignment=fixture(group)
        noisy=np.full(len(pcm)//2,4000,dtype='<i2').tobytes()
        return json.dumps({'audio_base64':base64.b64encode(noisy).decode(),'alignment':alignment}).encode(),{}

    def test_two_received_quality_failures_switch_only_later_jobs_to_singles(self):
        jobs=[job(i) for i in range(24)];single_ids=[]
        def single(j,budget):
            single_ids.append(j['id'])
            return dict(bg._receipt(j,'single-test'),status='accepted_acoustic')
        responses=[self.failed_quality_response(jobs[:8]),self.failed_quality_response(jobs[8:16])]
        with patch.object(bg,'request',side_effect=responses) as post,patch.object(bg,'synthesize',side_effect=single):
            result=bg.generate_batches(jobs,workers=1)
        self.assertEqual(post.call_count,2)
        self.assertEqual(single_ids,[j['id'] for j in jobs[16:]])
        self.assertTrue(all(r['status']=='rejected_or_unknown' for r in result[:16]))
        # Failed batch members remain cached, never retried as singles or batches.
        with patch.object(bg,'request',side_effect=AssertionError('Must not retry')) as post:
            cached=bg.generate_batches(jobs[:16],workers=1)
        post.assert_not_called();self.assertEqual(len(cached),16)

    def test_isolated_quality_failure_does_not_switch(self):
        jobs=[job(i) for i in range(24)]
        responses=[self.failed_quality_response(jobs[:8]),self.fake_response(jobs[8:16]),self.fake_response(jobs[16:])]
        with patch.object(bg,'request',side_effect=responses) as post,patch.object(bg,'synthesize',side_effect=AssertionError('Unexpected single')):
            result=bg.generate_batches(jobs,workers=1)
        self.assertEqual(post.call_count,3)
        self.assertTrue(all(r['status']=='accepted_acoustic' for r in result[8:]))

    def test_single_fallback_still_stops_on_auth_and_preserves_orphan_batch_guard(self):
        jobs=[job(i) for i in range(24)];budget=self.budget()
        responses=[self.failed_quality_response(jobs[:8]),self.failed_quality_response(jobs[8:16])]
        def auth(j,budget):
            budget.abort('API authentication rejected')
            return dict(bg._receipt(j,'single-test'),status='failed_or_unknown')
        with patch.object(bg,'Budget',return_value=budget),patch.object(bg,'request',side_effect=responses),patch.object(bg,'synthesize',side_effect=auth) as single:
            result=bg.generate_batches(jobs,workers=1)
        self.assertEqual(single.call_count,1)
        self.assertTrue(all(r['status']=='not_generated' for r in result[17:]))

    def test_fallback_does_not_bypass_existing_batch_reservation(self):
        jobs=[job(i) for i in range(24)];budget=self.budget()
        key=bg.request_id(bg.batch_identity(jobs[16:]));budget.reserve(key,.1)
        responses=[self.failed_quality_response(jobs[:8]),self.failed_quality_response(jobs[8:16])]
        with patch.object(bg,'Budget',return_value=budget),patch.object(bg,'request',side_effect=responses) as post,patch.object(bg,'synthesize',side_effect=AssertionError('Orphan batch must not become singles')):
            result=bg.generate_batches(jobs,workers=1)
        self.assertEqual(post.call_count,2)
        self.assertTrue(all(r['status']=='failed_or_unknown' for r in result[16:]))

    def test_auth_rate_unknown_and_missing_returned_sources_do_not_count(self):
        group=[job(1),job(2)];identity=bg.batch_identity(group);key=bg.request_id(identity)
        path=bg.OUT/'batches'/key/'receipt.json'
        for error in ('ElevenLabs HTTP 401; status=invalid_api_key','ElevenLabs HTTP 429; status=too_many_concurrent_requests','timeout','Interphrase boundary is not quiet'):
            write(path,{'identity':identity,'status':'rejected_or_unknown','error':error})
            self.assertFalse(bg.received_quality_failure(group))

    def test_prepaid_refusal_stops_batch_route_before_other_pending_calls(self):
        for index,error in enumerate(('ElevenLabs HTTP 400; status=quota_exceeded',
                                      'ElevenLabs HTTP 403; status=insufficient_credits',
                                      'ElevenLabs HTTP 402; status=unknown')):
            with self.subTest(error=error):
                # Unique actor/text identities avoid sharing prior refusal receipts.
                jobs=[job(index*100+i,voice_id='quota-actor-'+str(index)) for i in range(16)]
                with patch.object(bg,'request',side_effect=RuntimeError(error)) as post:
                    result=bg.generate_batches(jobs,workers=1)
                self.assertEqual(post.call_count,1)
                self.assertEqual(sum(r['status']=='not_generated' for r in result),8)
                self.assertTrue(all(r['reason']=='API prepaid quota or payment rejected' for r in result if r['status']=='not_generated'))


    def test_unhandled_actor_write_failure_aborts_other_queued_actors_and_raises(self):
        jobs=[job(i) for i in range(2)]+[job(10+i,voice_id='actor-b',family='archer') for i in range(2)]
        budget=self.budget();original=(bg.OUT/'budget.json').read_bytes()
        with patch.object(bg,'Budget',return_value=budget),patch.object(bg,'synthesize_batch',side_effect=MemoryError('simulated budget write allocation failure')) as dispatch:
            with self.assertRaises(MemoryError):bg.generate_batches(jobs,workers=1)
        self.assertEqual(dispatch.call_count,1)
        self.assertTrue(budget.stopped.is_set())
        self.assertIn('Unexpected local generation failure',budget.stop_reason)
        self.assertEqual((bg.OUT/'budget.json').read_bytes(),original)
        self.assertFalse((bg.OUT/'receipts').exists())


if __name__=='__main__':unittest.main()
