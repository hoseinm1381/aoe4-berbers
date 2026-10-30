# Revised original Imperial sources

Authoritative export: `export_lod0_v2/`. Root visually cleared the revised native-grain previews. Earlier `export_lod0/`, `export_lod0_ready/` and incomplete `export_lod0_final/` are superseded disposable output, not current inputs.

Packed editable source: `<kind>_040_original.blend`. Geometry is original procedural topology, no donor shell. Six solid orthographic views and `textured_gamecamera.png` are current. `geometry-audit.json` records actual per-mesh bounds, stages, UV layers, manifold topology and signed volumes. `final-source-validation.json` contains measured interfaces, stage sets and current hashes. Earlier source-checks are superseded by these audits.

Native material inputs are retained losslessly as PNG in `../fez/native_texture_inputs/`; provenance.json identifies native texture names, original DDS SHA256 and decoded cache manifest. No external cache is required to regenerate this atlas. Original DDS is only provenance. `research/berber_040_fez_native_atlas.py` builds both albedo atlases and low strength normals from those retained PNGs. The original geometric zellij texture is explicitly procedural; other surface grain comes from those native PNGs. Fez/references retains inspected Bou Inania and Bab Agnaou photographs with URL/hash/use records.

Reproduction: run the atlas script with bundled Python/Pillow/numpy; run research/berber_040_fez_build.py or berber_040_grand_keep_build.py through isolated background Blender5.2. The runner writes packed editable sources and reviews. Run research/berber_040_fez_export_final.py -- fez or -- grand_keep for native export; choose a fresh export path when revising because Garrison preserves existing export directories. --audit before the kind audits without exporting. Then run research/berber_040_fez_validate_final.py.

Source mesh closure, outward signed volumes, real masonry portal clearance and stage metadata were checked. Grand Keep has seated cedar door leaves inside the masonry opening. All six stage thresholds [0,20,40,60,80,100] occur in native building JSON. Native flags are supplied by integration using flag-transform.json; source poles are present.

Single LOD0 only. Native actor/marker/lifecycle/owner flag integration remains separate. Source visual approval/export does not establish native-match appearance, team colour, construction, damage or destruction.
