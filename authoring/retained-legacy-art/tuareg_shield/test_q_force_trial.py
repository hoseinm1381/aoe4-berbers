"""Forced native branch submission fixtures, not visible native acceptance."""
from pathlib import Path
import os
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from test_q_posture_trial import PostureTests, MOCK, POSE_MOCK, OWNER, LuaRuntime

FORCE_MOCK = r'''
force_calls={}
function Entity_IsMoving(e) return e.moving or false end
function Entity_IsAttacking(e,time) assert(time==0.3);return e.attacking or false end
local old_get_bool=Entity_GetStateModelBool
function Entity_GetStateModelBool(e,key)
    if key=='is_bracing' or key=='is_charging' then return e[key] or false end
    return old_get_bool(e,key)
end
function StateTree_QueueGlobalStateTreeEntity(keepAlive,path,e)
    assert(keepAlive==false and e.valid)
    table.insert(force_calls,{path=path,eid=e.id,time=clock})
end
'''

class ForceTests(PostureTests):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(MOCK + POSE_MOCK + FORCE_MOCK)
        module = os.environ.get("TUAREG_FORCE_TEST_MODULE", "tuareg_q_force_trial.scar")
        self.lua.execute((ROOT / "art/tuareg_shield" / module).read_text())
        self.g = self.lua.globals(); self.g.BerberTuaregQTrial_Start()
        self.q = self.g.BP_GetAbilityBlueprint(OWNER + "ber_spearman_ranged_damage_reduction")
        self.squad = self.g.new_squad(7, OWNER + "unit_spearman_tuareg_1_ber")
        self.entity = self.g.new_entity(self.squad)

    def test_moving_cast_submits_one_known_guard_leaf(self):
        self.entity.moving = True
        self.cast(); self.cast(); self.advance(1)
        self.assertEqual(len(self.g.force_calls), 1)
        self.assertEqual(self.g.force_calls[1].path, 'anims_spearshield\\Locomotion\\Walk\\defensive\\jog_shieldwall_01')
        self.assert_no_gameplay_command()

    def test_moving_effect_end_submits_one_normal_leaf(self):
        self.entity.moving = True; self.cast()
        self.squad.active[self.q] = False; self.advance(15)
        self.assertEqual(len(self.g.force_calls), 2)
        self.assertEqual(self.g.force_calls[2].path, 'anims_spearshield\\Locomotion\\Walk\\tense\\walk_tense_f_01')

    def test_idle_cast_does_not_force_until_move(self):
        self.cast(); self.assertEqual(len(self.g.force_calls), 0)
        self.entity.moving = True; self.advance(1)
        self.assertEqual(len(self.g.force_calls), 1)

    def test_attack_brace_charge_do_not_receive_forced_restart(self):
        self.entity.moving = True; self.entity.attacking = True; self.cast()
        self.assertEqual(len(self.g.force_calls), 0)
        self.entity.attacking = False; self.entity.is_charging = True; self.advance(1)
        self.assertEqual(len(self.g.force_calls), 0)
        self.entity.is_charging = False; self.entity.is_bracing = True; self.advance(2)
        self.assertEqual(len(self.g.force_calls), 0)
        self.entity.is_bracing = False; self.advance(3)
        self.assertEqual(len(self.g.force_calls), 1)

    def test_dead_actor_never_receives_restore_force(self):
        self.entity.moving = True; self.cast()
        self.entity.valid = False; self.squad.count = 0; self.advance(1)
        self.assertEqual(len(self.g.force_calls), 1)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ForceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
