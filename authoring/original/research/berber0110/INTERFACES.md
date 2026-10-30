# 0.11.0 shared task contract

Root: E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai.
Author only research/berber0110/ai; root promotes later. Never edit another
worker's modules or reset existing changes. Read the approved spec in docs/
superpowers/specs/2026-10-18-berber-ai-build-order-design.md for exact behavior.

## Common existing interfaces (root owns engine)

- BerberAI.Snapshot(st) supplies now, age, home, player, pid, config, squads,
  buildings, live/counts by role, queued_upgrades, reserved, producer_used,
  budget, production_pending, build_pending and rt food/wood/gold/stone.
- Squad records {squad,id,role,name,pos}; building records {entity,id,name,pos,complete}.
- config {workers,traders,bonus,interval=1,alliance='zenata',scouts=1,name}.
- st.worker_role[id] is persistent resource key food/wood/gold/stone. Economy
  owns assignment. st.worker_jobs retained for construction identity. Root
  initializes missing state tables; modules must also initialize their fields
  for focused tests/restore. st.reserved[id] means do not reassign this tick.
- st.saving_age boolean: pause all NEW spending except villagers/houses.
- Name, Pos, Distance (SQUARED metres), EntityValid, SquadValid, WithEntity,
  WithSquads, Target(st,squad_array,SCMD,entity,queued), Move(squads,pos,attack).
- SafePoint(st,pos,buffer) returns bool, excludes enemy TC radius >=24m and
  enemy combat; SafeMove(st,squads,pos,attack,buffer) returns bool and moves via
  safe waypoint(s) or refuses. Military/navigation owns implementation.
- Workers(st,pos,count,options) -> squads,ids. options.resource='food'/'wood'/
  'gold' filters worker_role strictly; options.ids explicit allowed squad IDs;
  options.role='archer' permits military construction. Unspecified=nearest
  eligible villager. Never steal st.reserved or held squads.
- Construct(st,name,anchor,count,economic,max_radius,options) -> bool. options
  accepts same worker filter keys plus influence=true (must be <=20m from a
  COMPLETE ordinary Tent or Tent landmark), max_distance actual placement
  bounded by max_radius, return_jobs=true. Placement is validated; no forced
  spawning or fake costs. Persist jobs/prior resource assignments until build
  completes; restore them afterward. Failed native command retries bounded.
- Train(st,role,options) -> bool. options.building_id restricts exact producer;
  options.exclude_ids excludes producers. Allow villagers up to actual capacity
  (do not block at two free slots). Debit one shared budget and pending queue.
- Cost(st,'squad'/'upgrade'/'entity',blueprint), Spend(st,cost), Require,
  CountBuilding(st,name,complete), FirstBuilding(st,name) -> entity.
- BuyStone(st,amount) -> bool (root engine): normal market command, cost/budget
  validated; if unavailable/insufficient return false for temporary mining.
- RefreshWorld supplies BerberAI_State.world_entities, valid spawned entities
  sorted by stable ID, full map, refreshed shared once per second.

## Module outputs and ownership

Economy module owns Economy(st), Gather, FindDeposit, Infrastructure, AgeUp,
MaintainConstruction and Repair; may keep wrappers for compatibility. Economy
calls housing/villager funding before discretionary spending, sets saving_age,
st.resource_counts actual assigned workers, st.trade_market_id when built,
st.trade_build_needed, st.mining_target, and counts archers ever trained using
st.archers_trained maintained root Snapshot. It may inspect st.contacts and
st.enemy_home supplied by Observe. st.castle_time initialized once in controller
via World_GetRand(720,840). Landmark names use existing catalog; resolve actual
mosque/Keep/Fez identities from source before hardcoding. Pending jobs count
toward requested buildings. No old direct resource grants.

Military module owns Observe(st), Army(st), SpecialUnits(st), VillagerSafety(st),
SiegeNeeds(st), navigation SafePoint/SafeMove. Observe populates contacts with
{entity,id,owner,name,pos,building,cavalry,heavy,economic,melee_infantry,ranged,
spearman,knight,scout,tc,keep,outpost,value}; objectives/relic/site/trade records,
st.enemy_player/home/stats for nearest enemy, st.threat_count/buildings,
st.observed_cavalry/heavy, st.enemy_knights, st.defense. Use actual resource costs
for military value. Set st.siege_targets={springald,mangonel,ram,treb,cannon};
st.needs_healer boolean; st.trade_blocked, st.trade_threat_value. st.trade_target
is nearest viable allied market/neutral post (not own military market).
SpecialUnits manages 1 scout (180s returns), traders with dedicated home market,
one relic Imam + one site Imam + one additional healer. Roles use stable IDs.

Production owns SelectAlliance, Research, Produce. Uses st.saving_age,
resource_counts, archers_trained, trade_market_id, siege_targets and needs_healer.
Villager funding occurs in Economy. All combat profiles Zenata. Research normal
core veterancy, economic thresholds and Blacksmith rules; RNG World_GetRand only
after stable candidate sorting. Feudal ram construction must use archer squads
and normal siege-engineering requirement, requesting an engine Construct with
options.role='archer'. No custom spawning.

Controller order: Snapshot -> Observe -> MaintainConstruction -> VillagerSafety
-> Economy -> Produce -> Army -> SpecialUnits -> IncomeAssistance. Root ensures
steady restore-safe interval and no local-player simulation authority.

## Verification

Python: C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe, use -B.
Lua5.1 via lupa.lua51 is installed. Each worker owns tests/test_<domain>.py;
write failing behavior tests before module changes, record red/green evidence.
Shared runtime research/berber0110/test_runtime.lua is root-owned; legacy
research/berber0100/sim_engine.lua is read-only. Tests may create local isolated
Lua stubs until shared runtime integration. Verify all new API names against
installed E:/Games/steamapps/common/Age of Empires IV/scardocs/api and official
C:/Users/RS/AppData/Local/Garrison/Kit/scar-library/scripts or AoE4 MCP. Do not
invent engine helper signatures. Report unknowns immediately to root.

Write task outcome/API evidence/test commands and counts to reports/<domain>.md.
Return concise summary and concerns. Do not create commits, packages, imported
client changes or game changes. Other workers are concurrently using the same
workspace but disjoint owned files.
