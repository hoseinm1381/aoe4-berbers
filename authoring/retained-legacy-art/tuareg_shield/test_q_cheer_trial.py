"""Lua 5.3 controller scenarios with native API fixtures, not game acceptance."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'output/tuareg_animation_failure2/test_runtime'))
from lupa.lua53 import LuaRuntime

MOCK=r'''
ST_SQUAD=1; ST_ENTITY=2; ST_SGROUP=3; ST_EGROUP=4; GE_AbilityExecuted=10
clock=0; groups={}; squads={}; commands={}; logs={}; abilities={}; registry={}; fresh_boxes=false
function print(s) table.insert(logs,s) end
function Core_RegisterModule(_) end
function scartype(o) return type(o)=='table' and o.kind or 99 end
function BP_GetAbilityBlueprint(name)
    if abilities[name]==nil then abilities[name]={name=name,kind=9} end
    return abilities[name]
end
function BP_GetSquadBlueprint(name)
    if registry[name]==nil then registry[name]=setmetatable({name=name,kind=9},bpmt) end
    return registry[name]
end
function World_GetGameTime() return clock end
function SGroup_CreateUnique(name)
    local g={kind=ST_SGROUP,list={},destroyed=false,name=name};table.insert(groups,g);return g
end
function SGroup_Add(g,s) g.list[#g.list+1]=s end
function SGroup_Destroy(g) assert(not g.destroyed);g.destroyed=true end
function SGroup_CountSpawned(g)
    local n=0;for _,s in ipairs(g.list) do if s.valid and s.count>0 then n=n+1 end end;return n
end
function SGroup_GetSpawnedSquadAt(g,index)
    local n=0;for _,s in ipairs(g.list) do if s.valid and s.count>0 then n=n+1;if n==index then return s end end end
end
function World_GetAllSquads(g) g.list={};for _,s in ipairs(squads) do SGroup_Add(g,s) end end
function Squad_GetID(s) return s.id end
function Squad_IsValid(id) for _,s in ipairs(squads) do if s.id==id then return s.valid end end return false end
function Squad_Count(s) return s.count end
function Squad_GetPlayerOwner(s) return {id=s.owner} end
function Player_GetID(p) return p.id end
function World_OwnsSquad(s) return s.owner==0 end
bpmt={__eq=function(a,b) return a.name==b.name end}
function Squad_GetBlueprint(s)
    if fresh_boxes then
        return setmetatable({name=s.bp.name,kind=9},bpmt)
    end
    return s.bp
end
function Squad_IsAbilityActive_CS(s,bp) return s.active[bp] or false end
function Squad_HasAbility(s,bp) return s.granted[bp] or false end
function SGroup_AddAbility(g,bp) for _,s in ipairs(g.list) do s.granted[bp]=true end end
function SGroup_RemoveAbility(g,bp) for _,s in ipairs(g.list) do s.granted[bp]=nil end end
function Cmd_Ability(g,bp)
    for _,s in ipairs(g.list) do
        assert(s.valid and s.count>0);assert(s.granted[bp]);
        s.active[bp]=not s.active[bp];table.insert(commands,{sid=s.id,bp=bp,on=s.active[bp]})
    end
end
function Entity_GetID(e) return e.id end
function Entity_IsValid(id) return true end
function Entity_GetSquad(e) return e.squad end
function EGroup_Count(g) return #g.list end
function EGroup_GetEntityAt(g,i) return g.list[i] end
function Rule_AddGlobalEvent(f,e) event=f end
function Rule_RemoveGlobalEvent(f) assert(event==f);event=nil end
function Rule_AddInterval(f,interval) tick=f end
function Rule_Remove(f) assert(tick==f);tick=nil end
function new_squad(id,name)
    local s={kind=ST_SQUAD,id=id,bp=BP_GetSquadBlueprint(name),valid=true,count=1,owner=1,active={},granted={}}
    table.insert(squads,s);return s
end
'''

OWNER='1d3145e8f1b2427f8bb0067851fcf0f1:'

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(MOCK)
        self.lua.execute((ROOT/'art/tuareg_shield/tuareg_q_cheer_trial.scar').read_text())
        self.g=self.lua.globals();self.g.BerberTuaregQTrial_Start()
        self.q=self.g.BP_GetAbilityBlueprint(OWNER+'ber_spearman_ranged_damage_reduction')
        self.cheer=self.g.BP_GetAbilityBlueprint('cheer_toggle')
        self.squad=self.g.new_squad(7,OWNER+'unit_spearman_tuareg_1_ber')
    def cast(self,actor=None):
        self.g.event(self.lua.table_from({'ability':self.q,'executer':actor or self.squad}))
        self.g.tick()
    def advance(self,time):self.g.clock=time;self.g.tick()
    def test_one_start_expiry_and_owned_removal(self):
        self.cast();self.assertEqual(len(self.g.commands),1)
        self.advance(14.99);self.assertEqual(len(self.g.commands),1)
        self.advance(15.01);self.assertEqual(len(self.g.commands),2)
        self.assertFalse(self.squad.active[self.cheer]);self.assertIsNone(self.squad.granted[self.cheer])
    def test_event_and_poll_deduplicate(self):
        self.squad.active[self.q]=True;self.cast();self.advance(0.5)
        self.assertEqual(len(self.g.commands),1)
    def test_foreign_unit_is_ignored(self):
        foreign=self.g.new_squad(9,'unit_spearman_2_eng');self.cast(foreign)
        self.assertEqual(len(self.g.commands),0)
    def test_dead_unit_has_no_stop_command(self):
        self.cast();self.squad.count=0;self.advance(1)
        self.assertEqual(len(self.g.commands),1)
    def test_mixed_entity_executor_table_deduplicates(self):
        entity=self.lua.table_from({'kind':2,'id':77,'squad':self.squad})
        self.cast(self.lua.table_from([entity,entity]))
        self.assertEqual(len(self.g.commands),1)
    def test_game_over_cleanup(self):
        self.cast();self.g.BerberTuaregQTrial_OnGameOver()
        self.assertIsNone(self.g.tick);self.assertIsNone(self.g.event)
        self.assertEqual(sum(not g.destroyed for g in self.g.groups.values()),0)
    def test_preexisting_inactive_ability_is_retained(self):
        self.squad.granted[self.cheer]=True;self.cast();self.advance(15.01)
        self.assertTrue(self.squad.granted[self.cheer])
    def test_existing_cheer_is_not_toggled_off(self):
        self.squad.granted[self.cheer]=True;self.squad.active[self.cheer]=True;self.cast()
        self.assertEqual(len(self.g.commands),0)
    def test_equal_blueprint_boxes_match_by_value(self):
        self.g.fresh_boxes=True;self.cast()
        self.assertEqual(len(self.g.commands),1)
    def test_conversion_stops_old_gesture(self):
        self.cast();self.squad.owner=2;self.advance(1)
        self.assertEqual(len(self.g.commands),2)
        self.assertFalse(self.squad.active[self.cheer])

if __name__=='__main__':unittest.main(verbosity=2)
