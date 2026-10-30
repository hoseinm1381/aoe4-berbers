import copy,unittest
import delivery

class DeliveryTests(unittest.TestCase):
    def fixture(self):
        coverage={'jobs':[{'id':'a','status':'accepted'},{'id':'b','status':'rejected'}]}
        manifest={'profiles':[{'family':'test'}],'files':[{'path':'test','sha256':'abc'}],
            'fallbacks':[{'job_id':'b','replacement_job_id':'a','reason':'same contract'}]}
        return coverage,manifest,copy.deepcopy(manifest)
    def test_exact_unresolved_fallbacks_and_current_payloads_pass(self):
        delivery.require_complete_audio(*self.fixture())
    def test_unrelated_or_duplicate_fallback_cannot_mask_missing_job(self):
        c,m,p=self.fixture();m['fallbacks'][0]['job_id']='a'
        with self.assertRaises(ValueError):delivery.require_complete_audio(c,m,p)
        c,m,p=self.fixture();m['fallbacks'].append(dict(m['fallbacks'][0]))
        with self.assertRaises(ValueError):delivery.require_complete_audio(c,m,p)
    def test_stale_manifest_payload_fails(self):
        c,m,p=self.fixture();m['files'][0]['sha256']='stale'
        with self.assertRaises(ValueError):delivery.require_complete_audio(c,m,p)

class ReportingTests(unittest.TestCase):
    def test_request_counts_and_reused_waveform_duration_are_distinct(self):
        rows=[{'id':'a','status':'accepted','source_sha256':'s','native_sha256':'n','duration_seconds':2},
              {'id':'b','status':'accepted','source_sha256':'s','native_sha256':'n','duration_seconds':2},
              {'id':'c','status':'rejected','duration_seconds':0}]
        stats=delivery.audio_statistics({'jobs':rows},{'files':[{'path':'one.wem','sha256':'w'},{'path':'two.wem','sha256':'w'}]})
        self.assertEqual(stats['accepted_request_records'],2);self.assertEqual(stats['unique_source_waveforms'],1)
        self.assertEqual(stats['unique_native_waveforms'],1);self.assertEqual(stats['unique_encoded_wem_payloads'],1)
        self.assertEqual(stats['accepted_request_source_duration_seconds'],4)
        self.assertEqual(stats['unique_source_waveform_duration_seconds'],2)
    def test_gap_report_includes_chronology_substitutions_and_duplicate_shortfall(self):
        coverage={'chronology_gaps':[{'family':'king','age':1}],
            'contexts':[{'family':'scout','distinct_take_shortfall':1}],'distinct_variation_complete':False}
        manifest={'fallbacks':[{'job_id':'bad','replacement_job_id':'good','reason':'same context'}]}
        text=delivery.render_delivery_gaps(coverage,manifest)
        for marker in ('king','scout','bad','good','pending'):self.assertIn(marker,text)
    def test_provisional_comparison_cannot_use_stale_source_or_plan(self):
        receipt={'native_wav':{'sha256':'s'},'normalization':{'provenance_sha256':'p'}}
        report={'status':'objective_comparison_complete','chosen_quality':'Medium','recording_plan_sha256':'plan','rationale':'provisional',
            'rows':[{'conversion':quality,'request_id':'key','source_sha256':'s','normalization_provenance_sha256':'p','sha256':quality,'bytes':10,'family':'scout','decode':{'snr_db':30,'clipped_samples':0}} for quality in ('Low','Medium','High')]}
        result=delivery.comparison_summary(report,'plan',{'key':receipt})
        self.assertEqual(result['chosen_quality'],'Medium');self.assertEqual(result['listening'],'pending')
        report['rows'][0]['source_sha256']='old'
        with self.assertRaises(ValueError):delivery.comparison_summary(report,'plan',{'key':receipt})
        with self.assertRaises(ValueError):delivery.comparison_summary(report,'newplan',{'key':receipt})

class EncodedVariationTests(unittest.TestCase):
    def fixture(self,repeats=1):
        assignments=[];files=[]
        for repeat in range(repeats):
            for index in range(3):
                path=f'civ_malian/malian_b01xx/select_{index}_{repeat}.wem'
                assignments.append({'family':'villager','event':'select','delivery':'inorm','era':'clow',
                    'job_id':f'take{index}','path':path})
                files.append({'path':path,'sha256':'a'*64})
        return {'assignments':assignments},{'files':files}
    def test_three_planned_takes_collapsed_to_one_encoded_payload_have_two_shortfalls(self):
        plan,manifest=self.fixture();report=delivery.encoded_variations(plan,manifest,'plan','manifest')
        context=report['contexts'][0]
        self.assertEqual(context['planned_distinct_takes'],3);self.assertEqual(context['native_slots'],3)
        self.assertEqual(context['encoded_distinct_recordings'],1);self.assertEqual(context['distinct_take_shortfall'],2)
        self.assertFalse(report['encoded_variation_complete'])
        self.assertEqual(report['plan_sha256'],'plan');self.assertEqual(report['audio_manifest_sha256'],'manifest')
        text=delivery.render_delivery_gaps({},manifest,report)
        self.assertIn('Encoded WEM distinct take shortfalls',text);self.assertIn('villager',text)
    def test_repeated_aliases_do_not_inflate_jobs_and_missing_duplicate_maps_fail(self):
        plan,manifest=self.fixture(repeats=2)
        report=delivery.encoded_variations(plan,manifest,'plan','manifest');row=report['contexts'][0]
        self.assertEqual(row['planned_distinct_takes'],3);self.assertEqual(row['native_slots'],6)
        for index,file in enumerate(manifest['files']):file['sha256']=str(index%3)*64
        self.assertTrue(delivery.encoded_variations(plan,manifest,'plan','manifest')['encoded_variation_complete'])
        missing=copy.deepcopy(manifest);missing['files'].pop()
        with self.assertRaises(ValueError):delivery.encoded_variations(plan,missing,'plan','manifest')
        duplicate=copy.deepcopy(manifest);duplicate['files'].append(dict(duplicate['files'][0],path=duplicate['files'][0]['path'].upper()))
        with self.assertRaises(ValueError):delivery.encoded_variations(plan,duplicate,'plan','manifest')
        plan['assignments'].append(dict(plan['assignments'][0]))
        with self.assertRaises(ValueError):delivery.encoded_variations(plan,manifest,'plan','manifest')

if __name__=='__main__':unittest.main()
