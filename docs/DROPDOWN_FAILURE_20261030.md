# Berber dropdown failure: confirmed native metadata omission

Date: 2026-10-30. Trial.1 failed the owner's in-game dropdown test.
The working comparison is the installed official-catalog Persians 0.1.0, SGA
SHA-256 `1e999c7220ab7a3b7868f3d48cfa66e3bce36abd068410609f1ff1b6745fc384`.
Its installed group identifies source
`https://raw.githubusercontent.com/AOE-Garrison/garrison-mod-catalog/main/catalog-v2.json`.

## Confirmed cause

AoE4 `warnings.log`, line 395, at 02:17:11:

> Error loading mod pack '.../berbers/berbers.sga': missing metadata.

The preceding ARC line identifies the exact trial owner and 769,805,910-byte
archive; it is not a different/older Berber mod. Garrison's installed digest
also matches the delivered trial.1 archive. The game scanned it but rejected it
before creating the native mod owner/race.

| Native/package surface | Working Persia | Berber trial.1 |
| --- | --- | --- |
| `info` TOC | Present | Absent |
| `mod.bin` in `info` (native compiled mod metadata) | Present | **Missing** |
| `mod.rrtex` in `info` (native mod image) | Present | Missing |
| Additive root Boolean false / own header ID | Present/correct | Present/correct |
| Hashed civilization declaration and one flat RaceBP | Present | Present |
| Visible multiplayer race / base-game eligibility | Enabled | Same relevant settings |
| Included in Garrison native provider request | Yes | Yes |
| Native resource mount, owner retention and race admission | Recorded | **No event** |

`garrison.json` and `garrison/civilizations.json` serve Garrison. They do not
replace AoE4's compiled `info:mod.bin`. The omission is in our assembly recipe:
it copied data/locales/attributes but never carried the author's own cooked info
members into the final archive. The generic structural validator allowed that
incomplete archive, and the earlier ZIP/CRC checks only proved its bytes readable.
This was an assembly and validation gap, not a missing civilization toggle.
The log directly establishes missing native metadata as the rejection; it does
not independently establish that the missing image alone would prevent loading.

Persia additionally has a finished flag suite, Overview bonuses, Codex layout and
client civilization-card metadata. Berber presentation remains provisional.
Those differences do not explain this earlier native metadata rejection.

## Local correction: 0.1.0-trial.2

New test ZIP: `F:\aoe_4_temp\New_custom_civilization\aoe4-berbers\output\dropdown-fix\delivery\Berbers-Garrison-0.1.0-trial.2.zip`

- ZIP bytes: **610,756,410**.
- ZIP SHA-256: `f76125706d75dd43358a2270cc67aeeefb33c5d07353ccce83d15415f5b3bcc1`.
- Native SGA SHA-256: `13d6bb024aa7f60b01a0cc94c0d0e74beca292e5c9fce318122d3f6b48fd6b4d`.
- Restored only `mod.bin` and `mod.rrtex` under the **info TOC**.
- Both inputs are byte-verified against our existing native cooked Berber core
  carrier, with its own `5fe8767c-ca3a-4e64-9e20-c9527cf014ec` project identity.
  No Persian metadata/UUID or original Berber identity was borrowed.
- All **2,846 previous member bytes and TOCs
  remain identical**, including gameplay, art, localization and scripts.
- All **2,848 final members** were read back and matched
  against path/TOC/SHA-256; stored CRC32/SHA1 verification passed.
- The new regression rejects the actual failed trial.1 inventory and accepts
  the complete recipe/cooked metadata. Packaging now enforces this check too.
- ZIP CRC and packaged SGA SHA-256 checks passed.

The old trial remains preserved for evidence. Nothing was installed, enabled,
disabled, launched or pushed by this correction. Native acceptance is **pending**;
restoring the proven missing metadata does not establish the later gameplay gates.

Close AoE4, import/update to **0.1.0-trial.2** in Garrison, enable it, and launch
fresh. Use Standard, Tuning Pack=None, Dark Age and a human Berber player. For this
test disable other custom civilization packs, including Persia, before launch.
The package version changes; its unchanged SCAR diagnostic marker still reports
the original trial.1 mechanics version because this fix adds metadata only.

## Reproduction and receipts

`tools/prepare_runtime.py` includes the own-carrier info inputs in the recipe.
`tools/check_native_metadata.py` is the failing-before/passing-after regression.
`tools/build_metadata_fix.py` adds exactly the missing info members with the native
archiver, preserves the previous package and verifies every final member.
`tools/package_trial.py` takes explicit build/delivery/version arguments and
rejects archives missing native metadata.

Evidence: `output/dropdown-investigation/package-comparison.json`,
`game-warning-evidence.json`, `admission-evidence.json`, `metadata-regression.json`,
and `output/dropdown-fix/build/report.json`. The delivery directory contains
`delivery-receipt.json` and `SHA256SUMS.txt`.
