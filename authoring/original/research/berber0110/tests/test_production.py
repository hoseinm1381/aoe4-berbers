"""Lua 5.1 behavior tests for the production policy; engine commands are strict adapters."""
from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r'''
BerberAI={Building={market='market',tent='tent',smith='smith',mill='mill',mosque='mosque',siege='siege'},
  Alliances={zenata={ability='zenata_sign',upgrade='zenata_upgrade'}}}
BerberAI_Catalog={buildings={},upgrades={},squads={}}
owned={}; commands={}; costs={}; random_draws=0
function BP_GetAbilityBlueprint(n) return n end
function BP_GetUpgradeBlueprint(n) return n end
function Player_HasUpgrade(p,n) return owned[n] or false end
RT_Gold='gold'
function Player_GetResource(p,r) return 5000 end
function Player_GetAbilityBPCost(p,n) return {gold=100} end
function Entity_HasProductionQueue(e) assert(e.valid~=false); return true end
function Entity_IsProductionQueueAvailable(e) assert(e.valid~=false);return true end
function Entity_GetProductionQueueSize(e) assert(e.valid~=false);return e.queue or 0 end
function LocalCommand_EntityUpgrade(player,e,n,instant,queued) assert(instant==false and queued==false);table.insert(commands,{kind='upgrade',name=n,id=e.id}) end
function LocalCommand_EntityAbility(player,e,n,skip,queued) assert(not skip and not queued);table.insert(commands,{kind='ability',name=n}) end
function World_GetRand(lo,hi) random_draws=random_draws+1;return lo end
function BerberAI.EntityValid(e) return e~=nil and e.valid~=false end
function BerberAI.Cost(st,kind,bp) return costs[bp] or {wood=10} end
function BerberAI.Spend(st,cost)
 for _,k in ipairs({'food','wood','gold','stone'}) do if (cost[k] or 0)>(st.budget[k] or 0) then return false end end
 for _,k in ipairs({'food','wood','gold','stone'}) do st.budget[k]=(st.budget[k] or 0)-(cost[k] or 0) end
 return true
end
function BerberAI.Require(st,r) return r~=false end
function BerberAI.WithEntity(e,fn) if BerberAI.EntityValid(e) then fn(e) end end
function BerberAI.Log() end
function BerberAI.CountBuilding(st,n,complete)
 local c=0;for _,b in ipairs(st.buildings) do if b.name==n and (not complete or b.complete) then c=c+1 end end
 for _,b in ipairs(st.build_pending) do if b.name==n then c=c+1 end end;return c
end
function BerberAI.FirstBuilding(st,n)
 for _,b in ipairs(st.buildings) do if b.name==n and b.complete and BerberAI.EntityValid(b.entity) then return b.entity end end
end
function BerberAI.Construct(st,n,anchor,count,economic,radius,options)
 table.insert(commands,{kind='construct',name=n,options=options,count=count})
 table.insert(st.build_pending,{name=n});return true
end
function BerberAI.Train(st,role,options)
 options=options or {};local producer=nil
 for _,b in ipairs(st.buildings) do
  if b.complete and not st.producer_used[b.id] and (not options.building_id or b.id==options.building_id)
    and not (options.exclude_ids and options.exclude_ids[b.id]) then
   for _,r in ipairs(b.roles or {}) do if r==role then producer=b;break end end
  end
  if producer then break end
 end
 if not producer or st.unaffordable[role] then return false end
 st.producer_used[producer.id]=true;st.counts[role]=(st.counts[role] or 0)+1
 table.insert(commands,{kind='train',name=role,id=producer.id});return true
end
function state(age)
 return {age=age or 2,now=100,player=1,pid=1,profile=1,observed_cavalry=0,observed_heavy=0,last_switch=-500,threat_count=0,threat_buildings=0,config={alliance='zenata',traders=10,scouts=1,interval=1},
 counts={scout=1},live={},buildings={},squads={},budget={food=5000,wood=5000,gold=5000,stone=5000},
 producer_used={},production_pending={},build_pending={},queued_upgrades={},research_retry={},
 resource_counts={},archers_trained=0,home={x=0,z=0},siege_targets={},unaffordable={}}
end
function building(st,id,name,roles,upgrades)
 local b={id=id,name=name,entity={id=id},complete=true,roles=roles or {},pos={x=0,z=0}}
 table.insert(st.buildings,b);BerberAI_Catalog.buildings[name]={upgrades=upgrades or {}};return b
end
function upgrade(name,age,requirement) BerberAI_Catalog.upgrades[name]={age=age or 2,requirement=requirement} end
function called(kind,name)
 local c=0;for _,v in ipairs(commands) do if v.kind==kind and (not name or v.name==name) then c=c+1 end end;return c
end
function core_owned(age)
 for _,a in ipairs({3,4}) do if a<=age then owned['upgrade_unit_archer_'..a..'_mal']=true;owned['upgrade_unit_horseman_'..a..'_mal']=true end end
end
'''

class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(HARNESS)
        self.lua.execute((ROOT / 'baseline-source/berber_ai_policy.scar').read_text(encoding='utf-8-sig'))
        self.lua.execute((ROOT / 'ai/berber_ai_production.scar').read_text(encoding='utf-8-sig'))

    def check(self, code):
        self.lua.execute(code)

    def test_all_profiles_sign_only_zenata(self):
        self.check("for p=1,4 do st=state();st.profile=p;st.config.alliance='masmuda';st.observed_heavy=99;st.observed_cavalry=99;building(st,1,'tent');BerberAI.SelectAlliance(st) end;assert(called('ability','zenata_sign')==4)")

    def test_saving_pauses_every_new_production_cost(self):
        self.check("st=state(3);st.saving_age=true;st.counts.scout=0;st.needs_healer=true;st.trade_target={};st.trade_market_id=1;building(st,1,'market',{'trader','zenata'});building(st,2,'tent');BerberAI.Produce(st);assert(#commands==0)")

    def test_all_available_core_producers_run_and_trade_is_separate(self):
        self.check("st=state();owned.zenata_upgrade=true;st.trade_market_id=10;st.trade_target={};for i=1,8 do building(st,i,'market'..i,{'zenata'}) end;building(st,9,'range',{'archer'});building(st,10,'market',{'trader','zenata'});BerberAI.Produce(st);assert(called('train','zenata')==8);assert(called('train','archer')==1);assert(called('train','trader')==1);for _,c in ipairs(commands) do if c.kind=='train' and c.name=='zenata' then assert(c.id~=10) end end")

    def test_unaffordable_ratio_preference_does_not_idle_other_producer(self):
        self.check("st=state();owned.zenata_upgrade=true;st.counts.zenata=10;st.unaffordable.archer=true;building(st,1,'market',{'zenata'});BerberAI.Produce(st);assert(called('train','zenata')==1)")

    def test_soft_ratio_prefers_archer_then_lancer(self):
        self.check("st=state();owned.zenata_upgrade=true;st.counts.zenata=1;building(st,1,'range',{'archer'});building(st,2,'market',{'zenata'});BerberAI.Produce(st);assert(commands[1].name=='archer');assert(called('train','zenata')==1)")

    def test_difficulty_trader_caps_count_queued_and_replace_losses(self):
        self.check("for _,cap in ipairs({10,20,30,40}) do commands={};st=state();owned.zenata_upgrade=true;st.config.traders=cap;st.counts.trader=cap;st.trade_target={};st.trade_market_id=4;building(st,4,'market',{'trader'});BerberAI.Produce(st);assert(called('train','trader')==0);st.counts.trader=cap-1;st.producer_used={};BerberAI.Produce(st);assert(called('train','trader')==1) end")

    def test_no_trader_without_dedicated_producer(self):
        self.check("st=state();owned.zenata_upgrade=true;st.trade_target={};building(st,1,'market',{'trader'});BerberAI.Produce(st);assert(called('train','trader')==0)")

    def test_two_religious_plus_one_demanded_healer_and_no_more(self):
        self.check("st=state(3);owned.zenata_upgrade=true;core_owned(3);st.needs_healer=true;for i=1,5 do building(st,i,'mosque'..i,{'monk'}) end;BerberAI.Produce(st);assert(called('train','monk')==3);st.producer_used={};BerberAI.Produce(st);assert(called('train','monk')==3)")

    def test_religious_losses_are_replaced_when_established_healer_is_idle(self):
        self.check("st=state(3);owned.zenata_upgrade=true;core_owned(3);st.counts.monk=2;st.needs_healer=false;st.imam_roles={site=4,healer=5};st.squads={{id=4,role='monk'},{id=5,role='monk'}};building(st,1,'mosque',{'monk'});BerberAI.Produce(st);assert(called('train','monk')==1)")

    def test_castle_core_upgrades_both_start_before_monastery(self):
        self.check("st=state(3);owned.zenata_upgrade=true;building(st,1,'range',{'archer'},{'upgrade_unit_archer_3_mal'});building(st,2,'tent',{}, {'upgrade_unit_horseman_3_mal'});upgrade('upgrade_unit_archer_3_mal',3);upgrade('upgrade_unit_horseman_3_mal',3);BerberAI.Produce(st);assert(called('upgrade')==2);assert(commands[1].kind=='upgrade' and commands[2].kind=='upgrade');assert(called('construct','mosque')==1)")

    def test_unfunded_core_upgrade_defers_monastery(self):
        self.check("st=state(3);owned.zenata_upgrade=true;costs.upgrade_unit_archer_3_mal={gold=99999};building(st,1,'range',{}, {'upgrade_unit_archer_3_mal'});upgrade('upgrade_unit_archer_3_mal',3);BerberAI.Produce(st);assert(called('construct','mosque')==0)")

    def test_busy_core_producers_drain_paid_queues_then_unlock_religion(self):
        self.check("""
st=state(3);owned.zenata_upgrade=true
local a=building(st,1,'range',{'archer'},{'upgrade_unit_archer_3_mal'})
local l=building(st,2,'tent',{'zenata'},{'upgrade_unit_horseman_3_mal'})
upgrade('upgrade_unit_archer_3_mal',3);upgrade('upgrade_unit_horseman_3_mal',3)
a.entity.queue=2;l.entity.queue=1
BerberAI.Produce(st)
assert(called('train','archer')==0 and called('train','zenata')==0,'needed upgrade producers must drain')
assert(a.entity.queue==2 and l.entity.queue==1,'already paid queues must remain intact')
assert(called('upgrade')==0 and called('construct','mosque')==0)
assert(st.budget.wood==4980,'research funding must be protected while draining')
st.now=101;st.producer_used={};st.budget={food=5000,wood=5000,gold=5000,stone=5000}
a.entity.queue=1;l.entity.queue=0;BerberAI.Produce(st)
assert(called('upgrade','upgrade_unit_horseman_3_mal')==1)
assert(called('train','archer')==0 and called('train','zenata')==0)
st.now=102;st.producer_used={};st.budget={food=5000,wood=5000,gold=5000,stone=5000}
a.entity.queue=0;BerberAI.Produce(st)
assert(called('upgrade','upgrade_unit_archer_3_mal')==1)
assert(called('construct','mosque')==1,'both funded core upgrades unlock monastery')
""")

    def test_economic_thresholds_and_ages(self):
        self.check("for tier,threshold in ipairs({8,15,22}) do for _,r in ipairs({'food','wood','gold','stone'}) do for _,n in ipairs({threshold-1,threshold}) do commands={};st=state(tier+1);st.resource_counts[r]=n;local name='upgrade_econ_resource_'..r..'_harvest_rate_'..(tier+1);building(st,1,'econ',{}, {name});upgrade(name,tier+1);BerberAI.Research(st);assert(called('upgrade',name)==(n>=threshold and 1 or 0)) end end end")

    def test_wheelbarrow_immediate_with_mill_in_dark_age(self):
        self.check("st=state(1);local n='upgrade_unit_town_center_wheelbarrow_1';building(st,1,'mill',{}, {n});upgrade(n,1);BerberAI.Research(st);assert(called('upgrade',n)==1)")

    def test_actual_mining_technology_becomes_eligible_for_stone_workers(self):
        self.check("for tier,n in ipairs({8,15,22}) do st=state(tier+1);st.resource_counts.stone=n;local name='upgrade_econ_resource_gold_harvest_rate_'..(tier+1);building(st,1,'mine',{}, {name});upgrade(name,tier+1);BerberAI.Research(st);assert(called('upgrade',name)==1) end")

    def test_actual_forestry_technology_uses_eight_wood_workers(self):
        self.check("local name='upgrade_econ_resource_wood_fell_rate_1';st=state(1);building(st,1,'lumber',{}, {name});upgrade(name,1);st.resource_counts.wood=7;BerberAI.Research(st);assert(called('upgrade',name)==0);st.resource_counts.wood=8;BerberAI.Research(st);assert(called('upgrade',name)==1)")

    def test_six_archers_trigger_only_one_smith_including_foundation(self):
        self.check("st=state();owned.zenata_upgrade=true;st.archers_trained=5;BerberAI.Produce(st);assert(called('construct','smith')==0);st.archers_trained=6;BerberAI.Produce(st);BerberAI.Produce(st);assert(called('construct','smith')==1)")

    def test_feudal_only_plus_one_ranged_damage_after_six(self):
        self.check("st=state();st.archers_trained=6;building(st,1,'smith',{}, {'upgrade_melee_damage_i','upgrade_ranged_damage_i','upgrade_siege_engineers'});for _,n in ipairs(BerberAI_Catalog.buildings.smith.upgrades) do upgrade(n,2) end;BerberAI.Research(st);assert(called('upgrade','upgrade_ranged_damage_i')==1);assert(called('upgrade')==1)")

    def test_castle_blacksmith_random_is_stably_sorted_and_affordable(self):
        self.check("st=state(3);core_owned(3);owned.upgrade_ranged_damage_i=true;st.archers_trained=6;building(st,9,'smith',{}, {'upgrade_ranged_armor_i','upgrade_melee_damage_i','upgrade_melee_armor_i'});for _,n in ipairs(BerberAI_Catalog.buildings.smith.upgrades) do upgrade(n,2) end;costs.upgrade_melee_armor_i={gold=99999};BerberAI.Research(st);assert(random_draws==1);assert(called('upgrade','upgrade_melee_damage_i')==1)")

    def test_research_respects_prerequisites_and_pending_retry(self):
        self.check("st=state(3);st.resource_counts.food=22;local n='upgrade_econ_resource_food_harvest_rate_2';building(st,1,'mill',{}, {n});upgrade(n,2,false);BerberAI.Research(st);assert(#commands==0);BerberAI_Catalog.upgrades[n].requirement=true;BerberAI.Research(st);st.producer_used={};st.queued_upgrades={};BerberAI.Research(st);assert(called('upgrade')==1)")

    def test_siege_targets_are_not_hard_caps_and_respect_existing_queues(self):
        self.check("st=state(3);owned.zenata_upgrade=true;core_owned(3);st.siege_targets={springald=3,mangonel=2,treb=3};st.counts.springald=2;st.counts.mangonel=2;st.counts.treb=3;building(st,1,'siege',{'springald','mangonel','treb'});BerberAI.Produce(st);assert(called('train','springald')==1);assert(called('train','mangonel')==0);assert(called('train','treb')==0)")

    def test_feudal_ram_requires_engineering_and_archer_builders(self):
        self.check("st=state();owned.zenata_upgrade=true;st.siege_targets.ram=3;BerberAI.Produce(st);assert(called('construct','unit_ram_2_mal')==0);owned.upgrade_siege_engineers=true;BerberAI.Produce(st);assert(called('construct','unit_ram_3_mal')==1);local c=commands[#commands];assert(c.options.role=='archer')")

    def test_ram_demand_requests_engineering_even_before_six_archers(self):
        self.check("st=state();st.siege_targets.ram=3;building(st,1,'smith',{}, {'upgrade_siege_engineers'});upgrade('upgrade_siege_engineers',2);BerberAI.Research(st);assert(called('upgrade','upgrade_siege_engineers')==1)")

    def test_ram_name_is_frozen_official_ebps_and_pending_demand_is_bounded(self):
        self.check("st=state();owned.zenata_upgrade=true;owned.upgrade_siege_engineers=true;st.siege_targets.ram=3;for i=1,5 do BerberAI.Produce(st) end;assert(called('construct','unit_ram_3_mal')==3);assert(called('construct','unit_ram_2_mal')==0)")

    def test_destroyed_producer_is_never_read(self):
        self.check("st=state(3);building(st,1,'smith',{}, {'upgrade_ranged_damage_i'}).entity.valid=false;upgrade('upgrade_ranged_damage_i',2);st.archers_trained=6;BerberAI.Research(st);assert(#commands==0)")

if __name__ == '__main__':
    unittest.main()
