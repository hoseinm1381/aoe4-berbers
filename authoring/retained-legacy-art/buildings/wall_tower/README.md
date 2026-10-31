# Wall tower source bundle

Age II through IV original Maghrebi wall tower. Age II starts with earth masonry; III adds lime and restrained carving; IV adds corbels and an ammunition chest. Each packed blend has mutually exclusive emplacement collections. Their source age minima follow inspected generic tower upgrades, not a proven native wall-tower progression.

Rebuild from the workspace root:

```powershell
& 'C:/Users/RS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' research/buildings_batch/wall_tower/run_hidden.py
& 'C:/Users/RS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' research/buildings_batch/wall_tower/run_hidden.py art/buildings/wall_tower/audit_saved.py
& 'C:/Users/RS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' art/buildings/wall_tower/finalize.py
```

The runner creates only a hidden task-owned Blender and uses a private config. `build_wall_tower.py` contains the atlas/material helpers, anatomy, explicit construction stages, functional wall passage/stair opening, real arrow/chamber recesses, fitted artillery options, numerical checks and presentation views. Packed age blends, per-state FBX and five PNG maps are local source exports. `ageN_construction.json` lists first visible stages; `ageN_states.json` lists source-option membership and socket anchors.

Ground origin is centered on the wall line at z0; X follows the wall. Deck z7 and clear width3m match `research/buildings_batch/wall/WALL_INTERFACE.json`. Wall ends meet x±3.2. The rear stair entry is physically open between x±0.85. Roof mounts seat at z10.5. The footprint remains native stamp/layout/simbox policy, not the source render rectangle.

Neutral owner band has `ber_owner_mask=1`; pattern.png shares the atlas UV layout and uses red only. This is not yet a supported native building shader route. Preserve stock stamp/layout/markers/selectors and validate actual owner colours, walking, firing, construction and LOD in a native match before integrating. No cook, distributable build or production modification was performed.
