# Berber 1.0.4 - native AI candidate

Import Berber-1.0.4.zip into Garrison, enable the update, select the Berber tuning pack and game mode, and start a fresh match. The package is self-contained for the existing Garrison voice/music route.

Native AI controls computer players from match initialization. The custom scripted controller is no longer imported, so its commands, watchdog, resource grants and difficulty override do not run. Existing native difficulty settings apply. Legacy AI files remain inactive rollback sources.

Adds native mappings for Berber units, research, relocated landmarks, Tribal Tent construction and placement, alliance abilities and defensive combat abilities. Villagers, scouts, traders, naval units and siege use the corresponding official production categories. Passive abilities and alliance-granted technologies do not become separate research requests. AI alliance selection stops once an alliance upgrade is present; human requirements and switching behavior are unchanged.

This release is composed onto final 1.0.3. Only the game-mode controller import changes among existing members; seven compiled AI tuning records are added. Existing art, voices, music, 22 UV repairs and player-facing gameplay tuning remain byte-identical.

Source checks, Content Editor cooking, compiled readback and archive/package verification are separate from native gameplay acceptance. You will perform import and native-match tests. Successful native economy, age advancement, alliance selection, combat abilities, save/load, Nomad and multiplayer remain unverified until tested in game. Keep 1.0.3 as rollback.
