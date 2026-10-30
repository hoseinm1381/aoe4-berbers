# Berber 0.10.0 implementation ledger

Approved spec: user's 2026-10-18 implementation request in this chat.

Build a deterministic SCAR controller for Berber computers only, replacing native
AI while keeping normal costs, fog, human mechanics and all 0.9.1 art/audio.
Connected land maps; classic/Nomad; teams/FFA; restore and cleanup.

Profiles: Easy Sanhaja + Tuareg (60 workers/8s); Intermediate Zenata + archers
2:1 (80/5s); Hard Masmuda + Mehari 1:1 with two scouts/upgrades (100/3s);
Hardest/other adaptive (110/2s). Recovery: non-Easy only, missing economic
resources up to 100 total/180s after 60s sustained stall; no lifetime cap.

Tasks: baseline/API evidence; red controller tests; implement economy,
production/alliance/scouting/military; green tests/static/MCP/review; compose
0.10.0 onto final 0.9.1; verify all preserved bytes; package; scoped cleanup.

Ruling: isolate release authoring in output/berber_update_0_10_0/work rather
than clone an unrelated Git HEAD. The current checkout contains user changes
and the actual release baseline is a retained SGA; it must never be replaced
by an old project cook. New editable SCAR modules remain in assets/scar/ai.

Ruling: no native control surface is available in the AoE4 MCP (reference and
validation tools only). Native command, lobby, sync and performance probes are
mandatory pending acceptance gates; ship explicitly as a candidate, with a
reproducible probe/checklist and log instrumentation, never a runtime pass.

Initial state: no implementation changes. 0.9.1 SGA SHA256
76bc149faf0a82214806d002a2d91dc6df07461e583a8da74b6a16caeb4b7d14.

Evidence: local installed-game Garrison SCAR library built
2026-10-17T17:42:36Z; official command.scar, core.scar, AI scoring, ScarDoc.
MCP doctor ready; older sanitized index is supplemental to installed sources.

Implementation: seven new AI modules; existing game-mode adds one import.
Packaged main mode is patched from091, retaining its newer speech/guards.
Shared alliance callback removes its second gold debit after normal ability
payment, preserving the intended free-first/100-gold-switch rule.

Review: fresh reviewer found sparse inherited requirement polarity, farm scaling
and stale Imperial savings. Resolved by read-only native RGD inspection,
three-valued engine predicates, farm capacity/continued construction, and
per-tick/age reservation reset. Regression tests cover all three findings.

Validation:32 Lua5.1 tests green, including abstract eight-slot normal/Nomad
30-minute runs, Feudal troop eligibility, two army compositions, FOW filtering,
official special_beacon sites, restore/cleanup, placements, reservations, farms,
alliance cost and recovery limits. All96 external engine/wrapper contracts have
exact installed official evidence. Source static/tuning checks0errors; inherited
source warnings retained. MCP parser unknowns resolve to local functions,
callback parameters/keywords;8 low-confidence indexed APIs retain native gates.

Follow-up review: adaptive Market queues could perpetually refill and block
switches. Confirmed alternative alliances now drain old recruitment and reserve
100 gold before switching. Added a continuously occupied queue regression.

Native feasibility, import, lobby values, real commands/costs/pathfinding/combat,
balance, sync, restore and performance: PENDING. No native proof is claimed.

Final resource regression: scout-discovered deposits outside the home scan are remembered under normal fog and used for gathering/drop-offs. Failed site searches are bounded; influence production remains within20 units. All8373 final archive members were decoded and SHA256 compared without retaining another art readback.
