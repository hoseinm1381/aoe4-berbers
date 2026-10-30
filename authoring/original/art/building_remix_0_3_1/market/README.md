# Berber 0.3.1 Tribal Market source handoff

Three Age II–IV Abbasid Market donors are reshaped in native GEOB. The broad
stock upper mass is vertically compressed into a compact courtyard hall, while
the new deep entrance, continuous arcaded frontage, timber shade and cargo sit
inside the original donor footprint. Age II uses earth/timber; Age III adds
lime-stone crenellation; Age IV adds carved/screened trim. No Byzantine annex
is used or referenced by these sources.

## Reproducible source route

1. `py -3.13 research/berber_031_market_native.py` creates the three
   `Berber_market_age0N_0_3_1.rrgeom` files, projections, and
   `native-geometry-validation.json` from the shared hashed official cache.
2. `E:/Blender5.2/blender.exe -b --python
   research/berber_031_market_blender.py -- age0N` makes each editable `.blend`,
   seven review views, kit FBX and `market_age0N-source-validation.json`.
3. `E:/Blender5.2/blender.exe -b --python
   research/berber_031_market_export.py -- age0N` prepares each source FBX,
   three texture material records and the Garrison static request. The
   resulting prepared workspace manifests are under
   `output/berber_update_0_3_1/market-static-prep/Assets/Custom/b031/mN/workspace.json`.

Installed Garrison `static prepare` passed for all three workspaces. A separate
`berber_market_uv_probe` Mod Project accepted all three through `mod-project
add`, producing three static model parts per age. UVs are within the base tile
and arch rings are manifold. This is authoring and add-path evidence, **not**
a Content Editor cook, a final stamp binding or native game acceptance.

## Integration contract

- Garrison short namespace/assets: `b031/m2`, `b031/m3`, `b031/m4`.
- Each age's three-part static kit is aligned to the donor local origin (all
  Blender mesh transforms identity). Include **all three** parts when binding
  the age's market stamp; no Byzantine annex part is active.
- Use the matching age `rrgeom` and projection for the native stock market core.
  Its stock UV/index topology, opaque chunks, native material owner-colour slots,
  origin and XY footprint are retained; vertices at/below `z=0.45` are exact.
- Reuse the 0.3.0 Market native material palette/owner-colour route on the core;
  the supplementary kit uses age-specific earth/stone/cedar images. The solid
  previews intentionally show stock core materials as grey, so they do not prove
  final colour or native player colour.
- The gate and front arcade are visual-only. The coordinator must verify their
  final stamp transforms and unit/trader clearance in game. The source Blender
  scene does not prove collision, exits, construction, damage or rally behavior.

The earlier oversize UV mapping was rejected by `mod-project add` and replaced
with per-polygon base-tile UVs. The first aggressive XY roof taper visibly
folded the donor roof, so it was removed; the delivered roof remix uses exact
XY preservation with a stronger measured vertical compression instead.
