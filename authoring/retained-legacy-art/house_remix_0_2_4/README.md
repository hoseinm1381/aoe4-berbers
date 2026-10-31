# House 0.2.4 sizing correction

User native feedback: the visible 0.2.3 houses were too small. These four saved `.blend` variants use root visual scale **1.38**, exactly three times **0.46**. Mesh topology, UVs and materials are preserved. `resize-validation.json` records measured per-object dimensions and source hashes.

The 0.2.4 ZIP changes only four freshly compiled native stamp resources. All 396 other archive members are byte-preserved from 0.2.3, including corrected attribute namespaces, game-side footprints, Tent, Tuareg and audio/SCAR.

Future 2x2-reference buildings use a 3x visual-size default and require comparison against native villagers. The durable project rule is [BUILDING_SCALE_POLICY.md](../../Design/asset_overhaul/BUILDING_SCALE_POLICY.md). Native sizing/overlap acceptance remains pending the user's next match.
