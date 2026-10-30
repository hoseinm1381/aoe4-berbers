# Berber 0.2.5 execution ledger

Plan: user-approved economic building material remixes, 2026-10-13.

- Baseline: accepted 0.2.4; archive SHA256 3246e2bbe002502ffb087c49af5ac83ffde75c4b956c918fe99881ac80d771c3.
- Three authors dispatched concurrently: mill_author, lumber_author, mining_author.
- Each owns separate sources, hidden Blender worker and Garrison project.
- Fresh Essence cooks serialized by root; no shared Editor race.
- Three fresh reviewers follow author completion. Root owns private bindings and final package.
- Native acceptance pending user match; house 0.2.4 accepted by user.

Ruling: reuse current codex/berber-house-022 branch and isolate candidate/source folders. Existing dirty user workspace and necessary stock fixtures remain in place; no commit, reset or checkout copying.

## Tasks

- [x] Mill source/cook
- [x] Lumber source/cook
- [x] Mining source/cook
- [x] Three independent asset reviews
- [x] Private bindings and allowlisted 0.2.5 package
- [x] Final whole-package review and delivery

Fresh mill/lumber/mining cooks succeeded with Live Reload off. One interrupted lumber run was retained as failed evidence and replaced by a fresh successful run. Source assembly uses original native transforms (including lumber logs scale 0.8), not the prior small primitive recipes. Root stock stamp parser checks all native type checksums against reflect.db; four preservation regression tests pass (scale, dropped component and selection mutations rejected).

Stamp source probes v1–v4 failed and were not promoted. Numeric Math fields and schema-named enum values are required; retained stock model/material definitions satisfy source validation. Fresh v5 stamp cook succeeded, as did the separate private-tier Garrison cook. Native readback verifies all 231 original objects/field layouts/array order, except deterministic private IDs and six intended model paths. Final archive SHA256 91b486656ed4194cdbd366a96cb4f539800ecb0634e87e40bd49afcbe1cefc0d; 469 members, 398 unchanged baseline members, two changed baseline actors, 69 new private media/binding members.

Final independent package review approved: ZIP/SGA integrity, all 71 allowlisted payloads/namespaces, three actor/tier visual-only diffs, 231 stamp objects/1257 reflected fields, 18 material roots, six native geometries, 162 texture references and 51 stamp references. All 15 focused native-stamp/material/namespace regression checks pass. Native game acceptance remains pending. No commits, merges, installs or publication performed; candidate sources/output retained on existing feature branch.
