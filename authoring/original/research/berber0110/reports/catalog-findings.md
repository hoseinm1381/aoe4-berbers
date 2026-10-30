# Targeted compiled-data and income research

All game/archive reads were read-only. New files are confined to the approved `reports/catalog-*` namespace. Reproduce with `Python313/python.exe -B research/berber0110/reports/catalog-research.py`. The script selectively extracts/decodes the same records and retains member SHA-256 plus source archive SHA-256. It prefers final0.10.1 records when present and otherwise uses current official records.

## Catalog handoff

`catalog-mapping.json` is the compact machine-readable handoff. `catalog-provenance.json` records 47 native RGD members, including source, archive path, member path, hashes and parsed requirements. Baseline SHA-256 matches pinned final0.10.1 `648a2a0c94de851c6eff8d8a242c2131c6db5394d3a508c8182ed8260bc90718`; official Attrib.sga SHA-256 is `03b8e431c91920535fa65cdae340ee206f31bbdfbb1740feddb4a0430625a977`.

Official and final0.10.1 agree on these lists:

| Building | Native upgrade_ext list |
|---|---|
| building_econ_wood_mal | upgrade_econ_resource_wood_harvest_rate_2, _3, _4; upgrade_econ_resource_wood_fell_rate_1 |
| building_econ_mining_camp_mal | upgrade_econ_resource_gold_harvest_rate_2, _3, _4 |

There are **no separate stone technologies in the real mining camp producer list**. Do not append those technologies to a producer merely because their standalone PBGs exist. The current gold-named tier1 mining upgrade contains `mining_rate=0.15` and `mining_rate_stone=0.15` properties and the action-tree opening branch `common_upgrade_master\mining_harvest_rate_2\normal_modifiers\mining_harvest_rate_2`; this strongly suggests a combined mining technology. Its stone effect has not been traced through the compiled action tree and is not claimed as proven. The data handoff preserves the real producer list.

Ruling: production allows the actual gold-named mining upgrade when either gold or stone reaches the corresponding threshold. This implements the approved resource-workforce trigger without adding a nonexistent native producer entry; native stone-effect coverage remains an explicit acceptance check. The real separate Forestry upgrade `wood_fell_rate_1` uses the eight-wood-worker threshold.

The prior `research/berber0100/catalog.py` requirement decoder selects nonexistent `default/requirement_ext` for upgrade records and consequently emits `true`. Actual upgrade requirements live under `default/upgrade_bag/requirements`. The new read-only script calls the same `rgdreq` predicate parser on `upgrade_bag`, resolving the actual age and previous-tier requirements. Examples:

- Wood/gold tier2 require Castle and prior tier1 (ordinary or improved Mongol variant). Tier3 requires Imperial and prior tier2.
- Ranged Damage II requires Castle and Ranged Damage I (ordinary/improved).
- Veteran archer/Lancer upgrades require Castle. Elite requires Imperial and the respective veteran upgrade.

The compact mapping includes all12 resource harvest PBGs, all12 Blacksmith damage/armor PBGs, core4 upgrades, Wheelbarrow, wood felling, Siege Engineering, ram EBPS and archer squad construction refs. Standalone stone records are included for evidence; they remain absent from the producer list.

## Archer-built ram

Both current official and final0.10.1 compiled data prove:

- EBPS `attrib/ebps/races/malian/units/unit_ram_3_mal.rgd` has `requirement_ext` requiring owned `upgrade_siege_engineers`.
- Its construction_ext links completed `unit_ram_3_mal` as its constructed squad.
- SBPS `attrib/sbps/races/malian/unit_ram_3_mal.rgd` requires Feudal; its `_3` spelling does not impose Castle.
- Archer SBPS `attrib/sbps/races/malian/unit_archer_2_mal.rgd` has squad_engineer_ext containing `unit_ram_3_mal` with `ability_build_battering_ram`; the native normal archer construction capability exists.

Native command acceptance, placement/pathing and completed-squad counting remain integration/runtime gates. This evidence does not prove the root's generic Construct implementation handles an engineer-built unit foundation correctly.

## Player_GetResourceRate source coverage

Official API `Essence_ScarFunctions.api:1300` defines `Player_GetResourceRate(Player& player,Integer type)` as the resources a player is getting per second. Official HTML `scardocs/html/function_list.htm:32813` repeats that description and attributes the binding to engine `runtime/presentation/public/presentation/lua/lualibs/unsorted/LuaPlayer.cpp:471`. That C++ implementation is not present in the installed source used here.

Exact `Player_GetResourceRate`/`GetResourceRate` search across installed official Garrison scar-library scripts found no invocation demonstrating gathering, trade, relic or other passive coverage. AoE4 MCP `find_api` confirms the same signature/description; `find_usage` returns no records. Broader official API/script searches found no verified cumulative all-sources earned-resource counter. `Player_GetResource` is a current-bank API; `Player_GetStateModel*` accepts arbitrary keys and is not proof that an undocumented cumulative-income key exists. ReplayStatViewer's Income template entry is a commented template example; its sample updater uses test data and does not supply a source-complete adapter. Rogue mode's resource counters belong to its own scripted economy and are unsuitable evidence for normal-match earnings.

**Result: source-complete total-income coverage remains unresolved.** Neither trade nor relic coverage can be asserted from the generic rate description. An isolated native matrix should measure gathering only, trade only, relic only and other actual passive sources with identical no-spend time windows, compare the documented API's sampled value against known delivered resources, and repeat with gather assistance active. The no-spend bank observation belongs solely to the validation experiment; production must not infer income from ordinary net bank changes. Do not silently rename a gather-only or unverified rate as total income.

## Scratch disposition

94 extracted RGD/decoded XML files total3,911,814 bytes under `catalog-scratch` after this targeted research. They are regenerable with the retained script and pinned archives. Preserve compact mapping/provenance/findings; root may dispose of this scratch after consuming the data and applying its release cleanup inventory. No release ZIP was created by this worker.
