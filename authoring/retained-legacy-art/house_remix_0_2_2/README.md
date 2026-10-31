# Berber house 0.2.2 — editable stock surface remix

These are decoded **Abbasid House Control A** game models for Ages I–IV, not buildings generated from primitives. Each untouched `.blend` retains the imported native geometry. Each `Berber_House_Age*_0_2_2.blend` retains that topology and both stock UV maps, with repainted earthen surfaces, darker timber and geometric trim. All models use uniform visual scale 0.46 to fit the existing Berber house's 4×4 footprint.

The cultural changes are a **surface/material remix**. No walls, openings, roof terraces or joinery geometry have been rebuilt. The age progression inherits the stock age-specific architecture, with warm earth tones and richer upper trim. [UNESCO's Ait-Ben-Haddou overview](https://whc.unesco.org/en/list/444/) supplies southern Moroccan earth/timber/upper-wall decoration cues; these are game art choices, not a dated reconstruction.

## Reproducible inputs

- `recipe.json`: exact stock model/archive hashes, per-material images and tonal parameters, team slots to preserve and visual scale.
- `textures/`: 40 editable source PNGs repainted from the decoded stock maps.
- `prepare_textures.py`: deterministic map repaint and Garrison native texture carrier recipes.
- `author_blender.py`: untouched/remixed Blender saves, UV/topology checks and six-side inspection captures.
- `native_materials.py`: uses the installed Garrison material rewrite on isolated native material roots, preventing repeated slot names from repainting unrelated wood/team layers.
- `test_native_materials.py`: real stock-fixture tests for root isolation, tonal parameters and team-colour preservation.
- `../../research/build_berber_update_0_2_2.py`: fresh cooks, private house bindings, final archive readback and packaging.

Garrison project: `E:/bh22/Mods/berber_house_022`. Source/compiled stamp project: `E:/bhs22`. Both are task-owned short-path build staging; durable source and evidence reside here and in `output/berber_update_0_2_2`.

For future revisions, run a fresh Garrison cook after any changed texture/recipe inputs and use a new stamp-build run directory. The helper's cached `stages` result is only for the existing inputs; it does not automatically invalidate a cook after source edits. Final extraction directories are bound to archive hashes.

## Native integration

Native Garrison model variants preserve the stock RGM/RGO/geometry, collection palette, layered structure shader, masks, UVs and team-colour layers. Forty modified albedo textures are freshly cooked. Per-material native tonal parameters match the authored palette. Four freshly compiled stamps apply only visual scale and do not add pathfinding blockers.

Only the existing Berber house actor receives private age attachment references. All three healthy house variant categories use the corresponding age remix. Existing Malian construction and wreck stamps remain. The separate Malian outskirts-house group is removed after checking that it only selects a visual attachment initially and at Castle Age, with no upgrade targets or reached/action effects. Gameplay, footprint, age actions and the entire 0.2.1 Tent/Tuareg/SCAR/audio content remain unchanged.

## Limits and testing

Native selectors and owner-colour resources are retained, not newly qualified. Blender's layered-material graph is an approximate preview. Test both player colours, construction/cancel, damage/burning/destruction, all age transitions, placement, orientation and near/far views in a fresh match. Auxiliary scaffold/wreck geometry may retain the stock Malian appearance. No native match or multiplayer acceptance is claimed.

The release ZIP is separate from the active main archive; importing 0.2.2 is the user's next action. Reimport 0.2.1 to roll back.
