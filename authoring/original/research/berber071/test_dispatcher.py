import unittest,json
from pathlib import Path
from lupa.lua53 import LuaRuntime
HERE=Path(__file__).parent

class DispatcherTests(unittest.TestCase):
 def setUp(self):
  self.lua=LuaRuntime(unpack_returned_tuples=True)
  self.module=self.lua.execute((HERE/'dispatcher.scar').read_text(encoding='utf8'))
  self.sent=[]
  self.clips=self.lua.table_from({'villager':self.lua.table_from({x:self.lua.table_from({'clip':'audio/'+x+'.wav','duration':1}) for x in ('select','move','attack','stop','work','pain','death')})})
  self.lua.globals().test_sink=lambda clip,x,z:self.sent.append(clip)
  self.state=self.module.new(self.clips,self.lua.eval('function(clip,x,z) test_sink(clip,x,z) end'))
 def events(self,*rows):return self.lua.table_from([self.lua.table_from(r) for r in rows])
 def test_one_group_response_and_stable_arbitration(self):
  self.module.tick(self.state,1,self.events({'id':8,'family':'villager','action':'move'},{'id':3,'family':'villager','action':'select'}))
  self.assertEqual(self.sent,['audio/select.wav'])
 def test_cooldown_and_no_overlap(self):
  e=self.events({'id':3,'family':'villager','action':'move'})
  self.module.tick(self.state,0,e);self.module.tick(self.state,.25,e)
  self.module.tick(self.state,1.5,e);self.module.tick(self.state,2.1,e)
  self.assertEqual(len(self.sent),2)
 def test_no_generic_fallback(self):
  self.module.tick(self.state,1,self.events({'id':3,'family':'villager','action':'trade'}))
  self.assertEqual(self.sent,[])
 def test_death_once_and_session_reset(self):
  e=self.events({'id':3,'family':'villager','action':'death'})
  self.module.tick(self.state,1,e);self.module.tick(self.state,8,e)
  self.assertEqual(len(self.sent),1)
  self.module.reset(self.state);self.module.tick(self.state,0,e)
  self.assertEqual(len(self.sent),2)
 def test_backward_clock_resets_presentation_only(self):
  e=self.events({'id':3,'family':'villager','action':'move'})
  self.module.tick(self.state,100,e);self.module.tick(self.state,0,e)
  self.assertEqual(len(self.sent),2)
 def test_mixed_unsupported_and_invalid_events(self):
  self.module.tick(self.state,1,self.events({'id':3,'family':'missing','action':'select'},{'id':4,'family':'villager','action':'pain'}))
  self.assertEqual(self.sent,['audio/pain.wav'])
 def test_duplicate_event_does_not_create_chorus(self):
  e={'id':3,'family':'villager','action':'move'}
  self.module.tick(self.state,1,self.events(e,e));self.assertEqual(len(self.sent),1)

if __name__=='__main__':unittest.main()
