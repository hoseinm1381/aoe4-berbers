# Original Tuareg art trial

Editable source: `Tuareg_Original_Ages_I_IV.blend`. Rebuild with Blender 5.2.2 `--background --factory-startup --python build_sources.py`, then run `build_garrison.py` through the configured Garrison toolchain. `mesh_runner.py` owns construction; `build_sources.py` owns the anatomy, weights, atlas and age recipes. Textures are PNGs, also packed in the blend. `REFERENCE ORIGINALS` retains the stock Abbasid reference. No installed game files are edited.

All clothing, veils/headwraps, hide shield and spear surfaces are newly constructed. The stock exposed hands/feet and native 48-bone hierarchy remain. Approximate human height 1.90 m; shield height 1.15 m; spear length 2.50 m. The shield has a waisted outline, leather rim, central reinforcement and original ochre motifs; spear has a leaf head, socket, grip and butt ferrule. Owner-colour mask is on the body waist stripe. Skeletal LODs fold to 48/32/26 through Garrison; geometry is not decimated by that operation.

Age I: muted grey cloth and simple wraps. II: indigo layers and leather carrier. III: mail surface and indigo tabard. IV: darker wraps, refined trim and fittings. Keep the light infantry silhouette.

Historical framing: this is an artistic Saharan Tuareg interpretation. Peabody's [Tuareg collection](https://peabody.harvard.edu/galleries/imazighen-tuareg-nomads-sahara) supports the leather agher shield, veiled face and indigo clothing direction, but its collected objects are later references, not proof of exact medieval clothing. The [Met's Almoravid/Almohad overview](https://www.metmuseum.org/essays/the-art-of-the-almoravid-and-almohad-periods-ca-1062-1269) provides medieval regional context, not a specific Tuareg spearman reconstruction. Mail progression and motifs here are design choices.

Animation limitation: these models use inherited native motion. The current Garrison spearman exporter only admits one idle replacement. No qualified private interruptible moving graph, phase-preserving arm layer, or broad animation writer was established. The new controller removes force.1's ineffective global leaf requests, persists its owned guard selector and records movement/stop edges. It does not claim a custom complete animation set or instant moving Q.

Native acceptance remains pending for all ages, action states, LODs, colour masks, skinning/contacts, gameplay and Q response. See the versioned trial's TEST-TRIAL.txt.
