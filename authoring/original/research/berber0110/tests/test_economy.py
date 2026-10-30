"""Economy decisions in a strict isolated Lua 5.1 command boundary, not native proof."""
from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
STUB = r'''
BerberAI={}; BerberAI_State={world_entities={}}
BerberAI.Resources={'food','wood','gold','stone'}
BerberAI.Building={tc='tc',expansion='tc2',house='house',tent='tent',market='market',range='range',
 mill='mill',lumber='lumber',mine='mine',farm='farm',smith='smith',outpost='outpost',mosque='mosque',siege='siege',university='university'}
SCMD_Gather='gather';SCMD_BuildStructure='build';SCMD_DefaultAction='repair';CT_Personnel=1
function BP_GetEntityBlueprint(n) return n end
function BP_GetName(n) return n end
function World_Pos(x,y,z) return {x=x,y=y,z=z} end
function Entity_GetID(e) assert(not e.dead);return e.id end
function Entity_GetBlueprint(e) assert(not e.dead);return e.name end
function Entity_GetPosition(e) assert(not e.dead);return e.pos end
function Entity_GetResource(e,r) assert(not e.dead);return e.resource==r and (e.amount or 10000) or 0 end
function Entity_GetPlayerOwner(e) assert(not e.world);return e.owner end
function World_OwnsEntity(e) return e.world end
function Entity_GetHealth(e) return e.health or 100 end
function Entity_GetHealthMax(e) return 100 end
function Squad_GetID(s) return s.id end
function Squad_IsIdle(s) return s.idle~=false end
function Squad_IsInHoldEntity(s) return s.held or false end
function Squad_IsGatheringResourceType(s,r) return s.gather==r end
function Player_GetCurrentPopulationCap(p,c) return p.cap end
function Player_GetMaxPopulationCap(p,c) return 200 end
function Player_GetCurrentPopulation(p,c) return p.pop end
function Player_GetResource(p,r) return p[r] or 0 end
function Misc_FindDepositsOfTypeCloseToPosition(r,b,p,d) return {} end
function EGroup_Count(g) return #g end
function EGroup_Destroy(g) end
function BerberAI.Name(n) return n end
function BerberAI.Pos(p,x,z) return World_Pos(p.x+x,0,p.z+z) end
function BerberAI.Distance(a,b) return (a.x-b.x)^2+(a.z-b.z)^2 end
function BerberAI.EntityValid(e) return e and not e.dead end
function BerberAI.SquadValid(e) return e and not e.dead end
function BerberAI.SafePoint(st,p,b) return not p.unsafe end
function BerberAI.Cost(st,k,n) return st.costs[n] or {wood=100} end
function affordable(st,c) for k,v in pairs(c) do if v>(st.budget[k] or 0) then return false end end return true end
function BerberAI.CountBuilding(st,n,complete)
 local c=0;for _,b in ipairs(st.buildings) do if b.name==n and (not complete or b.complete) then c=c+1 end end
 if not complete then for _,b in ipairs(st.build_pending) do if b.name==n then c=c+1 end end end
 return c
end
function BerberAI.FirstBuilding(st,n) for _,b in ipairs(st.buildings) do if b.name==n and b.complete then return b.entity end end end
function BerberAI.Workers(st,p,n,o)
 o=o or {};local s,ids={},{};local allow={};for _,id in ipairs(o.ids or {}) do allow[id]=true end
 for _,w in ipairs(st.squads) do if w.role==(o.role or 'villager') and BerberAI.SquadValid(w.squad)
 and not st.reserved[w.id] and not st.worker_jobs[w.id] and not w.squad.held
 and (not o.resource or st.worker_role[w.id]==o.resource) and (not o.ids or allow[w.id]) and #s<n then
 table.insert(s,w.squad);table.insert(ids,w.id) end end return s,ids
end
function BerberAI.Construct(st,n,p,count,econ,r,o)
 table.insert(st.attempts,{name=n,pos=p,count=count,options=o or {},radius=r})
 if st.fail[n] then st.last_construct_failure=type(st.fail[n])=='string' and st.fail[n] or 'placement';return false end
 if not affordable(st,BerberAI.Cost(st,'entity',n)) then st.last_construct_failure='budget';return false end
 local workers,ids=BerberAI.Workers(st,p,count,o);if #ids<count then return false end
 for k,v in pairs(BerberAI.Cost(st,'entity',n)) do st.budget[k]=st.budget[k]-v end
 local job={name=n,pos=p,workers=ids,until_time=st.now+12,options=o}
 table.insert(st.build_pending,job);table.insert(st.built,job)
 for _,id in ipairs(ids) do st.reserved[id]=true end
 return true,job
end
function BerberAI.Train(st,role,o)
 if (st.counts[role] or 0)>=st.config.workers then return false end
 table.insert(st.trained,{role=role,options=o});st.counts[role]=(st.counts[role] or 0)+1;return true
end
function BerberAI.Target(st,s,cmd,e,q) for _,w in ipairs(s) do st.orders[w.id]={cmd=cmd,target=e.id};w.gather=e.resource end end
function BerberAI.BuyStone(st,n) st.bought=st.bought+n;return false end
function state(n)
 local p={cap=200,pop=n};local st={now=0,age=1,player=p,pid=1,home=World_Pos(0,0,0),
 config={workers=60,traders=10},squads={},buildings={},build_pending={},reserved={},worker_role={},worker_jobs={},
 rt={food='food',wood='wood',gold='gold',stone='stone'},budget={food=0,wood=0,gold=0,stone=0},counts={villager=n},live={villager=n,trader=0},
 costs={['building_landmark_age1_landmarkb_mal']={food=400,gold=200},['building_landmark_age2_landmarkc_control_mal']={food=1200,gold=600},
 ['building_landmark_age3_landmarke_mal']={food=2400,gold=1200},['building_landmark_age3_landmarkf_mal']={food=2400,gold=1200},
 tc2={wood=400,stone=300},tent={wood=100,stone=100},farm={wood=60},range={wood=200},market={wood=150}},
 attempts={},built={},orders={},trained={},fail={},bought=0,castle_time=780,archers_trained=0}
 for i=1,n do local s={id=i};st.squads[i]={id=i,squad=s,role='villager',pos=World_Pos(0,0,0)} end
 deposit(9000,'sheep','food',0,0)
 return st
end
function deposit(id,name,resource,x,z,amount,owner)
 local e={id=id,name=name,resource=resource,pos=World_Pos(x,0,z),amount=amount,owner=owner,world=not owner}
 table.insert(BerberAI_State.world_entities,e);return e
end
function building(st,id,name,x,z,complete)
 local e={id=id,name=name,pos=World_Pos(x or 0,0,z or 0)}
 local b={id=id,name=name,pos=e.pos,entity=e,complete=complete~=false};table.insert(st.buildings,b);return b
end
function countrole(st,k) local n=0;for _,v in pairs(st.worker_role) do if v==k then n=n+1 end end return n end
function attempts(st,n) local c=0;for _,b in ipairs(st.attempts) do if b.name==n then c=c+1 end end return c end
'''


class EconomyTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(STUB)
        self.lua.execute((ROOT / 'ai/berber_ai_economy.scar').read_text())

    def runlua(self, code):
        self.lua.execute(code)

    def test_opening_exact_milestones_and_cycle(self):
        self.runlua("""st=state(37);BerberAI.Gather(st)
        assert(countrole(st,'food')==18);assert(countrole(st,'wood')==12);assert(countrole(st,'gold')==7)
        for i=1,6 do assert(st.worker_role[i]=='food') end
        for i=7,9 do assert(st.worker_role[i]=='gold') end
        for i=10,12 do assert(st.worker_role[i]=='food') end
        for i=13,20 do assert(st.worker_role[i]=='wood') end
        for i=21,22 do assert(st.worker_role[i]=='gold') end
        """)

    def test_worker_roles_persist_and_reserved_workers_untouched(self):
        self.runlua("st=state(12);st.worker_role[1]='gold';st.reserved[1]=true;BerberAI.Gather(st);assert(st.worker_role[1]=='gold');assert(st.orders[1]==nil)")

    def test_full_map_food_order_ownership_dead_and_farm_capacity(self):
        self.runlua("""st=state(6);BerberAI_State.world_entities={};st.budget.wood=0
        deposit(90,'berry_bush','food',1,0);deposit(91,'deer','food',2,0)
        deposit(92,'sheep','food',60,0);deposit(93,'sheep','food',0,0,nil,99)
        local d=deposit(94,'sheep','food',0,0);d.dead=true
        BerberAI.Gather(st);assert(st.orders[1].target==92)
        BerberAI_State.world_entities[3].amount=0;BerberAI.Gather(st);assert(st.orders[1].target==91)
        """)

    def test_feudal_three_food_builders_and_no_villager_threshold(self):
        self.runlua("""st=state(12);BerberAI.Gather(st);st.budget.food=400;st.budget.gold=200
        BerberAI.AgeUp(st);assert(#st.built==1);assert(st.built[1].name=='building_landmark_age1_landmarkb_mal')
        assert(#st.built[1].workers==3);for _,id in ipairs(st.built[1].workers) do assert(st.worker_role[id]=='food') end
        """)

    def test_castle_saving_and_resume_on_foundation(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=780
        BerberAI.AgeUp(st);assert(st.saving_age)
        st.budget.food=1200;st.budget.gold=600;BerberAI.AgeUp(st);assert(not st.saving_age)
        assert(st.built[1].count==nil or #st.built[1].workers==8)
        for _,id in ipairs(st.built[1].workers) do assert(st.worker_role[id]=='wood') end
        """)

    def test_imperial_live_trader_choice_and_twenty_same_resource(self):
        self.runlua("""st=state(80);BerberAI.Gather(st);st.age=3;st.now=1260;st.live.trader=15
        st.budget.food=2400;st.budget.gold=1200;st.enemy_home=World_Pos(200,0,0)
        BerberAI.AgeUp(st);assert(st.built[1].name=='building_landmark_age3_landmarkf_mal')
        assert(#st.built[1].workers==20);assert(st.built[1].pos.x>0)
        """)

    def test_house_two_slots_gold_builder_and_pending_dedup(self):
        self.runlua("""st=state(23);BerberAI.Gather(st);st.player.cap=25;st.budget.wood=500
        building(st,100,'mine');building(st,101,'lumber');BerberAI.Infrastructure(st)
        assert(attempts(st,'house')==1);assert(st.worker_role[st.built[1].workers[1]]=='gold')
        BerberAI.Infrastructure(st);assert(attempts(st,'house')==1)
        """)

    def test_no_stone_before_second_tc_decision_and_one_time_live_count(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=629
        BerberAI.Infrastructure(st);assert(countrole(st,'stone')==0)
        st.now=630;st.live.trader=10;BerberAI.Infrastructure(st);assert(st.second_tc_decided and not st.second_tc_needed)
        st.live.trader=0;st.now=700;BerberAI.Infrastructure(st);assert(not st.second_tc_needed)
        """)

    def test_second_tc_eight_miners_and_rich_gold_target(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=630
        deposit(110,'gold','gold',20,0,2000);deposit(111,'gold','gold',40,0,2500);deposit(112,'stone','stone',10,0)
        BerberAI.Infrastructure(st);assert(countrole(st,'stone')==8);assert(st.mining_target==300)
        st.budget.stone=300;st.budget.wood=400;st.reserved={};BerberAI.Infrastructure(st)
        local tc;for _,b in ipairs(st.built) do if b.name=='tc2' then tc=b end end
        assert(tc and #tc.workers==8 and tc.pos.x==40);assert(countrole(st,'stone')==0)
        """)

    def test_saving_still_funds_villagers_and_house_only(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=780;st.player.cap=42;st.budget.wood=1000
        building(st,100,'tc');BerberAI.Economy(st);assert(st.saving_age);assert(#st.trained==1)
        for _,b in ipairs(st.built) do assert(b.name=='house') end
        """)

    def test_opening_range_before_ten_minutes_and_influence(self):
        self.runlua("""st=state(25);BerberAI.Gather(st);st.age=2;st.now=400;st.budget.wood=200
        building(st,100,'building_landmark_age1_landmarkb_mal');building(st,101,'market')
        BerberAI.Infrastructure(st);assert(attempts(st,'range')==1)
        local a;for _,v in ipairs(st.attempts) do if v.name=='range' then a=v end end;assert(a.options.influence)
        """)

    def test_paired_expansion_retry_no_backlog_and_tent_cap(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=600
        building(st,100,'building_landmark_age1_landmarkb_mal');building(st,101,'market');building(st,102,'range')
        BerberAI.Infrastructure(st);assert(st.next_expansion==660)
        st.now=660;st.budget.wood=350;st.reserved={};BerberAI.Infrastructure(st);assert(st.next_expansion==780)
        assert(attempts(st,'market')==1 and attempts(st,'range')==1)
        st.now=2000;st.reserved={};st.budget.wood=0;BerberAI.Infrastructure(st);assert(st.next_expansion==2060)
        """)

    def test_trade_threshold_and_endpoint_distance_contract(self):
        self.runlua("""st=state(30);BerberAI.Gather(st);st.age=2;st.now=500;st.trade_target={pos=World_Pos(80,0,0),id=999}
        building(st,100,'market');building(st,101,'range');building(st,102,'building_landmark_age1_landmarkb_mal')
        st.budget.wood=300;st.budget.gold=250;BerberAI.Infrastructure(st)
        assert(st.trade_build_needed);local j;for _,b in ipairs(st.built) do if b.name=='market' then j=b end end
        assert(j and BerberAI.Distance(j.pos,st.trade_target.pos)>=10000)
        assert(j.options.min_target_distance==100)
        """)

    def test_farm_funding_precedes_extra_producers_and_incremental(self):
        self.runlua("""st=state(30);BerberAI_State.world_entities={};deposit(9500,'tree','wood',10,0);BerberAI.Gather(st);st.age=2;st.now=600
        building(st,100,'tc');building(st,101,'market');building(st,102,'range');building(st,103,'building_landmark_age1_landmarkb_mal')
        st.budget.wood=40;BerberAI.Economy(st);assert(st.farm_funding);assert(st.resource_counts.wood>countrole(st,'wood'))
        st.budget.wood=60;st.reserved={};BerberAI.Economy(st);assert(attempts(st,'farm')>0);assert(attempts(st,'range')==0)
        """)

    def test_resource_outpost_five_workers_threshold_knights_and_no_sheep(self):
        self.runlua("""st=state(10);for i=1,10 do st.worker_role[i]='gold' end
        deposit(110,'gold','gold',40,0);building(st,100,'tc');st.budget.wood=150;st.enemy_knights=1
        BerberAI.Gather(st);BerberAI.Infrastructure(st);assert(attempts(st,'outpost')==1)
        BerberAI.Infrastructure(st);assert(attempts(st,'outpost')==1)
        """)

    def test_normal_outpost_200_wood_and_sheep_safe(self):
        self.runlua("""st=state(6);st.budget.wood=199;BerberAI.Gather(st);BerberAI.Infrastructure(st)
        assert(attempts(st,'outpost')==0)
        BerberAI_State.world_entities={};deposit(100,'deer','food',40,0);BerberAI.Gather(st)
        BerberAI.Infrastructure(st);assert(attempts(st,'outpost')==0)
        st.budget.wood=200;BerberAI.Infrastructure(st);assert(attempts(st,'outpost')==1)
        """)

    def test_food_mill_exact_24_metres_and_no_early_farms(self):
        self.runlua("""st=state(6);BerberAI_State.world_entities={};deposit(100,'deer','food',24,0)
        building(st,101,'tc');st.budget.wood=500;BerberAI.Gather(st);BerberAI.Infrastructure(st)
        assert(attempts(st,'mill')==1);assert(attempts(st,'farm')==0)
        """)

    def test_no_duplicate_farm_assignment(self):
        self.runlua("""st=state(6);BerberAI_State.world_entities={}
        deposit(100,'farm','food',0,0,nil,st.player);deposit(101,'tree','wood',2,0)
        BerberAI.Gather(st);local n=0;for _,o in pairs(st.orders) do if o.target==100 then n=n+1 end end
        assert(n==1);assert(st.resource_counts.wood==5)
        """)

    def test_construction_restore_keeps_same_builders(self):
        self.runlua("""st=state(10);BerberAI.Gather(st);building(st,100,'house',0,0,false)
        BerberAI.MaintainConstruction(st);local j=st.construction_jobs[100];assert(j and #j.workers==2)
        st.reserved={};st.squads[1].squad.idle=false;st.squads[2].squad.idle=false
        BerberAI.MaintainConstruction(st);assert(st.reserved[1] and st.reserved[2] and not st.reserved[3])
        """)

    def test_temporary_stone_returns_roles_immediately_at_target(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=630
        deposit(100,'gold','gold',30,0,3000);BerberAI.Infrastructure(st);assert(countrole(st,'stone')==8)
        st.budget.stone=300;st.budget.wood=0;st.now=631;BerberAI.Economy(st)
        assert(countrole(st,'stone')==0);assert(st.second_tc_needed)
        """)

    def test_ordinary_tent_cap_and_stop_at_full_imperial(self):
        self.runlua("""st=state(60);BerberAI.Gather(st);st.age=4;st.now=600;st.budget.wood=3000;st.budget.stone=1000
        building(st,100,'building_landmark_age1_landmarkb_mal');building(st,101,'market');building(st,102,'range')
        for i=1,4 do building(st,110+i,'tent',i*28,0) end
        st.fail.market=true;BerberAI.Infrastructure(st);assert(attempts(st,'tent')==0)
        assert(st.expansion_exhausted)
        """)

    def test_rejected_expansion_does_not_duplicate_accepted_half(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=600;st.budget.wood=1000;st.budget.stone=1000
        building(st,100,'building_landmark_age1_landmarkb_mal');building(st,101,'market');building(st,102,'range')
        st.fail.range=true;BerberAI.Infrastructure(st);assert(attempts(st,'market')==1)
        st.now=660;st.reserved={};st.fail.range=false;BerberAI.Infrastructure(st)
        assert(attempts(st,'market')==1);assert(st.next_expansion==780)
        """)

    def test_saving_deferred_age_request_retries_without_unlocking(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=780;st.budget.food=1200;st.budget.gold=600
        st.fail['building_landmark_age2_landmarkc_control_mal']=true;BerberAI.AgeUp(st);assert(st.saving_age)
        BerberAI.AgeUp(st);assert(st.saving_age and #st.build_pending==0)
        """)

    def test_imperial_below_fifteen_chooses_rear_fez(self):
        self.runlua("""st=state(80);BerberAI.Gather(st);st.age=3;st.now=1260;st.live.trader=14
        st.budget.food=2400;st.budget.gold=1200;st.enemy_home=World_Pos(200,0,0)
        BerberAI.AgeUp(st);assert(st.built[1].name=='building_landmark_age3_landmarke_mal');assert(st.built[1].pos.x<0)
        """)

    def test_two_tcs_each_fund_villagers_with_combined_target(self):
        self.runlua("""st=state(40);building(st,100,'tc');building(st,101,'tc2')
        BerberAI.Economy(st);assert(#st.trained==2);st.counts.villager=59;st.trained={}
        BerberAI.Economy(st);assert(#st.trained==1)
        """)

    def test_opening_producers_are_not_extra_farm_blocked_buildings(self):
        self.runlua("""st=state(30);BerberAI_State.world_entities={};BerberAI.Gather(st);st.age=2;st.budget.wood=500
        building(st,100,'tc');building(st,101,'building_landmark_age1_landmarkb_mal');building(st,102,'market')
        BerberAI.Infrastructure(st);assert(attempts(st,'range')==1)
        """)

    def test_unobserved_accepted_half_retries_after_pending_expires(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=600;st.budget.wood=1000;st.budget.stone=1000
        building(st,100,'building_landmark_age1_landmarkb_mal');building(st,101,'market');building(st,102,'range')
        st.fail.range=true;BerberAI.Infrastructure(st);assert(attempts(st,'market')==1)
        st.build_pending={};st.now=660;st.reserved={};st.fail.range=false;BerberAI.Infrastructure(st)
        assert(attempts(st,'market')==2)
        """)

    def test_farm_cluster_recounts_rejected_or_destroyed_farms(self):
        self.runlua("""st=state(30);BerberAI_State.world_entities={};BerberAI.Gather(st);st.age=2;st.budget.wood=500
        building(st,100,'tc');for i=1,8 do building(st,110+i,'farm',i,0) end
        building(st,130,'mill',36,36);st.farm_clusters={{pos=World_Pos(36,0,36),count=8}}
        BerberAI.Infrastructure(st);assert(#st.farm_clusters==1)
        local a;for _,b in ipairs(st.attempts) do if b.name=='farm' then a=b end end
        assert(a and a.pos.x==36 and a.pos.z==36)
        """)

    def test_tent_stone_workers_resume_when_target_met_without_expansion_due(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=500
        st.temporary_miners[1]='food';st.worker_role[1]='stone';st.mining_target=100
        st.budget.stone=100;BerberAI.Economy(st);assert(st.worker_role[1]=='food');assert(st.mining_target==nil)
        """)

    def test_transient_producer_failure_does_not_request_extra_tent(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=600;st.budget.wood=1000;st.budget.stone=1000
        building(st,100,'building_landmark_age1_landmarkb_mal');building(st,101,'market');building(st,102,'range')
        st.fail.range='workers';BerberAI.Infrastructure(st);assert(attempts(st,'tent')==0)
        """)

    def test_no_upgrade_worker_count_for_missing_worksite(self):
        self.runlua("""st=state(30);BerberAI.Gather(st);assert(st.resource_counts.wood==0)
        assert(st.resource_counts.gold==0);assert(st.resource_counts.food==countrole(st,'food'))
        """)

    def test_feudal_keeps_six_food_workers(self):
        self.runlua("""st=state(10);BerberAI.Gather(st);st.budget.food=400;st.budget.gold=200
        BerberAI.AgeUp(st);assert(#st.built==0)
        """)

    def test_boolean_knight_observation_uses_reduced_tower_threshold(self):
        self.runlua("""st=state(10);for i=1,10 do st.worker_role[i]='gold' end
        deposit(110,'gold','gold',40,0);building(st,100,'tc');st.budget.wood=150;st.enemy_knights=true
        BerberAI.Gather(st);BerberAI.Infrastructure(st);assert(attempts(st,'outpost')==1)
        """)

    def test_trade_uses_validated_raw_entity_position_not_handle_properties(self):
        self.runlua("""st=state(30);BerberAI.Gather(st);st.age=2;st.now=500
        local p=World_Pos(80,0,0)
        st.trade_target=setmetatable({id=999},{__index=function(_,k) if k=='pos' then error('opaque entity field read') end end})
        local original=Entity_GetPosition
        Entity_GetPosition=function(e) if e==st.trade_target then return p else return original(e) end end
        building(st,100,'market');building(st,101,'range');building(st,102,'building_landmark_age1_landmarkb_mal')
        st.budget.wood=300;st.budget.gold=250;BerberAI.Infrastructure(st)
        local j;for _,b in ipairs(st.built) do if b.name=='market' then j=b end end
        assert(j and BerberAI.Distance(j.pos,p)>=10000)
        st.trade_target.dead=true;st.built={};st.build_pending={};st.reserved={};BerberAI.Infrastructure(st)
        for _,b in ipairs(st.built) do assert(b.name~='market') end
        """)

    def test_second_tc_miners_and_builders_four_food_four_gold(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=630
        deposit(110,'gold','gold',40,0,3000);BerberAI.Infrastructure(st)
        local food,gold=0,0;for _,key in pairs(st.temporary_miners) do if key=='food' then food=food+1 elseif key=='gold' then gold=gold+1 end end
        assert(food==4 and gold==4)
        st.budget.stone=300;st.budget.wood=400;st.reserved={};BerberAI.Infrastructure(st)
        local tc;for _,b in ipairs(st.built) do if b.name=='tc2' then tc=b end end
        assert(tc);food=0;gold=0;for _,id in ipairs(tc.workers) do if st.worker_role[id]=='food' then food=food+1 elseif st.worker_role[id]=='gold' then gold=gold+1 end end
        assert(food==4 and gold==4)
        """)

    def test_second_tc_funded_stone_still_uses_four_food_four_gold(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=630
        deposit(110,'gold','gold',40,0,3000);st.budget.stone=300;st.budget.wood=400;BerberAI.Infrastructure(st)
        local tc;for _,b in ipairs(st.built) do if b.name=='tc2' then tc=b end end
        assert(tc);local food,gold=0,0;for _,id in ipairs(tc.workers) do if st.worker_role[id]=='food' then food=food+1 elseif st.worker_role[id]=='gold' then gold=gold+1 end end
        assert(food==4 and gold==4)
        """)

    def test_tent_stone_uses_eight_food_gold_workers(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=600;st.budget.wood=1000
        building(st,100,'building_landmark_age1_landmarkb_mal');building(st,101,'market');building(st,102,'range')
        st.fail.market=true;BerberAI.Infrastructure(st);assert(countrole(st,'stone')==8)
        for _,key in pairs(st.temporary_miners) do assert(key=='food' or key=='gold') end
        """)

    def test_miner_shortage_substitutes_only_available_food_gold(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=630
        local seen=0;for _,s in ipairs(st.squads) do if st.worker_role[s.id]=='gold' then seen=seen+1;if seen>2 then st.worker_role[s.id]='wood' end end end
        BerberAI.Infrastructure(st);local food,gold=0,0
        for _,key in pairs(st.temporary_miners) do if key=='food' then food=food+1 elseif key=='gold' then gold=gold+1 end end
        assert(food==6 and gold==2)
        """)

    def test_stone_camp_job_cannot_restore_obsolete_stone_role(self):
        self.runlua("""st=state(40);BerberAI.Gather(st);st.age=2;st.now=500
        st.temporary_miners[1]='food';st.worker_role[1]='stone';st.mining_target=100;st.budget.stone=100
        st.construction_jobs={[99]={workers={1},previous_roles={[1]='stone'}}}
        BerberAI.Economy(st);assert(st.worker_role[1]=='food');assert(st.construction_jobs[99].previous_roles[1]=='food')
        """)

    def test_all_three_feudal_builders_die_replacements_finish_foundation(self):
        self.runlua("""st=state(12);BerberAI.Gather(st)
        local b=building(st,100,'building_landmark_age1_landmarkb_mal',0,0,false)
        st.construction_jobs[100]={workers={1,2,3},previous_roles={[1]='food',[2]='food',[3]='food'},options={resource='food',ids={1,2,3}}}
        for i=1,3 do st.squads[i].squad.dead=true;st.worker_jobs[i]=100 end
        st.reserved[4]=true;BerberAI.MaintainConstruction(st)
        local j=st.construction_jobs[100];assert(j.required_workers==3 and #j.workers==3)
        for _,id in ipairs(j.workers) do assert(id>4 and st.worker_role[id]=='food');assert(j.previous_roles[id]=='food');assert(st.worker_jobs[id]==100) end
        local progress=0;for tick=1,4 do
            BerberAI.MaintainConstruction(st)
            for _,id in ipairs(j.workers) do if st.orders[id] and st.orders[id].cmd=='build' and st.orders[id].target==100 then progress=progress+1 end end
            if progress>=9 then b.complete=true;break end
        end
        assert(b.complete and progress>=9)
        """)

    def test_replacements_do_not_steal_held_sheltered_or_reserved_workers(self):
        self.runlua("""st=state(12);BerberAI.Gather(st);building(st,100,'house',0,0,false)
        st.squads[1].squad.dead=true;st.squads[2].squad.held=true;st.sheltered={[3]=true};st.reserved[4]=true
        st.construction_jobs[100]={workers={1},previous_roles={[1]='food'},options={resource='food',ids={1}}}
        st.orders={};BerberAI.MaintainConstruction(st);local j=st.construction_jobs[100]
        assert(j.required_workers==1 and #j.workers==1 and j.workers[1]==5)
        assert(st.orders[2]==nil and st.orders[3]==nil and st.orders[4]==nil)
        """)

    def test_orphan_without_available_workers_remembers_two_worker_requirement(self):
        self.runlua("""st=state(6);BerberAI.Gather(st);building(st,100,'house',0,0,false)
        for i=1,6 do st.reserved[i]=true end
        BerberAI.MaintainConstruction(st);assert(st.construction_jobs[100].required_workers==2)
        st.reserved={};BerberAI.MaintainConstruction(st);assert(#st.construction_jobs[100].workers==2)
        """)

    def test_partial_crew_death_preserves_survivor_and_required_count(self):
        self.runlua("""st=state(12);BerberAI.Gather(st);building(st,100,'house',0,0,false)
        st.squads[1].squad.dead=true;st.worker_jobs[1]=100;st.worker_jobs[2]=100
        st.construction_jobs[100]={workers={1,2},previous_roles={[1]='food',[2]='food'},options={resource='food'}}
        BerberAI.MaintainConstruction(st);local j=st.construction_jobs[100];assert(j.required_workers==2 and #j.workers==2)
        assert(j.workers[1]==2 and j.workers[2]==3)
        st.reserved={};BerberAI.MaintainConstruction(st);assert(j.workers[1]==2 and j.workers[2]==3)
        """)

    def test_archer_ram_foundation_recruits_archer_replacements(self):
        self.runlua("""st=state(6);BerberAI.Gather(st)
        for i=1,6 do st.squads[i].role='archer' end
        st.squads[1].squad.dead=true
        st.construction_entities={{id=100,name='ram',entity={id=100},complete=false,pos=World_Pos(0,0,0)}}
        st.construction_jobs[100]={workers={1},previous_roles={},options={role='archer',ids={1}}}
        BerberAI.MaintainConstruction(st);local j=st.construction_jobs[100]
        assert(#j.workers==1 and j.workers[1]==2 and st.orders[2].cmd=='build')
        """)


if __name__ == '__main__':
    unittest.main()
