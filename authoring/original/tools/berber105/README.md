# Berber maintained development workspace

Version 1.0.5 changes package metadata and development storage only. All 8,529
game resources come from exact final 1.0.4, including native AI, art, voices,
music and UV repairs. Native acceptance remains pending with the user.

## Authoritative inputs

- One immutable archive: `output/berber_update_1_0_4/Berber_future_kingdom.sga`,
  SHA256 `55629909581fd0035a141f212e38274d3e1f7f185fecffed635b821e2b7204a6`.
  This is also the unchanged 1.0.5 archive; do not retain a redundant loose copy.
- Sole playable rollback: original `output/berber_update_1_0_4/Berber-1.0.4.zip`.
- Editable project, gameplay/localization XML and source art remain under the
  existing E: root and mapped F: art/research folders. Existing local edits were
  preserved. They are not assumed to equal final compiled release values.
- `source-index.json.gz` maps compressed original paths to the one current
  SHA-addressed input store under F: `rebuild_inputs/current/source-blobs.zip`.
  It preserves required decoded/projection data and redundant rebuild inputs.
  Historical voice/diagnostic inputs also use this store, avoiding one 256 KB
  exFAT allocation per small file. Current Blender image dependencies stay loose.
- `retired-package-inputs.json.gz` indexes additional non-SGA source/provenance
  from old ZIPs. Unique bytes are in `rebuild_inputs/current/retired-package-inputs.zip`;
  this preserves package-only inputs without retaining old playable releases.
- `native_ai/` contains independent author XML, editor allocations, official
  analogues and reference/media cook snapshots. `frozen/` contains exact current
  SCAR and protected native resources. `resource-map.json.gz` indexes all archive
  members and available editable/input matches. It distinguishes compiled
  resources from editable source candidates; an opaque native format is not XML.
- Unique ambiguous sources and Blender backups stay when supersession cannot be
  established. Their retained storage is intentional, not an unreported deletion.

## Build and edit

Use Python 3.13 with Lupa, installed Garrison 0.1.4 authoring tools, Blender
5.2.2 LTS, current compatible Content Editor and FFmpeg. `workspace.py` records
the installed archiver/SGA reader locations. No historical Python imports or
older release archives participate in the maintained build.
`output/berber_update_1_0_5/toolchain.json` records the measured toolchain and
Content Editor binary SHA; its Windows version fields are generic 1.0.0.0.

From the project root:

```powershell
python -B tools/berber105/test_workspace.py
python -B tools/berber105/native_ai/test_native.py
python -B tools/berber105/workspace.py validate-inputs
python -B tools/berber105/build.py compose --output F:/aoe_4_temp/berber-new/Berber_future_kingdom.sga
python -B tools/berber105/workspace.py package --destination F:/aoe_4_temp/berber-new/delivery
python -B tools/berber105/workspace.py verify --destination F:/aoe_4_temp/berber-new/delivery
```

The package command reproduces this unchanged 1.0.5 release only. It never
silently packages an arbitrary edited archive. For a future changed release,
set the next version, explicit archive path and manifest measured SHA in the
package recipe, then verify the change allowlist and package anew.

For an edited build, supply `compose --overrides selected-members.json` where
the JSON is an explicit `{ "archive/member": "path/to/new/file" }` mapping.
New destinations are mandatory. Every unselected member must retain its hash.
The compositor carries forward missing native speech extensions and empty
attachment speaker overrides, and repairs UV0 for the 22 known models while
preserving position edits. It refuses incompatible topology instead of guessing.
Review deliberately changed speech/UV behavior separately before changing these
guards. No source edit or raw cook automatically replaces the current archive.

`build.py cook` restores hash-pinned reference/media snapshots and cooks the
seven native AI source overlays. It checks their compiled hashes against the
retained records. To author tuning, supply `--source-dir DIRECTORY` containing
only the intended `instances`-relative XML overlays; reference snapshots supply
the rest. Extract and select only intended cooked records for composition.
The cook uses `output/berber_update_1_0_5/work`; remove verified scratch via the
cleanup procedure before another cook. Do not overwrite a running editor job.

```powershell
python -B tools/berber105/build.py cook
python -B tools/berber105/build.py cook --source-dir F:/aoe_4_temp/berber-edits/instances
```

For models, edit the retained Blender master and use its existing native
geometry/material recipe. The original model identity, topology, attachments,
team-color bindings and textures matter. Restore needed recipe inputs before
running it. The independent `uv.py` algorithm and exact frozen resources retain
the shipped UV correction. Blender/FBX export, native geometry composition and
Content Editor cooking have separate evidence in the release reports.

`audio_prepare.py` retains the complete 48-source/145-playback-file music recipe;
it writes generated catalogs into its output instead of an older source folder.
Speech PCM masters, receipts, recording plans and the exact frozen dispatcher/
voice bank remain available. Preserve the shipped speaker suppression after
recooking unit or attachment XML. Normal Garrison embedded audio remains the
delivery route; no native audio installation or development runtime is added.
To regenerate the complete music preparation in disposable working storage:
`python -B tools/berber105/audio_prepare.py`.

## Restore compressed inputs

```powershell
python -B tools/berber105/workspace.py restore --path 'ORIGINAL_PHYSICAL_FILE_OR_DIRECTORY_PATH'
```

Restoration validates SHA256, skips identical existing files and refuses to
overwrite edited files. Restore just the directory required by your recipe;
restoring every historical voice input recreates the small-file allocation cost.
Use
`research/source_bundle.py --root PHYSICAL_DIRECTORY` for old recipes: its reader
now routes to the current store. Historical release generators are retired and
are not expected to recreate deleted playable versions. Source recipes and
their needed inputs remain available for development.
Its `--run` compatibility launcher restores decoded/projection/cache and archived
historical inputs before running a recipe; this broader restore can be large.

Export the canonical bundled inputs with `workspace.py export-inputs --destination
NEW_DIRECTORY`. For an additional package-only input, use `workspace.py
restore-extra --path SHA256 --destination NEW_FILE`, selecting its hash from the
package-input index. Existing loose sources remain in the editable project.

For relocation, copy E: sources, mapped F: art/research, current input store,
1.0.4 baseline/rollback and 1.0.5 deliverable. Set `BERBER_STORAGE` to the new
physical external root. Remap source-index scope/relative paths and Blender
external file paths when changing drives; no credentials or official game
archives belong in a distributed mod.

Also retain the adjacent native donor directories `F:/aoe_4_temp/b031siege`,
`F:/aoe_4_temp/berber_040_university_donors` and
`F:/aoe_4_temp/berber_040_wonder_envelope`. They total 160,676,063 bytes and are
required by some historical art recipes. Their current ownership/accounting is
in `adjacent-storage.json`; remap those recipe paths when relocating them.

## Verification and cleanup

Retained footprint excludes temporary working copies; report their peak
separately. Cook and independent verification may temporarily need several GB.
F: uses exFAT with 262,144-byte clusters; compare file bytes with occupied space
using `python -B tools/berber105/allocation.py`. Reports exclude directory metadata.
Release cleanup inventories physical files, rejects reparse traversal, checks
all retained hashes and ZIP integrity, and preserves compact reports. No Git
history, object, reflog or worktree may be expired for storage savings.

For this consolidation, `cleanup.py retire` is a one-time gated migration;
`cleanup.py finish` removes verified release-owned scratch and rechecks delivery.
For future releases use a new release/output configuration and fresh evidence;
do not reuse the 1.0.5 completion reports as proof for a later failed cook.
