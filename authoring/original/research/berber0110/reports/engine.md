# 0.11.0 engine/controller outcome

Implemented only the assigned research sources: engine, controller, policy,
test_engine.py and test_runtime.lua. No promotion, package, game changes or Git
commit. Execution follows the approved spec and Task 1; ordinary native commands
retain cost/prerequisite enforcement.

## Behavior and contracts

- All profiles use Zenata, one scout, one-second ticks; workers 60/75/90/105,
  traders 10/20/30/40, conditional gathering bonus .1/.2/.3/.5.
- Shared full-map cache refreshes once a second. Player/world entity and squad
  enumeration uses matching spawned-only count/getter pairs. Invalid/dead handles
  are rejected before blueprint/position reads and stable IDs sort snapshots.
  Borrowed player groups are retained; owned temporary command/scan groups are
  destroyed. World ownership remains guarded by Observe and FindDeposit; the
  combined controller fixture includes world-owned deposits and strict owner reads.
- Snapshot includes living, queued and unobserved pending unit counts; research
  pending records remain research. Population uses actual current capacity minus
  living, queue and pending population costs. Villagers can fill the last two
  slots and train only from actual TCs. Producer filters honor exact building IDs
  and exclusions; one pending command prevents repeated unobserved requests.
- Construction filters builders by resource, explicit IDs or archer role, stable
  distance/ID order, held/reserved status and existing jobs. It requires the
  requested number. Placement honors actual maximum radius, exact-anchor first,
  minimum trade-target distance and complete Tent/landmark influence within 20 m.
  Construct returns bool,job; last_construct_failure distinguishes placement,
  workers, requirements, cost, savings, pending and command_limit failures.
- Pending foundations match within 10 m, exclude previously existing IDs and
  cannot claim the same observed entity twice. Pending jobs reserve builders for
  up to 12 s; observed foundations retain reservations until completion/death.
  Previous resource roles restore then, including economy-adopted foundations
  whose ID was initially only the construction_jobs map key. Dedicated trade
  foundation recognition sets trade_market_id. Squad-owned constructed siege
  foundations are observed via their first entity as well.
- Normal entity-target orders deduplicate per squad, command and target with a
  bounded refresh. Changed moves/targets and explicitly queued commands remain
  observable. This prevents one-second resets of normal gathering/trade/build
  actions; native command timing/path behavior still needs acceptance.
- Controller order is Snapshot, Observe, MaintainConstruction, VillagerSafety,
  Economy, Produce, Army, SpecialUnits, IncomeAssistance. No recovery grants,
  adaptive alliance/composition policy or autonomous wonder-building remains.
- Castle time draws World_GetRand(720,840) once at initialization and is preserved
  by restore. Restore replaces only the named interval rule, preserves strategy,
  pending state and existing modifier handles, and clears ephemeral world/orders.
  Defeat/game-over removes owned gathering modifiers and clears active jobs.
- Every 60 s, the adapter sums all four documented Player_GetResourceRate values
  multiplied by 60 and compares the highest living hostile player. A reversible
  villager-blueprint multiplier enables only while behind and never reapplies
  while active. Equal income/no living enemies removes it. The source explicitly
  records native all-source coverage as unverified; no net-bank proxy is used.
- BuyStone uses the genuine core_market_buy_stone Market ability with
  LocalCommand_EntityAbility(false,false). It reserves all remaining spare gold,
  keeps one three-second pending request, observes a real stone increase and
  otherwise permits temporary-miner fallback with a 30-second retry cooldown.
  true means request pending or increase observed, not a verified completed
  transaction. Amount, dynamic price, fees and controller-context success remain
  native acceptance gates. Ability static cost zero is never treated as its
  exchange price. See catalog-market-findings.md for root-supplied provenance.

## Official API/source evidence

Installed official API root:
E:/Games/steamapps/common/Age of Empires IV/scardocs/api/Essence_ScarFunctions.api.

- Lines 585/602: EGroup_CountSpawned / EGroup_GetSpawnedEntityAt.
- Lines 1434/1448: SGroup_CountSpawned / SGroup_GetSpawnedSquadAt.
  Official scar/game_modifiers.scar:315-316 uses the one-based spawned loop;
  scar/core_objectives.scar:1223-1225 uses spawned entity/squad index 1.
- Lines 760/1652: Entity_IsValid / Squad_IsValid accept stable integer IDs.
- Lines 1284/1305: Player_GetEntities excludes squad entities; Player_GetSquads
  returns a SquadGroupObs. Line 1552: Squad_GetFirstEntity supplies first member.
- Lines 578/1397: EBP_PopulationCost / SBP_GetFirstEBP. Official
  scar/gameplay/chatcheats.scar:289-294 uses that exact combination.
- Lines 673-675: production queue item blueprint/type/size, zero-based indices.
- Lines 1010/1011/1035: normal LocalCommand entity ability, squad training and
  squad construction signatures. Line 1266: placement legality check.
- Lines 1300/1948: resource rate is per second; World_GetRand is inclusive.
- Line 1188: Modifier_ApplyToPlayer duration zero is indefinite.
- Official Garrison Kit scar/gameplay/chatcheats.scar:526-529 applies the four
  resource_entity_harvest_rate_* modifiers to an entity blueprint using
  MAT_EntityType and MUT_Multiplication. Only the Berber villager blueprint is
  targeted here. Official scar/modifiers.scar:108 defines reversible
  Modifier_Remove; engine explicitly imports modifiers.scar.
- BuyStone provenance: reports/catalog-market-findings.md, editable Market
  ability_ext and root-extracted official ability/state-tree evidence. No quote
  getter or fixed exchange amount is inferred.

## Verification

Tests were written before implementation. The first red run rejected baseline
Snapshot's mixed EGroup_Count path in all 18 initial engine cases. After spawned
snapshots, remaining red assertions exposed old profiles, population behavior,
construction/restore state, RNG and callback order. Additional red-green rounds
covered complete-building pending counts, exact builder counts, pending research,
non-building/squad-owned siege foundations, command-limit reason, market requests,
and adopted-foundation worker restoration.

Final command:

    C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B -m unittest discover -s research/berber0110/tests

Result: 138 tests passed, including 33 engine cases. Independent module tests
also pass; shared runtime has strict mixed-group getter failures, invalid reads,
world-owner errors, documented ability/upgrade command argument checks and
reversible modifier handles. One combined eight-player, seven-Berber-controller
run of 181 startup/control-flow ticks passed. It uses intentionally simplified
path/command/cost fixtures and proves no gameplay or native engine behavior.

validate_scar.py: controller and policy clean. Engine: zero errors, two investigated
warnings: job.options is a construction-options object, not lobby setup; fn is
the explicit callback parameter to WithSquads/WithEntity. MCP check_code for all
three: status ok, missing locdb none. Unknown calls are project/local functions,
Lua keywords or comment-token false positives. Engine low-confidence entries
Entity_CalcConstructionPlacement, LocalCommand_EntityBuildSquad,
Player_GetResourceRate and World_PosInBounds all exist in installed official API;
controller AI_GetDifficulty/AI_IsAIPlayer likewise. MCP usage-index sparsity is
not evidence of a missing documented API.

Required separate gates: current-source root integration/review and package
validation; native normal command legality/costs, rejected-command behavior,
market amount/fees/payment, all-source income coverage, pathfinding, save/load,
multiple AI/player arrangements, deaths, another-match lifecycle and performance.
