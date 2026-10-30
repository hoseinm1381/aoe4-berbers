# Berber development cleanup completed

Removed **6,207 files**. Net scoped file storage decreased by
**5,339,204,428 bytes (5.34 GB / 4.97 GiB)**,
including the new rebuild bundle and all cleanup evidence.

| Drive | Before bytes | After bytes | Net bytes reclaimed |
|---|---:|---:|---:|
| E: | 5,325,346,748 | 4,501,937,504 | 823,409,244 |
| F: | 26,548,997,390 | 22,033,202,206 | 4,515,795,184 |
| Total | 31,874,344,138 | 26,535,139,710 | 5,339,204,428 |

Counted physical paths once, excluding Git and junction traversal. These are
file bytes rather than a machine-wide free-space delta. All deletion targets
had a single hardlink; no editable hardlinks were introduced.

## Preserved

- Playable checkpoint ZIPs and matching SGAs: **1.0.0, 0.11.0, 0.9.1, 0.8.1,
  Dark Age Music Test2**, unchanged and reverified after deletion.
- Current gameplay/AI/music sources, all original music/voices/textures,
  all Blender models/backups, native donor inputs and required build archives.
- Exactly **6,089 historical paths** retained as
  **1,999 content-hash blobs**, **1,025,090,225 bytes**.
  Every unique blob was physically extracted and SHA256 checked before deletion.
- First music test retired as a standalone delivery. Its SGA remains lossless
  in the source bundle; its ZIP metadata remains in retired-test1-metadata.zip.
- Required 0.10.1/0.10.0/0.9.0 ZIPs remain pinned build inputs. Other source SGAs
  and independent pre-existing rebuild/tool bundles remain preserved.

## Verification

- **101,012 protected files rehashed**;
  documented reader/test/storage edits recorded individually in source-changes.json.
- Five retained delivery ZIP CRC checks and contained/loose SGA SHA256 passed.
- 22 retained SGAs passed native integrity validation. The unchanged 428-byte
  historical Tuareg probe is still unsupported by the installed archiver and
  remains provenance outside the production build chain.
- **185 tests passed**: 144 AI, 31 music/audio, 7 source-bundle, 3 legacy restore.
- Real decoded/projection/duplicate inputs restored correctly, preserved edited
  files, and probe-owned restored copies were removed again.
- **20 UV donor paths**, **13,382 file restore routes** (3,907 now bundled) and
  **5,664 decoder restore routes** checked without missing dependencies.
- Git refs, logs, index/worktree metadata unchanged; no game files modified.
- Current release package hashes unchanged. No new native-match claim.

## Development and restoration

See [PORTING.md](../../PORTING.md), updated [REBUILD_NEXT.md](../../REBUILD_NEXT.md)
and [STORAGE.md](../../STORAGE.md). The source index is source-index.json;
the external source-blobs.zip hash is 76178a0674512ad24a7328be6a8dfe3129e5f981c8ed7444d0e60aef3bd8fb2a.
Use `python -B research/source_bundle.py --root PHYSICAL_CACHE_DIRECTORY`
for scoped restoration, or `--run research/RECIPE.py` for older recipes.
Current music/AI editing does not require restoring historical caches.

## Retained caches and remaining opportunities

Native donor/model/material/DDS inputs remain loose because they supply UV
restoration, Blender textures, geometry recipes and existing restore maps.
Opaque Content Editor caches remain where regeneration/dependency replacement
was not independently established. All Blender backups remain because active
scene ownership could not be qualified. Unknown files were preserved.

Outside copies remain inspection-only: see [OUTSIDE_CANDIDATES.md](OUTSIDE_CANDIDATES.md)
for exact counts and matching-content candidates. No outside deletions occurred.
The separate normal Berber project and unmatched external source work remain.
Further deletion of those files or removal of pinned archives requires its own
dependency/ownership migration; this cleanup does not claim they are disposable.
