# Berber 0.3.1 Siege Workshop donor and art report

The active Age III and IV models are edited copies of the official Abbasid
Siege Workshop models. This is a game-art interpretation of a Maghrebi
artisans' yard, not a reconstruction of a documented medieval workshop.

## Donors and retained geometry

| Age | Stock model | Native geometry SHA-256 | GEOB groups | Vertices moved over 15 cm |
| --- | --- | --- | ---: | ---: |
| III | `abb_siege_workshop_control_age03.rgm` | `f6c61514979d68670050d3c54101f92e1011307d17b87ba26dc876de7d97f811` | 4 | 45,527 |
| IV | `abb_siege_workshop_control_age04.rgm` | `2f604020495ccb28ed4dcd45273a6687837dbcae4d7419b7898bfa6f251ef982` | 5 | 71,887 |

The stock L-shaped wall plan, low masonry and entrance arches are retained.
Above 2.15 m, the upper wall/roof proportions are compressed and inset, the
rear and west roof lines are pitched toward the yard, the tall flues are
shortened, the inner north roof is recessed below its retained parapet, and
the gatehouse crown is raised. The native patch updates only
vertex positions and tangent frames in matched GEOB chunks. Triangle indices,
UV bytes, material mapping, opaque native chunks, origin, and the lower
ground/entrance band remain byte-preserved. The native owner-colour albedo slot
`albedoTex7` remains in the primary stock material for both ages. Age IV also
has that slot in its `extra` material.

## New connected work-yard kit

Each age has one UV-mapped, single-material FBX kit attached at identity
transform. The roof's rear wall plate crosses the donor inner wall plane
`y=1.32` by 0.12 m; front timber posts start at ground `z=0` and enter the
eave beam by 0.13 m. The pitched roof seats on the rafters and wall plate.
Kit vertices do not enter the siege-exit envelope `x < -1.2, y < -2.0`.

The rear wall holds a shallow shelter while the front two-thirds of the yard
remains visibly open at default camera zoom. Age III uses earthen/plaster
walls, cedar beams and a cloth shaded work bay. Age IV has a stronger pitched
tile shed, brighter plaster and a raised
stone-and-cedar hoist tower, providing a different silhouette. Benches,
timber stock, wheels and an anvil occupy the east edge of the yard, leaving
the larger central working area open. The palette and yard treatment draw on
the crafts and traditional materials described for the [Medina of Marrakesh](https://whc.unesco.org/en/list/331/), especially lime plaster,
painted and carved wood, ironwork and artisanal trades. These references
support material and visual choices, not an exact siege-workshop typology.

## Integration contract

`art/building_remix_0_3_1/siege/recipe.json` supplies exact donors,
projections and private kit manifests. Garrison `static prepare` passed all
six readiness gates for each kit; isolated `mod-project add` accepted both
into `F:/aoe_4_temp/b031siege/scratch_library/Mods/berber_siege_031_scratch`
as `b031/sg3` and `b031/sg4`, one static model each. No native cook has run.
The coordinator will cook the native
model and private static kit serially, then replace one stock sagebush visual
with the kit in each healthy Malian stamp at identity transform. All other
stamp objects and weapon/production attachments stay in place. Native cook
and archive readback are pending this integration step; source checks and
Blender previews are not native runtime acceptance.

Validated source reports are `siege_age03-source-validation.json`,
`siege_age04-source-validation.json`, and `native-geometry-validation.json`.
Seven solid-view previews per age include front, rear, left, right, top,
bottom and default game zoom.

## Rebuild after release cache cleanup

The retained `.blend` files, `siege_age0N.rrgeom` files, source atlas/maps,
`recipe.json`, and the three `research/berber_031_siege_*.py` scripts are the
rebuild inputs. The scratch Garrison library and its canonical source bundles
at `F:/aoe_4_temp/b031siege` are regenerable: run
`research/berber_031_siege_blender.py` in Blender background once with
`BERBER_SIEGE_AGE=3` and again with `BERBER_SIEGE_AGE=4`, then run
`garrison-core static prepare` with the generated age-specific request JSONs.
This recreates `workspace.json` at the paths recorded in `recipe.json`.
`garrison-core mod-project add` can then add those manifests to the intended
fresh project. The scratch project's GUID is not the civilization's GUID.
