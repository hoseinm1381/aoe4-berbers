# Berbers for Age of Empires IV

Independent Garrison civilization by **hosein81 and marcokistan**. Select
**Berbers**, **Standard**, **Tuning Pack: None** with Garrison client 0.1.9 or newer.

[Download the playable ZIP and editable input packs](https://github.com/hoseinm1381/aoe4-berbers/releases/tag/v0.1.0).
Only `Berbers-Garrison-0.1.0.zip` is needed to play. See [START-HERE.md](START-HERE.md)
and [original credits](CREDITS.md).

The owner confirmed trial.3 loaded and worked on 2026-10-30. Version 0.1.0 retains
that gameplay and replaces civilization presentation with the original Villager
banner. The new flag presentation needs an in-game visual retest. Detailed
mechanics, AI, repeated matches, save/load, multiplayer and performance are not
independently certified by that brief acceptance.

## Develop

The repository contains current SCAR, editable typed native attribute tables,
localization/UI inputs, tools, input manifests and compact evidence. Large native
resources and editable art/audio masters are hash-checked release assets.

1. Clone this repository. Install Garrison authoring extension/core 0.1.8 and Python 3.13.
2. Run `python tools/inputs.py fetch` to download the exact four input packs.
3. Run `python tools/build.py --output output/current` from the repository.
4. To edit geometry, textures or recordings, run `python tools/inputs.py restore-masters --destination authoring`.

The build reads this repository and its native-input pack, plus installed tools.
It does not read the original E:/F: project or trial output. Set
`GARRISON_EXTENSION` if the extension is installed elsewhere.

[Development and art workflow](docs/DEVELOPMENT.md) explains source formats,
relocation and validation limits. Stable owner:
`5fe8767c-ca3a-4e64-9e20-c9527cf014ec`; bundle/audio key: `berbers`.
