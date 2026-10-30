# Berbers 0.1.2 — local review and native retest

Owner screenshots of tested 0.1.1 show empty overview lists for the three new
ports, inherited Malian overview technologies for Berbers, missing selector
flags and overlapping or misplaced tech-tree icons. The owner specifically
identified Berber blacksmith research appearing in Age I.

## Changes

- 7 owned unique-unit entries and 4 owned unique-technology entries.
  `source/codex-review.json` owns these reviewed lists. Real blueprint UI supplies
  names, icons and tooltips. Internal markers are not presented as research.
- Seven source-backed bonus explanations, plus the hidden combined lobby
  summary at trait index 0. Active alliance, research and landmark requirements
  are explicit. Existing unit/research mechanics are unchanged.
- Plural display labels, without changing race/bundle/audio keys or UUIDs.
- Clear RaceBP `icon_small`, following the installed Garrison authoring guide;
  the native Codex falls back to its already cooked `icon` flag.
- Build both Codex representations from native construction tabs, spawners and
  research lists. Follow positive current official/private prerequisites;
  ignore negative/self-exclusion requirements when computing admission ages.
  Keep producer availability and landmark construction/production ages separate.
- Use local x pitch 2 and persistent family lanes, reserve producer header rows,
  merge same-name producer variants and report conditional-unit aliases. Bind
  actual unit-tier research through `upgrade_pbg`. Native age rows remain 0–11.
- Stock foreign Villager menus do not import an entire donor civilization's
  construction tree. Such conditional production slots remain untouched in
  gameplay and are recorded in `docs/CODEX_GRAPH.json` for native review.
- Use maximum standard ZIP compression while preserving SDK package member
  bytes. Keep HD loading screens and world textures/geometry unchanged.

## Evidence and limits

`tests/fixtures/codex-before-012.rgd` was extracted from the tested 0.1.1 ZIP and
SHA-256 checked against its original final member manifest. Regressions prove
the previous empty/donor lists and Age-I blacksmith defect, check corrected
research tiers, icon pitch, both native views, selector fields and UI-only scope.
The final assembler verifies native identity, CRC/SHA1, every member's SHA-256,
declaration hashes, exact change allowlist and outer ZIP/SGA integrity.

See `docs/BUILD_VERIFICATION.json`, `docs/FINAL_MEMBER_MANIFEST.json.gz`,
`docs/SOURCE_TESTS.json` and `docs/SIZE_REPORT.json` for current results. This is
typed-native validation/assembly/readback, not a new art cook or Content Editor
burn. No new world art requires cooking. Native appearance, tooltip layout,
audio listening, gameplay, AI, save/load, multiplayer and VRAM/frame-time
remain separate acceptance gates. No runtime performance claim follows from
ZIP or audio size reduction.

Retest the checklist in START-HERE.md. Tested 0.1.1, original masters, native
world assets, credits and stable identity are retained. Nothing is installed
or published. Push requires owner acceptance and a separate manual instruction.

## Audio compression

`source/audio-012-recipe.json` records every source master, original source/PCM
hash, rotation segment, quality setting, output hash and full decode result.
1,151 PCM speech clips use Vorbis quality 5. Music uses quality 4.5, rebuilt
directly from the ranked original WAV/FLAC/supplied-MP3 masters with identical
full-track rotations and entry order. A music conversion is retained only if
smaller than the existing MP3. 88 music files benefit; 57 smaller MP3s remain.
No track, voice event, dynamic-music sequence or scheduling logic is removed.

Audio member bytes decrease from 467,304,543 to 273,181,832 (41.54%). All 1,239
replacements fully decode. Vorbis packet tails differ by -128 to +1,009 frames
at 48 kHz (at most 21.03 ms); playback scheduling durations stay unchanged.
`docs/update_012/AUDIO_QUALITY.json` compares 24 voice and 8 music samples with
their exact original PCM. These measurements do not replace listening tests.

All source audio is preserved. The 1,138 previously native-only speech masters
now have explicit unchanged files under `authoring/audio-originals/`, indexed
in the editable master manifest. The tested ZIP also retains old encodings.
`tools/audio_rebuild.py --output <new-review-directory>` re-encodes editable
masters without modifying the active manifest or release. Full mod rebuilds
use the verified native inputs and do not need FFmpeg. Vorbis page identifiers
can vary between encoder runs; exact native inputs remain versioned.

Final ordinary producer headers lead their available age band; units/research follow. The supported one-member native refinement, when needed, is recorded in update_012/HEADER_REVIEW.json. Every untouched member was re-extracted and hash checked. The normal full builder produces this final layout directly.

The generic SCAR checker reports two existing lifecycle-name findings. These unchanged passive modules are explicitly started in BerbersPilot_Start; review evidence is in update_012/SCAR_STATIC_REVIEW.json. No gameplay was changed to silence the checker.
