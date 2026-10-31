# Native structure owner colour: bounded continuation

2026-10-13 status: **stock team layer confirmed; custom static producer remains unqualified; native owner rendering pending**.

The Malian stonewall tower is positive evidence that native buildings use an owner-colour layer. Its `main` and `main_collection` materials have class `structure`, geometry effect `structure_collection`, and these layer-7 slots:

| Slot | Stock texture name | Decoded format |
|---|---|---|
| `albedoTex7` | `str_debug_team_color_alb` | see exact per-material evidence |
| `normalMap7` | `str_debug_team_color_emi` | packed normal/emissive/AO |
| `metalTex7` | `str_debug_team_color_mtl` | packed material channels |
| `maskTex5` | `mal_stonewall_tower_main_mask5` | RGB selects layers 5, 6, 7 |

The native `options` Float4 is exactly `[64, 36, 1, 8]`. Its bit meanings were **not** verified. Texture naming and that vector are evidence of a team-capable stock contract, not a sufficient custom source recipe. Do not infer a team flag bit or reuse the vector blindly.

The decoder's channel contract is `normalMap` BC3 R=emissive, G=normal_y, B=ambient_occlusion, A=normal_x; `metalTex` BC3 R=metalness, G=dielectric, B=height, A=roughness. These packed images are different from Garrison's ordinary source normal/metalness/roughness PNGs. `maskTex5.B` addresses the seventh stock layer; the shared red authoring mask is not directly interchangeable with this slot.

For all 31 building authors, continue saving neutral owner-colour surface albedo and a separate red-only authoring mask in the same UV layout. Keep neutral trim outside that mask. Preserve the `ber_owner_mask` authoring annotation. A future qualified structure producer must explicitly convert that semantic authoring mask into its chosen native layer mask and preserve the neutral material regions. Layer 7 belongs to this fixture; it is not a universal prescribed layer for every building.

The inspected static exporter iterates only albedo, normal, roughness and metalness. It explicitly treats decoder owner-colour mixes as preview only and follows their unblended input during adoption. Baking a coloured preview does not preserve runtime owner colour.

Missing producer contracts before a small cook is justified:

1. A documented/native-tested `source="structure"` material source schema, including scalar/vector types, layer/owner options, texture producer format declarations, and required defaults.
2. The source-image to native packed structure channel mapping, including team/generated albedo semantics. A stock `gen7_team_alb_packed.rrtex` name alone supplies no generation algorithm.
3. The supported FBX UV/stream/collection mapping for newly authored static geometry with that structure material, preserving construction-stage and LOD behavior.
4. A material-scoped writer. The installed variant `material_slots` returns flat texture/parameter names and selects the first duplicate. For this tower its reported `albedoTex7` is the `extra` building-kit layer, while `main` uses the team layer. Unscoped slot replacement cannot be assumed to target just the desired native material. Variants also retain stock geometry.

No new cook, stripe FBX, production edit, iteration 004 or distributable was made because the supported producer schema was not established. Prior `unit_collection` substitution and skinned-child failures were not repeated. This is a bounded source-contract result, not a claim that the engine lacks building owner colour.

Evidence: `research/buildings_batch/player_colour/structure_probe/native-material-evidence.json` (exact material blocks/slots, source hashes, API signatures, collision table and native index results). The reproducible inspection script uses Blender's Python 3.13 and makes read-only queries of installed stock/source data.

Acceptance remains two differently coloured player-owned buildings in the same game, with neutral trim preserved, across required stages, ages and LODs. A future cook/readback result will be a separate gate.
