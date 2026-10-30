# Qualification evidence

- Installed Garrison manifest: 0.1.4. Reviewed installed guide `rig-and-animation.html`, `remix-a-game-model.html`, and installed building exporter plus compiled building recipe API.
- `api.json`: current compiled building API signatures and read-only game asset index schema.
- `stock-candidates.json`: current indexed source/archive candidates.
- `stock-house/a9a752db305fef70848f/decoded-static.json`: read-only stock Abbasid house decode, including archive provenance, geometry and layered native material.
- `stock-material.json`: extracted material-only portion for easier inspection.
- `stock-owner-contract.json`: named colour/pattern parameter survey; ordinary highlight/midtone/shadow colour constants are not owner-selection proof.
- `output/buildings_batch/player_colour/probe-inputs.json`: saved age-1 red-only mask statistics and original construction FBX hash.
- `output/buildings_batch/player_colour/probe-cook/`: initial incomplete fixture, missing `effects.edfm`, AccessViolationException during EdfDatabase cleanup. Not shader compatibility evidence.
- `output/buildings_batch/player_colour/probe-cook-with-edfm/`: base editor fails material preview because `unit_collection` effect is absent.
- `output/buildings_batch/player_colour/probe-cook-prepared-editor/`: prepared Garrison editor emits RGM but RRGeometry fails because `unit_collection` effect is absent (exit -6). Partial SGA/RGM are failed diagnostic outputs, not deployable results.

No distributable package, production archive, live Blender changes, or game test was performed. The experimental project retains the original mod GUID only as a local diagnostic fixture; never install this fixture alongside the real mod.
