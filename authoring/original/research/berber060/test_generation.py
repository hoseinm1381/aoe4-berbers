import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import generation
from generation import Budget, request_id, safe_relative

class GenerationTests(unittest.TestCase):
    def test_request_identity_tracks_voice_model_text_seed(self):
        a={'text':'حاضر','voice_id':'actor1','model_id':'eleven_v3','seed':1}
        self.assertEqual(request_id(a),request_id(dict(reversed(list(a.items())))))
        for k,v in [('text','نعم'),('voice_id','actor2'),('seed',2)]:
            self.assertNotEqual(request_id(a),request_id({**a,k:v}))
    def test_reservation_persists_and_enforces_cap(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'budget.json';b=Budget(p,1)
            b.reserve('a',.6);b.reserve('a',.6)
            self.assertAlmostEqual(b.spent,.6)
            with self.assertRaises(ValueError):b.reserve('b',.5)
            b=Budget(p,1);self.assertAlmostEqual(b.spent,.6)
            b.reserve('c',.4);self.assertAlmostEqual(b.spent,1)
    def test_cap_cannot_be_silently_raised(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'b.json';Budget(p,1)
            with self.assertRaises(ValueError):Budget(p,2)
    def test_path_rejects_windows_escape(self):
        for name in ['../x','C:/foo','a\\..\\b','/root','a//b']:
            with self.assertRaises(ValueError):safe_relative(name)
        self.assertEqual(safe_relative('masters/abc.wav'),'masters/abc.wav')

    def test_orphan_retry_reservation_never_reissues_paid_call(self):
        from batch_generation import single_identity
        from common import write
        job={'id':'test','family':'tuareg','voice_id':'actor','generation_text':'حاضر','seed':1}
        key=request_id(single_identity(job))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);budget=Budget(root/'budget.json',100)
            budget.reserve(key,.1);budget.reserve(key+':retry1',.1)
            write(root/'receipts'/f'{key}.json',{'status':'failed_or_unknown','error':'ElevenLabs HTTP 409; status=already_running','previous_attempts':[]})
            with patch.object(generation,'OUT',root),patch.object(generation,'ART',root/'art'),patch.object(generation.time,'sleep'),patch.object(generation,'request') as post:
                result=generation.synthesize(job,budget)
            self.assertEqual(result['status'],'failed_or_unknown')
            self.assertIn('reservation',result['error']);post.assert_not_called()

    def test_authentication_failure_stops_other_actors_without_more_calls(self):
        import batch_generation
        jobs=[{'id':str(i),'family':'tuareg','voice_id':'actor'+str(i),'generation_text':'حاضر','seed':i,
               'age':'high','delivery':'norm','event':'select'} for i in (1,2)]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch.object(generation,'OUT',root),patch.object(generation,'ART',root/'art'),patch.object(batch_generation,'OUT',root),patch.object(batch_generation,'ART',root/'art'),patch.object(generation,'request',side_effect=RuntimeError('ElevenLabs HTTP 401; status=invalid_api_key')) as post:
                result=batch_generation.generate_batches(jobs,workers=1)
            self.assertEqual(post.call_count,1)
            self.assertEqual([r['status'] for r in result],['failed_or_unknown','not_generated'])

    def test_prepaid_refusal_stops_single_route_before_other_actors(self):
        import batch_generation
        for error in ('ElevenLabs HTTP 400; status=quota_exceeded',
                      'ElevenLabs HTTP 429; status=insufficient_credits',
                      'ElevenLabs HTTP 402; status=payment_required'):
            with self.subTest(error=error),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                jobs=[{'id':str(i),'family':'tuareg','voice_id':'actor'+str(i),
                       'generation_text':'حاضر','seed':i,'age':'high','delivery':'norm','event':'select'} for i in (1,2)]
                with patch.object(generation,'OUT',root),patch.object(generation,'ART',root/'art'),patch.object(batch_generation,'OUT',root),patch.object(batch_generation,'ART',root/'art'),patch.object(generation,'request',side_effect=RuntimeError(error)) as post:
                    result=batch_generation.generate_batches(jobs,workers=1)
                self.assertEqual(post.call_count,1)
                self.assertEqual([r['status'] for r in result],['failed_or_unknown','not_generated'])
                self.assertEqual(result[1]['reason'],'API prepaid quota or payment rejected')

    def test_concurrency_refusal_remains_nonfatal(self):
        self.assertIsNone(generation.provider_stop_reason(RuntimeError('ElevenLabs HTTP 429; status=too_many_concurrent_requests')))
        self.assertIsNone(generation.provider_stop_reason(RuntimeError('network timeout')))


if __name__=='__main__':unittest.main()
