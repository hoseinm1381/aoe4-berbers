# Rebuild Berber 0.10.1

Use Python 3.13 with lupa.lua51 and the installed Garrison archiver. Run from
the project root with `python -B`, using the verified interpreter recorded in
the validation reports. Retain the final 0.10.0 SGA and ZIP; their hashes are
pinned in pipeline.py/release.py. Never use a raw Content Editor cook as the
baseline: the packaged art, voices and newer game-mode scripts must survive.

1. `research/berber0101/pipeline.py prepare`
2. `research/berber0101/pipeline.py stage`
3. `research/berber0101/checks.py`
4. Run AoE4 MCP check_code on both complete edited SCAR files and review the
   results into output/berber_update_0_10_1/mcp-check.json. Both owner APIs have
   official documentation. Existing local methods and Lua keyword/comment
   false positives must be distinguished from unresolved engine calls.
5. `research/berber0101/pipeline.py compose`
6. `research/berber0101/release.py`
7. `research/berber0101/cleanup.py`

Existing final SGA/ZIP outputs are protected against overwrite. Reproduce in a
fresh output directory by updating OUT and cleanup's EXPECTED physical path.
The recipe replaces exactly military/economy SCAR; it proves all other 8,371
decoded member hashes identical to 0.10.0. No Blender or tuning edit/cook is
required. Work consists of regenerable baseline SCAR extracts/payload/member
lists, and is deleted after verified packaging. Source recipes, tests, reports,
baseline/final SGA/ZIP, art/audio/Blender inputs and rollbacks remain retained.

The strict owner mock reproduces the native failure instead of silently
returning nil. Run test_ownership.py for the focused regression; checks.py
runs it together with the existing 32 AI tests and static/tuning validators.
Test fixtures are not a native engine, multiplayer or performance test.

Native retest: import 0.10.1 personally in Garrison; select Berber Game Mode
and Tuning Pack; start a match with Berber AI on the failing map. Verify the
opening passes the former two-second failure and workers gather each resource.
Finish another match and start Berber again without restarting the process.
Check no ownership fatal errors recur. Save/load and multiplayer remain pending.
