"""Behavioral policy and simulated-engine tests; not native match proof."""
from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

ROOT=Path(__file__).resolve().parents[2]
AI=ROOT/'assets/scar/ai'

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('AID_EASY=0; AID_NORMAL=1; AID_HARD=2; AID_EXPERT=3')
        self.lua.execute((AI/'berber_ai_policy.scar').read_text())
        self.p=self.lua.globals().BerberAI_Policy
    def counts(self,**kw):return self.lua.table_from(kw)
    def test_actual_difficulties_and_all_higher_aliases(self):
        for raw,want in [(0,1),(1,2),(2,3),(3,4),(4,4),(5,4),(6,4),(127,4)]:
            self.assertEqual(self.p.ProfileIndex(raw),want)
    def test_zenata_support_losses_are_replaced(self):
        self.assertEqual(self.p.CoreRole(2,'zenata',self.counts(zenata=20,archer=2)),'archer')
        self.assertEqual(self.p.CoreRole(2,'zenata',self.counts(zenata=4,archer=4)),'zenata')
    def test_hard_composition_and_losses(self):
        self.assertEqual(self.p.CoreRole(3,'masmuda',self.counts(masmuda=10,mehari=3)),'mehari')
        self.assertEqual(self.p.CoreRole(3,'masmuda',self.counts(masmuda=2,mehari=7)),'masmuda')
    def test_raid_does_not_launch_without_support(self):
        self.assertFalse(self.p.ArmyReady(2,self.counts(zenata=14,archer=0),False))
        self.assertTrue(self.p.ArmyReady(2,self.counts(zenata=8,archer=4),False))
    def test_hard_requires_both_components(self):
        self.assertFalse(self.p.ArmyReady(3,self.counts(masmuda=12,mehari=0),False))
        self.assertTrue(self.p.ArmyReady(3,self.counts(masmuda=6,mehari=6),False))
    def test_emergency_defense_does_not_wait_for_ratio(self):
        self.assertTrue(self.p.ArmyReady(2,self.counts(zenata=2),True))
    def test_grants_are_economic_missing_amount_not_each_resource(self):
        r=self.p.Recovery(2,100,0,-180,self.counts(food=30,wood=90,gold=80,stone=0),self.counts(food=50,wood=150,gold=100,stone=0),True)
        self.assertEqual(r['food']+r['wood']+r['gold']+r['stone'],100)
        self.assertEqual(r['food'],20)
        self.assertEqual(r['wood'],60)
        self.assertEqual(r['gold'],20)
    def test_no_aid_easy_or_before_stall_or_during_cooldown(self):
        have=self.counts(food=0,wood=0,gold=0,stone=0);need=self.counts(food=100)
        for profile,now,stall,last,blocked in [(1,100,0,-180,True),(2,59,0,-180,True),(2,180,0,1,True),(2,300,0,0,False)]:
            self.assertIsNone(self.p.Recovery(profile,now,stall,last,have,need,blocked))
    def test_recovery_can_repeat_after_180_seconds(self):
        self.assertIsNotNone(self.p.Recovery(4,360,300,180,self.counts(),self.counts(wood=150),True))
    def test_reservations_prevent_double_spending(self):
        r=self.counts(food=100,wood=100,gold=0,stone=0)
        self.assertTrue(self.p.Reserve(r,self.counts(food=75)))
        self.assertFalse(self.p.Reserve(r,self.counts(food=50)))
        self.assertEqual(r['food'],25)
    def test_alliance_needs_two_evaluations_and_affordability(self):
        s=self.counts(alliance='zenata',candidate='',candidate_count=0,last_switch=0)
        self.assertIsNone(self.p.Switch(s,'masmuda',200,200,False))
        self.assertIsNone(self.p.Switch(s,'masmuda',230,50,False))
        self.assertEqual(self.p.Switch(s,'masmuda',260,100,False),'masmuda')
    def test_switch_waits_for_queues_and_cooldown(self):
        s=self.counts(alliance='zenata',candidate='sanhaja',candidate_count=2,last_switch=100)
        self.assertIsNone(self.p.Switch(s,'sanhaja',200,1000,False))
        self.assertIsNone(self.p.Switch(s,'sanhaja',300,1000,True))

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
          AID_EASY=0;AID_NORMAL=1;AID_HARD=2;AID_EXPERT=3
          RT_Food=1;RT_Wood=2;RT_Gold=3;RT_Stone=4
          players={{id=11,race='malian',ai=true,enabled=true,difficulty=2,alive=true},
                   {id=22,race='english',ai=true,enabled=true,difficulty=6,alive=true},
                   {id=33,race='malian',ai=false,enabled=false,difficulty=0,alive=true},
                   {id=44,race='malian',ai=true,enabled=true,difficulty=6,alive=true}}
          rules={};events={};commands={};R_ENEMY=2;PITEM_Spawn=1;CT_Personnel=1
          function Core_RegisterModule(n) end
          function import(n) end
          function Setup_GetWinConditionOptions(o) end
          function World_GetPlayerCount() return #players end
          function World_GetPlayerAt(i) return players[i] end
          function Player_GetID(p) return p.id end
          function Player_GetRaceName(p) return p.race end
          function Player_IsAlive(p) return p.alive end
          function Player_IsHuman(p) return not p.ai end
          function AI_IsAIPlayer(p) return p.ai end
          function AI_GetDifficulty(p) return p.difficulty end
          function AI_SetDifficulty(p,d) p.difficulty=d end
          function AI_Enable(p,on) p.enabled=on end
          function AI_IsEnabled(p) return p.enabled end
          function World_GetGameTime() return 0 end
          function Rule_AddInterval(f,t) rules[f]=t end
          function Rule_Remove(f) rules[f]=nil end
          function World_GetAllEntities(g) end
          function EGroup_CreateUnique() return {} end
          function EGroup_Destroy(g) end
          function EGroup_Count(g) return #g end
          function EGroup_GetEntityAt(g,i) return g[i] end
          function print(...) end
        ''')
        for n in ['policy','catalog','engine','economy','production','military','controller']:
            self.lua.execute((AI/('berber_ai_'+n+'.scar')).read_text())
    def test_only_initial_berber_computers_are_disabled(self):
        g=self.lua.globals();g.BerberAI_OnInit();g.BerberAI_SetDifficulty()
        self.assertFalse(g.players[1]['enabled']);self.assertTrue(g.players[2]['enabled'])
        self.assertFalse(g.players[3]['enabled']);self.assertFalse(g.players[4]['enabled'])
        self.assertEqual(g.BerberAI_State.players[11]['profile'],3)
        self.assertIsNone(g.BerberAI_State.players[33])
    def test_cheating_difficulty_is_normalized_but_profile_retained(self):
        g=self.lua.globals();g.BerberAI_OnInit();g.BerberAI_SetDifficulty()
        self.assertEqual(g.players[4]['difficulty'],3)
        self.assertEqual(g.BerberAI_State.players[44]['original_difficulty'],6)
        self.assertEqual(g.BerberAI_State.players[44]['profile'],4)
        self.assertEqual(g.players[2]['difficulty'],6)
    def test_start_and_restore_do_not_duplicate_interval_or_reset_grants(self):
        g=self.lua.globals();g.BerberAI_OnInit();g.BerberAI_Start();g.BerberAI_Start()
        g.BerberAI_State.players[44]['granted']=100
        g.BerberAI_OnGameRestore()
        self.assertEqual(self.lua.eval('(function() local n=0;for _ in pairs(rules) do n=n+1 end;return n end)()'),1)
        self.assertEqual(g.BerberAI_State.players[44]['granted'],100)
    def test_game_over_removes_rules_and_releases_memory(self):
        g=self.lua.globals();g.BerberAI_OnInit();g.BerberAI_Start();g.BerberAI_OnGameOver()
        self.assertEqual(self.lua.eval('(function() local n=0;for _ in pairs(rules) do n=n+1 end;return n end)()'),0)
        self.assertTrue(g.BerberAI_State.stopped)
    def test_game_over_then_new_setup_starts_clean_controller(self):
        g=self.lua.globals();g.BerberAI_OnInit();g.BerberAI_Start();g.BerberAI_OnGameOver()
        g.BerberAI_OnGameSetup();g.BerberAI_OnInit();g.BerberAI_Start()
        self.assertFalse(g.BerberAI_State.stopped)
        self.assertFalse(g.BerberAI_State.players[11].finished or False)
    def test_enemy_target_uses_player_handle_not_player_id_as_slot(self):
        self.lua.execute('''
          function Player_ObserveRelationship(a,b) return R_ENEMY end
          local st={player=players[1],profile=2,defense=false,home={x=0,z=0},
            contacts={{id=200,owner=players[2],pos={x=10,z=10},name='unit_villager',economic=true,building=false}}}
          selected_target=BerberAI.SelectTarget(st)
        ''')
        self.assertIsNotNone(self.lua.globals().selected_target)
    def test_unchanged_move_order_does_not_interrupt_combat_every_tick(self):
        self.lua.execute('''
          time=100;move_count=0
          function World_GetGameTime() return time end
          function Squad_GetID(s) return s.id end
          function Squad_IsValid(id) return true end
          function Squad_Count(s) return 1 end
          function Squad_IsIdle(s) return false end
          function SGroup_CreateUnique() return {} end
          function SGroup_Add(g,s) table.insert(g,s) end
          function SGroup_Count(g) return #g end
          function SGroup_Destroy(g) end
          function Cmd_AttackMove(g,p,q) move_count=move_count+1 end
          BerberAI.Move({{id=900}}, {x=30,z=30},true)
          time=102
          BerberAI.Move({{id=900}}, {x=30,z=30},true)
        ''')
        self.assertEqual(self.lua.globals().move_count,1)
    def engine_stubs(self):
        self.lua.execute('''
          function BP_GetName(bp) return bp end
          function BP_GetEntityBlueprint(n) return n end
          function BP_GetSquadBlueprint(n) return n end
          function BP_GetUpgradeBlueprint(n) return n end
          players[1].upgrades={feudal_age=true}
          function Player_HasUpgrade(p,bp) return (p.upgrades or {})[bp]==true end
          function Entity_IsValid(id) return true end
          function Entity_IsAlive(e) return true end
          function Entity_GetID(e) return e.id end
          function Entity_GetPosition(e) return e.pos end
          function Entity_HasProductionQueue(e) return true end
          function Entity_IsProductionQueueAvailable(e) return true end
          function Entity_GetProductionQueueSize(e) return #(e.queue or {}) end
          function Entity_GetProductionQueueItem(e,i) return e.queue[i+1] end
          function Entity_GetProductionQueueItemType(e,i) return PITEM_Spawn end
          function EGroup_Add(g,e) table.insert(g,e) end
          function Player_GetSquadBPCost(p,bp) return {food=50,wood=0,gold=0,stone=0} end
          function Player_GetEntityBPCost(p,bp) return {food=0,wood=100,gold=0,stone=0} end
          function Player_GetCurrentPopulationCap(p,c) return 20 end
          function Player_GetCurrentPopulation(p,c) return 10 end
          function LocalCommand_EntityBuildSquad(p,g,bp) table.insert(commands,bp) end
          function Squad_GetID(s) return s.id end
          function Squad_IsValid(id) return true end
          function Squad_Count(s) return 1 end
          function Squad_IsInHoldEntity(s) return false end
          function SGroup_CreateUnique() return {} end
          function SGroup_Add(g,s) table.insert(g,s) end
          function SGroup_Count(g) return #g end
          function SGroup_Destroy(g) end
          function Player_CanConstruct(p,bp) return true end
          function World_Pos(x,y,z) return {x=x,y=y,z=z} end
          function World_PosInBounds(p) return true end
          function Entity_CalcConstructionPlacement(bp,p,pos) return {success=false} end
          st={player=players[1],pid=11,now=0,age=2,buildings={},squads={},reserved={},counts={},live={},
            build_pending={},budget={food=100,wood=100,gold=100,stone=100},
            command_count=0,producer_used={},production_pending={},site_cursor=0,config={interval=3}}
        ''')
    def test_archer_comes_from_range_and_producer_is_reserved(self):
        self.engine_stubs()
        self.lua.execute('''
          st.buildings={{id=200,name='building_unit_ranged_mal',complete=true,entity={id=200,queue={}}}}
          first=BerberAI.Train(st,'archer');second=BerberAI.Train(st,'archer')
        ''')
        g=self.lua.globals();self.assertTrue(g.first);self.assertFalse(g.second)
        self.assertEqual(g.commands[1],'unit_archer_2_mal')
        self.assertEqual(g.st.counts['archer'],1)
        self.assertEqual(g.st.budget['food'],50)
    def test_failed_placement_is_retried_without_crash_or_spend(self):
        self.engine_stubs()
        self.lua.execute('''
          st.squads={{role='villager',id=1,squad={id=1},pos={x=0,z=0}}}
          placed=BerberAI.Construct(st,'building_house_mal',{x=0,z=0},1,true)
        ''')
        self.assertFalse(self.lua.globals().placed)
        self.assertEqual(self.lua.globals().st.budget['wood'],100)
    def test_resolved_feudal_units_do_not_require_veteran_upgrades(self):
        self.engine_stubs()
        self.lua.execute('''
          players[1].upgrades.upgrade_cul_medical_centers_ayy=true
          zenata=BerberAI.Require(st,BerberAI_Catalog.squads.unit_horseman_2_mal.requirement)
          players[1].upgrades.upgrade_econ_agriculture_ayy=true
          masmuda=BerberAI.Require(st,BerberAI_Catalog.squads.unit_masmuda_cb_2_ber.requirement)
          tuareg=BerberAI.Require(st,BerberAI_Catalog.squads.unit_spearman_tuareg_1_ber.requirement)
          veteran=BerberAI.Require(st,BerberAI_Catalog.squads.unit_horseman_3_mal.requirement)
        ''')
        g=self.lua.globals()
        self.assertTrue(g.zenata);self.assertTrue(g.masmuda);self.assertTrue(g.tuareg);self.assertFalse(g.veteran)
    def test_unknown_requirement_under_negation_defers_to_engine(self):
        self.engine_stubs()
        self.assertTrue(self.lua.eval("BerberAI.Require(st,{op='not',items={{op='engine'}}})"))
    def test_imperial_age_releases_landmark_reservation(self):
        self.engine_stubs()
        self.lua.execute('st.age=4;st.age_cost={food=2400,gold=1200};BerberAI.AgeUp(st)')
        self.assertIsNone(self.lua.globals().st.age_cost)
    def test_farms_keep_scaling_after_first_farm_provides_food(self):
        self.engine_stubs()
        self.lua.execute('''
          st.age=2;st.config.workers=20;st.live.villager=20;st.counts.villager=20
          st.food_missing=false;st.natural_food=false;st.home={x=0,z=0};st.deposits={}
          st.threat_count=0;st.threat_buildings=0;st.profile=2
          function Player_GetMaxPopulationCap(p,c) return 200 end
          function BerberAI.CountBuilding(st,n,complete) return n==BerberAI.Building.farm and 1 or 2 end
          requested={}
          function BerberAI.Construct(st,n,...) table.insert(requested,n);return true end
          BerberAI.Infrastructure(st)
        ''')
        self.assertIn('building_resource_farm_mal',list(self.lua.globals().requested.values()))
    def test_farm_workers_are_distributed_one_per_farm(self):
        self.engine_stubs()
        self.lua.execute('''
          st.live.villager=6;st.home={x=0,z=0};st.rt={food=1,wood=2,gold=3,stone=4};st.worker_jobs={}
          for i=1,6 do table.insert(st.squads,{id=i,role='villager',squad={id=i}}) end
          function Player_GetResource(p,r) return 1000 end
          function Squad_IsIdle(s) return true end
          function BerberAI.FindDeposit(st,k,p)
            if k=='food' then return {id=10},{{id=10,entity={id=10},farm=true},{id=11,entity={id=11},farm=true}} end
            return {id=20},{{id=20,entity={id=20},farm=false}}
          end
          assigned_farms={}
          function BerberAI.Target(st,s,cmd,e,q) assigned_farms[e.id]=(assigned_farms[e.id] or 0)+#s end
          BerberAI.Gather(st)
        ''')
        g=self.lua.globals();self.assertEqual(g.assigned_farms[10],1);self.assertEqual(g.assigned_farms[11],1)
    def test_confirmed_adaptive_switch_drains_old_market_queue(self):
        self.engine_stubs()
        self.lua.execute('''
          st.profile=4;st.config={alliance='zenata',scouts=0,interval=2};st.alliance='zenata'
          st.observed_cavalry=0;st.observed_heavy=8;st.threat_count=0;st.threat_buildings=0
          st.last_switch=0;st.now=200;st.last_alliance_eval=-30;st.candidate_count=0;st.research_retry={}
          st.player.upgrades.upgrade_cul_medical_centers_ayy=true
          st.buildings={{id=200,name='building_econ_market_mal',complete=true,
            entity={id=200,queue={'unit_horseman_2_mal'}}}}
          function Player_GetResource(p,r) return 1000 end
          function BerberAI.Research(st) end
          BerberAI.SelectAlliance(st)
          st.now=230
          BerberAI.SelectAlliance(st)
          BerberAI.Produce(st)
        ''')
        self.assertEqual(len(self.lua.globals().commands),0)

class FullTickTests(unittest.TestCase):
    def boot(self,nomad):
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute((ROOT/'research/berber0100/sim_engine.lua').read_text())
        for n in ['policy','catalog','engine','economy','production','military','controller']:
            lua.execute((AI/('berber_ai_'+n+'.scar')).read_text())
        lua.execute((ROOT/'assets/scar/buildings/tribal_tent.scar').read_text())
        lua.globals().setup_match(nomad)
        lua.execute('tribal_tent_start();BerberAI_OnGameSetup();BerberAI_OnInit();BerberAI_SetDifficulty();BerberAI_Start()')
        return lua
    def simulate(self,nomad):
        lua=self.boot(nomad)
        for _ in range(180):
            lua.execute('advance(10);BerberAI_Tick()')
        return lua
    def test_official_sacred_site_type_and_hidden_enemy_filter(self):
        lua=self.boot(False)
        lua.execute('''
          local st=BerberAI_State.players[11]
          BerberAI.Snapshot(st)
          BerberAI_State.world_entities={
            {id=5000,name='holy_site',types={special_beacon=true},pos=pos(0,0)},
            {id=5001,name='unit_knight',player=players[2],hidden=true,pos=pos(0,0),types={cavalry=true,heavy=true}}
          }
          BerberAI.Observe(st)
          objective_count=#st.objectives;contact_count=#st.contacts
        ''')
        self.assertEqual(lua.globals().objective_count,1)
        self.assertEqual(lua.globals().contact_count,0)
    def test_exhausted_home_resource_uses_scout_discovery(self):
        lua=self.boot(False)
        lua.execute('''
          local p=players[1]
          for _,e in ipairs(all_entities) do
            if e.resource_type==RT_Gold and BerberAI.Distance(e.pos,p.start)<10000 then e.resource_type=nil end
          end
          p.squads[7].pos=pos(350,350)
          local gold={id=9000,name='gold_mine',resource_type=RT_Gold,pos=pos(355,355)}
          table.insert(all_entities,gold)
          local st=BerberAI_State.players[p.id];BerberAI.Snapshot(st)
          discovered_gold=BerberAI.FindDeposit(st,'gold',st.home)
        ''')
        self.assertIsNotNone(lua.globals().discovered_gold)
        self.assertEqual(lua.globals().discovered_gold.id,9000)
    def test_eight_player_classic_control_flow_for_thirty_simulated_minutes(self):
        lua=self.simulate(False);g=lua.globals()
        self.assertTrue(g.players[8].enabled)
        self.assertTrue(g.players[1].upgrades.feudal_age)
        self.assertTrue(g.players[2].upgrades.upgrade_cul_medical_centers_ayy)
        self.assertTrue(g.players[3].upgrades.upgrade_econ_agriculture_ayy)
        orders=list(g.orders.values())
        self.assertTrue(any(x.name=='unit_archer_2_mal' and x.player==22 for x in orders))
        self.assertTrue(any(x.name=='unit_masmuda_cb_2_ber' and x.player==33 for x in orders))
        self.assertTrue(any(x.name=='mehari_2_ber' and x.player==33 for x in orders))
    def test_eight_player_nomad_builds_initial_town_centers(self):
        lua=self.simulate(True);g=lua.globals()
        for i in range(1,8):
            self.assertTrue(any(b.name=='building_town_center_capital_mal' for b in g.players[i].buildings.values()))

class AllianceTests(unittest.TestCase):
    def test_engine_paid_switch_cost_is_not_charged_twice(self):
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
          ST_ENTITY=1;RT_Gold=3;MAT_Ability=1;MUT_Addition=1;GE_AbilityExecuted=1
          function Core_RegisterModule(n) end
          function BP_GetEntityBlueprint(n) return n end
          function BP_GetSquadBlueprint(n) return n end
          function BP_GetAbilityBlueprint(n) return n end
          function BP_GetUpgradeBlueprint(n) return n end
          function Rule_AddGlobalEvent(...) end
          function Entity_GetBlueprint(e) return 'building_hut_ayy' end
          function scartype(e) return ST_ENTITY end
          function Entity_GetID(e) return 1 end
          function Entity_IsValid(id) return true end
          function Entity_IsAlive(e) return true end
          function World_OwnsEntity(e) return false end
          function Entity_GetPlayerOwner(e) return player end
          player={id=1,gold=0,upgrades={}}
          function Player_GetID(p) return p.id end
          function Player_HasUpgrade(p,bp) return p.upgrades[bp]==true end
          function Player_CompleteUpgrade(p,bp) p.upgrades[bp]=true end
          function Player_RemoveUpgrade(p,bp) p.upgrades[bp]=nil end
          function Player_GetResource(p,r) return p.gold end
          function Player_SetResource(p,r,v) p.gold=v end
          function Modifier_Create(...) return {} end
          function Modifier_ApplyToPlayer(...) end
          function EGroup_CreateUnique() return {} end
          function EGroup_AddEGroup(...) end
          function Player_GetEntities(p) return {} end
          function EGroup_Filter(...) end
          function EGroup_Count(g) return 0 end
          function EGroup_Destroy(g) end
          function print(...) end
        ''')
        lua.execute((ROOT/'assets/scar/buildings/tribal_tent.scar').read_text())
        lua.execute('''
          tribal_tent_start()
          TribalTent_OnAbilityExecuted({executer={},ability='increase_armor_song_cmp'})
          -- A normal ability command has already paid the 100 gold engine cost.
          player.gold=0
          TribalTent_OnAbilityExecuted({executer={},ability='increase_damage_song_cmp'})
        ''')
        self.assertTrue(lua.globals().player.upgrades['upgrade_econ_agriculture_ayy'])
        self.assertIsNone(lua.globals().player.upgrades['upgrade_cul_medical_centers_ayy'])
        self.assertEqual(lua.globals().player.gold,0)

if __name__=='__main__':unittest.main(verbosity=2)
