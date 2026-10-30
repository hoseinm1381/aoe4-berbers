# Rebuild Berber 0.11.0

Authoritative base: retained final0.10.1 SGA,
`648a2a0c94de851c6eff8d8a242c2131c6db5394d3a508c8182ed8260bc90718`.
Its ZIP is `ff5512ea42f771214b603495d526745c42b87519607daa229959e589c2213720`.
Never substitute a raw Content Editor cook: some editable voice/entry scripts
predate the current delivered versions. The overlay replaces only AI SCAR.

Editable authoring modules are in this directory's ai/ and promoted copies in
assets/scar/ai/. baseline-source/ preserves the prior editable AI bytes. The
approved design and implementation plan are in docs/superpowers/. Tests and
the strict test_runtime.lua are retained; normal game files are never edited.

Use verified Python3.13 with lupa.lua51:
`C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe -B`.
From project root:

1. Run research/berber0110/checks.py (complete behavior suite, syntax, static,
   skill self-test and unchanged tuning validation).
2. Run research/berber0110/simulation.py (two identical simplified eight-slot
   30-minute traces including restore and death/despawn).
3. Run research/berber0110/evidence.py and AoE4 MCP check_code for all complete
   authored modules. Review scanner false positives; retain mcp-check.json.
4. Run pipeline.py prepare, then pipeline.py stage. Both pin the final0101 base.
5. Run pipeline.py compose, then release.py. Existing final SGA/ZIP outputs are
   protected against overwrite; use a new output directory for reproduction.
6. Run cleanup.py only after all delivery/member checks pass.

The corrected frozen catalog contains verified inherited camp production lists
and upgrade_bag requirements. The old catalog decoder's requirement_ext lookup
missed actual technology prerequisites. Compact mappings, exact official/base
member hashes and source research scripts remain in reports/catalog-*.json/md/py.
Ordinary reproduction uses the frozen catalog, not extracted RGD/XML caches.
For deliberate catalog regeneration, catalog-research.py and the documented
official Attrib.sga/retained0101 source paths provide the extraction route.
Generated reports/catalog-scratch and catalog-market are disposable and are
deleted only after verified release packaging. Compact evidence remains.

BuyStone uses the Market's real core_market_buy_stone native ability, reserves
spare gold, tracks an outstanding attempt and falls back to mining if it fails.
No resource is manufactured, and static zero ability cost is not treated as a
market quote. Exact native amount/fees/payment and route behavior need testing.
Income sums the documented per-second rates of all four resources. Native
trade/relic/passive coverage has not been established; do not claim it has.

Native acceptance is in the ZIP and output's NATIVE_AI_ACCEPTANCE.md. Static,
mock simulation, package/hash checks, client import and actual gameplay are
different evidence layers. Preserve0101/0100/091/090/081 rollbacks until the
operator accepts a newer release. Future updates start from final0110 SGA.
