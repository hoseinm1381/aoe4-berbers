# Native market buy/sell SCAR path

Read-only research; no SCAR authoring, gameplay, UI or game files changed for this follow-up.

There is a genuine existing market ability dispatch route:

```lua
local ability=BP_GetAbilityBlueprint("core_market_buy_stone")
BerberAI.WithEntity(market,function(eg)
    LocalCommand_EntityAbility(st.player,eg,ability,false,false)
end)
```

The two false parameters mean **do not skip native cost/prerequisites**, and **do not queue**. This is an ordinary native ability invocation; it adds no resource grants or manual exchange. The corresponding sell ability is `core_market_sell_stone`.

## Evidence

- Installed official API `Essence_ScarFunctions.api:1010` documents `LocalCommand_EntityAbility(PlayerID,EGroupID,ScarAbilityPBG,Boolean skipCostAndPrereq,Boolean queued)`; line426 documents `BP_GetAbilityBlueprint(String)`.
- Official `scar/command.scar` defines `Cmd_Ability` at1226. Its untargeted EGroup branch at1344 delegates to exactly this native command with the same arguments.
- Existing editable Berber Market `assets/attrib/instances/ebps/races/malian/buildings/building_econ_market_mal.xml:41` includes `abilities/timed_abilities/civ_core/core_market_buy_stone` in ability_ext. Line38 includes the normal sell-stone ability. Thus this is a real capability of the project's normal Market.
- Current official Attrib.sga contains `attrib/abilities/timed_abilities/civ_core/core_market_buy_stone.rgd` and `core_market_sell_stone.rgd`. Native extraction and decode are retained under `catalog-market`.
- Buy-stone decoded `default/ability_bag/entity_tree` equals `core_market_buy_stone\buy_stone_1`; sell-stone equals `core_market_sell_stone\sell_stone_1`. Both have ordinary construction-state/landmark-active/native civilization restrictions, not a custom SCAR exchange.
- Current official Data.sga `statetrees/simulation/statetree.bin` contains genuine `core_market_buy_stone`, `buy_stone_1`, `deferred_buy_stone` and `Buy_Failed` identifiers. Plain strings establish matching compiled tree presence, **not its internal control flow or exact amounts**.
- Exact Buy/Sell/Market/Exchange search across installed Essence_ScarFunctions API finds only market debug rendering helpers, no dedicated transaction/quote function. Official SCAR source search found no market-buy example or exposed quote adapter. MCP exact base-data lookup found no indexed ability record, so native compiled data supplies the blueprint evidence.

## Price and amount limitation

The native ability's `cost_to_player` is all zero, including gold. Therefore **Player_GetAbilityBPCost is not evidence of the native market transaction quote** and must not be used to claim a zero-price stone purchase. Its actual exchange is delegated to the native ability's compiled state tree. No supported SCAR getter for the current dynamic market quote/fee was found. No verified standalone state-model key for that quote was found; do not invent one.

The normal singular buy-stone ability is the supported native candidate for the normal purchase action. The exact100-stone exchange amount, dynamic price and fees are not visible in the decoded ability bag and were not independently decoded from the compiled state tree. They require a native acceptance check. This research does **not** establish that a command successfully completes or that the native engine accepts it from this controller context.

If root uses the candidate path, an honest conservative spending adapter can isolate one request: reserve all available spare gold for this native attempt, block other new gold spending that tick, and observe the real gold/stone result on the next snapshot with a bounded retry. The native ability remains responsible for payment and rejection. This avoids inventing a quote, but remains a candidate until native validation; its function must not report a completed purchase merely because the void command was dispatched. If the required interface demands a confirmed legal quote/payment before dispatch, the currently established API surface is insufficient and `BuyStone` should report unavailable so economy temporarily mines.

No `Player_SetResource`, free grant, hardcoded price, invented command or undocumented quote key is authorized by this evidence.

Scratch: `catalog-market/simulation-statetree.bin` is a45,493,176-byte regenerable decoded member from current official Data.sga. Its retained compact provenance is in `catalog-market-provenance.json`. Root can remove this temporary raw member after integration review; retain the small report, ability provenance and existing pinned game archives.
