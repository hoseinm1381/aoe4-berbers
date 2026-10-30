# Previous-release cache restoration

Update 2026-10-17: older delivery ZIPs and temporary SGAs were intentionally
retired. Only the 0.7.3 delivery ZIPs remain; required base SGAs and source/rebuild
bundles are retained. The active restore map was checked against these retained
inputs. Two temporary-SGA restore entries were retired as well. The original
map remains as historical evidence in `../archive_cleanup_20261017/previous-restore-map.json`.
Use the active map, not that historical snapshot. See the project-root
`REBUILD_NEXT.md` for the supported future-release workflow.

This cleanup preserves release ZIPs, authoritative SGAs, Blender files and
backups, editable sources, original and normalized WAVs, encoded voice banks,
profiles, receipts, recipes and reports. It never targets installed game files.

`deletion-plan.json` records every removed duplicate and its SHA-256, together
with an exact retained source file or verified ZIP member. A retained source is
never also a deletion target. Decoded listening-test WAVs are admitted separately
only when their full-decode proof matches both the cached WAV and retained WEM.
The pinned decoder and a byte-identical regeneration probe establish their route.

Before running an older recipe that directly consumes a removed cache, run:

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/restore_cleanup_cache.py --root 'F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/RELEASE/CACHE'
```

Replace RELEASE/CACHE with the exact older release and cache directory needed.
The helper restores only listed missing files under that root, verifies restored
hashes, and preserves any existing edited files. It requires no network, paid
generation or new encoding. Do not restore all caches unless actually needed.

The 0.6.0 archive readback helper restores listed missing files automatically.
Directly referenced blueprint RGDs remain in place. Unique decoded-static JSON
caches remain uncompressed because older authoring recipes still require their
existing paths; no regeneration route is assumed. Shared stock caches remain
untouched. Checkpoints without an exact verified replacement also remain.

Reports distinguish logical bytes removed from a conservative physical-space
estimate: a hardlinked file may not release data until its last link is removed.
