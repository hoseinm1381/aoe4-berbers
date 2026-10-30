from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

HERE=Path(__file__).resolve().parent
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.lua=LuaRuntime(unpack_returned_tuples=True)
  self.lua.execute((HERE/'fixtures/test_runtime.lua').read_text())
  self.lua.execute('''
   function Player_GetNumGatheringSquads(p,r)
    local n=0;for _,s in ipairs(p.squads) do if s.alive~=false and s.gather==r and not s.hold then n=n+1 end end;return n
   end
   function EGroup_Count(g) return #g end
   function EGroup_GetEntityAt(g,i) return g[i] end
   function EGroup_Remove(g,e) for i=#g,1,-1 do if g[i]==e then table.remove(g,i) end end end
   function World_GetAllNeutralEntities(g) for _,e in ipairs(all_entities) do if e.player==nil then table.insert(g,e) end end end
   function Player_GetAllEntities(p) local g={};for _,e in ipairs(all_entities) do if e.player==p then table.insert(g,e) end end;return g end
   function Entity_GetBlueprint(e) assert(not e.invalid);return e.name end
   function Entity_GetPosition(e) assert(not e.invalid);return e.pos end
   function LocalCommand_SquadSquad(p,g,cmd,target,queued)
    assert(cmd==SCMD_Gather);squad_gathers=(squad_gathers or 0)+1
    for _,s in ipairs(g) do s.gather=RT_Food;s.idle=false end
   end
   local original_add=EGroup_Add
   function EGroup_Add(g,e) assert(e.squad==nil,'squad animal sent through entity group');original_add(g,e) end
  ''')
  for n in ['policy','catalog','engine','navigation','economy','production','military','controller']:
   self.lua.execute((HERE/'scar/ai'/f'berber_ai_{n}.scar').read_text())
  self.lua.execute('setup_match(false);BerberAI_OnInit();st=BerberAI_State.players[players[1].id];BerberAI.Snapshot(st);st.contacts={}')
 def check(self,s):self.lua.execute(s)
 def test_live_sheep_uses_squad_target(self):
  self.check("local s=add_squad(players[1],'sheep',st.home);s.entity.resource_type=RT_Food;assert(BerberAI.Target(st,{st.squads[1].squad},SCMD_Gather,s.entity,false));assert(squad_gathers==1)")
 def test_corpse_is_discovered_and_gathered(self):
  self.check("local e={id=new_id(),name='sheep_corpse',alive=false,pos=st.home,resource_type=RT_Food};table.insert(all_entities,e);BerberAI.RefreshWorld(0);local found=BerberAI.FindDeposit(st,'food',st.home);assert(found==e,'edible corpse excluded');assert(BerberAI.Target(st,{st.squads[1].squad},SCMD_Gather,e,false));assert(st.squads[1].squad.gather==RT_Food)")
 def test_exhausted_and_invalid_deposits_are_rejected(self):
  self.check("all_entities={};local e={id=900,invalid=true,name='sheep',pos=st.home,resource_type=RT_Food};table.insert(all_entities,e);BerberAI_State.world_entities={e};assert(BerberAI.FindDeposit(st,'food',st.home)==nil);e.invalid=false;e.resource_type=nil;assert(BerberAI.FindDeposit(st,'food',st.home)==nil)")
 def test_dead_animal_with_squad_uses_native_entity_enumeration(self):
  self.check("local s=add_squad(players[1],'sheep',st.home);s.alive=false;s.entity.alive=false;s.entity.resource_type=RT_Food;local calls=0;LocalCommand_SquadEntity=function(p,g,c,t,q) assert(#t==1 and t[1]==s.entity);calls=calls+1 end;assert(BerberAI.Target(st,{st.squads[1].squad},SCMD_Gather,s.entity,false));assert(calls==1)")
 def test_stall_strictly_longer_than_15_seconds(self):
  self.check('assert(not BerberAI.EconomyWatchdog(st,0));assert(not BerberAI.EconomyWatchdog(st,15));assert(BerberAI.EconomyWatchdog(st,16));assert(st.native_fallback and players[1].enabled)')
 def test_gathering_resets_the_clock(self):
  self.check('BerberAI.EconomyWatchdog(st,0);st.squads[1].squad.gather=RT_Wood;assert(not BerberAI.EconomyWatchdog(st,14));st.squads[1].squad.gather=nil;assert(not BerberAI.EconomyWatchdog(st,29));assert(BerberAI.EconomyWatchdog(st,30))')
 def test_handoff_removes_bonus_once_and_survives_restore(self):
  self.check('st.income_modifiers={Modifier_ApplyToPlayer({},st.player,0)};BerberAI.EconomyWatchdog(st,0);BerberAI.EconomyWatchdog(st,16);assert(modifier_removed==1);BerberAI_OnGameRestore();assert(players[1].enabled and st.native_fallback);BerberAI_SetDifficulty();assert(players[1].enabled);assert(modifier_removed==1)')
 def test_no_script_orders_after_handoff_other_players_continue(self):
  self.check('BerberAI.EconomyWatchdog(st,0);BerberAI.EconomyWatchdog(st,16);local seen={};BerberAI.RefreshWorld=function() end;BerberAI.Snapshot=function(s) seen[s.pid]=true end;for _,n in ipairs({"Observe","MaintainConstruction","VillagerSafety","Economy","Produce","Army","SpecialUnits","IncomeAssistance"}) do BerberAI[n]=function() end end;time=17;BerberAI_Tick();assert(not seen[st.pid]);assert(seen[players[2].id]);assert(players[1].enabled and not players[2].enabled and players[8].enabled)')
 def test_higher_native_difficulty_stays_capped(self):
  self.check('st.profile=4;st.player.difficulty=99;BerberAI.EconomyWatchdog(st,0);BerberAI.EconomyWatchdog(st,16);assert(st.player.difficulty==AID_EXPERT and st.player.enabled)')

if __name__=='__main__':unittest.main(verbosity=2)
