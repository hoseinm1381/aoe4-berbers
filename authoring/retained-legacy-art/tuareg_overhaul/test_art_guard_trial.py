import os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'art/tuareg_shield'))
os.environ['TUAREG_POSTURE_TEST_MODULE']='../tuareg_overhaul/tuareg_q_art_guard_trial.scar'
from test_q_posture_trial import PostureTests
class GuardTests(PostureTests):
    def setUp(self):
        super().setUp()
        self.lua.execute('motion_calls=0; function Entity_IsMoving(e) motion_calls=motion_calls+1;return e.moving==true end')
    def test_active_owned_guard_repairs_external_clear(self):
        self.cast();self.entity.pose=False;self.advance(2)
        self.assertTrue(self.entity.pose)
        self.assert_no_gameplay_command()
    def test_move_stop_does_not_lower_guard_or_issue_orders(self):
        self.entity.moving=True;self.cast();self.advance(1)
        self.entity.moving=False;self.advance(2)
        self.assertTrue(self.entity.pose);self.assert_no_gameplay_command()
        self.assertGreater(self.g.motion_calls,0)
    def test_expiry_does_not_reassert_guard(self):
        self.cast();self.entity.pose=False;self.squad.active[self.q]=False;self.advance(1)
        self.assertFalse(self.entity.pose);self.assert_no_gameplay_command()
if __name__=='__main__':unittest.main(defaultTest='GuardTests',verbosity=2)
