# Berbers for Age of Empires IV

Independent Garrison civilization by **hosein81 and marcokistan**.

**Players:** [download Berbers-Garrison-0.1.0.zip](https://github.com/hoseinm1381/aoe4-berbers/releases/download/v0.1.0/Berbers-Garrison-0.1.0.zip).
Import it in Garrison client 0.1.9 or newer. Choose **Berbers**, **Standard**,
**Tuning Pack: None**. See [player instructions](START-HERE.md) and [credits](CREDITS.md).

**Developers:** clone this repository with GitHub Desktop, or Git with Git LFS
installed. Gameplay, models, textures, sound, music, recipes and native build
inputs are all in this repository. There are no separate sound packs, release
input downloads, submodules or additional source repositories.

```powershell
git clone https://github.com/hoseinm1381/aoe4-berbers.git
cd aoe4-berbers
python tools/inputs.py verify
python tools/build.py --output output/current
```

Use Python 3.13 and Garrison authoring extension/core 0.1.8 for the build.
Set `GARRISON_EXTENSION` if the extension is installed elsewhere.
Large donor files use Git LFS and arrive with a normal LFS-enabled clone.

Edit current gameplay in `source/scar` and `source/tables`, UI/localization in
`source/resources`, and art/audio in `authoring/original` and `authoring/external`.
`inputs/native` preserves the composed runtime resources required to rebuild.
[Development details](docs/DEVELOPMENT.md) explain formats and art integration.
This repository's `main` branch belongs only to Berbers.

The owner confirmed trial.3 loaded and worked on 2026-10-30. Version 0.1.0 retains
that gameplay and uses the original Villager banner for civilization presentation.
The new flag layout needs an in-game visual retest. Broader mechanics, AI,
repeated matches, save/load, multiplayer and performance remain separate tests.

Stable owner: `5fe8767c-ca3a-4e64-9e20-c9527cf014ec`; bundle/audio key: `berbers`.
