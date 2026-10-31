# Berber mill 0.2.5 sources

Material-only modification of installed Malian `mal_gristmill_control_age01`.
The native two-mesh main/roof assembly, all 23,150 vertices and 23,458 faces,
UVs, normals, geometry buffers and placement orientation are retained.
Native dimensions and transforms are proved equal in the author's
`dimension-validation.json`; native scale stays 1.0 because this donor never
used the earlier tiny primitive 2x2 reference.

`UNTOUCHED_Malian_Mill_Age1.blend` preserves the decoded donor. The separate
`Berber_Mill_Age1_0_2_5.blend` contains packed recoloured source textures.
Twelve albedo layers now read as warm earth/plaster, darker wood and subdued
woven/thatch surfaces. Texture relief remains recognizable. Native team/debug
layer, packed normal/PBR, masks and charred layers are preserved without baking
a fixed owner colour. Native GMat roots are rewritten separately to prevent
repeated layer names from overwriting the roof with main-wall material.

The official mill has one healthy model/tier serving Ages I–IV. Root integration
privately clones the native healthy stamp and attachment tier, preserving its
component transforms and state selectors. Existing stock construction
`const_house_wood_d` and destruction `dest_house_stone_d` stamps are retained.
No gameplay, placement or pathfinding changes are supplied by this author.

Author evidence and payload: `output/berber_update_0_2_5/authors/mill/`.
Eight previews include before/after gameplay angle and solid six-side views.
Fresh cook, payload manifest and dimension/source validation are distinct from
native game acceptance, which remains pending the user's test.
