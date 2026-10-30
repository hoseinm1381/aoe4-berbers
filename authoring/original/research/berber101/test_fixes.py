"""Regressions for reported1.0.0 fatal and cumulative individual trader speed."""
from pathlib import Path
import importlib.util,unittest
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('old_military_tests',ROOT.parent/'berber0110/tests/test_military.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
SQUAD_COST_FIXTURE='''
function BP_GetEntityBPCost(bp) error('Entity BP did not have cost_ext!') end
function Squad_GetBlueprint(s) return s.name or s.entity.name end
function Player_GetSquadBPCost(p,bp) assert(p~=nil and bp~=nil);return costs[bp] or {food=100} end
'''

class CostTests(unittest.TestCase):
 def setUp(self):
  self.lua=LuaRuntime(unpack_returned_tuples=True);self.lua.execute(old.FIXTURE+SQUAD_COST_FIXTURE)
  self.lua.execute((ROOT/'ai/berber_ai_navigation.scar').read_text());self.lua.execute((ROOT/'ai/berber_ai_military.scar').read_text())
 def test_owned_costless_entity_never_reads_entity_cost(self):
  self.lua.execute("st=state();ent(1,'spawn_marker',0,2);BerberAI.Observe(st);assert(st.contacts[1].value==0)")
 def test_actual_unit_uses_squad_cost_and_ignores_health(self):
  self.lua.execute("st=state();unit(st,1,'zenata',10,.1);costs.zenata={food=100,gold=120};BerberAI.Observe(st);assert(st.army_value==220)")
 def test_attachment_with_same_squad_is_not_double_valued(self):
  self.lua.execute("st=state();s=unit(st,1,'zenata',10);e=ent(2,'rider_attachment',10,1,{});e.squad=s;costs.zenata={gold=200};BerberAI.Observe(st);assert(st.army_value==200 and st.squad_values[1]==200)")
 def test_enemy_costless_and_real_squads_together(self):
  self.lua.execute("st=state();ent(1,'marker',4,2);enemy(2,'archer',5,{ranged=true});costs.archer={wood=80};BerberAI.Observe(st);assert(st.enemy_stats.value==80)")

TRADER_FIXTURE='''
now=0;entities={};rules={};mods={};nextmod=0;groups=0
MAT_Entity=1;MUT_Addition=2;FILTER_KEEP=1
ST_ENTITY=1
function scartype(e) return ST_ENTITY end
function import() end;function Core_RegisterModule() end
function World_GetGameTime() return now end
function Rule_Exists(f) return rules[f]~=nil end
function Rule_AddInterval(f,t) rules[f]=t end
function Rule_Remove(f) rules[f]=nil end
function World_GetPlayerCount() return 2 end
function World_GetPlayerAt(i) return i end
function Player_IsAlive(p) return true end
function Player_GetRaceName(p) return p==1 and 'malian' or 'english' end
function Player_GetAllEntities(p) local g={};for _,e in pairs(entities) do if e.owner==p and not e.dead then table.insert(g,e) end end;return g end
function EGroup_Filter(g,t,keep) assert(t=='trade_cart');for i=#g,1,-1 do if not g[i].trader then table.remove(g,i) end end end
function EGroup_Count(g) return #g end
function EGroup_GetEntityAt(g,i) return g[i] end
function EGroup_Destroy(g) error('Player observer group is engine-owned') end
function Entity_GetID(e) return e.id end
function Entity_IsValid(id) return entities[id]~=nil and not entities[id].dead end
function Entity_IsAlive(e) return not e.dead end
function Entity_IsOfType(e,t) return e.trader and t=='trade_cart' end
function Entity_FromID(id) return entities[id] end
function Modifier_Create(application,kind,usage,exclusive,value,tag) assert(application==MAT_Entity and usage==MUT_Addition and exclusive==false);return {kind=kind,value=value} end
function Modifier_ApplyToEntity(m,e,duration) assert(not e.dead and duration==0);nextmod=nextmod+1;mods[nextmod]={entity=e,kind=m.kind,value=m.value};return nextmod end
function Modifier_Remove(id) assert(type(id)=='number');mods[id]=nil end
function add(id,owner,trader) local e={id=id,owner=owner or 1,trader=trader~=false};entities[id]=e;return e end
function bonus(id) local value=0;for _,m in pairs(mods) do if m.entity==entities[id] and not m.entity.dead and m.kind=='speed_maximum_modifier' then value=value+m.value end end;return value end
function modcount() local n=0;for _ in pairs(mods) do n=n+1 end;return n end
'''
class TraderTests(unittest.TestCase):
 def setUp(self):
  self.lua=LuaRuntime(unpack_returned_tuples=True);self.lua.execute(TRADER_FIXTURE);self.lua.execute((ROOT/'saharan_trader.scar').read_text());self.g=self.lua.globals()
  self.g.add(1);self.g.saharan_trader_start()
 def tick(self,now):self.g.now=now;self.g.saharan_trader_count_check()
 def test_five_minutes_ten_increments(self):
  for t in range(1,301):self.tick(t)
  self.assertAlmostEqual(self.g.bonus(1),.8);self.assertEqual(self.g.modcount(),2)
 def test_new_trader_has_own_clock(self):
  self.tick(90);self.g.add(2);self.tick(91);self.tick(120)
  self.assertAlmostEqual(self.g.bonus(1),.32);self.assertEqual(self.g.bonus(2),0)
  self.tick(121);self.assertAlmostEqual(self.g.bonus(2),.08)
 def test_repeated_tick_and_restore_do_not_duplicate(self):
  self.tick(60);self.tick(60);self.g.BST_OnGameRestore();self.g.BST_OnGameRestore();self.tick(60)
  self.assertAlmostEqual(self.g.bonus(1),.16);self.assertEqual(self.g.modcount(),2)
  self.assertEqual(self.lua.eval('(function() local n=0 for _ in pairs(rules) do n=n+1 end return n end)()'),1)
 def test_other_civ_and_nontrader_unaffected(self):
  self.g.add(2,2);self.g.add(3,1,False);self.tick(60)
  self.assertEqual(self.g.bonus(2),0);self.assertEqual(self.g.bonus(3),0);self.assertEqual(self.g.groups,0)
 def test_converted_trader_loses_only_owned_bonus(self):
  self.tick(60);self.lua.execute('entities[1].owner=2');self.tick(61)
  self.assertEqual(self.g.bonus(1),0)
 def test_id_reuse_does_not_inherit_experience(self):
  self.tick(60);self.lua.execute('entities[1].dead=true');self.tick(61);self.g.add(1);self.tick(62);self.tick(91)
  self.assertEqual(self.g.bonus(1),0)
  self.tick(92);self.assertAlmostEqual(self.g.bonus(1),.08)
 def test_cleanup_removes_rules_and_modifiers(self):
  self.tick(60);self.g.BST_OnGameOver();self.g.BST_OnGameOver()
  self.assertEqual(self.g.modcount(),0);self.assertTrue(self.lua.eval('next(rules)==nil'));self.assertEqual(self.g.groups,0)

if __name__=='__main__':unittest.main()
