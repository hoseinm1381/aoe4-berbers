# Bounded skinned banner alternative review

Reviewed 2026-10-13. Result: **no independently supported building attachment and construction-stage contract found**. This leaves native building player colour pending while other building source work can continue.

The proposed mesh itself has a documented authoring route: use the unchanged qualified English spearman prototype, rigid-weight every vertex to one existing bone, one UV atlas/material, and explicit unit pattern PNG red channel. Installed `guide/rig-and-animation.html` describes Rigid to One Bone; `unit_export.py` exports mesh plus armature and preserves the qualified rig records. Such a model can use the existing unit shader export lane. Building it would only demonstrate skinned model encoding, not its installation on a building.

The integration gate is missing. Installed attachment replacement is documented for the prototype's existing combat slots (spear, spearwall, charge, torch). It preserves their inherited unit attachment rules. Compatible model-only replacements in the existing Tuareg workflow retain a compatible target's own animator. Neither fixture establishes that a construction building can provide the unchanged 48-bone spearman bind palette, nor a separately animating child skinned visual with inherited building owner and no actor spawn.

Installed `building_panel.export_building` creates evaluated mesh copies, removes the armature relationship and exports FBX with `object_types={"MESH"}`. Its recipe owns one static model/atlas and construction selectors within that model. The queried compiled `building_project.selectors` maps parts to `sel_construct_00`, `sel_construct_20`, `sel_construct_40`, `sel_construct_60`, `sel_construct_80`, `sel_healthy`. A probe row with `banner` first visible at 80 is added to the 80 and healthy selectors of that same model. It does not return a child attachment resource or child visibility condition. Adding a separately built unit model would therefore need a new verified bridge from building construction progress to the child visual's visibility.

The existing Tent stamp points to the static model. Simply adding skinned geometry to its FBX is not supported by its exporter, and replacing a stamp with a unit model does not preserve its construction selectors. Spawning an invisible/unit actor beside the building would introduce gameplay/entity lifecycle and violates this alternative's scope, so it was not attempted.

Required independently verified contract before coding this route:

1. A native visual-only skinned attachment resource, attached to the building owner without entity/squad spawn.
2. A valid independent palette/animator or compatible host palette for the exact stock 48-bone rig; root weighting alone does not supply runtime matrices.
3. A construction-condition binding that hides/shows that child at its intended stage and preserves healthy/damage/cancel/destroy cleanup and LOD behavior.
4. An isolated cook/readback demonstrating those references and selectors, followed by a two-owner native test.

No new Blender file, model cook, attachment blueprint, unit actor, production write, or ZIP was created for this alternative because the documented/export-qualified integration gate was not met. This is an installed-route limitation finding, not proof that the engine cannot support such an attachment.
