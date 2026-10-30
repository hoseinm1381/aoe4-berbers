# Standard Berber Mosque, Ages III and IV

## Reference and scope

The form is a compact game interpretation of Moroccan courtyard mosques, not a reconstruction of a specific monument. The [UNESCO Marrakesh record](https://whc.unesco.org/en/list/331/) documents the Koutoubiya mosque and its monumental minaret among the city's medieval architectural features, and names lime plaster, carved wood and zellige among continuing local crafts. The older [project source study](buildings_batch/mosque/README.md) records the Ministry of Habous account of Moroccan hypostyle plans and square minarets. These cues are reduced for the existing 8×8 game footprint.

## Donor anatomy and remix

Both variants retain their own decoded Abbasid monastery donor geometry, native material graph, UVs, collection assignments, and complete triangle/index topology. The earlier original procedural Mosque source remains a backup and is not part of the native geometry.

| Part | Donor feature | Age III change | Age IV change |
| --- | --- | --- | --- |
| Courtyard | Rectangular front sahn and gate | Plan compacted to about 8.7×8.6 m visual bounds, including overhang | About 8.9×8.7 m visual bounds |
| Prayer hall | Central onion dome with four small domelets | Donor roof loops reshaped to a low four-sided hip over a reduced hall | Higher, more developed central hip and stronger roof-course relief |
| Minarets | Twin front towers, plus two extra Age IV towers | One offset square tower retained; opposite crown becomes a low entry pier | Same offset tower grows taller; three other crowns reduced to entry piers |
| Entrance | Front portal and courtyard route | Door and ground threshold remain from donor | Same route retained with richer stock Age IV facade geometry |

The large masses change through native donor vertex positions, not through a detached decorative asset. No new static kit is required. The donor's existing curtain walls, prayer-hall shell, pointed openings and materials remain recognizable as the structural substrate. The roof and tower transforms are continuous from the unmodified lower facade zone at z≤2.85 m. Because the native vertex positions are transformed identically across all material groups, their shared contacts remain coincident. Native ground-contact z values, origin, UV indices, opaque chunks, and owner-colour material slots are preserved.

## Evidence and remaining gates

`art/building_remix_0_3_1/mosque/source-validation.json` and the per-age geometry reports record hashes, 280,044/358,032 donor vertices, transformed counts, bounds, contact and native chunk checks. Editable `.blend` files and solid isometric/front/back/left/right/top/bottom previews are alongside the recipe. The final stamp bindings are governed by `output/berber_update_0_3_1/binding-specs.json` and remain for the release integrator's serialized Garrison/Content Editor cook. Native construction, damage, ruin, unit exit, two-player colour and match rendering still require the release and in-game gates.
