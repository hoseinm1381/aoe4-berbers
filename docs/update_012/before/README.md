# Berbers for Age of Empires IV

Independent Garrison civilization by **hosein81 and marcokistan**.

**Players:** the local 0.1.1 candidate is `release/Berbers-Garrison-0.1.1.zip`. It has not been published. The previous tested 0.1.0 ZIP remains in `archives/accepted_0.1.0/`.
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
python -B tools/build.py --replace-current
```

Use Python 3.13 and Garrison authoring extension/core 0.1.8 for the build.
Set `GARRISON_EXTENSION` if the extension is installed elsewhere.
Large donor files use Git LFS and arrive with a normal LFS-enabled clone.

Edit current gameplay in `source/scar` and `source/tables`, UI/localization in
`source/resources`, and art/audio in `authoring/original` and `authoring/external`.
`inputs/native` preserves the composed runtime resources required to rebuild.
[Development details](docs/DEVELOPMENT.md) explain formats and art integration.
This repository's `main` branch belongs only to Berbers.

The owner confirmed trial.3 loaded and worked on 2026-10-30. The previous version 0.1.0 retained
that gameplay and uses the original Villager banner for civilization presentation.
The new flag layout needs an in-game visual retest. Broader mechanics, AI,
repeated matches, save/load, multiplayer and performance remain separate tests.

Stable owner: `5fe8767c-ca3a-4e64-9e20-c9527cf014ec`; bundle/audio key: `berbers`.

Current 0.1.1 adds the requested client card, HD loading art and native Codex bounds repair. See docs/UPDATE_011.md. Native retest and separate manual push approval are pending.
