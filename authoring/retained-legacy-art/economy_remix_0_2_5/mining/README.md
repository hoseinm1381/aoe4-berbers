# Berber mining camp material remix 0.2.5

The donor is AoE4's common mining-camp native visual family, consumed by the English tier-I attachment currently used by Berber's Malian mining actor. The official tier uses `art/stamps/civ_common/com_mining_camp` in default and xp3; campaign adds the stock wood-house construction stamp. Root integration clones the native stamp and preserves its components and transforms. There is no authored age progression: the native camp remains consistent through Ages I–IV.

The three decoded source models are the combined assembly, standalone crane and standalone furnace. Do not add standalone components to the combined assembly unless the native consuming stamp uses them: doing so would duplicate equipment. The original-to-private map is recorded in `output/berber_update_0_2_5/authors/mining/integration.json` after the fresh cook. Only referenced payload entries should enter the final release.

Warm ochre earthen/plaster and muted roof surfaces complement the accepted house; timber remains distinct, as do stone loads. Recolouring preserves source luminance detail and alpha. Native team-colour slot 5, all masks, normal/roughness maps, charred maps, UVs, topology, selectors, hidden construction/destruction fragments and LODs remain unchanged. No primitive or replacement geometry was generated.

Native scale is retained at 1.0; this donor never used the older 0.46 small-house authoring reference. Root preserves native stamp scale and gameplay footprint. Bounds that include every hidden damage fragment are not healthy-building dimensions; inspect the visible assembly separately. Ground contact and native part connections remain stock; destructive visual behaviour and player colours need the user game test.

Untouched and editable remix `.blend` sources retain the complete decoded native family. Preview-only PNG projections are pixel-equivalent decodes of the stock DDS maps to avoid packed-DDS GPU reload warnings in Blender. They do not replace native material dependencies. Private cooked albedo maps are generated from the repaint recipe; per-material native rewrites avoid slot collisions.

Reproduction scripts: `research/economy_025_mining_prepare.py`, `research/economy_025_mining_blender.py`, `research/economy_025_mining_compose.py`. Run the Blender script in its own hidden factory-startup GUI process, not the user's live file. Do not recook concurrently with another author's Essence Editor build.

Evidence is source and native cook/package evidence. Native game acceptance remains pending; root package test instructions cover construction, near/far views, age transitions, two colours, destruction, villager movement and gold/stone drop-off.
