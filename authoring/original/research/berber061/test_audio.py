import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from audio import select_one

class SelectionTests(unittest.TestCase):
 def test_one_take_shared_across_ages(self):
  rows=[dict(id='late',event='move',delivery='norm',age='high',take=1,status='accepted'),dict(id='early',event='move',delivery='norm',age='lowest',take=1,status='accepted'),dict(id='extra',event='move',delivery='norm',age='lowest',take=2,status='accepted')]
  self.assertEqual(select_one(rows)[('move','norm')]['id'],'early')
 def test_deliveries_and_nonverbal_are_not_commands(self):
  rows=[dict(id=str(i),event=e,delivery=d,age='none',take=1,status='accepted') for i,(e,d) in enumerate([('move','high'),('move','norm'),('effortpain','none')])]
  self.assertEqual(len(select_one(rows)),3)
 def test_rejected_audio_is_not_selected(self):
  rows=[dict(id='bad',event='move',delivery='norm',age='lowest',take=1,status='review_required'),dict(id='ok',event='move',delivery='norm',age='med',take=2,status='accepted')]
  self.assertEqual(select_one(rows)[('move','norm')]['id'],'ok')

if __name__=='__main__':unittest.main()
