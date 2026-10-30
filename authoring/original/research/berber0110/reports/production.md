# Berber 0.11.0 production/research task

Authoring namespace only; no promotion, packaging, commits, game execution or client edits.

## Behavior

- Every profile selects only Zenata via its existing paid ability, confirms the real upgrade, and bounds rejected-order retries to 15 seconds.
- A saving-age pause blocks every production/research/alliance/build command. Villager funding remains the economy owner's responsibility.
- All affordable military producers receive orders, using a soft two-archer-per-Lancer preference and affordable-role fallback. The dedicated trade Market is excluded from combat training; trader target uses living/queued/pending counts and the difficulty target.
- Castle/Imperial archer and Lancer upgrades receive highest research priority and can begin on separate producers in one tick. Monastery construction/religious training waits until these upgrades are owned or queued. Maintain two religious Imams and one additional healer only on demand.
- Final review identified a real starvation defect: constantly replenished paid military queues prevented queue-empty research forever. Production now retains a chosen research drain per producer, stops its new ordinary training through the shared producer_used reservation, protects affordable upgrade funding in the tick budget, preserves every existing paid queue, and starts the upgrade when the queue drains. It clears stale/owned/queued/invalid demands and deduplicates each chosen upgrade across producers. Saving pauses preserve the plan and dispatch nothing.
- Economic resource harvest tiers use 8/15/22 actual assigned workers and catalog age/prerequisite restrictions. Wheelbarrow is eligible immediately through an existing mill, including a legal Dark Age opportunity.
- At six archers ever trained, request one Blacksmith including pending foundations; Feudal prioritizes +1 ranged attack. Later affordable Blacksmith candidates are sorted by upgrade name and stable building ID before simulation RNG draws.
- Normal siege producer construction/training follows military siege demand and normal engine prerequisites. Feudal ram demand requests Siege Engineering; only after its real upgrade is owned does production ask the engine for an archer-built `unit_ram_3_mal`, with pending construction counted toward demand.

## TDD and verification

Python: `C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe`; actual Lua 5.1 through `lupa.lua51`.

Initial legacy run after loading its real policy dependency: 20 tests, 17 failures/errors. The failures exposed missing new policy, saving pause, thresholds, producer separation, random research and the invalid-producer read. One unsupported old-alliance fixture was also present; that path disappears in the Zenata-only implementation. One accumulating trader-test counter was corrected after the first implementation; the test now checks each difficulty independently.

The later exact-official-ram-name regression failed before changing the old `_2` name and passed after switching to verified `_3`.

Commands:

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B -m unittest discover -s research/berber0110/tests -p test_production.py
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B -m unittest discover -s research/berber0110/tests
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B 'C:/Users/RS/.codex/skills/aoe4-game-mode-skill/scripts/validate_scar.py' research/berber0110/ai/berber_ai_production.scar --project-root research/berber0110
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B 'C:/Users/RS/.codex/skills/aoe4-game-mode-skill/scripts/self_test.py'
```

Focused result: **25 passed** after additional red/green regressions for idle-healer religious replacement, real mining-tech eligibility for stone workers, eight-wood-worker Forestry eligibility, and busy-core-producer research starvation. The busy-queue regression first failed with `needed upgrade producers must drain`, then passed across three ticks proving paid queues preserved, no replenishment, protected research funding, both core upgrades queued and monastery unlocked. Military retains a living healer role even after wounds heal; production includes that living assigned healer in its target instead of withholding a replacement religious Imam. The gold-named native mining technology becomes eligible when either gold or stone reaches its tier threshold, preserving the actual producer list. Static validator: **zero errors, zero warnings**. Skill smoke self-test passed. Full concurrent authoring-suite results are reported separately to root because other workers are still adding tests. No Content Editor/package/native game result is claimed.

## Evidence ledger

Official/API: installed `E:/Games/steamapps/common/Age of Empires IV/scardocs/api/Essence_ScarFunctions.api`:

| Symbol | Line | Contract used |
|---|---:|---|
| BP_GetAbilityBlueprint | 426 | ability short name to PBG |
| BP_GetUpgradeBlueprint | 477 | upgrade short name to PBG |
| Entity_GetProductionQueueSize | 675 | current queue item count |
| Entity_HasProductionQueue | 712 | production queue presence |
| Entity_IsProductionQueueAvailable | 747 | queue available |
| LocalCommand_EntityAbility | 1010 | player, group, ability, skipCostAndPrereq=false, queued=false |
| LocalCommand_EntityUpgrade | 1021 | player, group, upgrade, instant=false, queued=false |
| Player_GetAbilityBPCost | 1278 | player-modified actual ability cost |
| Player_HasUpgrade | 1335 | player upgrade ownership |
| World_GetRand | 1948 | inclusive synchronized integer range |

Official usage: `C:/Users/RS/AppData/Local/Garrison/Kit/scar-library/scripts/scar/command.scar` defines `Cmd_Upgrade` at 1167 and delegates to the exact entity-upgrade command in its EGroup branch; `Cmd_Ability` at 1226 delegates to the exact untargeted entity-ability command in its EGroup branch. Production calls these official low-level commands directly, so it adds no wrapper import dependency. Official `scar/autotest.scar:60,64` and `scar/ai/army.scar:878` select an index with `World_GetRand(1,#candidates)`.

Project definitions/imports: shared engine `EntityValid`, `WithEntity`, `Cost`, `Spend`, `Require`, `CountBuilding`, `FirstBuilding`, `Construct`, `Train`; controller imports engine before production. Research writes producer reservations, queued-upgrade names and `production_pending[id]={name,upgrade=true,until_time}`. Engine owner confirmed its Snapshot preserves these until queue/ownership observation with bounded retry.

Blueprint evidence: targeted native decoding is now complete in `catalog-findings.md`, `catalog-mapping.json`, `catalog-provenance.json`, with a reproducible read-only script. It verifies actual camp lists, archer ram capability and ram EBPS engineering prerequisite. It also corrects the older decoder's upgrade requirement root from nonexistent requirement_ext to actual upgrade_bag/requirements. The real mining camp exposes gold-named mining technologies only; separate stone PBGs must not be fabricated into its producer list. Root owns catalog integration.

MCP result: `doctor` ready; project layout inspected; final `check_code` returns no missing locdb IDs. Its 21 unknown-call entries are six exact local helper definitions, shared `BerberAI.*` methods, standard `string.match`, and tokens parsed from the harvest-name pattern/string. No unresolved engine API names. `Player_GetAbilityBPCost` is flagged low usage confidence (no indexed usage) but its exact signature and actual modified-cost return description are present in current official API at line1278. No stronger usage claim is made.

Unofficial evidence: none used as an engine contract. Unresolved contracts: root must integrate the verified inherited catalog mappings and confirm its Construct supports engineer-built ram foundations before integration acceptance. Income source-coverage research is separately documented as unresolved in catalog-findings.md.

Cleanup/multiplayer: this module creates no groups, rules, modifiers or listeners; shared wrappers own temporary group lifetimes. It uses shared simulation state, stable sorting and `World_GetRand`, with no local-player state/OS RNG. Pending/retry fields persist in player state and do not redraw on restore.

Runtime scenarios still required: normal paid ability/upgrade command acceptance, queue observation/rejected-command recovery, simultaneous research and military spending, actual unit build capability of archers, ram completion counting, trader producer identity across restore, population/age prerequisites, and deterministic multiplayer/save-load behavior. Policy mocks do not prove these.
