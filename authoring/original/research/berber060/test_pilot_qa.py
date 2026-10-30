import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import pilot_qa as q
from common import write


class ResumeGuards(unittest.TestCase):
    def test_no_second_budget_writer_during_synthesis(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'generation.lock').write_text('active')
            with patch.object(q,'OUT',root),patch.object(q,'Budget') as budget:
                with self.assertRaisesRegex(ValueError,'single budget'):q.transcribe({}, {'request_id':'a'})
                budget.assert_not_called()

    def test_reserved_asr_is_not_blindly_repeated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.object(q,'OUT',root),patch.object(q,'Budget') as budget,patch.object(q.urllib.request,'urlopen') as call:
                budget.return_value.data={'reservations':{'asr:a':{}}}
                with self.assertRaisesRegex(ValueError,'without receipt'):q.transcribe({}, {'request_id':'a'})
                budget.return_value.reserve.assert_not_called();call.assert_not_called()

    def test_changed_source_rejects_old_transcription(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source.wav';source.write_bytes(b'changed')
            write(root/'pilot-asr/a.json',{'source_sha256':'old'})
            with patch.object(q,'OUT',root):
                with self.assertRaisesRegex(ValueError,'source changed'):
                    q.transcribe({}, {'request_id':'a','source':str(source)})


if __name__=='__main__':unittest.main()
