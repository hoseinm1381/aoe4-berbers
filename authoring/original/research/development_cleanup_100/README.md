# Berber development cleanup, 2026-10-18

Approved retention: 1.0.0, 0.11.0, 0.9.1, 0.8.1, accepted Dark Age Test2.
Archives needed by recipes are build inputs and are retained independently.
Unique historical editable work is retained losslessly. No game files or Git
history/index/objects are cleanup targets. External copies are inspection only.

Execution ledger:

- Inventory: physical E: project and mapped F: tree, excluding .git/reparse
  targets; per-file SHA256, size, link count and timestamp before deletion.
- Ruling: preserve all .blend and .blend backups in place because the Blender
  MCP inventory did not respond. No live Blender scene was modified.
- Ruling: perform cleanup in the existing requested physical workspace; a Git
  worktree would not isolate the linked build storage being cleaned.
- Historical recipes must use the lossless source launcher after bundling:
  `python -B research/source_bundle.py --run research/RECIPE.py [arguments]`.
  This restores archived decoded/projection/cache inputs, then runs the recipe.
  For a smaller restore, use `--root PHYSICAL_CACHE_DIRECTORY` instead.
- Current 1.0.0/0.11.0 authoring, original music/voice/texture inputs, all native
  binary donors and current editable model exports remain immediately accessible.
- Source deduplication uses content-hash ZIP members, not hardlinks between
  editable files. No coupled source edits or hidden cross-project links.

The source index records exact physical paths. On a different workstation,
restore to a scratch directory using the relocation/export route documented in
PORTING.md before adapting recipes and project identity.
