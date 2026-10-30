# Berbers independent-dropdown pilot

**Superseded by native test evidence:** AoE4 rejected trial.1 with "missing
metadata." See [confirmed failure and trial.2 correction](DROPDOWN_FAILURE_20261030.md).
The original preparation receipt below is retained as history, not native acceptance.

Status 2026-10-30: local **0.1.0-trial.1**, ready for owner import and game test.
Scope: Berbers only. Vietnam, Persia and Korea have not been migrated in this trial.
The owner explicitly accepts the test version's size; release optimization remains
a later gate. No installation, original-project edit, Git commit or push was made.

Playable ZIP: `F:\aoe_4_temp\New_custom_civilization\aoe4-berbers\output\pilot\delivery-final\Berbers-Garrison-0.1.0-trial.1.zip`

- ZIP: **610,755,687 bytes**; SHA-256 `e57ef45926f1589dee9085243cd7fb60aa0f936a89cfbba61ac345c648731626`.
- Native SGA: **769,805,910 bytes**; SHA-256 `129b8deec6a2483b4682acc10c1207e08c21fca6f15db4801960f9579e888ce5`.
- Reduction from original 1.0.5 ZIP: **74,316,588 bytes**.
- Bundle/member key `berbers`, role/content type `civilization`, minimum Garrison 0.1.9.
- Owner UUID `5fe8767c-ca3a-4e64-9e20-c9527cf014ec`;
  native race `5fe8767cca3a4e649e20c9527cf014ec:berbers`. Never substitute the original Berber owner.

Read [START-HERE.md](../START-HERE.md) before testing. Use a human Berber player,
Standard, Tuning Pack=None, a fresh Dark Age match and a stock opponent. Restart
the game through Garrison after enabling. Do not select the old Berber game mode.

## What was converted

The immutable composed Berber 1.0.5 resources were selected, rather than assuming
a raw editable cook would reproduce final UV/speech fixes. Its SGA is the retained
1.0.4 final archive at `F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\berber_update_1_0_4\Berber_future_kingdom.sga`; SHA-256 was freshly checked as
`55629909581fd0035a141f212e38274d3e1f7f185fecffed635b821e2b7204a6`.
The original E: project, F: source-blobs, art/audio masters and previous packages
remain unchanged and are still the authoritative editable preservation stores.

The pilot contains 2,846 native members, including 294 compiled
attributes, one additive root and one flat `attrib/racebps/berbers.rgd`. The root
Boolean is false; header/root/declaration owners agree. A generated owned RaceBP,
ArmyBP, generic player schema, layout and Codex replace the Malian selection
identity. Compiled entity/squad memberships and exact private/locale references
were rebased. Identical duplicate villager/trade-cart squad identities were
collapsed only after comparing their native IDs and complete decoded scalar data.

The starting army retains the accepted native tables: capital TC, scout, six
villagers and five sheep, with their offsets and starting resources. Donor identity
StateTrees were cleared on the native startup/TC paths. Scripts enroll players by
the exact owned race. The old StandardMode/victory initializer and scripted AI are
not imported. Native AI replacement data stays preserved in the original inputs
but is excluded from this human-only pilot to avoid global stock-AI overrides.

The original voices, music and art are carried byte-for-byte. The scoped external
audio route uses `Garrison.audio.forMod("berbers")`; the inactive experimental
native-WEM replacement vault/manifest is excluded from the playable package,
preserved in the originals. No authored recording was recompressed or removed.
The existing Berber emblem replaces otherwise unauthored profile flag paths.

The dispatcher imports 18 mechanic/presentation modules. Every one of the
15 old custom startup handlers has a static
entry path. A failing-before/passing-after regression caught empty callbacks for
Zenata, tribal camel archer and Sanhaja, and an unregistered Almohad Grand Keep
module. The finalization registers the Keep's existing Start/OnGameOver callbacks;
all 2,845 other final members
were compared byte-for-byte with the supported assembler's verified build.

## Evidence and remaining gates

| Gate | Result |
| --- | --- |
| Installed core authoring/native carrier cook | Completed; Essence stdout records the compiled archive copied to output; derived definitions read back |
| Additive assembler validation/build | Completed with supported civilization CLI; separate typed RGD guarded edits |
| Prepared native reference/localization audit | 3,819 typed references; 0 unresolved stock/private references, stale owners, missing owned locale IDs or native-ID collisions |
| Imported numerical gameplay preservation | All 66,264 numeric/Boolean leaves across 288 imported attributes match the original |
| Final archive | 2,846 members read back with path/TOC/SHA-256 equality; stored CRC32/SHA1 verified |
| Prematch inventory | 67 owned EBPs, 52 owned SBPs, 85 explicitly shared EBPs |
| SCAR static validator | 25 files, 0 errors, 13 warnings; skill self-test passed |
| Changed dispatcher engine calls | AoE4 MCP reports no unknown/low-confidence engine calls in the new enrollment boundary |
| ZIP | CRC scan and packaged-SGA SHA-256 passed; native civilization bundle writer used |
| Import/dropdown/selection/map load | **Pending owner test** |
| Mechanics, roster, visuals and audible playback | **Pending owner test** |
| AI, save/load, replays, multiplayer and repeated matches | **Not qualified** |
| Standalone editable modder/source bundle | **Not complete**; originals preserved, pilot depends on pinned local inputs |
| Runtime performance and texture residency | **Not measured** |

The 13 conservative SCAR warnings include inherited Garrison audio/string aliases,
the original `Rule_RemoveSquadEvent` cleanup call, temporary group lifetime and
Enduring Generations interval cleanup. They are recorded in
`output/pilot/audit/scar-validation.json`; a zero-error static result is not full
Lua execution, API qualification or an in-game pass. In particular, no separate
Lua VM compilation/execution claim is made.

The Codex currently copies Malian presentation with owned references where present.
It is not a complete custom Berber technology tree. Bonus Overview and custom flag
surface layouts are provisional. The generic player schema may need demonstrated
donor-specific state properties after gameplay testing; no wholesale Malian schema
was copied. Nomad, later-age starts and campaign are outside this first trial.

## Size and authoring preservation

Decoded packaged art/UI bytes: **296,253,222**. Voice bytes: **164,978,236**;
music bytes: **302,326,272**. These are file payload totals, not GPU residency.
The trial remains above the 600,000,000-byte complete-ZIP target, which the owner
explicitly accepts for this test. Decoded texture memory, active LOD cost and
native frame-time/VRAM are unmeasured; ZIP reduction is not runtime optimization.

Editable pilot files are `authoring-profile.json`, the generated authoring project,
`source/scar`, the build recipe and `tools/*.py`. Prepared compiled attributes and
lossless resources remain under `output/pilot`, with all edits/hashes in `audit`.
This does not replace the original editable XML, Blender, textures/audio and
compiled-only rebuild stores. A portable source/rebuild bundle follows only after
the owner accepts this method. No other civilization port should start yet.

## Reproduction and diagnostics

Use Blender's Python 3.13, `E:/Blender5.2/5.2/python/bin/python.exe`, with the installed
0.1.8 Garrison shared package; the player is separately updated to 0.1.9.
Retain the original baseline digest and extracted input/core directories.
The sequence used is `prepare_trial.py`, `prepare_runtime.py`, `audit_trial.py`,
`check_lifecycle.py`, supported `garrison-core civilization build build-recipe.json
--output <fresh folder>`, the guarded `finalize_trial.py`, and `package_trial.py`.
Scripts currently pin named pilot generations; do not rerun over existing outputs
or treat them as a portable generic arbitrary-mod importer.

Evidence is in `output/pilot/audit`, `output/pilot/build-003/report.json` and
`output/pilot/finalized/report.json`. The finalizer has exactly one allowed changed
member. Earlier local build/delivery generations are intermediate diagnostics;
**only delivery-final is the current owner-test ZIP**. Do not distribute them.
