"""SCAR SquadID tables and native AISquad userdata are different domains."""
from pathlib import Path
import importlib.util,unittest
from lupa.lua51 import LuaRuntime
SOURCE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('old_handles_tests',SOURCE.parent/'berber0110/tests/test_military.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
STRICT='''
ST_AISQUAD=71;ST_SQUAD=72
ai_available=true;ai_lookup=0;path_calls=0;ais={};ai_units={}
function scartype(value) return type(value)=='userdata' and ST_AISQUAD or ST_SQUAD end
function AI_FindAISquadByID(player,id)
 assert(player==1);ai_lookup=ai_lookup+1
 if not ai_available then return nil end
 if not ais[id] then ais[id]=newproxy(true);ai_units[ais[id]]=normal_squads[id] end
 return ais[id]
end
function AI_IsSquadValid(ai) assert(type(ai)=='userdata','expected native AISquad');return ai_units[ai]~=nil and not ai_units[ai].dead_ai end
function AISquad_HasPathWithinDistance(ai,pos,distance)
 assert(type(ai)=='userdata','Invalid parameter1 expected=AISquad*, received=table')
 assert(ai_units[ai]~=nil);path_calls=path_calls+1;return not ai_units[ai].unreachable
end
normal_squads={}
local original_unit=unit
function unit(st,id,role,x,hp) local s=original_unit(st,id,role,x,hp);normal_squads[id]=s;return s end
'''

class HandleTests(unittest.TestCase):
 def setUp(self):
  self.lua=LuaRuntime(unpack_returned_tuples=True);self.lua.execute(old.FIXTURE+STRICT)
  for n in ('berber_ai_navigation.scar','berber_ai_military.scar'):self.lua.execute((SOURCE/'scar/ai'/n).read_text())
 def test_scout_normal_squad_is_converted_before_native_path_query(self):
  self.lua.execute("st=state();s=unit(st,1,'scout',0);assert(BerberAI.SafeMove(st,{s},pos(50),false,4));assert(ai_lookup>0 and path_calls>0)")
 def test_ai_disabled_without_aisquad_uses_normal_move(self):
  self.lua.execute("st=state();s=unit(st,1,'scout',0);ai_available=false;assert(BerberAI.SafeMove(st,{s},pos(50),false,4));assert(path_calls==0 and orders[1].pos.x==50)")
 def test_unreachable_native_squad_is_rejected(self):
  self.lua.execute("st=state();s=unit(st,1,'trader',0);s.unreachable=true;assert(not BerberAI.SafeMove(st,{s},pos(50),false,4));assert(path_calls>0 and orders[1]==nil)")
 def test_garrison_uses_the_same_typed_adapter(self):
  self.lua.execute("st=state();s=unit(st,1,'villager',0);building(st,2,'town_center',5,10,0);e=enemy(3,'archer',3,{ranged=true});st.sheltered={[1]=true};st.contacts={{entity=e,pos=pos(3),ranged=true}};BerberAI.VillagerSafety(st);assert(ai_lookup>0 and path_calls>0)")
 def test_wrong_lookup_type_is_never_forwarded(self):
  self.lua.execute("st=state();s=unit(st,1,'scout',0);AI_FindAISquadByID=function() return {} end;assert(not BerberAI.SafeMove(st,{s},pos(50),false,4));assert(path_calls==0)")
 def test_invalid_ai_wrapper_defers_to_normal_pathfinder(self):
  self.lua.execute("st=state();s=unit(st,1,'scout',0);s.dead_ai=true;assert(BerberAI.SafeMove(st,{s},pos(50),false,4));assert(path_calls==0)")
 def test_dead_normal_squad_never_does_lookup(self):
  self.lua.execute("st=state();s=unit(st,1,'scout',0);s.dead=true;assert(not BerberAI.SafeMove(st,{s},pos(50),false,4));assert(ai_lookup==0 and path_calls==0)")

if __name__=='__main__':unittest.main()
