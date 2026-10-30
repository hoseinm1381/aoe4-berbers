# Almohad Grand Keep — original source landmark

Completed age IV only; construction occurs in III. Current target requirements require `castle_age` present and `imperial_age` absent; completed action uses `landmark_age_3_action_apply`. The villager build list references this mod landmark at line1538. Installed official core wonder_age3 and Malian landmark3f readbacks preserve the same age-transition family; filename age3 describes its construction age. This is an age-up landmark, not an ordinary age-III completed Keep.

Current target XML site footprint is 8×8, entity_scale100, animator_scale125. Source geometry is deliberately 0.8 times the design: foundation 6.24m source becomes7.8m after1.25 animator multiplication. Site footprint is independently read from XML, never inferred from donor/render bounds. Origin ground Z0. Native scale/axis/loading still requires a match check.

## Design evidence and inference

[UNESCO Rabat](https://whc.unesco.org/en/list/1401) identifies Almohad ramparts and gates as surviving elements of the planned imperial capital. [UNESCO evaluation](https://whc.unesco.org/document/152576) describes the gates' synthesis of Oriental and Andalusian influences. [Rabat tourism Bab El Had](https://www.visitrabat.com/en/lieux/bab-el-had-2/) identifies an Almohad defensive gateway built in the late12th century. These support the fortified monumental-gate vocabulary. They do not document this invented keep's exact plan or proportions.

Original design inference: four battered square towers around a genuinely hollow court; lower gate towers, taller rear watch towers, connected crenellated curtains/walks, rear royal hall, court access stair, recessed arrow slits and timber shutters. Stone horseshoe through-gateway and geometric plaster diamonds express the monumental gate vocabulary without reproducing religious inscriptions. The sebka-inspired relief is an abstract geometric adaptation, not an archaeological replica. The silhouette is a compact defensive citadel rather than an ordinary single Keep or ceremonial Wonder.

Closest preserved stock comparator: installed Garrison0.1.4 read-only Abbasid keep, `art/civilizations/abbasids/structures/keep/abb_keep_control_age03/abb_keep_control_age03.rgm`. Decoded geometry is copied intact into this task's research cache and rebuilt untouched in a separate reference Blend. Original final geometry fits the specific8×8 landmark site and original hollow royal court better than rescaling the much larger stock keep. Donor topology/material/selector/anchor data remain a reference, not a qualified inherited custom binding.

## Delivery and limits

One packed age-IV Blend, mesh-only open-state FBX, five same-UV maps and red-only owner mask; cumulative constructionIII reuse manifest. Visible neutral tower standards and hall stripes carry `ber_owner_mask=1`; all other surfaces0. This is the source annotation/mask contract only; native player colour is blocked by the shared static structure shader/export contract. No native-ready claim.

Door leaf hinge transforms and closed/open Actions are retained in Blend and state manifest. FBX is static open-state geometry; native playback is unqualified. Walk faces, actual through aperture and empty court are source geometry; gameplay site impass still covers8×8. This landmark must not be treated as a native passable gate merely because its visual gateway is hollow. Preserve gameplay, stock wonder attachments and child effects until separately mapped. Native LOD, fire/damage/death, construction selectors, skin/owner shader, placement/rotation/scale, walk surfaces, and age-up gameplay remain future gates. No production assets, GUIDs, archive, or distributable changed.

History: iteration1 authored the courtyard citadel; visual/interface review caught wall-walk ends stopping short of the battered faces and planar hanging cloth not following taper. Iteration2 extends walk/curtain ends into the towers and seats hanging standards to the slope. Saved-source audit independently measures actual tower-face overlap, banner-to-slope penetration, both gate Action states, owner-map samples and FBX readback.
