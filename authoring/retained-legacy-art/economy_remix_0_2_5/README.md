# Berber economic building sources — 0.2.5

Material-only remixes of native AoE4 donors. Original geometry, UVs, normals, construction selectors and player-colour layers are retained. Native assembly transforms are preserved; these assets do not use the earlier small primitive recipes. House 0.2.4 is the user-accepted comparison reference.

- `mill/`: untouched/remix Malian gristmill, packed textures and recipe. One native healthy model across Ages I–IV.
- `lumber/`: four untouched/remix components and complete native assembly sources. Logs retain their stock 0.8 scale.
- `mining/`: untouched/remix combined camp plus separate crane/furnace provenance sources. Only the combined model is integrated; separate parts would duplicate it.
- `reflect.db`: retained native reflection schema used to validate every stock/cooked stamp type checksum and field layout. Copied from preserved discovery evidence; no game schema is modified.

Each building's editable `.blend` files contain packed images. Author scripts are `research/economy_025_<building>*.py`. Build integration is `research/build_berber_update_0_2_5.py`; native stamp source/verification is `research/economy_025_native_stamp.py`. Run native-module helpers with `E:/Blender5.2/5.2/python/bin/python.exe` (installed Garrison is compiled for Python 3.13).

Evidence/previews: `output/berber_update_0_2_5/authors/<building>/`. Final source/media reviews: `output/berber_update_0_2_5/reviews/`. Final ZIP and installation guide: `output/berber_update_0_2_5/`.

The stamp authoring route requires numeric Math fields and named native enums; raw decompiler blobs are diagnostic representations, not accepted source authoring. Private object IDs are deterministic and separate from stock IDs. Cook validation stages stock model definitions and the original native splat material bytes under the source validator's `.material` suffix. These material aliases are not burned or delivered; the final stamps still reference the original native decals. Readback compares every native field and array order, allowing only private object IDs and the six intended model-path changes.

Native game appearance, two player colours, construction/damage/destruction, drop-off, technologies and pathing remain pending the user's test. Stock auxiliary construction/wreck stamps, resource outskirts and decals are deliberately retained.
