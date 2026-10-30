# Current source and rebuild workflow

## Retained source

`source/scar` is maintained independent-civilization SCAR.
`source/tables/attrib/**/*.rgd.json` is a lossless typed representation of the
actual tested native records: variants, keys/hashes, types, IDs and opaque header
chunks. Every unchanged table reproduces its original bytes. This is **not
Attribute Editor XML** and does not recreate inheritance/list-edit history.
Edit existing typed values while retaining identities. Allocate new instances
through the current Attribute Editor or Garrison derive/cook route.

`source/resources` contains current localization/UI resources. Existing English
UCS IDs remain. `source/presentation/berbers.png` is unchanged original Villager
artwork. `source/baseline-members.json` inventories tested trial.3;
`source/release-changes.json` is the build-enforced presentation allowlist.

`inputs/native` contains the composed native art/audio, metadata, speech
suppression and 22 UV fixes as whole files. `inputs/native-manifest.json` pins
their sizes and hashes. `authoring/original` and `authoring/external` contain all
10,726 retained editable masters, textures, recordings, recipes and donor inputs.
`source/master-index.json` records original provenance/hashes. Historical paths
and former pack names in that index describe the import, not download requirements.
Only oversized donor files use Git LFS. There are no separate developer packs.

## Build

Use Python 3.13 and Garrison extension/core 0.1.8. The compiled SDK needs that
Python ABI. Set GARRISON_EXTENSION if its installation differs. Run:

```powershell
python tools/inputs.py verify
python tools/build.py --output output/current
```

Choose a fresh output directory. The build encodes tables, collects current
SCAR/UI and native inputs, then runs supported civilization validate/build.
It checks final owner, native metadata, CRC/SHA1, all TOCs/readback hashes,
declaration hashes, Boolean false root, preserved art/audio and exact allowlist.
It packages one import ZIP and verifies ZIP CRC and packaged archive SHA-256.
No original project, trial output or editable masters participates.

A real native UI cook supplied the original Villager texture. Normal builds
reuse that verified texture. `tools/cook_flag.py` recreates it from the original
PNG with a disposable supported native authoring project.

For future changes, review/update the allowlist explicitly. New models or audio
require export/cook and an intentional native-input update. Editing a master
does not activate its shipped resource. Do not replace composed resources with a
raw old-project cook.

## Editable masters

Masters are already in `authoring/` after cloning. GitHub Desktop handles Git
LFS automatically; command-line Git requires Git LFS installed before cloning.
On Windows use a short checkout path and enable `git config --global core.longpaths true`
if your Git reports long filenames. No extraction or per-part fetching is required.

The original recipes retain historical drive paths as provenance. They are not
the current build entrypoint. Adapt a historical recipe to the current checkout
when reusing it; never run it against the old project. External Blender image paths are stored relative to each checked-out master.
To audit them, run background Blender with
`--background --factory-startup --python tools/relocate_blends.py -- --check`.
The tool opens only the indexed masters with embedded Python disabled; it does
not access the unrelated live Blender scene.

Original editor XML and project files are retained as authoring provenance, with
the original replacement-mod identity. They are not the independent build entry.
Use the current typed tables/private identity map when integrating fresh cooked
changes. Native inputs are authoritative for existing composed resources.

## Evidence boundary

The owner reports trial.3 loaded and worked, with detailed coverage unspecified.
This release changes presentation only. Clean-source reconstruction, native image
cook, master restoration, import and gameplay remain distinct gates. Native flag
layout, all abilities/ages, AI, second matches, save/load, multiplayer and
frame-time/VRAM require their own acceptance.
