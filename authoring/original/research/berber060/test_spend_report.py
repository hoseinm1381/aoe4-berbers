"""Pure fixture accounting only: no budget, receipt or report files are read/written."""
import copy,math,unittest
from unittest.mock import patch
import spend_report as s

def budget(**statuses):
    return {'cap_usd':100,'reservations':{key:{'status':value,'reserved_usd':.01} for key,value in statuses.items()}}

class SpendReportTests(unittest.TestCase):
    def test_invalid_credit_headers_never_reduce_or_poison_total(self):
        invalid=(-1,'-0.1','NaN','Infinity','-Infinity',float('nan'),float('inf'),True,{},'garbage')
        rows=[(f'invalid{i}',{'request_id':str(i),'provider_receipt':{'character-cost':v}}) for i,v in enumerate(invalid)]
        rows+=[('valid',{'request_id':'valid','provider_receipt':{'character-cost':'12.5'}}),
               ('zero',{'request_id':'zero','provider_receipt':{'character-cost':'0'}})]
        result=s.build_report(budget(),rows)
        self.assertEqual(result['provider_reported_character_credits'],12.5)
        self.assertEqual(len(result['invalid_credit_receipts']),len(invalid))
        self.assertFalse(result['credit_evidence_complete'])
        self.assertEqual(result['provider_receipts_with_credit_counts'],2)
        for value in invalid:
            with self.assertRaises(ValueError):s.parse_credit(value)

    def test_batch_members_do_not_duplicate_credit_or_unknown_outcome(self):
        parent={'batch_id':'b1','jobs':[{}],'identity':{},'status':'rejected_or_unknown',
            'error':'ElevenLabs transport error; outcome unknown'}
        members=[{'request_id':f'm{i}','batch_id':'b1','identity':{},'status':'rejected_or_unknown',
            'provider_receipt':{'character-cost':'40','request-id':'provider-b1'}} for i in range(8)]
        result=s.build_report(budget(b1='rejected_or_unknown'),[('batch',parent)]+[(f'member{i}',r) for i,r in enumerate(members)])
        self.assertEqual(result['unknown_outcomes'],1)
        self.assertEqual(result['provider_reported_character_credits'],0)

    def test_complete_response_quality_rejection_not_transport_ambiguity(self):
        rows=[('batch',{'batch_id':'b','jobs':[{}],'status':'rejected_or_unknown',
            'master_sha256':'a'*64,'error':'Interphrase boundary is not quiet',
            'provider_receipt':{'character-cost':'25','history-item-id':'h1'}})]
        result=s.build_report(budget(b='rejected_or_unknown'),rows)
        self.assertEqual(result['unknown_outcomes'],0)
        self.assertEqual(result['provider_reported_character_credits'],25)

    def test_rejected_transport_unknown_counts_even_if_headers_exposed(self):
        rows=[('batch',{'batch_id':'b','jobs':[{}],'status':'rejected_or_unknown',
            'error':'ElevenLabs response read error; outcome unknown',
            'provider_receipt':{'request-id':'response-header-only'}})]
        self.assertEqual(s.build_report(budget(b='rejected_or_unknown'),rows)['unknown_outcomes'],1)

    def test_missing_rejected_evidence_and_orphan_reservations_count_conservatively(self):
        result=s.build_report(budget(a='reserved_before_request',b='started',c='failed_or_unknown',d='rejected_or_unknown',e='response_received'),[])
        self.assertEqual(result['unknown_outcomes'],4)
        self.assertEqual({x['attempt_key'] for x in result['unknown_outcome_attempts']},{'a','b','c','d'})

    def test_previous_retry_attempts_are_independently_accounted(self):
        old={'request_id':'job','attempt_key':'job','status':'failed_or_unknown','error':'ElevenLabs transport error; outcome unknown'}
        current={'request_id':'job','attempt_key':'job:retry1','status':'accepted_acoustic','source_sha256':'a'*64,
            'previous_attempts':[old],'provider_receipt':{'character-cost':'9','history-item-id':'h'}}
        result=s.build_report(budget(**{'job':'failed_or_unknown','job:retry1':'response_received'}),[('job',current)])
        self.assertEqual(result['unknown_outcomes'],1)
        self.assertEqual(result['unknown_outcome_attempts'][0]['attempt_key'],'job')
        self.assertEqual(result['provider_reported_character_credits'],9)

    def test_explicit_refusal_and_preconnect_proof_are_known_nontransmitted_outcomes(self):
        rows=[('auth',{'request_id':'a','status':'failed_or_unknown','error':'ElevenLabs HTTP 401; status=invalid_api_key'}),
            ('dns',{'request_id':'d','status':'failed_or_unknown','error':'ElevenLabs preconnect DNS failure; request not transmitted'})]
        self.assertEqual(s.build_report(budget(a='failed_or_unknown',d='failed_or_unknown'),rows)['unknown_outcomes'],0)

    def test_duplicate_provider_receipts_and_conflicts_are_explicit(self):
        rows=[('a',{'request_id':'a','provider_receipt':{'character-cost':'10','history-item-id':'same'}}),
              ('b',{'request_id':'b','provider_receipt':{'character-cost':'10','history-item-id':'same'}}),
              ('c',{'request_id':'c','provider_receipt':{'character-cost':'11','history-item-id':'same'}})]
        result=s.build_report(budget(),rows)
        self.assertEqual(result['provider_reported_character_credits'],10)
        self.assertEqual(len(result['credit_receipt_conflicts']),1)
        self.assertFalse(result['credit_evidence_complete'])

    def test_builder_has_no_side_effects(self):
        data=budget(a='rejected_or_unknown');original=copy.deepcopy(data)
        with patch.object(s,'read',side_effect=AssertionError('No file reads')),patch.object(s,'write',side_effect=AssertionError('No writes')):
            result=s.build_report(data,[])
        self.assertEqual(data,original);self.assertEqual(result['unknown_outcomes'],1)

if __name__=='__main__':unittest.main()
