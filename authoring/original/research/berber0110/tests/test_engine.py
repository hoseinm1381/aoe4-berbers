"""Strict Lua 5.1 engine/control regressions; these are not native acceptance."""
from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

ROOT=Path(__file__).resolve().parents[1]

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'test_runtime.lua').read_text())
        for name in ['policy','catalog','engine','controller']:
            self.lua.execute((ROOT/'ai'/f'berber_ai_{name}.scar').read_text())
        self.lua.execute('setup_match(false); BerberAI_OnInit(); st=BerberAI_State.players[players[1].id]; BerberAI.Snapshot(st)')
    def check(self,code): self.lua.execute(code)
    def test_profiles(self):
        self.check('for i,p in ipairs(BerberAI.Profiles) do assert(p.workers==({60,75,90,105})[i]);assert(p.traders==i*10);assert(p.bonus==({.1,.2,.3,.5})[i]);assert(p.interval==1 and p.scouts==1 and p.alliance=="zenata") end')
    def test_spawned_only_snapshot_and_world(self):
        self.check('players[1].buildings.despawned=200;players[1].squads.despawned=200;add_building(players[1],"dead",pos(1,1),true).alive=false;BerberAI.Snapshot(st);BerberAI.RefreshWorld(10);assert(#st.buildings==1);for _,e in ipairs(BerberAI_State.world_entities) do assert(e.alive~=false) end')
    def test_workers_resource_ids_reservations_and_hold(self):
        self.check('local a,b,c=st.squads[1],st.squads[2],st.squads[3];st.worker_role={[a.id]="food",[b.id]="gold",[c.id]="gold"};st.reserved[b.id]=true;c.squad.hold={};local x=BerberAI.Workers(st,st.home,4,{resource="gold"});assert(#x==0);local _,ids=BerberAI.Workers(st,st.home,4,{ids={a.id}});assert(#ids==1 and ids[1]==a.id)')
    def test_train_last_two_slots_and_exact_producer(self):
        self.check('players[1].cap=8;assert(BerberAI.Train(st,"villager",{building_id=st.buildings[1].id}));assert(st.counts.villager==7);assert(not BerberAI.Train(st,"villager",{building_id=-99}))')
    def test_train_pending_counts_and_queue_population(self):
        self.check('players[1].cap=8;local b=st.buildings[1];assert(BerberAI.Train(st,"villager"));time=1;BerberAI.Snapshot(st);assert(st.counts.villager==7);assert(not BerberAI.Train(st,"villager"));assert(#b.entity.queue==1)')
    def test_pending_unobserved_unit_counts_once(self):
        self.check('LocalCommand_EntityBuildSquad=function() end;assert(BerberAI.Train(st,"villager"));time=1;BerberAI.Snapshot(st);assert(st.counts.villager==7);assert(not BerberAI.Train(st,"villager"))')
    def test_train_filters_exclude_and_new_producer(self):
        self.check('local b=add_building(players[1],BerberAI.Building.tc,pos(30,0),true);BerberAI.Snapshot(st);assert(BerberAI.Train(st,"villager",{exclude_ids={[st.buildings[1].id]=true}}));assert(#b.queue==1)')
    def test_shared_budget_prevents_overspend(self):
        self.check('st.budget={food=50};assert(BerberAI.Train(st,"villager"));assert(not BerberAI.Spend(st,{food=1}));assert(st.budget.food==0)')
    def test_construct_returns_job_and_matches_only_new_foundation(self):
        self.check('local old=add_building(players[1],BerberAI.Building.house,pos(6,0),true);BerberAI.Snapshot(st);local ok,job=BerberAI.Construct(st,BerberAI.Building.house,st.home,1,true,20,{return_jobs=true});assert(ok and job and job.existing_ids[old.id]);time=1;BerberAI.Snapshot(st);assert(#st.build_pending==0);assert(job.entity_id and job.entity_id~=old.id);assert(st.construction_jobs[job.entity_id]==job)')
    def test_construct_reserved_until_complete_restores_jobs(self):
        self.check('st.worker_role={};for _,s in ipairs(st.squads) do st.worker_role[s.id]="gold" end;local ok,j=BerberAI.Construct(st,BerberAI.Building.house,st.home,1,true,20,{resource="gold",return_jobs=true});assert(ok);local id=j.workers[1];time=1;BerberAI.Snapshot(st);assert(st.reserved[id] and st.worker_jobs[id]);st.worker_role[id]="wood";for _,b in ipairs(players[1].buildings) do b.complete=true end;time=2;BerberAI.Snapshot(st);assert(not st.reserved[id] and st.worker_jobs[id]==nil and st.worker_role[id]=="gold")')
    def test_failed_construct_bounded_retry_and_release(self):
        self.check('LocalCommand_PlayerSquadConstructBuilding=function() end;local ok,j=BerberAI.Construct(st,BerberAI.Building.house,st.home,1,true,20);assert(ok);for i=1,3 do time=i;BerberAI.Snapshot(st);assert(not BerberAI.Construct(st,BerberAI.Building.house,st.home,1,true,20)) end;time=20;BerberAI.Snapshot(st);assert(#st.build_pending==0);assert(not st.reserved[j.workers[1]])')
    def test_placement_influence_and_exact_anchor_constraints(self):
        self.check('players[1].upgrades.feudal_age=true;BerberAI.Snapshot(st);local ok=BerberAI.Construct(st,BerberAI.Building.range,st.home,1,false,20,{influence=true});assert(not ok and st.last_construct_failure=="placement");local t=add_building(players[1],BerberAI.Building.tent,pos(st.home.x+20,st.home.z),true);BerberAI.Snapshot(st);local accepted,j=BerberAI.Construct(st,BerberAI.Building.range,t.pos,1,false,20,{influence=true});assert(accepted and BerberAI.Distance(t.pos,j.pos)<=400)')
    def test_trade_market_foundation_identity_and_distance(self):
        self.check('players[1].upgrades.feudal_age=true;BerberAI.Snapshot(st);local target=pos(st.home.x+120,st.home.z);local ok,j=BerberAI.Construct(st,BerberAI.Building.market,st.home,1,true,24,{trade=true,exact_anchor=true,target_pos=target,min_target_distance=100});assert(ok and BerberAI.Distance(j.pos,target)>=10000);time=1;BerberAI.Snapshot(st);assert(st.trade_market_id==j.entity_id)')
    def test_target_deduplicates_per_squad_respects_move_and_queue(self):
        self.check('target_commands=0;local native=LocalCommand_SquadEntity;LocalCommand_SquadEntity=function(...) target_commands=target_commands+1;native(...) end;local s=st.squads[1].squad;local e=st.buildings[1].entity;BerberAI.Target(st,{s},SCMD_DefaultAction,e,false);BerberAI.Target(st,{s},SCMD_DefaultAction,e,false);assert(target_commands==1);BerberAI.Move({s},pos(10,10),false);BerberAI.Target(st,{s},SCMD_DefaultAction,e,false);assert(target_commands==2);BerberAI.Target(st,{s},SCMD_DefaultAction,e,true);assert(target_commands==3)')
    def test_castle_rng_once_and_restore_preserves_clock(self):
        self.check('assert(rand_calls==7 and st.castle_time>=720 and st.castle_time<=840);local t=st.castle_time;BerberAI_Start();BerberAI_OnGameRestore();BerberAI_OnGameRestore();assert(rand_calls==7 and st.castle_time==t);local n=0;for f in pairs(rules) do n=n+1 end;assert(n==1)')
    def test_income_highest_enemy_cadence_no_stacking_and_remove(self):
        self.check('for _,p in ipairs(players) do p.rates={0,0,0,0} end;players[2].rates={1,2,3,4};time=59;st.now=59;BerberAI.IncomeAssistance(st);assert(not st.income_bonus_active);time=60;st.now=60;BerberAI.IncomeAssistance(st);assert(st.income_bonus_active and st.income_enemy_per_minute==600 and #st.income_modifiers==4);local n=modifier_created;time=61;st.now=61;BerberAI.IncomeAssistance(st);assert(modifier_created==n);players[1].rates={10,0,0,0};time=120;st.now=120;BerberAI.IncomeAssistance(st);assert(not st.income_bonus_active and modifier_removed==4)')
    def test_game_over_removes_owned_modifiers(self):
        self.check('for _,p in ipairs(players) do p.rates={0,0,0,0} end;players[2].rates={10,0,0,0};time=60;st.now=60;BerberAI.IncomeAssistance(st);BerberAI_OnGameOver();assert(modifier_removed==4 and BerberAI_State.stopped);BerberAI_OnGameOver();assert(modifier_removed==4)')
    def test_controller_order(self):
        self.check('local out={};for _,k in ipairs({"Snapshot","Observe","MaintainConstruction","VillagerSafety","Economy","Produce","Army","SpecialUnits","IncomeAssistance"}) do BerberAI[k]=function(s) if s==st then table.insert(out,k) end end end;BerberAI_Tick();assert(table.concat(out,",")=="Snapshot,Observe,MaintainConstruction,VillagerSafety,Economy,Produce,Army,SpecialUnits,IncomeAssistance")')
    def test_complete_build_count_excludes_pending(self):
        self.check('assert(BerberAI.Construct(st,BerberAI.Building.house,st.home,1,true,20));assert(BerberAI.CountBuilding(st,BerberAI.Building.house,true)==0 and BerberAI.CountBuilding(st,BerberAI.Building.house,false)==1)')
    def test_pending_upgrade_not_counted_as_unit(self):
        self.check('st.production_pending[st.buildings[1].id]={name="upgrade_test",upgrade=true,until_time=3};time=1;BerberAI.Snapshot(st);assert(st.queued_upgrades.upgrade_test and not st.counts.other and st.queued_population==0)')
    def test_construct_requires_requested_builder_count(self):
        self.check('local ok=BerberAI.Construct(st,BerberAI.Building.house,st.home,8,true,20);assert(not ok and st.last_construct_failure=="workers" and #st.build_pending==0)')
    def test_pending_nonbuilding_siege_observed_and_released(self):
        self.check('players[1].upgrades.upgrade_siege_engineers=true;players[1].upgrades.feudal_age=true;BerberAI.Snapshot(st);LocalCommand_PlayerSquadConstructBuilding=function(p,g,bp,where) local e={id=new_id(),name=bp,player=p,pos=where,complete=false};table.insert(p.buildings,e);table.insert(all_entities,e) end;local ok,j=BerberAI.Construct(st,"unit_ram_3_mal",st.home,1,false,20);assert(ok);time=1;BerberAI.Snapshot(st);assert(j.entity_id and #st.build_pending==0);local e=players[1].buildings[#players[1].buildings];e.complete=true;time=2;BerberAI.Snapshot(st);assert(st.worker_jobs[j.workers[1]]==nil)')
    def test_destroyed_foundation_restores_and_invalid_handles_ignored(self):
        self.check('local ok,j=BerberAI.Construct(st,BerberAI.Building.house,st.home,1,true,20);time=1;BerberAI.Snapshot(st);local e=players[1].buildings[#players[1].buildings];e.invalid=true;st.squads[2].squad.invalid=true;time=2;BerberAI.Snapshot(st);assert(st.worker_jobs[j.workers[1]]==nil and #st.squads==6);BerberAI.RefreshWorld(2)')
    def test_repeated_match_has_fresh_clocks_and_no_old_orders(self):
        self.check('BerberAI_State.orders={[1]={}};BerberAI_OnGameOver();BerberAI_OnGameSetup();BerberAI_OnInit();assert(rand_calls==14 and not BerberAI_State.orders and not BerberAI_State.started)')
    def test_income_modifier_handles_survive_restore_without_reapply(self):
        self.check('for _,p in ipairs(players) do p.rates={0,0,0,0} end;players[2].rates={1,0,0,0};st.now=60;time=60;BerberAI.IncomeAssistance(st);local n=modifier_created;BerberAI_OnGameRestore();st.now=120;time=120;BerberAI.IncomeAssistance(st);assert(modifier_created==n and #st.income_modifiers==4);for _,m in ipairs(st.income_modifiers) do assert(m.type==MAT_EntityType and m.value==1.1 and m.bp=="unit_villager_1_mal") end')
    def test_squad_owned_siege_foundation_observed(self):
        self.check('players[1].upgrades.upgrade_siege_engineers=true;players[1].upgrades.feudal_age=true;BerberAI.Snapshot(st);LocalCommand_PlayerSquadConstructBuilding=function(p,g,bp,where) local s=add_squad(p,bp,where);s.entity.complete=false end;local ok,j=BerberAI.Construct(st,"unit_ram_3_mal",st.home,1,false,20);assert(ok);time=1;BerberAI.Snapshot(st);assert(j.entity_id and #st.build_pending==0 and st.construction_jobs[j.entity_id])')
    def test_command_limit_does_not_report_placement_full(self):
        self.check('st.command_count=12;assert(not BerberAI.Construct(st,BerberAI.Building.house,st.home,1,true,20));assert(st.last_construct_failure=="command_limit")')
    def test_stone_purchase_native_ability_pending_reserves_gold_once(self):
        self.check('local m=add_building(players[1],BerberAI.Building.market,pos(10,10),true);BerberAI.Snapshot(st);calls=0;LocalCommand_EntityAbility=function(p,g,bp,skip,queued) calls=calls+1;assert(g[1]==m and bp=="core_market_buy_stone" and not skip and not queued) end;assert(BerberAI.BuyStone(st,100));assert(st.budget.gold==0 and calls==1 and st.stone_purchase_pending.before_stone==players[1].resources[4]);assert(BerberAI.BuyStone(st,100) and calls==1);players[1].resources[4]=players[1].resources[4]+100;assert(BerberAI.BuyStone(st,100) and not st.stone_purchase_pending)')
    def test_stone_purchase_native_rejection_timeout_falls_back(self):
        self.check('add_building(players[1],BerberAI.Building.market,pos(10,10),true);BerberAI.Snapshot(st);calls=0;LocalCommand_EntityAbility=function() calls=calls+1 end;assert(BerberAI.BuyStone(st,100));st.now=3;assert(not BerberAI.BuyStone(st,100));assert(st.stone_purchase_retry==33);st.now=4;assert(not BerberAI.BuyStone(st,100) and calls==1);st.now=33;st.budget.gold=100;assert(BerberAI.BuyStone(st,100) and calls==2)')
    def test_stone_purchase_no_producer_no_gold_and_saving(self):
        self.check('assert(not BerberAI.BuyStone(st,100));add_building(players[1],BerberAI.Building.market,pos(10,10),true);BerberAI.Snapshot(st);st.budget.gold=0;assert(not BerberAI.BuyStone(st,100));st.budget.gold=100;st.saving_age=true;assert(not BerberAI.BuyStone(st,100))')
    def test_empty_groups_and_destroyed_cached_world(self):
        self.check('BerberAI.RefreshWorld(0);local e=all_entities[1];e.invalid=true;players[1].buildings={};players[1].squads={};BerberAI.Snapshot(st);assert(#st.buildings==0 and #st.squads==0);all_entities={};BerberAI.RefreshWorld(1);assert(#BerberAI_State.world_entities==0);BerberAI.WithSquads({},function() error("empty callback") end)')
    def test_income_no_living_enemies_removes_bonus(self):
        self.check('for _,p in ipairs(players) do p.rates={0,0,0,0} end;players[2].rates={1,0,0,0};st.now=60;BerberAI.IncomeAssistance(st);for _,p in ipairs(players) do if p.team~=st.player.team then p.alive=false end end;st.now=120;BerberAI.IncomeAssistance(st);assert(not st.income_bonus_active and modifier_removed==4)')
    def test_adopted_foundation_job_without_entity_id_releases_workers(self):
        self.check('local b=add_building(players[1],BerberAI.Building.house,pos(10,10),false);local id=st.squads[1].id;st.construction_jobs[b.id]={workers={id},previous_roles={[id]="gold"}};st.worker_jobs[id]=b.id;st.worker_role[id]="wood";b.complete=true;time=1;BerberAI.Snapshot(st);assert(st.worker_jobs[id]==nil and st.worker_role[id]=="gold")')

if __name__=='__main__': unittest.main()
