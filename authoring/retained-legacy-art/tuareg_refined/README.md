# Refined Tuareg trial

Editable source: Tuareg_Refined_Ages_I_IV.blend. The four stock Abbasid anatomy references stay in `Reference originals - unchanged`; derived bodies retain their rig weights and the native 48-bone hierarchy. New wraps, veils, clothing and equipment use explicit authored geometry. `build_sources.py` and `bake_atlas.py` reproduce the scene, unique UV atlases, PBR sources and Garrison exports. `build_garrison.py` builds through current installed public routes; no prototype fingerprint/admission changes.

Quality direction: stock AoE4 proportions/surface detail, Tuareg veiled headwear and indigo/grey desert cloth. Age III-IV retain appropriate source protection with cloth overlays. Medieval regional context and later Tuareg design references are separated in the earlier art README; this remains an artistic interpretation.

Spear: 4.375m overall, exactly +75% from 2.50m. Extend shaft only on the blade side by 1.875m; preserve head geometry, thickness, grip and butt position. This is visual length, not changed attack reach or damage.

Shield: retain 1.15m shell height and native hand origin. Refit body lower relative to grip; mounts seat near the upper part of the shield. Check pose measurements in output/tuareg_refined_trial/shield-fit.json and actual game results separately.

Animations: stock movement and combat remain. Native Q selector/control is preserved byte-for-byte; new logs proved it stays asserted during movement. A private interruptible graph or phase-preserving arm layer is still unqualified in the installed 0.1.3 tooling. This version does not claim an instant-moving Q fix.

Build-path qualification: the native texture writer failed with `StringToPtrUTF8: Buffer too small` at the long workspace path. A byte-identical copy of the Garrison project at `E:/trf1` cooked successfully with no source changes. `build_garrison.py` accepts `TUAREG_BUILD_PROJECT` to select a short isolated build copy; final integration uses the successful project recorded in `garrison-art-build.json`. Keep that copy for reproducible cook diagnostics. The long-path project and editable Blender sources remain here.
