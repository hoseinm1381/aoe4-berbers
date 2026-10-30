import unittest,sys
from pathlib import Path
from lupa.lua53 import LuaRuntime
HERE=Path(__file__).parent
class PilotTests(unittest.TestCase):
 def setUp(self):
  self.lua=LuaRuntime(unpack_returned_tuples=True)
  self.lua.execute('''
    calls={}; now=0; all={}; chosen={}; alive=true
    function import(_) end
    function Core_RegisterModule(_) end
    function Rule_AddInterval(f,t) tick=f end
    function Rule_Remove(_) tick=nil end
    function World_GetGameTime() return now end
    function Game_GetLocalPlayer() return 'local' end
    function Camera_GetCurrentTargetPos() return {x=0,z=0} end
    function Player_GetAllEntities(_) return all end
    function EGroup_CreateUniqueWithPrefix(_) return {} end
    function EGroup_Destroy(_) end
    function SGroup_CreateUniqueWithPrefix(_) return {} end
    function SGroup_Destroy(_) end
    function SGroup_CountSpawned(g) return #g end
    function SGroup_GetSpawnedSquadAt(g,i) return g[i] end
    function Misc_GetSelectedSquads(g,_) for i=#g,1,-1 do g[i]=nil end; for i,s in ipairs(chosen_squads or {}) do g[i]=s end end
    function Squad_Count(s) return s.first and 1 or 0 end
    function Squad_GetFirstEntity(s) return s.first end
    function Squad_GetBlueprint(s) return s.bp end
    function Entity_GetSquad(e) return e.squad end
    function Player_GetID(p) return type(p)=='table' and p.id or p end
    function World_OwnsEntity(e) return e.owner=='world' end
    function EGroup_CountSpawned(g) return #g end
    function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
    function Misc_GetSelectedEntities(g,_) for i=#g,1,-1 do g[i]=nil end; for i,e in ipairs(chosen) do g[i]=e end end
    function Entity_GetID(e) return e.id end
    function Entity_IsValid(id) for _,e in ipairs(all) do if e.id==id then return true end end return false end
    function Entity_IsAlive(e) return e.alive~=false end
    function Entity_GetPlayerOwner(e) return e.owner end
    function Entity_GetBlueprint(e) return e.bp end
    function BP_GetName(p) return p end
    function Entity_GetPosition(e) return {x=e.id,z=0} end
    function Entity_GetHealth(e) return e.hp end
    function Entity_IsMoving(e) return e.moving or false end
    function Entity_IsAttacking(e,_) return e.attacking or false end
    function Entity_ActiveCommandIs(e,c) return e.command==c end
    CMD_Stop=1; CMD_Gather=2; CMD_Attack=3; CMD_AttackForced=4; CMD_Move=5
    Garrison={audio={forMod=function(_) return {
      session=function() calls[#calls+1]='session' end,
      pulse=function(_) end,
      stop=function() calls[#calls+1]='stop' end,
      play=function(clip,...) calls[#calls+1]=clip end} end}}
    Berber071PilotClips={villager={},tuareg={}}
    for _,family in ipairs({'villager','tuareg'}) do
      for _,event in ipairs({'select','move','attack','stop','pain','death'}) do
        Berber071PilotClips[family][event]={clip=family..'/'..event,duration=.1}
      end
    end
    Berber071PilotClips.villager.work={clip='villager/work',duration=.1}
    function print(_) end
  ''')
  self.lua.execute((HERE/'dispatcher.scar').read_text());self.lua.execute((HERE/'pilot.scar').read_text())
  self.lua.execute("e={id=1,owner='local',bp='unit_villager_1_mal',hp=100,command=0}; all={e}; Berber071VoicePilot_OnInit()")
 def values(self):return list(self.lua.globals().calls.values())
 def test_selection_is_edge_only(self):
  self.lua.execute('chosen={e}; tick(); now=3; tick()')
  self.assertEqual(self.values(),['session','villager/select'])
 def test_order_change_move_stop_work(self):
  self.lua.execute('tick(); now=1; e.command=CMD_Move; tick(); now=4; e.command=CMD_Stop; tick(); now=7; e.command=CMD_Gather; tick()')
  self.assertEqual(self.values(),['session','villager/move','villager/stop','villager/work'])
 def test_stock_and_other_owners_do_not_trigger(self):
  self.lua.execute("e.owner='other'; e.bp='unit_archer_1_eng'; chosen={e}; tick(); now=3; e.command=CMD_Move; tick()")
  self.assertEqual(self.values(),['session'])
 def test_disappearance_is_not_death(self):
  self.lua.execute('tick(); all={}; now=2; tick()')
  self.assertEqual(self.values(),['session'])
 def test_known_dead_entity_does_emit_death(self):
  self.lua.execute('tick(); e.alive=false; now=2; tick()')
  self.assertEqual(self.values(),['session','villager/death'])
 def test_idempotent_start_and_cleanup(self):
  self.lua.execute('Berber071VoicePilot_OnInit(); Berber071VoicePilot_OnGameOver(); Berber071VoicePilot_OnGameOver()')
  self.assertEqual(self.values(),['session','stop'])
 def test_squad_only_villager_selection(self):
  self.lua.execute("s={first=e,bp='unit_villager_1_mal'}; chosen={}; chosen_squads={s}; tick()")
  self.assertEqual(self.values(),['session','villager/select'])
 def test_qualified_tuareg_entity_name(self):
  self.lua.execute("e.bp='1d3145e8f1b2427f8bb0067851fcf0f1:unit_spearman_tuareg_1_ber'; chosen={e}; tick()")
  self.assertEqual(self.values(),['session','tuareg/select'])
 def test_qualified_squad_identifies_variant_member(self):
  self.lua.execute("e.bp='tuareg_variant_entity'; s={first=e,bp='1d3145e8f1b2427f8bb0067851fcf0f1:unit_spearman_tuareg_1_ber'}; e.squad=s; chosen_squads={s}; tick()")
  self.assertEqual(self.values(),['session','tuareg/select'])
 def test_player_identity_uses_numeric_id(self):
  self.lua.execute("function Game_GetLocalPlayer() return {id=3} end; e.owner={id=3}; chosen={e}; tick()")
  self.assertEqual(self.values(),['session','villager/select'])
 def test_own_guid_only_and_duplicate_union(self):
  self.lua.execute("s={first=e,bp=e.bp}; chosen={e}; chosen_squads={s}; tick(); now=3; e.bp='unrelatedguid:unit_spearman_tuareg_1_ber'; chosen_squads={}; tick()")
  self.assertEqual(self.values(),['session','villager/select'])
if __name__=='__main__':unittest.main()
