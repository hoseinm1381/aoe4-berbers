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

`inputs/manifest.json` binds four large release assets by name, bytes and SHA-256.
Native inputs preserve final composed art/audio, metadata, speech suppression and
22 UV fixes. Editable art/audio/recipe packs are separate. `source/master-index.json`
maps original authoring layouts to content-addressed blobs; identical bytes are
stored once. Historical paths in the index are provenance, not build dependencies.

## Build

Use Python 3.13 and Garrison extension/core 0.1.8. The compiled SDK needs that
Python ABI. Set GARRISON_EXTENSION if its installation differs. Run:

```powershell
python tools/inputs.py fetch
python tools/build.py --output output/current
```

Choose a fresh output directory. The build encodes tables, collects current
SCAR/UI and native inputs, then runs supported civilization validate/build.
It checks final owner, native metadata, CRC/SHA1, all TOCs/readback hashes,
declaration hashes, Boolean false root, preserved art/audio and exact allowlist.
It packages one import ZIP and verifies ZIP CRC and packaged archive SHA-256.
No original project, trial output or editable master restoration participates.

A real native UI cook supplied the original Villager texture. Normal builds
reuse that verified texture. `tools/cook_flag.py` recreates it from the original
PNG with a disposable supported native authoring project.

For future changes, review/update the allowlist explicitly. New models or audio
require export/cook and an intentional native-input-pack update. Editing a master
does not activate its shipped resource. Do not replace composed resources with a
raw old-project cook.

## Editable masters

```powershell
python tools/inputs.py restore-masters --destination authoring
```

This verifies packs/blobs and restores relative layouts below authoring/original
and authoring/external. Text recipes are relocated from historical absolute roots
to these copies; packed originals stay exact. Edited existing files are preserved.
Blender binaries retain original image paths until background Blender runs
`tools/relocate_blends.py` on restored copies. It saves only those restored files.
All retained blends were inspected for external image dependencies. That check
is not a full native re-export/cook qualification of every original model.

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
