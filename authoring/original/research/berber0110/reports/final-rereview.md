# Scoped final re-review

Both findings in `final-review.md` are resolved in the reviewed implementation. No remaining actionable P1/P2 defect was established within this scoped re-review.

- **P1 queue starvation resolved:** `berber_ai_production.scar:70-129` now selects eligible research even while its producer is busy, persists the selected drain, reserves that producer against training, protects affordable research funds, and starts the upgrade when the paid queue empties. Existing queues are preserved. The added three-tick regression covers two occupied core producers, staggered queue completion, both upgrades and monastery unlocking.
- **P2 abandoned foundations resolved:** `berber_ai_economy.scar:150-203` retains a required crew size, prunes dead IDs, preserves living assigned workers and recruits eligible replacements with worker-job identity, prior resource role and reservations recorded. The construction-entity traversal includes tracked squad-owned ram foundations. Added regressions cover all three landmark builders dying, partial crew death, held/sheltered/reserved exclusions, delayed recruitment for an orphan foundation and archer replacement for a ram.

Fresh reviewer verification:

    C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B -m unittest discover -s research/berber0110/tests -p test_production.py
    C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B -m unittest discover -s research/berber0110/tests -p test_economy.py

Results: **25 production tests and 44 economy tests passed**, both exit code 0. The landmark test simulates completion after observing build commands; it is policy regression evidence, not native construction proof. Source inspection confirms replacement workers populate the existing previous-role restoration ledger.

Scope was the changed functions, changed focused tests and prior review findings. No gameplay source edits, game execution, packaging or commits. Native command acceptance, actual queue/construction behavior, pathfinding, costs, total-income coverage, save/load and multiplayer/performance acceptance remain separate pending gates.
