# Final independent review of Berber 0.11.0

Read-only review of authored sources, approved design, INTERFACES.md, domain reports and focused tests. No game run, source changes, packaging or commits. Findings below concern deterministic implementation behavior, not the separately disclosed native acceptance gates.

## P1: Continuous training starves the required Castle archer upgrade and religion

Location: `research/berber0110/ai/berber_ai_production.scar:75-77`; related `berber_ai_engine.scar:399`, `berber_ai_production.scar:132`.

Research only considers an entirely empty producer queue, while normal production fills any queue with fewer than two entries. With sufficient income an Archery Range completing one archer still has the second paid archer queued, so research skips it and Produce replenishes that queue. This repeats indefinitely. The Castle archer upgrade cannot start despite being affordable; `BerberAI_CoreReady` then also withholds monastery construction and all religious/healing Imam production. A newly expanded Range can escape this by starting empty, but expansion being unaffordable, exhausted or unavailable must not be required for core upgrades. This contradicts the explicitly prioritized Castle upgrades and religion order.

Smallest fix: when a producer has an eligible affordable core upgrade, reserve it against new unit training until its existing paid queue drains, then research. Alternatively enqueue the upgrade behind existing paid orders using a verified native queued-upgrade contract. Preserve existing paid queues and simultaneous upgrades on separate producers. Add a multi-tick test with an already occupied Range, sustained funds, queue progress and replenishment.

Reproduction using the existing isolated production harness and real production module: Castle state with horseman upgrade owned, affordable archer upgrade, one queued archer in its Range and sufficient funds; 100 Produce ticks resetting per-tick producer reservations issued **0 upgrades, 100 archer requests and 0 monasteries**. The harness does not emulate time/progress, but the actual engine's `<2` refill rule supplies the steady occupied-queue condition. This is policy evidence, not native execution evidence.

## P2: A surviving foundation is permanently abandoned when its recorded builders die

Location: `research/berber0110/ai/berber_ai_economy.scar:151-159`; related `berber_ai_engine.scar:195-200`.

For an existing construction job, MaintainConstruction only iterates the recorded worker IDs; it never removes dead IDs or replaces missing builders. ReconcileConstruction keeps that job for as long as the foundation exists and is incomplete. If all assigned builders die, replacement villagers remain available but no worker ever receives a build command. A surviving Feudal landmark foundation can therefore prevent aging for the rest of the match: AgeUp sees the foundation and declines another project, while the recovery crew branch is reachable only when no job exists. Houses, TCs, farms and other foundations share the same problem.

Smallest fix: reconcile each unfinished job's assigned IDs against living eligible squads and replenish missing builders with a bounded crew, recording prior jobs and reservations exactly as for new construction. Retain living assigned workers and do not steal sheltered/reserved workers. Apply the same recovery to squad-owned construction foundations where supported. Add regressions for all builders killed, one builder killed and replacement workers after a save/restore.

Reproduction using the existing economy harness and real economy module: incomplete Feudal landmark with job worker IDs 101/102/103 absent from the live squad list, plus six available villagers. After 100 MaintainConstruction calls, the job still contained the same three absent IDs and **zero build commands** had been issued.

## Other reviewed boundaries

The current world/player enumeration uses matching spawned-only getters/counts and owner guards. Official installed API confirms these getters and the entity/squad ID contract. The harvest modifier construction/removal matches the installed official `chatcheats.scar:526-529` and `modifiers.scar:108` pattern. No additional actionable P1/P2 native-contract finding was established in this pass. The previously documented total-income coverage, market transaction pricing/fees, pathfinding, command acceptance, native save/load and multiplayer/performance gates remain unverified; this review does not relabel them as code defects or claim native acceptance.
