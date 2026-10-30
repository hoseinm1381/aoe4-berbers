# Berber 1.0.4 native acceptance - user testing

1. Import the new ZIP in Garrison. Select its tuning pack and game mode. Restart AoE4 and begin a fresh land match with at least one Berber computer and a stock-civilization control. Record map, difficulty, player slots and selected version.
2. Observe the first five minutes: villagers gather sheep/wood/gold, new villagers train, houses prevent population blockage, scouts explore, and the economy continues after sheep die or run out. No scripted-controller initialization or native-fallback watchdog messages should appear in warnings.log.
3. Continue through all ages. Check landmark construction and completion, resource drop-offs, Tribal Tent placement, barracks/range/stable/siege production, blacksmith/university research, custom unit tiers, and replacement after losses. Compare Standard/Hard/Hardest and any higher native difficulty you use.
4. Check that a Tent alliance is selected when affordable, its granted units become available, and the AI does not continually pay to switch alliances. Observe Tuareg shields and the other mapped defensive abilities during combat. Mappings establish eligibility, not a promise about native timing or tactical competence.
5. Check trade on a suitable map, fishing and warship production on a water map, and Nomad setup using the supported lobby configuration. These scenarios may require longer matches and appropriate resources.
6. Save and load an active match. Check that native AI continues and music/voices/trader progression still behave as before. Test multiplayer separately if used; do not infer synchronization from solo success.

For a failure, retain warnings.log immediately after the match, screenshots, selected version/difficulty/map and approximate simulation time. Preserve 1.0.3 for rollback. Do not reuse an old 1.0.3 save as proof of fresh 1.0.4 initialization.
