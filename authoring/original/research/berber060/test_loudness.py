import math,tempfile,unittest,wave
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import numpy as np
from common import sha,write
import loudness
from loudness import gain_decision,normalize_to_reference,reference_target,normalize_native

class LoudnessTests(unittest.TestCase):
    @contextmanager
    def native_case(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);key='b'*64;target=root/'wav'/f'{key}.wav';target.parent.mkdir()
            with wave.open(str(target),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
                w.writeframes((np.sin(np.arange(24000)*.1)*12000).astype('<i2').tobytes())
            source_hash=sha(target);master=root/'synthesis-master.wav';master.write_bytes(target.read_bytes())
            count=[0]
            def measurement(path):
                count[0]+=1
                return {'integrated_lufs':-15 if count[0]%2 else -21.5,
                    'true_peak_dbtp':-8 if count[0]%2 else -14.5,'sha256':sha(path),'path':str(path)}
            with patch.object(loudness,'OUT',root),patch('loudness.measure',side_effect=measurement),patch('loudness.reference_target',return_value={'target_lufs':-21.5}),patch('loudness.shutil.which',return_value=None):
                yield root,key,target,master,source_hash,count
    def test_reference_attenuation_and_no_dynamics_processing(self):
        r=gain_decision({'integrated_lufs':-15,'true_peak_dbtp':-1},-21.5)
        self.assertEqual(r['applied_gain_db'],-6.5)
        self.assertAlmostEqual(r['predicted_lufs'],-21.5)
        self.assertFalse(r['target_constrained'])

    def test_true_peak_headroom_and_boost_limits(self):
        r=gain_decision({'integrated_lufs':-30,'true_peak_dbtp':-2},-21.5)
        self.assertEqual(r['applied_gain_db'],1)
        self.assertTrue(r['target_constrained'])
        r=gain_decision({'integrated_lufs':-40,'true_peak_dbtp':-30},-21.5)
        self.assertEqual(r['applied_gain_db'],6)

    def test_invalid_measurements_and_config_rejected(self):
        for value in (None,float('inf'),float('nan')):
            with self.assertRaises(ValueError):gain_decision({'integrated_lufs':value,'true_peak_dbtp':-2},-21.5)
        for target in (-50,0):
            with self.assertRaises(ValueError):gain_decision({'integrated_lufs':-15,'true_peak_dbtp':-2},target)

    def test_short_effort_nonfinite_lufs_uses_explicit_stock_rms_proxy(self):
        for missing in (None,float('-inf')):
            r=gain_decision({'integrated_lufs':missing,'rms_dbfs':-12,'true_peak_dbtp':-1},-21.5,target_rms_dbfs=-22)
            self.assertEqual(r['applied_gain_db'],-10)
            self.assertEqual(r['matching_metric'],'rms_proxy')
            self.assertIsNone(r['predicted_lufs'])
            self.assertIn('not an EBU',r['matching_basis'])
            self.assertEqual(r['predicted_rms_dbfs'],-22)
        r=gain_decision({'integrated_lufs':None,'rms_dbfs':-25,'true_peak_dbtp':-1},-17,target_rms_dbfs=-18)
        self.assertEqual(r['applied_gain_db'],0)
        self.assertTrue(r['target_constrained'])

    def test_short_effort_copy_preserves_rms_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'short.wav';target=Path(d)/'copy.wav'
            with wave.open(str(source),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
                w.writeframes((np.sin(np.arange(9600)*.1)*5000).astype('<i2').tobytes())
            with patch('loudness.measure',side_effect=[{'integrated_lufs':None,'rms_dbfs':-19,'true_peak_dbtp':-6},
                {'integrated_lufs':None,'rms_dbfs':-22,'true_peak_dbtp':-9}]):
                result=normalize_to_reference(source,target,-21.5,target_rms_dbfs=-22)
            self.assertEqual(result['decision']['matching_metric'],'rms_proxy')
            self.assertEqual(result['decision']['target_rms_dbfs'],-22)
            self.assertIsNone(result['output']['integrated_lufs'])

    def test_copy_normalization_preserves_source_format_length_and_shape(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.wav';target=Path(d)/'copy.wav'
            samples=(np.sin(np.arange(48000)*.1)*12000).astype('<i2')
            with wave.open(str(source),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(samples.tobytes())
            before=sha(source)
            with patch('loudness.measure',side_effect=[{'integrated_lufs':-15,'true_peak_dbtp':-8},{'integrated_lufs':-21.5,'true_peak_dbtp':-14.5}]):
                normalize_to_reference(source,target,-21.5)
            self.assertEqual(sha(source),before)
            with wave.open(str(target),'rb') as w:
                self.assertEqual((w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()),(1,2,48000,48000))
                output=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
            expected=np.rint(samples*10**(-6.5/20)).astype('<i2')
            self.assertTrue(np.array_equal(output,expected))
            with self.assertRaisesRegex(ValueError,'new output copy'):normalize_to_reference(source,source,-21.5)
            with self.assertRaisesRegex(ValueError,'new output copy'):normalize_to_reference(source,target,-21.5)

    def test_postmeasurement_peak_violation_removes_only_new_copy(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.wav';target=Path(d)/'copy.wav'
            with wave.open(str(source),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(np.full(48000,5000,dtype='<i2').tobytes())
            with patch('loudness.measure',side_effect=[{'integrated_lufs':-23,'true_peak_dbtp':-3},{'true_peak_dbtp':-.5}]):
                with self.assertRaisesRegex(ValueError,'true peak exceeds'):normalize_to_reference(source,target,-21.5)
            self.assertFalse(target.exists());self.assertTrue(source.exists())

    def test_reference_uses_event_matched_efforts_and_conservative_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'reference.json'
            write(p,{'rows':[{'event':'effortpain','kind':'effort','status':'measured','stock':{'integrated_lufs':-16,'rms_dbfs':-17}},
                {'event':'effortpain','kind':'effort','status':'measured','stock':{'integrated_lufs':-18,'rms_dbfs':-19}},
                {'event':'select','kind':'command','status':'measured','stock':{'integrated_lufs':-21.5,'rms_dbfs':-23}}]})
            self.assertEqual(reference_target('effortpain',True,p)['target_lufs'],-17)
            self.assertEqual(reference_target('effortpain',True,p)['target_rms_dbfs'],-18)
            self.assertEqual(reference_target('effortwarcry',True,p)['target_lufs'],-21.5)
            self.assertEqual(reference_target('effortwarcry',True,p)['target_rms_dbfs'],-23)
            self.assertEqual(reference_target('select',False,p)['target_lufs'],-21.5)

    def test_native_wrapper_retains_original_and_returns_receipt_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);key='a'*64;target=root/'wav'/f'{key}.wav';target.parent.mkdir()
            samples=(np.sin(np.arange(48000)*.1)*12000).astype('<i2')
            with wave.open(str(target),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(samples.tobytes())
            original_hash=sha(target);count=[0]
            def measurement(path):
                count[0]+=1
                return {'integrated_lufs':-15 if count[0]==1 else -21.5,'true_peak_dbtp':-8 if count[0]==1 else -14.5,
                    'sha256':sha(path),'path':str(path)}
            with patch.object(loudness,'OUT',root),patch('loudness.measure',side_effect=measurement),patch('loudness.reference_target',return_value={'target_lufs':-21.5}),patch('loudness.shutil.which',return_value=None):
                result=normalize_native(key,'select',original_hash)
                self.assertEqual(sha(root/'loudness/native-pre-normalization'/f'{key}.wav'),original_hash)
                self.assertEqual(sha(target),result['output']['sha256'])
                self.assertTrue(result['receipt_update_required'])
                self.assertEqual(normalize_native(key,'select',sha(target)),result)
                self.assertEqual(normalize_native(key,'select',original_hash),result)
                with self.assertRaisesRegex(ValueError,'differs from normalization provenance'):normalize_native(key,'select','f'*64)
            self.assertFalse((root/'receipts').exists());self.assertFalse((root/'budget.json').exists())

    def test_proof_durable_before_promotion_permission_failure_and_resume(self):
        with self.native_case() as (root,key,target,master,source_hash,count):
            real_replace=Path.replace;attempts=[]
            def denied_native(source,destination):
                if Path(destination)==target:
                    attempts.append(1);raise PermissionError('simulated sharing violation')
                return real_replace(source,destination)
            with patch.object(Path,'replace',denied_native),patch('loudness.time.sleep'):
                with self.assertRaises(PermissionError):normalize_native(key,'select',source_hash)
            self.assertEqual(len(attempts),8)
            self.assertEqual(sha(target),source_hash);self.assertEqual(sha(master),source_hash)
            proof_path=root/'loudness/normalization-provenance'/f'{key}.json'
            proof=loudness.read(proof_path);pending=Path(proof['native_promotion']['pending_output'])
            self.assertEqual(sha(pending),proof['output']['sha256'])
            self.assertEqual(count[0],2)
            resumed=normalize_native(key,'select',source_hash)
            self.assertEqual(resumed,proof);self.assertEqual(count[0],2)
            self.assertEqual(sha(target),proof['output']['sha256']);self.assertFalse(pending.exists())
            self.assertEqual(sha(master),source_hash)

    def test_crash_after_promotion_before_caller_receipt_replays_without_gain(self):
        with self.native_case() as (root,key,target,master,source_hash,count):
            real_replace=loudness._replace_with_retry
            def promote_then_crash(source,destination):
                real_replace(source,destination)
                if Path(destination)==target:raise RuntimeError('simulated crash after promotion')
            with patch('loudness._replace_with_retry',side_effect=promote_then_crash):
                with self.assertRaisesRegex(RuntimeError,'after promotion'):normalize_native(key,'select',source_hash)
            proof=loudness.read(root/'loudness/normalization-provenance'/f'{key}.json')
            self.assertNotEqual(sha(target),source_hash)
            self.assertEqual(sha(target),proof['output']['sha256'])
            self.assertEqual(normalize_native(key,'select',source_hash),proof)
            self.assertEqual(count[0],2);self.assertEqual(sha(master),source_hash)

    def test_proof_write_failure_keeps_original_native_and_retries_from_original(self):
        with self.native_case() as (root,key,target,master,source_hash,count):
            with patch('loudness.write',side_effect=PermissionError('proof write denied')):
                with self.assertRaises(PermissionError):normalize_native(key,'select',source_hash)
            self.assertEqual(sha(target),source_hash);self.assertEqual(sha(master),source_hash)
            self.assertFalse((root/'loudness/normalization-provenance'/f'{key}.json').exists())
            result=normalize_native(key,'select',source_hash)
            self.assertEqual(result['decision']['applied_gain_db'],-6.5)
            self.assertEqual(sha(target),result['output']['sha256'])
            self.assertEqual(count[0],4)

    def test_prepared_proof_rebuilds_missing_pending_from_recorded_gain(self):
        with self.native_case() as (root,key,target,master,source_hash,count):
            real_replace=loudness._replace_with_retry
            def deny_promotion(source,destination):
                if Path(destination)==target:raise PermissionError('before promotion')
                return real_replace(source,destination)
            with patch('loudness._replace_with_retry',side_effect=deny_promotion):
                with self.assertRaises(PermissionError):normalize_native(key,'select',source_hash)
            proof=loudness.read(root/'loudness/normalization-provenance'/f'{key}.json')
            Path(proof['native_promotion']['pending_output']).unlink()
            result=normalize_native(key,'select',source_hash)
            self.assertEqual(sha(target),proof['output']['sha256'])
            self.assertEqual(result,proof);self.assertEqual(count[0],2)

if __name__=='__main__':unittest.main()
