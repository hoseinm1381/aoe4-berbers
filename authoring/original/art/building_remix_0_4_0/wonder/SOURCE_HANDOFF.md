# Wonder 040 source handoff

Original Koutoubia inspired geometry, not donor geometry. Rebuild from project root:

1. `python research/berber_040_wonder_atlas.py` regenerates native-grain atlas from retained Fez native_texture_inputs (provenance recorded).
2. `E:/Blender5.2/blender.exe --background --factory-startup --python research/berber_040_wonder_blockout.py` regenerates clean original blockout.
3. `E:/Blender5.2/blender.exe --background --factory-startup --python research/berber_040_wonder_build.py` builds details, six solid views, textured camera, packed blend and export_lod0. Uses explicit compiled garrison_shared alias to avoid namespace directory ambiguity.
4. `E:/Blender5.2/blender.exe --background --factory-startup --python research/berber_040_wonder_audit.py` verifies evaluated bounds, UVs, signed volumes, manifold edges and hashes.

Review: koutoubia_final_gamecamera.png. Audit: geometry-audit.json. Source: Berber_Koutoubia_Wonder_040.blend. Export: export_lod0/model.fbx + building.json + materials. Flag: flag-transform.json.

113 original mesh parts; zero nonmanifold edges. Evaluated bounds 14.2 x 14.0 x 14.6 m local; actor scaling 150% is integration responsibility. Source-validation contact measurements are recipe anchors, not native lifecycle proof. Current packed blend/export passed Garrison source preflight. Native solo game appearance and lifecycle remain unverified. Integrator owns stock owner cloth, markers/RGO/lifecycle, shared cook and release cleanup. Root source visual clearance pending.
`nNative texture compatibility correction: generator resamples complete normalized five-strip atlas to2048x1024. Allfour exported maps verified2048x1024 by texture-power-of-two-check.json. Existing failed2560x1024 export preserved in export_failed_npot_evidence pending verified release cleanup. Rebuild requires archiving/removing prior export_lod0 first because Garrison refuses overwrite. Geometry remains113parts, zero nonmanifold.
