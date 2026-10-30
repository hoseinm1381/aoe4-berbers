# Berbers — independent Garrison civilization

Current local candidate: **0.1.2**, in `release/Berbers-Garrison-0.1.2.zip`.
Native in-game acceptance is pending. The owner authorized the 2026-10-31
02:15 AM source-only GitHub upload. This repository contains complete developer
inputs; the current player ZIP remains local while acceptance is pending.
No new GitHub Release, tag or installation is included. See
[source publication scope](docs/SOURCE_PUBLICATION.md).

0.1.2 populates native Unique Units/Technologies, explains the actual civilization
mechanics, corrects research ages and spaces tech-tree icons at the native pitch.
Civilization labels are plural and the selector uses the existing flag fallback.
World gameplay, stable IDs and HD loading/art resources are preserved. Berber
audio is smaller; existing compact Vietnamese voices retain their current codec.

Players need the single ZIP. Follow [the test instructions](START-HERE.md).
Developers use this complete repository: editable art/rigs/textures, original
audio, native inputs, typed whole-file attribute source and recipes live here.
There are no separate required source/art/sound downloads.

- [0.1.2 changes and evidence](docs/UPDATE_012.md)
- [Native package verification](docs/BUILD_VERIFICATION.json)
- [Source regressions](docs/SOURCE_TESTS.json)
- [Size measurements](docs/SIZE_REPORT.json)
- [Developer workflow](docs/DEVELOPMENT.md)
- [Design boundaries](docs/DESIGN.md)
- [Release policy](RELEASES.md)

Rebuild locally with Python 3.13 and the
installed Garrison 0.1.8 authoring/core plus Content Editor:

```text
python -B tools/inputs.py verify
python -B tools/build.py --replace-current
```

Native staging uses one temporary `garrison-independent-builds/<owner>/current`
directory per civilization to avoid copying thousands of tiny files twice on
F: exFAT. Failed diagnostics are protected. Verified staging may be cleaned only
after checking the final ZIP and retained inputs. The current source workspace
does not change. Current stock prerequisite evidence is retained under `source/`.

The tested 0.1.1 ZIP remains under `archives/tested_0.1.1/`; its exact native Codex
is a hashed regression fixture. Source/UI snapshots are in `docs/update_012/before/`.
The earlier standalone split came from accepted combined Garrison 1.1.0 commit
`d58326f447b6444332e9a15c42c7496d57fb26be`. Normal/combined sources are preserved.

Credits: **hosein81, marcokistan, Karyu, lammet and ForsakenCryz**.

After verifying a build, preview staging retirement with `python tools/cleanup_staging.py`; apply it with `--apply`. The tool preserves player ZIPs, source, masters, native inputs and receipts.
