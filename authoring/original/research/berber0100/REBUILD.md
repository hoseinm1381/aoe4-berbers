# Rebuild Berber 0.10.0

Authoritative baseline: final `output/berber_update_0_9_1/Berber_future_kingdom.sga`,
SHA256 `76bc149faf0a82214806d002a2d91dc6df07461e583a8da74b6a16caeb4b7d14`.
Preserve its ZIP and the working 0.8.1/0.9.0 rollback archives. Never substitute
the current editable project's older art cook or voice dispatcher for final091.

Edit `assets/scar/ai/berber_ai_*.scar` and, when needed, the shared
`assets/scar/buildings/tribal_tent.scar`. The root game mode has the new import,
but the packaged mode is rebuilt from091 plus that import to preserve its newer
speech dispatcher and guards. `pipeline.py stage` is the authoritative recipe.
No RDO, localization or compiled tuning changes are made by0100.

Use verified Python3.13 with lupa (Lua5.1) and the installed Garrison archiver.
From the project root, run with Python's `-B` flag:

1. `research/berber0100/pipeline.py prepare`
2. `research/berber0100/pipeline.py stage`
3. `research/berber0100/checks.py`
4. `research/berber0100/evidence.py` and AoE4 MCP `check_code` on complete SCAR.
5. `research/berber0100/pipeline.py compose`
6. `research/berber0100/release.py`
7. `research/berber0100/cleanup.py`

The delivery archive/ZIP must not exist for compose/build; existing outputs are
protected. For a new iteration, choose and update a new version/output directory
and preserve the old candidate until the replacement is verified.

The frozen `berber_ai_catalog.scar` is a required source input: it contains
existing production names and actual resolved inherited requirements decoded
read-only from091 plus official Attrib.sga. It is not speculative tuning XML.
Ordinary reproduction uses this retained file and does not need decoded RGD/XML
caches. Regenerate deliberately using `catalog.py` only after reviewing the
current official archive and source changes; it records donor-member hashes in
`catalog-provenance.json`. Unknown engine-only predicates are deferred to normal
engine commands, never bypassed. No author Blender operation is necessary.

Output is physically on F: through the established output junction. Cleanup
removes only this version's verified `work` folder, preserving scripts, frozen
catalog, reports, output ZIP/SGA, rollback archives and all original art/audio.

Testing layers: Lua5.1 tests plus static/MCP checks, abstract multi-player
control-flow simulation, native archive CRC/SHA1, all-member decoded SHA256 and
ZIP/member checks. Native engine, import, save/restore, combat/pathfinding,
multiplayer and performance acceptance remain pending; see the packaged
`NATIVE_AI_ACCEPTANCE.md` and its minute-log/checklist requirements.

Package cover: `assets/mod.png` is retained as the editable in-game cover source.
`release.py` copies its exact bytes to `cover.png` and sets `details.cover` in
`garrison.json`. `set_cover.py` upgrades the original coverless0100 candidate
without changing SGA or other package payloads; its validation records both
ZIP hashes. The1920x1080 PNG is below Garrison's4MiB/4096px limits.
Reimport the updated ZIP to refresh Garrison's independent installed cover.
