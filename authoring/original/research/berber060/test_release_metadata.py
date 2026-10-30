"""Tuareg metadata reports plans separately from accepted waveform snapshots."""
import tempfile,unittest
from pathlib import Path
import release
from common import write,sha
from batch_generation import job_key,single_identity

class MetadataCountsTests(unittest.TestCase):
    def test_planned_and_accepted_duplicate_waveforms_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);master=root/'master.wav';master.write_bytes(b'source');native=root/'native.wav';native.write_bytes(b'native')
            jobs=[{'id':str(i),'family':'tuareg','voice_id':'v','seed':i,'generation_text':'text','event':'select'} for i in range(3)]
            for j in jobs[:2]:
                key=job_key(j);write(root/(key+'.json'),{'request_id':key,'job_id':j['id'],'identity':single_identity(j),'status':'accepted_acoustic',
                  'source':str(master),'source_sha256':sha(master),'native_path':str(native),'native_wav':{'sha256':sha(native)},'quality':{'duration_seconds':1,'clipped_samples':0}})
            result=release.recording_counts({'jobs':jobs},root)
            self.assertEqual(result,{'planned_request_records':3,'accepted_request_records':2,'unique_source_waveforms':1,'unique_native_waveforms':1})
            native.write_bytes(b'changing during generation')
            result=release.recording_counts({'jobs':jobs},root)
            self.assertEqual(result['accepted_request_records'],0);self.assertEqual(result['planned_request_records'],3)

if __name__=='__main__':unittest.main()
