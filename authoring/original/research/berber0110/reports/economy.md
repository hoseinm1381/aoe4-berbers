# Economy task outcome - Berber 0.11.0

Authoring files only:

- `research/berber0110/ai/berber_ai_economy.scar`
- `research/berber0110/tests/test_economy.py`
- this report

Implemented persistent opening assignments (six food, three gold, nine food,
eight wood, five gold, fourteen food, then two food/two wood/one gold), loss
replacement, filtered first-miner camp/house and first-woodcutter camp,
housing at two free slots using gold builders, and villager funding at every
owned TC with one combined difficulty target. Roles survive construction and
temporary farm-funding; held/reserved workers receive no gather orders.

Food selection uses the full shared world snapshot with stable ordering:
sheep, deer, berries/other edible sources, then single-worker farms. Enemy-owned,
dead and unsafe sources are excluded. Food mills start at the exact 24m boundary.
Farm funding temporarily sends food workers to wood; farm building is incremental,
uses TC space first (eight nearby plots per TC), then complete eight-farm mill
clusters. Missing/rejected farms are recounted rather than assumed complete.
Farm funding blocks extra production pairs while allowing opening producers.
Protective outposts need five active workers at a non-sheep site outside 24m TC
protection and 200 spare wood (150 when enemy knights exist); foundations count.

Feudal uses Funduq and three food builders with at least six remaining food
assignments. Castle savings start at the controller's retained synchronized
720-840s draw, use eight wood workers by the woodline, and unlock immediately
on accepted landmark construction. Imperial savings start at 1260s: live traders
>=15 choose the forward Keep; otherwise rear Fez. Twenty villagers from the
nearest resource cohort construct it. Necessary houses and villagers precede
the savings gate; all discretionary economy construction respects it.

The dedicated trade Market starts at 300W/250G, uses the closest legal anchor
to home outside the destination's 100m circle, and passes exact native placement
constraints to the engine. Military Markets remain separate. At 630s the
one-time second-TC decision uses live trader count (<10). Four food/four gold workers
mine only missing native stone cost and build at nearest safe gold with >2400
remaining, falling back to nearest safe woodline. Temporary miners resume their
prior roles once funded. Paired Market/Range expansion starts at 600s, retries
after 60s on failure, and advances 120s after a funded pair. Retains one outstanding
pair and retries unobserved expired halves. Only full influence requests more
Tents; ordinary caps are 1/2/3/4 by age, excluding Funduq. Missing stone is bought
normally or temporarily mined by eight food/gold workers. Four complete full Tents plus Funduq stop further
expansion until a capacity signature changes.

Production owns Blacksmith, monastery, workshop/university and all research;
the economy does not duplicate those requests. No direct recovery grants remain.

## Verification and TDD

Baseline red: 15 initial tests ran; 14 failed against baseline after legacy
resource-discovery stubs were supplied. Failures included missing Economy entry,
percentage assignments, wrong housing threshold, no savings phases and no timed
TC/expansion behavior. Subsequent new regression batches were observed failing
before their fixes: construction identity and full influence stopping (2),
opening farm precedence/rejected half/farm recount/miner restoration (4),
transient failure creating unnecessary Tent (1), actual resource-worker counts
and six-food Feudal minimum (2). Review follow-up added five failing regressions
for raw trade handle shape, boolean knight observations, four/four TC cohorts
(both mined and already funded), and eight Tent miners. A further failing
regression demonstrated stone-camp completion resurrecting an expired temporary
stone role; restoration now updates pending/active jobs' saved resource role.
Final review supplied a known-job dead-builder stall. Five new tests failed
before correction: all three Feudal builders killed, held/sheltered/reserved
replacement exclusion, empty orphan crew retention, partial crew death, and
archer-built ram replacement. MaintainConstruction now retains required crew
size before pruning dead IDs, preserves surviving crew, recruits missing workers
through original resource/role filters, relaxes obsolete explicit IDs, captures
replacement prior roles and reserves them. Existing orphan foundations retain
a two-worker requirement even when no worker is initially available. Shared
construction_entities includes squad-owned ram foundations, with duplicate IDs
visited once. The killed-Feudal-crew regression receives three replacement build
commands and reaches completion in its explicit construction-progress fixture.

Final command:

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B -m unittest discover -s research/berber0110/tests -p test_economy.py -v
```

Result: **44 focused tests passed**, Lua 5.1 via `lupa.lua51`. The full available
authoring suite also passed **144 tests** on this worker's final run. Tests cover deterministic
milestones, role persistence, full-map resource selection and dead guards,
exact builder/resource selection, both Imperial choices, savings and rejection
retry, population housing deduplication, TC decision boundary, rich-gold target,
two-TC villager funding, dedicated trade endpoint constraints, farm priorities,
mill threshold, single-worker farm occupancy, cluster rejection recount,
protective tower thresholds, influence caps and placement-vs-transient failure,
validated raw trade handles, numeric/boolean knight observations, exact four/four
TC cohorts, cohort-shortage substitution, eight Tent miners, and mining-camp role
restoration. Substitution uses only eligible food/gold workers when a cohort is
actually short; held/reserved workers cannot be selected.

SCAR validator: **0 errors, 1 warning**. `b.options` / `job.options` are engine-owned
construction job metadata, not lobby options. Root now defines `BerberAI.BuyStone`,
resolving the prior standalone unknown-call warning. SCAR skill fixture self-test passed.

AoE4 MCP `doctor`: ready. `check_code`: all unknown names resolve to module-local
helpers or pinned BerberAI interfaces (also lexical false positives `and/or/not`),
no missing localization IDs. `Entity_GetResource` is flagged low confidence because
the official API has no typed return or indexed usage. Its explicit numeric-amount
description is present at installed `Essence_ScarFunctions.api:680`; no official
source usage was found, so native resource coverage remains a gate.

## Evidence ledger and integration contracts

- Official/API: installed `E:/Games/steamapps/common/Age of Empires IV/scardocs/api/Essence_ScarFunctions.api`
  lines651/658-661/671-672/680 (entity blueprint, health, identity, ownership,
  position, resources),1281-1291 (population),1627/1630/1633 (gather/idle/hold),
 1970 (world ownership). World ownership is tested before `Entity_GetPlayerOwner`.
- Official usage: `scar/ai/wave_generator.scar:514,537`, `scar/groups.scar:519,543`
  and `ai/tactics.scar:856` demonstrate world-owner guard before owner access.
- Project definitions/imports: `INTERFACES.md`; engine `Workers/Construct/Train`,
  navigation `SafePoint`, shared world snapshot, root construction lifecycle.
  SafePoint uses buffer0 because navigation adds the buffer to its base24m TC rule.
- Project source: editable landmark folders confirm Funduq=b, Mosque=age2c,
  Fez=age3e, Almohad Keep=age3f; native costs always resolved through `Cost`.
  No tuning XML, GUID, RDO, CSV or official archive was modified.
- Corpus analogue: baseline economy only, as existing integration evidence.
- Unresolved contracts: no invented raw engine calls. Root integration must supply
  `Construct -> bool,job`, job `{workers,previous_roles,name,pos,until_time,options}`,
  `options.trade/min_target_distance/target_pos/exact_anchor`, `existing_ids`
  exclusion during pending reconciliation, and `last_construct_failure='placement'`
  only for a genuinely exhausted placement search. Root receives these explicitly.
- Cleanup/multiplayer: no rules, modifiers, persistent engine groups, OS randomness
  or local-player authority are created here. Economy state is serializable and
  retained on `st`; all unordered worksite decisions sort stable IDs.
- Static result: 44 focused behavior tests, full suite144 and validator above. Shared-engine integration
  tests remain root-owned and must run after root modules are complete.
- Content Editor result: not run; authoring-only task boundary.
- Runtime matrix: no live game, multiplayer, pathfinding or save/load engine test
  run. Native placement, real resource availability, costs/requirements and the
  whole income adapter remain distinct acceptance gates.

No source promotion, commits, release ZIPs, live imports or game modification.
