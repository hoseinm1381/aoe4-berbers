# Building owner-colour contract — 2026-10-13

Status: **authored mask inputs available; static native shader route blocked; game acceptance pending**.

Use a saved RGB PNG with the same UV layout as albedo. Red 0 preserves the base surface; red 255 marks the owner-colour region. Keep green and blue 0 for buildings (the documented unit shader interprets them as skin and hair). Keep wood, masonry, ropes, pottery and decorative badges outside the red mask. Author the intended stripes/cloth in a neutral surface colour; a painted blue texture is a fixed preview, not native owner colour.

For Blender source materials record `ber_owner_mask` = 1 on intended owner-colour zones, 0 elsewhere. This is an authoring annotation only. Bake this annotation to a red-only pattern PNG independently of albedo; save all images. Neither that property nor a preview node is exported automatically by Garrison's static/building workflow.

Known native unit input: `<material type="shader" source="unit">` with `albedoTexture`, `normalMap`, `metalTex`, `roughnessTex`, `patternTex`. Installed Garrison 0.1.4 unit build accepts explicit pattern source PNG. **Do not assign this contract directly to an unrigged building and claim support.**

Current static construction export emits `source="object"` and four maps only. Its `building.json` has no pattern input; saved pattern PNGs are omitted from generated materials. An isolated unchanged Tent age-1 FBX with `source="unit"` + `patternTex` failed the prepared Essence RRGeometry burner: `Couldn't locate effect with name 'unit_collection'`, followed by `Failed to find effect for material 'berber_tent_age1_atlas baked atlas_collection'`. Exit -6, no qualified model output. The cooker chooses collection geometry for static meshes and cannot find a matching unit collection effect.

Stock Abbasid age-I house decoded read-only from installed archives uses `structure` material and `structure_collection` geometry. It is a layered material/structure collection contract, not this static four-map object recipe. That fixture supplies no directly named owner/pattern texture parameter in its decoded structure material. This observation does not prove that all native structure shaders lack owner colour.

Pending native routes: qualify a genuine structure shader/stream export with documented owner-mask semantics, or a supported rigged owner-colour attachment with correct building construction-stage activation. Both require separate source/export and small cook/readback validation before production use.

The bounded rigged banner alternative was also reviewed. Rigid root weighting on the unchanged spearman rig has a documented unit authoring lane, but no independently supported building child-visual palette/owner/selector binding was found. The building exporter explicitly emits meshes only and owns same-model stage selectors; prototype attachment replacement covers combat slots. See `research/buildings_batch/player_colour/SKINNED_ATTACHMENT_ALTERNATIVE.md` for the precise missing integration contract. Continue authoring other building geometry and masks while this qualification remains open.

Acceptance gate: two buildings owned by players with distinctly different colours in the same solo match must display the correct stripe colour with neutral trim preserved; repeat at all required construction stages and ages, inspect LODs, orientation and scale. Cook or viewport preview alone does not pass this gate.

Evidence lives in `research/buildings_batch/player_colour/` and `output/buildings_batch/player_colour/`. Accepted Tribal Tent iteration 003 and production mod assets were not modified. Iteration 004 was not created because no supported building native owner-colour contract was found.
