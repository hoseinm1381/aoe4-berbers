# Berber house source family — 2026-10-13

Design evidence: UNESCO's [Ksar of Ait-Ben-Haddou](https://whc.unesco.org/en/list/444/) describes modest houses and larger dwellings, rammed earth/adobe/clay brick, timber and geometric upper-wall motifs. This family uses those earthen massing and restrained relief cues with an open courtyard, flat roof decks, projecting timber drains, recessed wooden shutters and horseshoe doorway. It is an original game-scale interpretation, not a reconstruction of a specific medieval house. The four-age limework/joinery progression is an art direction choice, not a historical dating claim.

Live project age evidence: `assets/attrib/instances/ebps/races/malian/buildings/building_house_mal.xml` has unrestricted first tier `tier1_house_a_mal` (lines 660-667), Feudal (686), Castle (705) and Imperial (724) attachment requirements. Ages I–IV are therefore authored. Inventory ID `building.house` points to that XML.

Stock donor evidence: installed Garrison library catalog resolves Abbasid house control A age01–04 from ArtHigh.sga/ArtAbbasids.sga. The previously decoded age-I geometry was read from `research/buildings_batch/player_colour/stock-house/a9a752db305fef70848f/decoded-static.json`, then copied unchanged into task-owned `donor_geometry.json`. Its source SHA and decoded positions/triangles remain in that copy. `UNTouched_Abbasid_Age1_Reference.blend` retains the decoded stock geometry separately, without material reconstruction. No donor geometry is reused in final house models; the donor establishes native game proportions/construction context.

Source anatomy: 3.2×3.0 four-wing dwelling on 3.65×3.4 foundation, open court, distinct habitable wings, roof parapets, functional-looking drains, real boolean opening/recesses, fitted shutters and door, anchored courtyard canopy, clay storage jars. Age I plain adobe/textile; II shallow diamond relief/stone corners; III lime walls, roof storage and ladder; IV improved lime corner courses and carved doorway trim. The same footprint remains across ages.

Build with task-owned hidden GUI Blender, not background:

`E:/Blender5.2/blender.exe --factory-startup --offline-mode -noaudio --python <absolute-path>/art/buildings/house/build_house.py`

Outputs: per-age packed `.blend`, FBX, explicit cumulative construction stage manifests, shared UV atlas albedo and red-only owner pattern PNG, per-age preview and six-side views, machine-readable geometry/contact validation. Flat hard surfaces; no decorative bevel modifiers. Per-face UVs occupy material tiles in the shared atlas; intentional same-material overlap is appropriate for this repeating palette texture, not a unique lightmap unwrap.

Integration limits: custom properties and stage manifests are source inputs. FBX contains final geometry; the Garrison construction recipe has not been exported or cooked. Shared `PLAYER_COLOUR_CONTRACT.md` currently blocks the static native shader lane. Neutral cloth source zones are annotated `ber_owner_mask=1`; masonry/timber/clay zones are 0. The saved red-only pattern uses exactly the albedo UV layout. This is mandatory authored input, not native owner-colour proof. Native shader integration, construction selector activation, LODs, destruction/burn state, lobby/match scale and two-owner colour acceptance remain pending. No production files or distributable archive changed.
