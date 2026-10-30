import json
import tempfile
import unittest
from pathlib import Path
from coverage import build_report, digest, identity, key_for, snapshot, markdown, casting_documentation


class CoverageTests(unittest.TestCase):
    def test_casting_history_rendered_without_qualification_promoted_to_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'casting-overrides.json').write_text(json.dumps({'bombard':{
                'voice_id':'new-actor','reason':'Prior actor clipped; abandoned pilot pronunciation uncertain.',
                'qualification':'Six acoustic pilots passed; human listening pending.',
                'qualification_report':str(root/'qualification.json')}}),encoding='utf8')
            report=self.report(root,[self.job()])
            report.update(snapshot_started_utc='test',snapshot_finished_utc='test',
                          casting_substitutions=casting_documentation(root))
            rendered=markdown(report)
            self.assertIn('Prior actor clipped',rendered)
            self.assertIn('human listening pending',rendered)
            self.assertIn('human age not verified',rendered)
            self.assertIn('qualification.json',rendered)
            self.assertEqual(report['accepted_request_records'],0)

    def job(self, jid='a', take=1):
        return dict(id=jid,family='scout',event='select',age='low',delivery='norm',
                    take=take,voice_id='actor',generation_text='حاضر',seed=take)

    def fixture(self, root, job):
        source=root/'source.wav';native=root/'native.wav'
        source.write_bytes(b'example source');native.write_bytes(b'example native')
        receipt=dict(request_id=key_for(job),identity=identity(job),status='accepted_acoustic',
                     source=str(source),native_path=str(native),source_sha256=digest(source.read_bytes()),
                     native_wav={'sha256':digest(native.read_bytes())},
                     quality={'duration_seconds':1.5,'clipped_samples':0})
        (root/(key_for(job)+'.json')).write_text(json.dumps(receipt),encoding='utf8')
        return receipt

    def report(self, root, jobs):
        assignments=[dict(family='scout',event=event,era='clow',delivery='inorm',
                          path=event+'.wem',job_id=jobs[0]['id'])
                     for event in ('select','selectgc')]
        profiles={'families':[{'family':'scout','media':[{'path':a['path']} for a in assignments]+[{'path':'unassigned.wem'}]}]}
        return build_report({'jobs':jobs,'assignments':assignments,'chronology_gaps':[{'family':'scout','gap':'example'}]},profiles,root)

    def test_exact_current_identity_accepted_alias_contexts_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);jobs=[self.job(),self.job('b',2)]
            self.fixture(root,jobs[0]);report=self.report(root,jobs)
            self.assertEqual(report['statuses'],{'accepted':1,'missing':1})
            self.assertEqual(report['duration_seconds'],1.5)
            self.assertEqual(report['source_bytes'],len(b'example source'))
            self.assertEqual([c['event'] for c in report['contexts']],['select','selectgc'])
            self.assertTrue(all(c['accepted_selectable_recordings']==1 for c in report['contexts']))
            self.assertEqual(len(report['profile_paths_without_assignment']),1)
            self.assertEqual(len(report['chronology_gaps']),1)

    def test_wrong_identity_or_changed_audio_never_counted_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);job=self.job();receipt=self.fixture(root,job)
            (root/'source.wav').write_bytes(b'changed')
            self.assertEqual(self.report(root,[job])['accepted_new_recordings'],0)
            receipt['identity']['seed']=999
            (root/(key_for(job)+'.json')).write_text(json.dumps(receipt),encoding='utf8')
            self.assertEqual(self.report(root,[job])['statuses'],{'unknown':1})

    def test_valid_json_wrong_shape_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);job=self.job()
            (root/(key_for(job)+'.json')).write_text('[]',encoding='utf8')
            self.assertEqual(self.report(root,[job])['statuses'],{'unknown':1})

    def test_rejection_unknown_and_quality_review_are_not_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);job=self.job();receipt=self.fixture(root,job)
            for state,expected in [('started','unknown'),('rejected_or_unknown','rejected_or_unknown'),('review_required','review_required')]:
                receipt['status']=state
                (root/(key_for(job)+'.json')).write_text(json.dumps(receipt),encoding='utf8')
                self.assertEqual(self.report(root,[job])['statuses'],{expected:1})
            receipt['status']='accepted_acoustic';receipt['quality']['clipped_samples']=1
            (root/(key_for(job)+'.json')).write_text(json.dumps(receipt),encoding='utf8')
            self.assertEqual(self.report(root,[job])['statuses'],{'review_required':1})

    def test_malformed_receipt_is_unknown_and_snapshot_ignores_tmp(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);job=self.job();path=root/(key_for(job)+'.json')
            path.write_text('{',encoding='utf8')
            path.with_suffix('.json.tmp').write_text('{}',encoding='utf8')
            with self.assertRaises(ValueError):snapshot(path,attempts=1)
            self.assertEqual(self.report(root,[job])['statuses'],{'unknown':1})

    def test_duplicate_accepted_take_bytes_are_one_distinct_recording(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);jobs=[self.job(),self.job('b',2)]
            for job in jobs:self.fixture(root,job)
            assignments=[dict(family='scout',event='select',era='clow',delivery='inorm',
                              path=f'select-{index}.wem',job_id=job['id']) for index,job in enumerate(jobs)]
            profiles={'families':[{'family':'scout','media':[{'path':a['path']} for a in assignments]}]}
            report=build_report({'jobs':jobs,'assignments':assignments},profiles,root)
            self.assertEqual(report['accepted_request_records'],2)
            self.assertEqual(report['accepted_new_recordings'],2)
            self.assertEqual(report['unique_source_waveforms'],1)
            self.assertEqual(report['unique_native_waveforms'],1)
            self.assertEqual(report['families'][0]['accepted_request_records'],2)
            self.assertEqual(report['families'][0]['unique_source_waveforms'],1)
            context=report['contexts'][0]
            self.assertEqual(context['accepted_request_records'],2)
            self.assertEqual(context['accepted_selectable_recordings'],1)
            self.assertEqual(context['duplicate_variation_gap'],1)
            self.assertEqual(context['distinct_take_shortfall'],1)
            self.assertFalse(report['distinct_variation_complete'])
            self.assertEqual(len(report['jobs'][0]['source_sha256']),64)
            self.assertEqual(len(report['jobs'][0]['native_sha256']),64)
            report.update(snapshot_started_utc='test',snapshot_finished_utc='test')
            self.assertIn('duplicate variation gap 1',markdown(report))
            # Corrupt shared source invalidates both records, never retains trusted hashes.
            (root/'source.wav').write_bytes(b'corrupt')
            corrupted=build_report({'jobs':jobs,'assignments':assignments},profiles,root)
            self.assertEqual(corrupted['statuses'],{'unknown':2})
            self.assertEqual(corrupted['unique_source_waveforms'],0)
            self.assertTrue(all(row['source_sha256'] is None for row in corrupted['jobs']))


if __name__=='__main__':unittest.main()
