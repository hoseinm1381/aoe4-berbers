# Berber1.0.1 patch reproduction

Base: exact final1.0.0 SGA/ZIP under output/berber_update_1_0_0, pinned in
build.py. Never substitute a raw Content Editor cook or stale editable GM.
Only three existing SCAR members change: AI military observation, trader speed,
and local music controls. All art, 22 UV repairs, voices, tuning and145 music
files remain byte-identical. No audio encoding, art cook or paid generation.

Authoritative patch sources are ai/berber_ai_military.scar,
saharan_trader.scar and music/berber_music.scar. Other ai/music modules are frozen
context for tests. baseline-source/ preserves the exact three previous files.
Promoted editable military/trader/music sources are in assets/scar; the frozen
package route remains authoritative because the editable GM has earlier drift.

Use verified Python3.13, LupaLua51/Lua53 and Garrison's native SGA archiver.
Run checks.py, build.py checks, and MCP check_code for the three changed files.
Then build.py build composes the three files on the pinned1.0.0, reads/hashes
every decoded member, checks exactly those three changed and none added/lost,
verifies native archiveCRC/SHA1, and packages exactly one manifest with the
inherited mod identity and cover. It refuses to overwrite existing releases.
For reproduction, use a new output directory/version and update the explicit
cleanup guard first. build.py verify is read-only; cleanup follows verification.

Trader progression is per living Berber trade_cart entity, discovered within
one simulation second. Every completed30seconds after first discovery adds
0.08m/s, without a cap. One replacement modifier stores the current cumulative
total; saved global state prevents duplicate restore grants. Conversion away
removes this module's modifiers; a newly converted Berber trader starts fresh.
Engine-owned player observer groups are never filtered or destroyed.

Military value uses the actual squad's player-qualified cost, matching official
score.scar. Decorative/marker entities without a valid squad cost zero. Squad
value is independent of current health and counted once per observation.
No EntityBPCost query is made for arbitrary observed entities.

Music defaults to25percent. The top-right Original button stops only the custom
bed and restores native music through official force-silence/music controls.
The button becomes Berber while native music is selected. Native volume uses
the normal game sliders; custom gain is retained. Returning to Berber starts a
legal random entry without replaying the opening. Speech retains session and
heartbeat ownership. Save/restore preserves explicit native selection.

Native acceptance requires a fresh match: reproduce the supplied multi-AI
opening; observe trader cohorts for5minutes (no age/movement bonuses confounding
the displayed stat); test late traders, death, conversion, save/load and pause;
toggle Original/Berber music, adjust volume, age up and trigger combat; verify
speech and audio sliders. Package/static/mock proof is not native acceptance.
