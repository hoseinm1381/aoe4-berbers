# Berber 0.11.0 military/navigation authoring evidence

Implemented only `ai/berber_ai_military.scar`, `ai/berber_ai_navigation.scar`, `tests/test_military.py` and this report under `research/berber0110`. No promotion, commit, package, installation or game run was performed by this worker.

## Behavior and integration

`Observe` reads the full shared spawned/validated world list without a fog gate. It guards every owner read with `World_OwnsEntity`, drops stale/destroyed contacts, selects the nearest living hostile base with stable player-ID ties, and computes resource-cost army values from each living military entity's unmodified blueprint cost. Buildings, economic units and scouts do not inflate combat force value. It exports contacts, objectives/relic/site/sheep/trade candidates, nearest enemy statistics, defense and trade threat fields, healer demand and siege targets.

Raids launch with the first Zenata Lancer. Mixed opposition shares the budget `spears/1.75 + knights + ranged/4 <= Lancers`, and the exact 1.75x spearman boundary is rejected. Exposed favorable alternatives take priority over a guarded nearer worker. Bad encounters produce a halfway-home regroup point. Archers require six for attack departure, follow regrouping Lancers, and have no individual health retreat. Lancers withdraw below 15% and remain near the TC until 80%. Defense retains rounded 30% raiding Lancers and recalls the rest, including siege. Escorts round up whole squads toward 130% of threatening military value and yield to urgent home defense.

Villager safety is independent of saving phases and reserves its squads. It uses 20m heavy cavalry / 12m other combat proximity, ignores scout proximity and proven scout-only hits above or equal to 10%, checks native recent hit provenance, and releases shelter only beyond 22m. Reachable shelters reserve capacity within a tick. Overflow villagers circle the TC while seeking shelter. Unknown hit provenance conservatively shelters; temporary attacker groups use spawned-only iterators and are destroyed.

Navigation uses bounded, deterministic segment/threat geometry and native squad reachability checks. TC exclusion includes the 24m boundary. Detours test one or two shoulders up to 216m from the direct line; failure refuses movement. A unit already inside danger may escape along a monotonically outward leg. There is no randomness or local-player authority. The controller must import navigation before military.

The starting scout chooses the nearest safe unclaimed sheep and returns after each 180-second collection interval. Trade uses only the dedicated market identity supplied by economy/production, selects the nearest allied market or neutral post, uses safe detour movement before trade commands, and moves home or stops when a route cannot be used. Two Imams have stable independent relic/site roles, with a third stable healer assigned only on demand. A relic carrier deposits before fetching another. Unsafe religious objectives are skipped. Siege demands use the nearest enemy's living composition, complete floor ratios, strict >20% melee-infantry share, and a threefold value threshold. Building target selection searches a 36m local band before a 60m band, so a remote Keep does not override a nearby house.

## TDD and validation

Tests were written and run before the corresponding implementation. Initial legacy run: 17 tests, 16 expected missing-behavior/legacy-dependency errors, one existing dead-contact case passing. First implementation: 17/17 pass. Edge batch then caught five failures (unsafe-start escape, home-market order, blocked trade stop, siege recall, archer regroup); fixes produced 26/26. Additional shared-spear-budget and exposed-alternative tests failed before fixes; 28/28 then passed. Light horseman classification regression failed before its correction; 29/29 then passed. A final edge batch caught archer survivor/reinforcement grouping and two missing trade-stop conditions before fixes; 32/32 then passed. A six-unit archer escort regression failed before its fix; final 33/33 pass.

Commands (verified Python 3.13, Lua runtime `lupa.lua51`):

```powershell
& C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B research/berber0110/tests/test_military.py
& C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B -m unittest discover -s research/berber0110/tests -v
& C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B C:/Users/RS/.codex/skills/aoe4-game-mode-skill/scripts/validate_scar.py research/berber0110/ai/berber_ai_military.scar --project-root research/berber0110
& C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B C:/Users/RS/.codex/skills/aoe4-game-mode-skill/scripts/validate_scar.py research/berber0110/ai/berber_ai_navigation.scar --project-root research/berber0110
& C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B C:/Users/RS/.codex/skills/aoe4-game-mode-skill/scripts/self_test.py
```

At the final worker run: focused 33/33; full currently available authoring domain suite 86/86; both SCAR static checks report no diagnostics; skill self-test passed.

## Official/API evidence

Installed API root: `E:/Games/steamapps/common/Age of Empires IV/scardocs/api/Essence_ScarFunctions.api`.

| Contract | Exact installed evidence |
| --- | --- |
| Unmodified living-entity resource value | `BP_GetEntityBPCost(ScarEntityPBG)` line 442 explicitly reads `cost_ext`; official `scar/gameplay/chi/current_dynasty_ui.scar` function `CreateCostData`, lines 246 onward, reads returned `.food/.wood/.gold/.stone`. Retained decoded official spearman EBPS also contains `cost_ext.time_cost.cost` food60 wood20. |
| World-safe ownership | `World_OwnsEntity`, `Entity_GetPlayerOwner`; preexisting 0.10.1 repair retained with strict world-owner mock. |
| Reachability | `AISquad_HasPathWithinDistance(SquadID,Position,Real)` line395 documents boolean existence of a path shorter than the maximum. No official installed usage found; native behavior remains a gate. |
| Shelter slots | `Entity_GetFilledHoldSquadSlots` line656, `Entity_GetMaxHoldSquadSlots` line667. |
| Hits/health | `Squad_GetHealthPercentage(SquadID,Boolean)`1556, `Squad_GetLastAttackers(SquadID,SGroupID,Real)`1565, `Squad_GetLastEntityAttacker(SquadID,EGroupID)`1566, `Squad_IsUnderAttack(SquadID,Real)`1647. Official `scar/groups.scar`3555 uses `Squad_GetLastAttackers`. |
| Spawned-only attack provenance enumeration | `EGroup_ForEachEx`595 and `SGroup_ForEachEx`1443 explicitly distinguish spawned/despawned flags; callback uses true,false and returns false to continue. |
| Garrison/ungarrison/stop | Official `scar/command.scar` definitions `Cmd_Garrison`932, `Cmd_UngarrisonSquad`1043 and `Cmd_Stop`1444. Official `scar/core_unitentry.scar`398,483 and `scar/scarutil.scar`290,1904 show normal garrison commands. No instant/overload garrison. |
| Native contextual entity commands | `LocalCommand_SquadEntity`1051, `SCMD_Attack`, `SCMD_DefaultAction`, `SCMD_Capture`, `SCMD_Trade` in official constants. Standard command routing through project `BerberAI.Target` preserves the existing boundary. |
| Normal trade | Official `scar/missionomatic/missionomatic_utility.scar` `AssignTradecartsToTrade`672-677 uses `LocalCommand_SquadEntity(...,SCMD_Trade,...,false)`. Official `scar/scarutil.scar`629 documents a trader's creator as its home market/dock; production is responsible for the dedicated creator. |
| Relic/site identity | Official `ai/cardinal_objects.scar`83-85 and117 uses `special_beacon` and `relic`; `scar/winconditions/annihilation.scar`111 uses `trade_post`. |
| World/squad positioning and holder state | Exact documented APIs `Squad_GetFirstEntity`1552, `Squad_GetPosition`1572, `Squad_IsHoldingAny`1628, `Squad_IsInHoldEntity`1633, `World_PosInBounds`1974; existing `BerberAI.Pos/Distance/Move` remain engine-owner wrappers. |

Official source root for paths in the table: `C:/Users/RS/AppData/Local/Garrison/Kit/scar-library/scripts`.

MCP `check_code` ran on both complete final modules. Its unknown lists contain project methods, module-local functions and parser tokens (`and/or/not`), all resolved to definitions/imports. There are no unknown engine symbols. It flags documented-low APIs `AISquad_HasPathWithinDistance`, `Squad_GetLastEntityAttacker` and `World_PosInBounds`; each exact installed signature was checked, but no nonexistent usage is claimed. No new API spelling was invented. No locdb references are added. Unofficial source was not used as engine-contract authority.

## Remaining engine gates

Static/mocked behavior does not prove native command acceptance, access to garrison entrances, native paths following the geometrically safe line, sheep following/claiming, trade payload retention when moving around danger, default-action healing/relic pickup/deposit behavior, or Sacred Site capture. Native trade auto-return can choose its own path; safe-waypoint interception and the dedicated producer/creator must be checked in a live match, and are not accepted as proof of an arbitrary engine navigation override. Documented AI reachability on script-controlled AI squads, stale attacker provenance, non-hold-building capacity queries, native target order cadence, multi-AI performance, save/load and multiplayer also require acceptance. Native unit type tags beyond official objective identities rely on the existing type API plus blueprint-name fallbacks; mixed-civilization composition needs in-game coverage.

No Content Editor, package/readback or runtime gate was attempted by this worker, as instructed. Root integration must retain normal native production/costs and the corrected bombard->cannon role catalog mapping, and deduplicate unchanged entity-target commands if its engine boundary requires it.



## Review repair: official relic carry state

The transport `Squad_IsHoldingAny` check was removed after review. Fresh read-only decoding of the installed official Attrib.sga proves pickup requires entity key `is_carrying_entity=false` and deposit requires the same entity key true. The monk entity schema is `monk`. The implementation now calls the documented Entity_GetStateModelBool on a validated Squad_GetFirstEntity, and the regression sets this entity state while leaving vehicle hold false; it also proves vehicle hold true does not imply carrying a relic. API687 and MCP api_context confirm Entity_GetStateModelBool(EntityID,String), with24 official usages.

Compact official member evidence (temporary native decoding inputs/output were automatically removed):

```json
[
  {
    "member": "/attrib/abilities/modal_abilities/core/pickup_relic.rgd",
    "raw_rgd_sha256": "461f3f6cc87d354e25a19b45e6cb95dcec97efcda9ea304a5a28d52149615c47",
    "evidence": [
      {
        "key": "is_carrying_entity",
        "default_value": "false",
        "$REF": "requirements\\required_statemodelbool",
        "data_source_type": "entity_datasource",
        "compare_to_value": "false",
        "reason": "usage"
      }
    ]
  },
  {
    "member": "/attrib/abilities/modal_abilities/core/monk_statetree_deposit_relic.rgd",
    "raw_rgd_sha256": "be09e610005891d970e3a6685fc7e41560708cd4ec7a4bb3b29d74fd53d52c8e",
    "evidence": [
      {
        "key": "is_carrying_entity",
        "default_value": "false",
        "$REF": "requirements\\required_statemodelbool",
        "data_source_type": "entity_datasource",
        "compare_to_value": "true",
        "reason": "usage_and_display"
      }
    ]
  },
  {
    "member": "/attrib/ebps/races/malian/units/unit_monk_3_mal.rgd",
    "raw_rgd_sha256": "8ed3b7d8e72cd5e23239b0973d7a2f125f493512df741dec18b75fcb13586ead",
    "evidence": [
      {
        "statemodel_ext": "<RGDNode Key=\"statemodel_ext\" Type=\"List\">\n      <RGDNode Key=\"$REF\" Type=\"CString\" Value=\"ebpextensions\\statemodel_ext\" />\n      <RGDNode Key=\"schema\" Type=\"List\">\n        <RGDNode Key=\"$PBGNAME\" Type=\"CString\" Value=\"monk\" />\n        <RGDNode Key=\"$PBGMAP\" Type=\"CString\" Value=\"statemodel_schema\" />\n      </RGDNode>\n    </RGDNode>\n    "
      }
    ]
  }
]
```

## Review repairs and final verification

Fresh military review findings were reproduced before changes: archer TC targeting, remote unsupported archer departure, guarded nearest trade endpoint, allied market foundation selection, sheep displacing villagers and boolean cavalry count all failed new behavior assertions. These now pass. Archers rendezvous within16m of a Lancer screen before focusing a target within24m of that screen, remain home without a Lancer raid screen, follow regrouping and filter enemy TC danger both during offense and home defense. Raid selection now uses a separate villager marker instead of the broad economic exclusion flag. Trade candidates are tried in stable distance order and incomplete allied Markets are rejected; only when no viable endpoint exists does the nearest blocked destination request protection. `enemy_knights` is now a numeric count, matching the finalized shared economy contract.

The relic entity-state regression failed while the vehicle-hold implementation remained, then passed after replacing it with the verified entity-datasource key above. No transport-hold claim remains. New Entity_IsUnderConstruction use is the same installed official API already used by the engine snapshot.

Final review-fix verification: military42/42 and the entire currently available authoring suite105/105 pass under Lua5.1; the final military static validator is clean and fresh MCP check reports no unknown engine symbols. Remaining MCP low-confidence documented APIs are unchanged. Native navigation, command acceptance, trade return paths, save/load and multiplayer remain acceptance gates.
