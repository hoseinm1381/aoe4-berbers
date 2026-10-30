"""Finalize exact byte accounting after protected-input postflight passes."""
from pathlib import Path
import collections,gzip,hashlib,json,os
from inventory import ROOT,EXTERNAL,REPORT,walk,sha,save

verification=json.loads((REPORT/'verification.json').read_text());assert verification['status']=='passed'
for name in ('restore-probes.json','dependency-postflight.json','test-results.json'):
 assert json.loads((REPORT/name).read_text())['status']=='passed',name
before=json.loads((REPORT/'scope-before.json').read_text())
removed=json.loads((REPORT/'removed.json').read_text());bundle=json.loads((REPORT/'bundle-verification.json').read_text())
assert all(not Path(r['path']).exists() for r in removed)
source_index=json.loads((REPORT/'source-index.json').read_text());assert sha(source_index['bundle'])==source_index['bundle_sha256']
native=json.loads((REPORT/'native-sga-verification.json').read_text())
(Path(source_index['bundle']).parent/'SHA256SUMS.txt').write_text(source_index['bundle_sha256']+'  source-blobs.zip\n'+sha(Path(source_index['bundle']).parent/'retired-test1-metadata.zip')+'  retired-test1-metadata.zip\n',encoding='utf8')

def footprint():
 totals=collections.Counter();files=0
 for root in (ROOT,EXTERNAL):
  pending=[root]
  while pending:
   with os.scandir(pending.pop()) as entries:
    for e in entries:
     if e.name=='.git':continue
     st=e.stat(follow_symlinks=False)
     if st.st_file_attributes & 0x400:continue
     if e.is_dir(follow_symlinks=False):pending.append(Path(e.path))
     elif e.is_file(follow_symlinks=False):totals[root.drive]+=st.st_size;files+=1
 return dict(totals),files

storage=ROOT/'STORAGE.md';base=storage.read_text(encoding='utf8')
marker='\n\n## 2026-10-18 development cleanup final accounting\n'
if marker in base:base=base.split(marker)[0]
changes=json.loads((REPORT/'source-changes.json').read_text())

for iteration in range(6):
 totals,files=footprint();after=sum(totals.values());net=before['bytes']-after
 result={'status':'passed','scope_file_bytes_before':before['bytes'],'scope_file_bytes_after':after,'net_bytes_reclaimed':net,'net_bytes_reclaimed_by_drive':{d:before['by_drive'][d]-totals[d] for d in ('E:','F:')},'files_after':files,'files_removed':len(removed),'gross_file_bytes_removed':sum(r['bytes'] for r in removed),'lossless_bundle_bytes':bundle['bundle_bytes'],'bundle_original_paths':bundle['original_paths'],'unique_source_blobs':bundle['unique_blobs'],'protected_inputs_rehashed':verification['protected_inputs_rehashed'],'selected_checkpoints':5,'native_sgas_passed':len(native['results'])-len(native['failures']),'historical_probe_exceptions':len(native['failures']),'tests_passed':185,'outside_files_deleted':0,'git':'unchanged','accounting':'Physical-path file lengths, E and F counted once, Git excluded. New bundles, scripts, documentation and cleanup evidence included in after total. Not a system free-space delta; filesystem allocation can differ.'}
 save(REPORT/'result.json',result)
 storage.write_text(base+marker+f'Completed verified deletion of {len(removed):,} files ({sum(r["bytes"] for r in removed):,} gross bytes).\nThe verified {bundle["bundle_bytes"]:,}-byte lossless source bundle retains\n{bundle["original_paths"]:,} original paths using {bundle["unique_blobs"]:,} unique SHA256 blobs.\nScope file bytes: {before["bytes"]:,} before, {after:,} after; net\n{net:,} bytes reclaimed, including all new evidence/bundles. E:\n{result["net_bytes_reclaimed_by_drive"]["E:"]:,}; F: {result["net_bytes_reclaimed_by_drive"]["F:"]:,} net bytes.\nFive checkpoint ZIP/SGA pairs, {verification["protected_inputs_rehashed"]:,} protected inputs, Git state,\n185 AI/music/restore tests and real source restoration passed. Twenty-two native\nSGAs validated; one unchanged historical 428-byte probe remains unsupported.\nAll 20 UV donor paths and 19,046 old restore routes remain usable.\n\nRetained loose caches: native donor/model/material/DDS resources used by Blender\ntextures, geometry recipes, source restore maps and UV restoration; Content\nEditor project caches without an independently proven regeneration/dependency\nreplacement. All .blend and .blend backups remain loose because live Blender\nownership could not be qualified. Older pinned 0.10.1/0.10.0/0.9.0 ZIPs and\nsource SGAs remain build dependencies. No model, gameplay, voice or music\nfeature was removed; no outside files or Git data were deleted.\n\nDetailed accounting, hashes, tests and outstanding outside candidates:\nresearch/development_cleanup_100/CLEANUP_REPORT.md and result.json. Current\nsource/porting map: PORTING.md. Historical recipe input restoration is explicit\nand can expand caches again; rerun a verified scoped cleanup after rebuilding.\n',encoding='utf8')
 for p in (storage,ROOT/'REBUILD_NEXT.md'):
  if str(p) in changes:changes[str(p)]['after']=sha(p)
 save(REPORT/'source-changes.json',changes)
 report=f'''# Berber development cleanup completed

Removed **{len(removed):,} files**. Net scoped file storage decreased by
**{net:,} bytes ({net/1e9:.2f} GB / {net/2**30:.2f} GiB)**,
including the new rebuild bundle and all cleanup evidence.

| Drive | Before bytes | After bytes | Net bytes reclaimed |
|---|---:|---:|---:|
| E: | {before['by_drive']['E:']:,} | {totals['E:']:,} | {result['net_bytes_reclaimed_by_drive']['E:']:,} |
| F: | {before['by_drive']['F:']:,} | {totals['F:']:,} | {result['net_bytes_reclaimed_by_drive']['F:']:,} |
| Total | {before['bytes']:,} | {after:,} | {net:,} |

Counted physical paths once, excluding Git and junction traversal. These are
file bytes rather than a machine-wide free-space delta. All deletion targets
had a single hardlink; no editable hardlinks were introduced.

## Preserved

- Playable checkpoint ZIPs and matching SGAs: **1.0.0, 0.11.0, 0.9.1, 0.8.1,
  Dark Age Music Test2**, unchanged and reverified after deletion.
- Current gameplay/AI/music sources, all original music/voices/textures,
  all Blender models/backups, native donor inputs and required build archives.
- Exactly **{bundle['original_paths']:,} historical paths** retained as
  **{bundle['unique_blobs']:,} content-hash blobs**, **{bundle['bundle_bytes']:,} bytes**.
  Every unique blob was physically extracted and SHA256 checked before deletion.
- First music test retired as a standalone delivery. Its SGA remains lossless
  in the source bundle; its ZIP metadata remains in retired-test1-metadata.zip.
- Required 0.10.1/0.10.0/0.9.0 ZIPs remain pinned build inputs. Other source SGAs
  and independent pre-existing rebuild/tool bundles remain preserved.

## Verification

- **{verification['protected_inputs_rehashed']:,} protected files rehashed**;
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
the external source-blobs.zip hash is {source_index['bundle_sha256']}.
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
'''
 (REPORT/'CLEANUP_REPORT.md').write_text(report,encoding='utf8')
 verification['final_documentation_hashes']={str(p):sha(p) for p in (storage,ROOT/'REBUILD_NEXT.md',ROOT/'PORTING.md')}
 save(REPORT/'verification.json',verification)
 actual,_=footprint()
 if actual==totals:break
else:raise RuntimeError('Accounting did not stabilize')
assert sum(actual.values())==result['scope_file_bytes_after']
assert all(sha(p)==h for p,h in verification['final_documentation_hashes'].items())
print('FINAL_CLEANUP_VERIFIED',json.dumps(result),flush=True)
