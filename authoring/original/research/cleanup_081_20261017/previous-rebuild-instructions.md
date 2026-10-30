# Building the next Berber release

## Villager attachment-speaker correction: 0.8.1

The latest candidate is `output/berber_update_0_8_1/Berber-0.8.1.zip` with retained
archive `Berber_future_kingdom.sga` (SHA-256
`c58ef43ad4b0e664609161eb35178c97500837e9a844d7583fb014a50b7cc441`).
The operator confirmed on 2026-10-17 that the Villager overlap correction worked
("yes yes it worked"). This accepts that reported symptom fix; it does not
enumerate every age/gender/context or multiplayer. The ZIP remains byte-identical
to delivery; release-validation.json carries the later operator annotation.

It changes only four custom Villager age-tier attachment RGDs from 0.8.0:
52 `attachment_speaker_code` CStrings per age, 208 total, are set empty.
These had explicitly assigned the original male/female speakers despite the
removed EBPS/SBPS speech tables. Empty values match working Scout/Archer controls.
All other typed data and archive members, including Spearman and audio/scripts,
remain unchanged. Operator confirmed Spearman working well in 0.8.0; Villager
overlap was present there. The reported 0.8.1 Villager overlap is now resolved;
complete context/age/lifecycle qualification remains separate.

Recipe and regression: `research/berber081/build.py` and
`research/berber081/test_speaker_overrides.py`. Reproduction requires the retained
0.8.0 SGA/ZIP and its existing source chain; originals are not modified. Cleanup
removed only source extraction, patched payload and readback copies, regenerated
by the recipe. Preserve the four attachment-field changes in future builds;
rebuilding only the EBPS/SBPS speech edits would reintroduce native overrides.
Use a fresh output location when reproducing; the builder refuses final-file
collisions. This candidate still imports/plays through normal Garrison.

## Normal-Garrison voice branch: 0.8.0

The latest normal-client candidate is `output/berber_update_0_8_0/Berber-0.8.0.zip`.
Its authoritative archive is `output/berber_update_0_8_0/Berber_future_kingdom.sga`,
SHA-256 `7d86a7ed79c6dcfd79dba6d69b9b4a68f6f77e2737b2989f5475cf2db866c379`.
It derives from the 0.7.4 handoff/0.7.5 content, with 11 speech-table-only RGD
changes and the two updated voice scripts plus 101 retained PCM recordings.
All unrelated handoff models, gameplay and voice banks are preserved. In-game
Villager/Tuareg overlap acceptance remains pending; do not call it qualified.

Editable scripts and recipes are in `research/berber080`. Run `prepare.py`, then
the two `test_*.py` scripts, then `build.py` for a fresh reproduction. The builder
refuses existing final output files; retain delivered outputs before reproducing
into a fresh release directory. The recorded sources/receipts, 0.6.1 simplified
Villager selection report, complete 0.7.4 handoff and original voice masters/WAVs
remain required. Removed inspection/payload/readback/stage files are generated
again by that recipe. `build.py --finish-cleanup` is a recovery entry point only
for an already verified package whose cleanup has not completed.

For the next unified version, start from this candidate's validated SGA after
its runtime gate is accepted and preserve the new `berber080` dispatcher/bank.
Do not run the older two-ZIP `next_release.py` for this branch or reconstruct it
from the 0.6.1 archive, which would lose the newer handoff and audio edits.
Use normal Garrison 0.1.6 import/Play; no native voice installation or experimental
launcher is needed. Native declaration/WEM inventory retained inside the archive
is inactive: this dispatcher does not call Garrison.speech.

## Experimental 0.7.5 audio branch

The operator-test package `output/berber_update_0_7_5/Berber-0.7.5-fixed.zip` uses the
separate development handoff `output/Berber-0.7.4-handoff.1-2026-10-17`, including
its paired experimental runtime. Reproduction recipe: `research/build_075_test.py`
(refuses to overwrite an existing ZIP). Preserve that handoff as the authoritative
SGA/runtime/source input for this branch. Its SGA remains unchanged in 0.7.5.
The original 0.7.3 route below remains the stable rollback path, not the base for
rebuilding this experimental integration. Do not use `next_release.py` to recreate
the unified test: that helper intentionally produces the older two-ZIP layout.
Test instructions are inside the new ZIP; actual client import and audible
acceptance remain pending. Known intermittent stock replies are not fixed.

The retained release is **0.7.3**, with separate main/Garrison and native-voice
installer ZIPs. Both are in `output/berber_update_0_7_3`. The output directory is
a junction to `F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output`; keep F:
connected. Native voice installers should be run from a normal extracted folder
or its physical F: location, not through the E: junction.

## Check the retained inputs

Run from the project root:

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/next_release.py --check
```

This verifies the current ZIPs, every member hash and the current content SGA.
It does not require any deleted older delivery ZIP. All original Blender files,
textures, models, voice masters, normalized WAVs, encoded WEMs, speech profiles,
receipts, scripts, project configuration and source/rebuild bundles remain.

## Make 0.8.0 or another version

1. Start changes from the current content base:
   `output/berber_update_0_6_1/Berber_future_kingdom.sga`.
   It is byte-identical to the archive in 0.7.3, SHA-256
   `48f09ed61020740932b0a653e165710fda49d25aa7739d05f6486b79dbe661bb`.
   Keep the stable mod GUID and preserve unrelated members. Do not rebuild a
   newer release from an older historical art base.
2. Edit the retained assets/gameplay sources and use the matching Garrison/
   Content Editor tools to cook the changed resources. Apply verified changes to
   a new archive, leaving the retained base unchanged. Read back and validate
   the candidate. Packaging alone does not cook source or Blender changes.
3. Package the validated candidate with a new three-part version:

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/next_release.py --version 0.8.0 --summary 'Describe the actual changes' --sga 'ABSOLUTE_PATH_TO_VALIDATED_CANDIDATE.sga'
```

The command writes two new ZIPs and a validation report in
`output/berber_update_0_8_0`, updates the manifest/version/installer instructions,
and verifies every packaged member. It refuses existing delivery destinations.
The voice recordings, profile identities, ownership state, Steam-folder finder,
progress display and uninstall behavior are reused from 0.7.3. For a metadata-only
release, omit `--sga` to reuse the unchanged current content base.

This helper intentionally does not change voice payloads. A release that edits
voices must update the native manifests, unique payloads and ownership/migration
policy first, then validate install/verify/uninstall on fixtures. Do not silently
reuse the 0.7.3 voice manifest for changed recordings.

Import the new main ZIP into Garrison and test a fresh game process. Package/hash
success is separate from installation, audible voices and gameplay acceptance.
The full-size packaging smoke test only reused current content; it was not a
completed 0.8.0 content release.

## Historical dependencies

The three important recent bases are 0.5.1 (voice patch baseline), 0.6.0
(`candidate.sga`, input to the 0.6.1 patch), and 0.6.1 (current content). Older
package SGAs required by the existing building/skin patch chain and tiny source
archives in Garrison project `project/archives` also remain. Their exact paths,
hashes and reasons are recorded in
`research/archive_cleanup_20261017/deletion-plan.json` under `retained`.

Historical packaging scripts are preserved as provenance; scripts that explicitly
consume retired release ZIPs are no longer the supported entry point. Use
`research/next_release.py` for future deliveries rather than running the old
0.6.1 -> 0.7.0 -> 0.7.2 -> 0.7.3 ZIP transformation chain.

The previous duplicate-cache restore map was checked before removing its archive
dependencies. Native audio references use the retained 0.7.3 voice ZIP; model
cache references point to retained files. Restore entries for intentionally
retired temporary SGAs were removed, rather than keeping another disguised copy
of those archives. Use `research/restore_cleanup_cache.py --root
<physical-cache-directory>` if an older recipe needs a removed non-archive cache.
It verifies every restored file's hash.

Compressed `rebuild-cache.zip`, source snapshots, sidecar evidence bundles and
the pinned decoder download are source/tool inputs, not retired release packages;
they remain where current readers expect them. No Blender/source/audio cleanup
is part of this archive-only pass.
