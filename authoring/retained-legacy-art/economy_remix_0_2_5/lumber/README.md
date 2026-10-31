# Berber lumber camp 0.2.5

Material-only remix of the official common lumber camp consumed by Malian `building_econ_wood_mal`. The English-named tier attachment is the actual Malian stock consumer, not an arbitrary gameplay replacement.

The native `art/stamps/civ_common/com_lumber_camp` stamp consumes the crane/foundation, construction lumber pile, wood logs and bow saw. All four receive private materials; stock topology, UVs, normals, native selectors, simulation bounds and stamp transforms remain intact. The native stamp also references debris, construction splat, decal and a sacred-object auxiliary visual: retain them as native state dependencies rather than inventing a shelter. No stock material is overwritten.

Surface palette: dark warm timber, subdued ochre rope/fabric, earthy foundation grout. Team-colour albedo and its native tonal controls are excluded from repainting; all packed masks, roughness/normal maps, overlays and charred maps retain stock references. No player colour is baked.

`recipe.json` contains source SHA-256 and per-material edits. The author payload/dependency mapping is `output/berber_update_0_2_5/authors/lumber/delivery.json`. Four component untouched/remix Blender pairs plus two assembly sources are editable and pack their images. Component and assembly before/after, six solid orthographic views and the gameplay angle are in the author previews folder.

Assembly sources preserve the official native translations/rotations/scales with native Y-up to Blender Z-up basis conversion. Wood-log scale is 0.8; the other remodelled components are 1.0. No guessed 2x2 shrink or automatic 3x native rescale is introduced. Assembly dimensions are 7.0493 x 7.6765 x 8.1641 including the native below-ground foundation extent; before/after bounds are equal. The assembly preview shows healthy crane/logs/saw with the construction pile hidden; that pile remains available for construction inspection. It does not simulate native animated selectors or damage state playback.

Fresh cook succeeded with Live Reload off, build `20261013T164923Z-b1c8aab2`, archive SHA256 `5126dd08b804ba6b405bfb917d3993d54b411cb60e0731a6942088d9b8ef4e76`. The first attempt was blocked by mandatory Documents logging; the next attempt was interrupted with no archive and was not used. The fresh retry generated the verified archive. Native geometry bytes are unchanged, and the final scoped material payload asserts that every unedited texture/parameter remains unchanged. Root packaging must use the payload (31 members) rather than donor gameplay/project resources.

Native acceptance is pending the user's game test: construction/completion, ages, two owners, LODs, damaged/wreck appearance, placement/movement and wood drop-off. Stock auxiliary damage/wreck references are retained; their visual playback is not claimed from Blender previews.
