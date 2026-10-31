"""Lua 5.3 pose-controller fixtures, independent of native visual acceptance."""
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from test_q_cheer_trial import MOCK, OWNER
from lupa.lua53 import LuaRuntime

POSE_MOCK = r'''
entities={}; pose_writes={}; next_entity=1000
function new_entity(s)
    next_entity=next_entity+1
    local e={kind=ST_ENTITY,id=next_entity,squad=s,valid=true,pose=false}
    entities[e.id]=e;s.entity=e;return e
end
function Squad_GetFirstEntity(s) return s.entity end
function Entity_IsValid(id) return entities[id]~=nil and entities[id].valid end
function Entity_GetStateModelBool(e,key) assert(key=='spearman_shield_wall_byz');return e.pose end
function Entity_SetStateModelBool(e,key,value)
    assert(e.valid and key=='spearman_shield_wall_byz');e.pose=value
    table.insert(pose_writes,{eid=e.id,value=value})
end
'''

class PostureTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(MOCK + POSE_MOCK)
        module = os.environ.get("TUAREG_POSTURE_TEST_MODULE", "tuareg_q_posture_trial.scar")
        self.lua.execute((ROOT / "art/tuareg_shield" / module).read_text())
        self.g = self.lua.globals()
        self.g.BerberTuaregQTrial_Start()
        self.q = self.g.BP_GetAbilityBlueprint(OWNER + "ber_spearman_ranged_damage_reduction")
        self.squad = self.g.new_squad(7, OWNER + "unit_spearman_tuareg_1_ber")
        self.entity = self.g.new_entity(self.squad)

    def cast(self, actor=None):
        actor = actor or self.squad
        actor.active[self.q] = True
        self.g.event(self.lua.table_from({"ability": self.q, "executer": actor}))
        self.g.tick()

    def advance(self, time):
        self.g.clock = time
        self.g.tick()

    def assert_no_gameplay_command(self):
        self.assertEqual(len(self.g.commands), 0)
        self.assertEqual(len(self.entity.squad.granted), 0)

    def test_raise_restore_and_no_command(self):
        self.cast()
        self.assertTrue(self.entity.pose)
        self.assert_no_gameplay_command()
        self.advance(14.99)
        self.assertTrue(self.entity.pose)
        self.advance(15.01)
        self.assertFalse(self.entity.pose)
        self.assertEqual(len(self.g.pose_writes), 2)

    def test_event_poll_deduplicated(self):
        self.cast(); self.cast()
        self.assertEqual(len(self.g.pose_writes), 1)
        self.assert_no_gameplay_command()

    def test_poll_without_event(self):
        self.squad.active[self.q] = True
        self.g.tick()
        self.assertTrue(self.entity.pose)

    def test_actual_effect_end_restores_early(self):
        self.cast()
        self.squad.active[self.q] = False
        self.advance(3)
        self.assertFalse(self.entity.pose)

    def test_unconfirmed_event_does_not_raise(self):
        self.g.event(self.lua.table_from({"ability": self.q, "executer": self.squad}))
        self.g.tick()
        self.advance(1)
        self.assertEqual(len(self.g.pose_writes), 0)
        self.assert_no_gameplay_command()

    def test_foreign_squad_ignored(self):
        foreign = self.g.new_squad(8, "unit_spearman_1_byz")
        entity = self.g.new_entity(foreign)
        self.cast(foreign)
        self.assertFalse(entity.pose)
        self.assertEqual(len(self.g.pose_writes), 0)

    def test_equal_blueprint_boxes(self):
        self.g.fresh_boxes = True
        self.cast()
        self.assertTrue(self.entity.pose)

    def test_conversion_restores_old_entity(self):
        self.cast(); self.squad.owner = 2
        self.advance(1)
        self.assertFalse(self.entity.pose)

    def test_upgrade_restores_previous_entity(self):
        self.cast()
        self.squad.bp = self.g.BP_GetSquadBlueprint(OWNER + "unit_spearman_tuareg_2_ber")
        replacement = self.g.new_entity(self.squad)
        self.advance(1)
        self.assertFalse(self.entity.pose)
        self.assertFalse(replacement.pose)

    def test_dead_removed_handle_not_written(self):
        self.cast(); self.entity.valid = False; self.squad.count = 0
        self.advance(1)
        self.assertEqual(len(self.g.pose_writes), 1)
        self.assert_no_gameplay_command()

    def test_preexisting_pose_not_claimed(self):
        self.entity.pose = True
        self.cast(); self.advance(16)
        self.assertTrue(self.entity.pose)
        self.assertEqual(len(self.g.pose_writes), 0)

    def test_gameover_and_restore_cleanup(self):
        self.cast()
        self.g.BerberTuaregQTrial_OnGameRestore()
        self.assertFalse(self.entity.pose)
        self.g.tick()
        self.assertTrue(self.entity.pose)
        self.g.BerberTuaregQTrial_OnGameOver()
        self.assertFalse(self.entity.pose)
        self.assertIsNone(self.g.event)
        self.assertIsNone(self.g.tick)

    def test_repeat_after_effect_end(self):
        self.cast(); self.squad.active[self.q] = False; self.advance(15)
        self.advance(91); self.cast()
        self.assertTrue(self.entity.pose)
        self.assertEqual(len(self.g.pose_writes), 3)

    def test_restored_flag_without_old_actor_is_cleared(self):
        self.entity.pose = True
        self.g.BerberTuaregQTrial_OnGameRestore()
        self.g.tick()
        self.assertFalse(self.entity.pose)

    def test_missing_entity_during_upgrade_does_not_crash(self):
        self.cast(); self.squad.entity = None
        self.advance(1)
        self.assertFalse(self.entity.pose)

    def test_mixed_entity_selection_raises_each_tuareg_once(self):
        second = self.g.new_squad(8, OWNER + "unit_spearman_tuareg_4_ber")
        second_entity = self.g.new_entity(second)
        foreign = self.g.new_squad(9, "unit_spearman_1_byz")
        foreign_entity = self.g.new_entity(foreign)
        self.squad.active[self.q] = True; second.active[self.q] = True
        group = self.lua.table_from({"kind": self.g.ST_EGROUP,
            "list": self.lua.table_from([self.entity, self.entity, second_entity, foreign_entity])})
        self.g.event(self.lua.table_from({"ability": self.q, "executer": group}))
        self.g.tick()
        self.assertTrue(self.entity.pose); self.assertTrue(second_entity.pose)
        self.assertFalse(foreign_entity.pose)
        self.assertEqual(len(self.g.pose_writes), 2)
        self.assert_no_gameplay_command()

if __name__ == "__main__":
    unittest.main(verbosity=2)
