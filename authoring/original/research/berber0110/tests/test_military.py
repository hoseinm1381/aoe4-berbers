"""Behavior tests execute the authoring modules under Lua 5.1, with strict engine handles."""
import pathlib
import unittest
from lupa.lua51 import LuaRuntime

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = r'''
BerberAI={Building={tc='town_center',expansion='town_center2',mosque='monastery',market='market'}}
BerberAI_State={world_entities={}}
R_ENEMY=2;R_ALLY=1;SCMD_Attack='attack';SCMD_DefaultAction='default';SCMD_Capture='capture';SCMD_Trade='trade'
orders={};groups=0
function pos(x,z) return {x=x,y=0,z=z or 0} end
function BerberAI.Pos(p,x,z) return pos(p.x+x,p.z+z) end
function BerberAI.Distance(a,b) return (a.x-b.x)^2+(a.z-b.z)^2 end
function BerberAI.Name(x) return x end
function BerberAI.EntityValid(e) return e~=nil and not e.dead end
function BerberAI.SquadValid(s) return s~=nil and not s.dead end
function Entity_GetID(e) assert(not e.dead,'dead entity');return e.id end
function Entity_GetBlueprint(e) assert(not e.dead);return e.name end
function Entity_GetPosition(e) assert(not e.dead);return e.pos end
function Entity_GetSquad(e) assert(not e.dead);return e.squad end
function Entity_GetStateModelBool(e,key) assert(not e.dead);assert(key=='is_carrying_entity');return e.carrying or false end
function World_OwnsEntity(e) assert(not e.dead);return e.owner==nil end
function Entity_GetPlayerOwner(e) assert(e.owner~=nil,'world owner fatal');assert(not e.dead);return e.owner end
function Player_ObserveRelationship(p,o) return o==p and 0 or (o==4 and R_ALLY or R_ENEMY) end
function Player_IsAlive(p) return p~=99 end
function Player_GetID(p) return p end
function Entity_IsBuilding(e) return e.building or false end
function Entity_IsUnderConstruction(e) assert(not e.dead);return e.foundation or false end
function Entity_IsOfType(e,t) return e.types[t] or false end
function BP_GetEntityBPCost(bp) return costs[bp] or {food=100} end
function Squad_GetID(s) assert(not s.dead);return s.id end
function Squad_GetPosition(s) assert(not s.dead);return s.pos end
function Squad_GetFirstEntity(s) assert(not s.dead);return s.entity end
function Squad_GetHealthPercentage(s,b) assert(b==false);assert(not s.dead);return s.hp or 1 end
function Squad_IsUnderAttack(s,t) return s.attacked or false end
function Squad_IsIdle(s) return s.idle~=false end
function Squad_IsHoldingAny(s) return s.holding or false end
function Squad_IsInHoldEntity(s) return s.held or false end
function Entity_GetMaxHoldSquadSlots(e) return e.capacity or 0 end
function Entity_GetFilledHoldSquadSlots(e) return e.filled or 0 end
function AISquad_HasPathWithinDistance(s,p,d) return not s.unreachable end
function World_PosInBounds(p) return math.abs(p.x)<1000 and math.abs(p.z)<1000 end
function World_GetWidth() return 500 end
function World_GetLength() return 500 end
function Player_CanSeeEntity() return false end
function Player_CanSeePosition() return false end
function BerberAI.WithSquads(a,f) if #a>0 then f(a) end end
function BerberAI.WithEntity(e,f) if BerberAI.EntityValid(e) then f({e}) end end
function BerberAI.Target(st,ss,c,e,q) assert(BerberAI.EntityValid(e));for _,s in ipairs(ss) do orders[s.id]={command=c,target=e,queued=q} end end
function BerberAI.Move(ss,p,a) for _,s in ipairs(ss) do assert(not s.dead);orders[s.id]={pos=p,attack=a} end end
function Cmd_Garrison(ss,es,o,q,i) assert(not o and not q and not i);for _,s in ipairs(ss) do orders[s.id]={garrison=es[1]} end end
function Cmd_UngarrisonSquad(ss,p,q) for _,s in ipairs(ss) do orders[s.id]={ungarrison=p} end end
function Cmd_Stop(ss) for _,s in ipairs(ss) do orders[s.id]={stop=true} end end
function SGroup_CreateUnique() groups=groups+1;return {} end
function SGroup_Destroy(g) groups=groups-1 end
function Squad_GetLastAttackers(s,g,t) for _,a in ipairs(s.attackers or {}) do table.insert(g,a) end end
function SGroup_ForEachEx(g,f,spawned,despawned) assert(spawned and not despawned);for i,s in ipairs(g) do if not s.dead then f(g,i,s) end end end
function EGroup_CreateUnique() groups=groups+1;return {} end
function EGroup_Destroy(g) groups=groups-1 end
function Squad_GetLastEntityAttacker(s,g) for _,e in ipairs(s.entity_attackers or {}) do table.insert(g,e) end end
function EGroup_ForEachEx(g,f,spawned,despawned) assert(spawned and not despawned);for i,e in ipairs(g) do if not e.dead then f(g,i,e) end end end
function BerberAI.FirstBuilding(st,name) for _,b in ipairs(st.buildings) do if b.name==name and b.complete and not b.entity.dead then return b.entity end end end
costs={}
function state() return {now=0,age=2,home=pos(0),player=1,pid=1,squads={},buildings={},reserved={},live={},config={},memory={},scout_progress={},special_until={},rt={food='food',wood='wood',gold='gold',stone='stone'},contacts={}} end
function ent(id,name,x,owner,types,building)
 local e={id=id,name=name,pos=pos(x),owner=owner,types=types or {},building=building};table.insert(BerberAI_State.world_entities,e);return e
end
function unit(st,id,role,x,hp)
 local s={id=id,pos=pos(x),hp=hp,role=role};s.entity=ent(id,role,x,st.player,{[role]=true});s.entity.squad=s
 table.insert(st.squads,{id=id,squad=s,pos=s.pos,role=role,name=role});return s
end
function enemy(id,name,x,types,owner)
 local e=ent(id,name,x,owner or 2,types or {});e.squad={id=id,pos=e.pos,entity=e};return e
end
function building(st,id,name,x,capacity,filled)
 local e=ent(id,name,x,st.player,{},true);e.capacity=capacity;e.filled=filled
 table.insert(st.buildings,{id=id,entity=e,name=name,pos=e.pos,complete=true});return e
end
'''


class MilitaryTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        for name in ("berber_ai_navigation.scar", "berber_ai_military.scar"):
            path = ROOT / "ai" / name
            if path.exists():
                self.lua.execute(path.read_text(encoding="utf-8-sig"))

    def check(self, code):
        self.lua.execute(code)

    def test_hidden_world_and_owner_safe_nearest_enemy(self):
        self.check('''st=state();ent(1,'tree',2,nil);enemy(2,'archer',150,{ranged=true});enemy(3,'spearman',90,{infantry=true,spearman=true},3);ent(4,'town_center',100,3,{},true);ent(5,'town_center',200,2,{},true);BerberAI.Observe(st);assert(#st.contacts==4);assert(st.enemy_player==3);assert(st.enemy_stats.melee_infantry==1)''')

    def test_dead_contacts_not_reused(self):
        self.check("st=state();e=enemy(2,'villager',80);BerberAI.Observe(st);e.dead=true;BerberAI.Observe(st);assert(#st.contacts==0)")

    def test_unmodified_value_not_health_weighted(self):
        self.check("st=state();unit(st,1,'zenata',10,.1);costs.zenata={food=100,gold=120};BerberAI.Observe(st);assert(st.army_value==220)")

    def test_combined_knight_archer_budget(self):
        self.check("assert(BerberAI.RaidFavorable(4,0,2,8));assert(not BerberAI.RaidFavorable(4,0,3,8));assert(not BerberAI.RaidFavorable(4,7,0,0));assert(BerberAI.RaidFavorable(1,0,1,0));assert(BerberAI.RaidFavorable(1,0,0,4))")

    def test_spears_share_the_force_budget_with_knights(self):
        self.check("assert(not BerberAI.RaidFavorable(4,6,1,0));assert(BerberAI.RaidFavorable(4,5,1,0))")

    def test_raid_prefers_exposed_villager_over_guarded_nearest(self):
        self.check("st=state();unit(st,1,'zenata',20);enemy(2,'villager',50);enemy(3,'spearman',51,{spearman=true});enemy(4,'spearman',52,{spearman=true});enemy(5,'villager',80);BerberAI.Observe(st);BerberAI.Army(st);assert(orders[1].target.id==5)")

    def test_first_lancer_raids_and_bad_encounter_regroups_halfway(self):
        self.check("st=state();s=unit(st,1,'zenata',40);enemy(2,'villager',80);BerberAI.Observe(st);BerberAI.Army(st);assert(orders[1].target.id==2);enemy(3,'spearman',81,{spearman=true,infantry=true});enemy(4,'spearman',82,{spearman=true,infantry=true});BerberAI.Observe(st);BerberAI.Army(st);assert(orders[1].pos.x==20)")

    def test_six_archers_and_no_individual_health_retreat(self):
        self.check("st=state();unit(st,100,'zenata',2);for i=1,5 do unit(st,i,'archer',1,.1) end;enemy(99,'villager',20);BerberAI.Observe(st);BerberAI.Army(st);assert(orders[1].target==nil);unit(st,6,'archer',1,.1);BerberAI.Observe(st);BerberAI.Army(st);assert(orders[1].target.id==99)")

    def test_deployed_archer_survivors_continue_but_reinforcements_wait_for_six(self):
        self.check("st=state();for i=1,6 do unit(st,i,'archer',1) end;unit(st,100,'zenata',2);enemy(99,'villager',20);BerberAI.Observe(st);BerberAI.Army(st);st.squads[6].squad.dead=true;st.squads[6].squad.entity.dead=true;unit(st,7,'archer',1);BerberAI.Observe(st);orders={};BerberAI.Army(st);assert(orders[1].target.id==99);assert(not orders[7].target)")

    def test_lancer_health_hysteresis_and_healer_demand(self):
        self.check("st=state();st.age=3;s=unit(st,1,'zenata',40,.14);enemy(2,'villager',80);BerberAI.Observe(st);BerberAI.Army(st);assert(st.needs_healer);assert(orders[1].pos.x<8);s.hp=.79;BerberAI.Army(st);assert(orders[1].target==nil);s.hp=.8;BerberAI.Army(st);assert(orders[1].target.id==2)")

    def test_tc_exclusion_and_safe_detour(self):
        self.check("st=state();st.contacts={{id=1,pos=pos(50),tc=true,building=true}};assert(not BerberAI.SafePoint(st,pos(74),0));assert(BerberAI.SafePoint(st,pos(75),0));route=BerberAI.FindSafeRoute(st,pos(0),pos(100),4);assert(route and #route>1);for _,p in ipairs(route) do assert(BerberAI.SafePoint(st,p,4)) end")

    def test_scout_proximity_and_scout_attack_exception(self):
        self.check("st=state();s=unit(st,1,'villager',0,1);a=enemy(3,'scout',1,{scout=true});building(st,2,'town_center',0,10,0);BerberAI.Observe(st);BerberAI.VillagerSafety(st);assert(orders[1]==nil);s.attacked=true;s.attackers={a.squad};BerberAI.VillagerSafety(st);assert(orders[1]==nil);s.hp=.09;BerberAI.VillagerSafety(st);assert(orders[1].garrison.id==2);assert(groups==0)")

    def test_knight_twenty_other_twelve_and_resume_twenty_two(self):
        self.check("st=state();s=unit(st,1,'villager',0);e=enemy(3,'knight',20,{cavalry=true});building(st,2,'town_center',0,10,0);BerberAI.Observe(st);BerberAI.VillagerSafety(st);assert(orders[1].garrison.id==2);s.held=true;e.pos=pos(23);BerberAI.Observe(st);BerberAI.VillagerSafety(st);assert(orders[1].ungarrison)")

    def test_shelter_capacity_reserved_and_overflow_circles(self):
        self.check("st=state();a=unit(st,1,'villager',0);b=unit(st,2,'villager',0);enemy(3,'knight',10,{cavalry=true});building(st,4,'town_center',0,1,0);BerberAI.Observe(st);BerberAI.VillagerSafety(st);assert(orders[1].garrison);assert(orders[2].pos);assert(st.reserved[1] and st.reserved[2]);assert(orders[2].pos.x~=0 or orders[2].pos.z~=0)")

    def test_scout_sheep_nearest_safe_and_180_return(self):
        self.check("st=state();s=unit(st,1,'scout',40);ent(2,'sheep',60,nil);ent(3,'sheep',45,nil);BerberAI.Observe(st);BerberAI.SpecialUnits(st);assert(orders[1].pos.x==45);st.now=180;BerberAI.SpecialUnits(st);assert(orders[1].pos.x==0)")

    def test_trade_endpoint_nearest_ally_and_neutral(self):
        self.check("st=state();ent(2,'market',200,4,{},true);ent(3,'trading_post',150,nil,{trade_post=true},true);ent(4,'market',5,1,{},true);BerberAI.Observe(st);assert(st.trade_target.id==3)")

    def test_escort_rounding_reaches_130_percent(self):
        self.check("st=state();for i=1,4 do unit(st,i,'zenata',10) end;st.trade_blocked=true;st.trade_threat_value=200;st.trade_threat_pos=pos(100);BerberAI.Observe(st);st.trade_blocked=true;st.trade_threat_value=200;st.trade_threat_pos=pos(100);BerberAI.Army(st);assert(st.escort_value==300);assert(#st.escort_ids==3)")

    def test_archer_escort_departure_keeps_six_unit_group(self):
        self.check("st=state();for i=1,7 do unit(st,i,'archer',10) end;BerberAI.Observe(st);st.trade_blocked=true;st.trade_threat_value=100;st.trade_threat_pos=pos(100);BerberAI.Army(st);assert(#st.escort_ids==6)")

    def test_independent_relic_site_healer_and_deposit(self):
        self.check("st=state();st.age=3;a=unit(st,1,'monk',0);b=unit(st,2,'monk',0);c=unit(st,3,'monk',0);w=unit(st,4,'zenata',1,.2);building(st,5,'monastery',0);ent(6,'relic',50,nil,{relic=true});ent(7,'sacred',60,nil,{special_beacon=true});BerberAI.Observe(st);BerberAI.SpecialUnits(st);assert(orders[1].target.id==6);assert(orders[2].target.id==7);assert(orders[3].target.id==4);a.entity.carrying=true;BerberAI.SpecialUnits(st);assert(orders[1].target.id==5)")

    def test_relic_carry_reads_monk_entity_state_not_vehicle_hold(self):
        self.check("st=state();st.age=3;a=unit(st,1,'monk',0);a.entity.carrying=true;building(st,5,'monastery',0);ent(6,'relic',50,nil,{relic=true});BerberAI.Observe(st);BerberAI.SpecialUnits(st);assert(orders[1].target.id==5);a.entity.carrying=false;a.holding=true;BerberAI.SpecialUnits(st);assert(orders[1].target.id==6)")

    def test_siege_ratios_nearest_enemy_and_threefold(self):
        self.check("st=state();for i=1,60 do unit(st,i,'zenata',0) end;ent(100,'town_center',100,2,{},true);for i=101,106 do enemy(i,'swordsman',100,{infantry=true,melee_infantry=true}) end;for i=107,116 do enemy(i,'archer',100,{ranged=true}) end;BerberAI.Observe(st);assert(st.siege_targets.springald==1 and st.siege_targets.mangonel==1);assert(st.siege_targets.ram==3);st.age=3;BerberAI.SiegeNeeds(st);assert(st.siege_targets.treb==3 and st.siege_targets.ram==0)")

    def test_siege_local_priority_avoids_entire_base_crossing(self):
        self.check("st=state();s=unit(st,1,'ram',50);ent(2,'house',55,2,{},true);ent(3,'keep',200,2,{},true);BerberAI.Observe(st);BerberAI.Army(st);assert(orders[1].target.id==2)")

    def test_real_hit_shelters_even_without_proximity(self):
        self.check("st=state();s=unit(st,1,'villager',0);s.attacked=true;building(st,2,'town_center',0,10,0);BerberAI.Observe(st);BerberAI.VillagerSafety(st);assert(orders[1].garrison.id==2);assert(groups==0)")

    def test_non_knight_twelve_boundary_and_unreachable_shelter(self):
        self.check("st=state();s=unit(st,1,'villager',0);enemy(3,'archer',12,{ranged=true});building(st,2,'town_center',0,10,0);s.unreachable=true;BerberAI.Observe(st);BerberAI.VillagerSafety(st);assert(orders[1].pos and not orders[1].garrison)")

    def test_safety_resumes_only_after_twenty_two(self):
        self.check("st=state();s=unit(st,1,'villager',0);e=enemy(3,'knight',20,{cavalry=true});building(st,2,'town_center',0,10,0);BerberAI.Observe(st);BerberAI.VillagerSafety(st);s.held=true;e.pos=pos(22);BerberAI.Observe(st);orders={};BerberAI.VillagerSafety(st);assert(st.reserved[1] and not orders[1])")

    def test_light_horseman_uses_twelve_not_knight_twenty(self):
        self.check("st=state();unit(st,1,'villager',0);enemy(3,'unit_horseman_2_eng',18,{cavalry=true});building(st,2,'town_center',0,10,0);BerberAI.Observe(st);BerberAI.VillagerSafety(st);assert(not orders[1]);assert(st.enemy_knights==0)")

    def test_knight_observation_is_numeric_count(self):
        self.check("st=state();enemy(1,'knight',40,{cavalry=true});enemy(2,'lancer',80,{cavalry=true});BerberAI.Observe(st);assert(st.enemy_knights==2)")

    def test_archers_rendezvous_before_remote_raid(self):
        self.check("st=state();unit(st,1,'zenata',150);for i=2,7 do unit(st,i,'archer',0) end;enemy(20,'villager',170);BerberAI.Observe(st);BerberAI.Army(st);assert(orders[2].pos and not orders[2].target);assert(orders[2].pos.x<=150)")

    def test_archers_never_focus_villager_in_tc_danger(self):
        self.check("st=state();unit(st,1,'zenata',80);for i=2,7 do unit(st,i,'archer',75) end;ent(20,'town_center',120,2,{},true);enemy(21,'villager',110);BerberAI.Observe(st);BerberAI.Army(st);assert(not orders[2].target)")

    def test_defending_archers_do_not_focus_inside_enemy_tc_zone(self):
        self.check("st=state();for i=1,6 do unit(st,i,'archer',0) end;ent(20,'town_center',30,2,{},true);enemy(21,'archer',20,{ranged=true});BerberAI.Observe(st);st.defense=true;BerberAI.Army(st);assert(not orders[1].target)")

    def test_archers_wait_for_lancer_screen(self):
        self.check("st=state();for i=1,6 do unit(st,i,'archer',0) end;enemy(20,'villager',20);BerberAI.Observe(st);BerberAI.Army(st);assert(not orders[1].target)")

    def test_raid_targets_villagers_before_enemy_sheep(self):
        self.check("st=state();unit(st,1,'zenata',20);enemy(2,'sheep',30);enemy(3,'villager',70);BerberAI.Observe(st);BerberAI.Army(st);assert(orders[1].target.id==3)")

    def test_trade_chooses_farther_safe_endpoint_when_nearest_guarded(self):
        self.check("st=state();ent(1,'trading_post',100,nil,{trade_post=true},true);ent(2,'town_center',100,2,{},true);ent(3,'market',150,4,{},true);BerberAI.Observe(st);assert(st.trade_target.id==3);assert(not st.trade_blocked)")

    def test_trade_rejects_allied_market_foundation(self):
        self.check("st=state();a=ent(1,'market',100,4,{},true);a.foundation=true;ent(2,'trading_post',150,nil,{trade_post=true},true);BerberAI.Observe(st);assert(st.trade_target.id==2)")

    def test_unsafe_start_can_escape_toward_safety(self):
        self.check("st=state();s=unit(st,1,'scout',20);enemy(2,'archer',22,{ranged=true});BerberAI.Observe(st);assert(BerberAI.SafeMove(st,{s},pos(0),false,4));assert(orders[1].pos.x==0)")

    def test_trader_uses_dedicated_creator_then_external_endpoint(self):
        self.check("st=state();s=unit(st,1,'trader',0);building(st,2,'market',0);st.trade_market_id=2;ent(3,'trading_post',150,nil,{trade_post=true},true);BerberAI.Observe(st);BerberAI.SpecialUnits(st);assert(orders[1].command=='trade' and orders[1].target.id==3)")

    def test_blocked_trader_stops_if_no_escape_route(self):
        self.check("st=state();s=unit(st,1,'trader',40);s.unreachable=true;building(st,2,'market',0);st.trade_market_id=2;ent(3,'trading_post',150,nil,{trade_post=true},true);BerberAI.Observe(st);st.trade_blocked=true;BerberAI.SpecialUnits(st);assert(orders[1].stop)")

    def test_native_unreachable_trade_route_stops_existing_orders(self):
        self.check("st=state();s=unit(st,1,'trader',40);s.unreachable=true;building(st,2,'market',0);st.trade_market_id=2;ent(3,'trading_post',150,nil,{trade_post=true},true);BerberAI.Observe(st);BerberAI.SpecialUnits(st);assert(orders[1].stop)")

    def test_destroyed_dedicated_trade_market_stops_trader(self):
        self.check("st=state();unit(st,1,'trader',40);h=building(st,2,'market',0);st.trade_market_id=2;h.dead=true;ent(3,'trading_post',150,nil,{trade_post=true},true);BerberAI.Observe(st);BerberAI.SpecialUnits(st);assert(orders[1].stop)")

    def test_defense_recalls_siege_and_retains_thirty_percent_lancers(self):
        self.check("st=state();for i=1,10 do unit(st,i,'zenata',80) end;unit(st,11,'ram',80);enemy(90,'villager',120);enemy(91,'archer',20,{ranged=true});BerberAI.Observe(st);st.defense=true;BerberAI.Army(st);local n=0;for i=1,10 do if orders[i] and orders[i].target and orders[i].target.id==90 then n=n+1 end end;assert(n==3);assert(orders[11].pos.x==0 or orders[11].target.id==91)")

    def test_archers_follow_lancer_regroup(self):
        self.check("st=state();unit(st,1,'zenata',60);for i=2,7 do unit(st,i,'archer',60) end;enemy(90,'villager',90);enemy(91,'spearman',91,{spearman=true});enemy(92,'spearman',92,{spearman=true});BerberAI.Observe(st);BerberAI.Army(st);assert(orders[2].pos and orders[2].pos.x==30)")

    def test_imam_stable_roles_survive_death_and_unsafe_sites(self):
        self.check("st=state();st.age=3;a=unit(st,1,'monk',0);b=unit(st,2,'monk',0);building(st,3,'monastery',0);ent(4,'relic',50,nil,{relic=true});ent(5,'sacred',60,nil,{special_beacon=true});BerberAI.Observe(st);BerberAI.SpecialUnits(st);a.dead=true;a.entity.dead=true;unit(st,6,'monk',0);BerberAI.Observe(st);BerberAI.SpecialUnits(st);assert(st.imam_roles.site==2 and st.imam_roles.relic==6);ent(7,'town_center',60,2,{},true);BerberAI.Observe(st);orders={};BerberAI.SpecialUnits(st);assert(not orders[2] or not orders[2].target)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
