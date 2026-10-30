"""Representative encoding selection never scans superseded receipts."""
from unittest.mock import patch
from pathlib import Path
import encoding
import final_audio
import unittest
import test_final_audio as fixtures
from common import write

class EncodingSelectionTests(unittest.TestCase):
    setUp=fixtures.FinalAudioTests.setUp
    def test_superseded_accepted_receipt_is_excluded(self):
        write(self.art/'recording-plan.json',self.plan)
        old=dict(self.receipt,request_id='old',job_id='superseded',native_path='superseded-unverified.wav')
        write(self.out/'receipts/superseded.json',old)
        with patch.object(encoding,'ART',self.art),patch.object(encoding,'OUT',self.out):
            selected=encoding.comparison_sources(families=('scout',))
        self.assertEqual([r['request_id'] for r in selected],[self.key])
        self.assertEqual(selected[0]['native_path'],str(self.native))
    def test_current_unnormalized_source_cannot_be_selected(self):
        write(self.art/'recording-plan.json',self.plan);del self.receipt['normalization'];write(self.rp,self.receipt)
        with patch.object(encoding,'ART',self.art),patch.object(encoding,'OUT',self.out):
            with self.assertRaises(ValueError):encoding.comparison_sources(families=('scout',))

if __name__=='__main__':
    import unittest
    unittest.main()
