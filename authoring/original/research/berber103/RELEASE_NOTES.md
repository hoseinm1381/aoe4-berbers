# Berber 1.0.3 - economy recovery candidate

Install Berber-1.0.3.zip in Garrison and start a fresh match.

Living animal food deposits use squad-target gathering commands. Valid resource-bearing corpses remain discoverable and use an exact native-enumerated entity target group, avoiding direct insertion of squad-owned animals.

Every Berber scripted computer has an independent watchdog. No active food/wood/gold/stone gatherers for more than 15 continuous simulation seconds transfers control permanently to the native AI (normally on the next one-second tick). Active gathering resets the timer. Stockpile changes, spending, passive income and reported resource rate do not mask a stall. All-workers building, traveling or garrisoned for this period also triggers fallback intentionally. It does not detect a partial economy stall while any gathering continues.

The script stops its economy, production, military and assistance commands after handoff, removes its income modifiers and preserves handoff across restore. Native AI uses the existing difficulty; Hardest and higher are capped to ordinary Hardest without higher native cheat bonuses. Other civilizations and human players are untouched. Existing native queues and buildings are retained. Fallback means native AI behavior; custom build order/alliance/unique-unit support is no longer guaranteed for that player.

Look in warnings.log for: native_fallback=enabled reason=no_active_gatherers idle_seconds=...

This patch is composed onto final1.0.2. Only engine/economy/controller SCAR members change. Music25percent/Original toggle, per-trader progression, voices, all art and22UV repairs remain byte-identical.

Offline regression, Lua syntax, static/MCP and archive/ZIP checks do not prove native acceptance. Test opening sheep gathering and killed sheep, exhaust food, force all gatherers idle for16seconds and confirm native takeover; then save/load. Multiplayer synchronization and whether the native AI can successfully run this custom civilization still require native testing. The previous log established initialization and an economy stall, but did not identify an exact rejected native command.
