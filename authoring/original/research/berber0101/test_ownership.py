"""Native owner precondition regressions; Lua mocks are not native acceptance."""
from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]

class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'research/berber0100/sim_engine.lua').read_text())
        self.lua.execute('''
          owner_reads=0
          function Entity_GetPlayerOwner(e)
            assert(not World_OwnsEntity(e),'world entity has no player owner: '..e.name)
            owner_reads=owner_reads+1
            return e.player
          end
        ''')
        for name in ['policy','catalog','engine','economy','production','military','controller']:
            self.lua.execute((ROOT/f'assets/scar/ai/berber_ai_{name}.scar').read_text())
        self.lua.execute('''
          setup_match(false)
          BerberAI_OnGameSetup();BerberAI_OnInit()
          st=BerberAI_State.players[11];st.now=0;st.home=players[1].start
          st.squads={};st.buildings={}
          tree={id=1000005024,name='elm_med_wild',pos=pos(st.home.x+1,st.home.z),resource_type=RT_Wood}
        ''')

    def test_observation_preserves_neutral_objectives_and_enemy_contacts(self):
        self.lua.execute('''
          relic={id=9001,name='relic',pos=st.home,types={relic=true}}
          site={id=9002,name='sacred_site',pos=st.home,types={special_beacon=true}}
          trade={id=9003,name='trading_post',pos=st.home,types={trade_post=true}}
          sheep={id=9004,name='sheep',pos=st.home}
          enemy={id=9005,name='unit_horseman',pos=st.home,player=players[2],types={cavalry=true}}
          hidden={id=9006,name='elm_med_wild',pos=st.home,hidden=true}
          dead={id=9007,name='elm_med_wild',pos=st.home,alive=false}
          BerberAI_State.world_entities={tree,relic,site,trade,sheep,enemy,hidden,dead}
          BerberAI.Observe(st)
          assert(#st.objectives==2 and #st.contacts==1)
          assert(st.threat_count==1 and st.observed_cavalry==1 and st.defense)
          assert(st.trade_target==trade and st.sheep_target.entity==sheep)
          assert(st.contacts[1].entity==enemy and owner_reads==1)
        ''')

    def test_deposit_search_accepts_world_and_own_but_rejects_enemy_farms(self):
        self.lua.execute('''
          st.rt={wood=RT_Wood,food=RT_Food}
          own={id=9008,name='building_resource_farm_mal',pos=st.home,player=players[1],resource_type=RT_Food}
          enemy={id=9009,name='building_resource_farm_mal',pos=st.home,player=players[2],resource_type=RT_Food}
          all_entities={tree,own,enemy}
          local wood=BerberAI.FindDeposit(st,'wood',st.home)
          local food,farms=BerberAI.FindDeposit(st,'food',st.home)
          assert(wood==tree and food==own and #farms==1)
          assert(owner_reads==2)
        ''')

    def test_complete_tick_and_second_match_with_strict_owner_contract(self):
        self.lua.execute('''
          table.insert(all_entities,tree)
          BerberAI_Tick()
          BerberAI_OnGameOver()
          players={};all_entities={};setup_match(false)
          BerberAI_OnGameSetup();BerberAI_OnInit();BerberAI_Start()
          BerberAI_Tick()
          assert(not BerberAI_State.stopped and BerberAI_State.initialized)
          assert(BerberAI_State.players[11].player==players[1])
        ''')

if __name__ == '__main__':
    unittest.main(verbosity=2)
