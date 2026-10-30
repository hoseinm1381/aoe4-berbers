BERBER DYNASTY 1.0.2 — fresh-match candidate

Fixes the reported startup error: AISquad_HasPathWithinDistance expected
AISquad*, received a normal SCAR squad table. Both scout/military navigation
and villager garrison selection now use a shared typed adapter. It resolves
native AI squad handles from the player and squad ID, verifies their type and
validity, and never passes a normal squad table to AISquad-only APIs.

With native AI disabled, a squad may have no AI wrapper. In that case the
controller retains its geometric threat checks and lets normal move/garrison
commands perform terrain pathfinding. This fallback does not prove that a
route is passable. A wrong-type lookup result is rejected conservatively.

All 34 packaged SCAR files were inventoried, compiled and checked with AoE4
MCP. All external call names/signatures, project definitions and imports have
an evidence index. MCP unknown-name output includes local helpers, dynamic
Garrison methods and comments; the lexical audit resolves them separately.
Several native APIs lack official usage examples, including the AI handle
lookup and path query. Documentation and mocks cannot establish runtime proof.

Only navigation and military SCAR members changed from final 1.0.1. The other
8,520 members are identical, including models, all 22 UV repairs, textures,
voices, tuning, soundtrack, 25% default music, Original/Berber toggle and
individual trader progression (+0.08 m/s per 30 seconds of each trader's life).

Close AoE4, import Berber-1.0.2.zip through normal Garrison, enable and Play.
Select Berber Game Mode AND Tuning Pack; choose Malians for Berber. Start a
FRESH match with the same AI mix as the supplied screenshot. Keep 1.0.1 as
rollback. Existing saves do not qualify this changed controller.

Native acceptance remains pending: verify startup beyond 00:02, scout movement,
villager shelter and exit, troops navigating blocked terrain, every difficulty,
multiple Berber AIs, other civilizations' native AI, Nomad, teams/FFA,
save/restore and multiplayer synchronization/performance. Check music controls
and individual trader cohorts as inherited regression cases.

236 Lua/mock regression tests and deterministic mock simulation are offline
evidence only. Archive/ZIP checks are packaging evidence. No fresh native match
or physical UI acceptance is claimed by this delivery.
