# Fresh read-only military/navigation review

Reviewed current `ai/berber_ai_military.scar` (375 lines), navigation (74 lines),
the approved full design, shared interfaces, military tests and installed API.
No implementation/test files edited. Existing fixture was executed in isolated
Lua5.1 instances with additional scenarios; these are semantic findings, not
claims about a live match. Line references below are against this reviewed copy.

## Findings

1. **P1 - Released archers can cross the map alone or enter a TC zone while
   their Lancers retreat.** `berber_ai_military.scar:281-284` uses a Lancer's
   position as the target-search origin, then directly attacks with every
   deployed archer regardless of each archer's distance to that Lancer or the
   target's TC safety. There is no rendezvous/tether check. Reproduction using
   the existing strict fixture: one Lancer at x150, six archers at x0 and an
   exposed villager at x170 gives all six archers a direct attack at x170.
   Another scenario puts a Lancer at80, six archers at75, enemy TC at120 and
   villager at110: Lancer correctly refuses the villager under TC cover, but
   archers attack that same villager. This violates staying close to Lancers
   for protection. Require safe rendezvous before assault, enforce follow
   distance, and apply the Lancers' current raid/regroup decision to archers.

2. **P1 - Trade never tries a farther viable endpoint after selecting an
   unusable nearest one.** `berber_ai_military.scar:69-70,88-97` sorts allied
   Markets/neutral posts, selects candidate1, then computes its route. A blocked
   first candidate remains selected on every refresh; safe later candidates
   are never considered. Foundations are also not filtered before selection.
   Reproduced with a neutral post at100 covered by an enemy TC at100 and an
   allied Market at150: selected endpoint2 is blocked while `FindSafeRoute`
   successfully reaches the allied Market. Thus trade permanently stops and
   requests protection even though a safe destination exists. Check candidate
   completion/legality and route viability in stable distance order, then
   choose the closest viable endpoint; retain blocked/escort behavior when
   no viable endpoint exists.

3. **P2 - Economic classification is too broad for the required villager raid
   priority.** `berber_ai_military.scar:11-12,200-215` includes sheep, cattle,
   traders and religious units in `economic`, and selects the nearest member
   without a villager priority. Reproduced with a Lancer at20, enemy sheep at30
   and exposed villager at70: the Lancer attacks the sheep. The approved raid
   target is exposed villagers; livestock/religious fallback targets must not
   displace an available exposed villager. Add a distinct villager marker or
   priority rather than reusing the army-value economic exclusion category.

4. **P1 integration - Observe/economy disagree on endpoint and cavalry field
   shapes.** `berber_ai_military.scar:33,61` exports boolean `enemy_knights`,
   while economy uses `(st.enemy_knights or 0)>0` in `towers` (reviewed economy
   line282), producing a Lua boolean/number comparison error when knights
   are present. `berber_ai_military.scar:89` exports an EntityID as `trade_target`,
   whereas economy's `trade_market` (reviewed lines485/488) expects `.pos` and
   will not start trade (or may index an opaque native handle). The shared
   interface does not pin these two shapes clearly enough. Both domain test
   fixtures conceal the mismatch by using different shapes. Normalize one
   contract and add a combined Observe->Economy regression. Root and both
   workers were notified; these should be resolved before promotion.

5. **P2 API contract - Relic-carry detection is asserted by mocks but not
   established by the selected engine API.** `berber_ai_military.scar:358`
   uses `Squad_IsHoldingAny` to decide whether an Imam must deposit a relic.
   Installed `Essence_ScarFunctions.api:1628` describes this as whether a squad
   has a hold on anything, specifically “use this on vehicles”; official
   `scar/syncweapons.scar:69-72` follows a true result with `Squad_GetSquadsHeld`,
   confirming a transport/squad-hold contract. The only test sets an invented
   `s.holding=true`. Editable `sbps/races/malian/unit_monk_3_mal.xml:54-59`
   exposes pickup/deposit/drop/remove relic abilities but does not establish
   that they populate a vehicle-style squad hold. This is an actual unverified
   receiver/state shape, beyond ordinary command-acceptance proof. Trace the
   native relic inventory/state contract or demonstrate the adapter on the
   relevant native source before asserting deposit-before-next-fetch. This
   finding does not assert the function definitely returns false for Imams;
   the current evidence is insufficient to assert the required state test.

## Scope notes

No unbounded Lua loop was found: navigation samples a finite six offsets,
two signs and up to two shoulders; scout fallback tries twelve candidates.
All reviewed live-target consumers validate entity/squad handles before native
getters. Owner reads in Observe are world-guarded. Native path shape, trade
auto-return, command acceptance and performance gates already disclosed in
the military report are intentionally not repeated as review defects.

The review additionally noticed economy/default mismatches while reading the
full design: second-TC miners must be four food/four gold, and Tent temporary
mining must use eight workers. The submitted economy implementation currently
chooses the first eight food/gold IDs and three Tent miners. Root was notified;
these are economy follow-up items rather than military findings.
