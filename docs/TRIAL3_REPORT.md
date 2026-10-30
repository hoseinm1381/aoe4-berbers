# Berber dropdown trial.3 — 2026-10-30

Current owner-test ZIP: **0.1.0-trial.3**, 611,849,959 bytes
(611.85 MB). Native acceptance is pending.

- [Playable ZIP](../output/trial3/delivery-ready/Berbers-Garrison-0.1.0-trial.3.zip)
- [Player test instructions](../START-HERE.md)
- [Verification receipt](../output/trial3/current/trial3-verification.json)
- [Delivery/manifest receipt](../output/trial3/delivery-ready/delivery-receipt.json)
- [Focused checks](../output/trial3-audit/checks.json)
- [Banner preview](../source/presentation/trial3/cover.png)

## Owner evidence and diagnosis

Trial.2 appeared in the native list and started a match. Screenshots showed Tent
Influence and music UI, magenta flag/loading/player-card images, provisional
civilization prose and stock-looking Malian starter units/buildings. The owner
reported **no crash** and did not try age-up, training or alliances after seeing
that start. Earlier shutdown logs are not evidence of a gameplay crash here.

The original Berber release contains custom capital, scout, male-villager and
many building/unit tier bindings. A wholly stock-looking start is therefore not
the intended representation. Some donor art is intentionally preserved in the
original: the female-villager fallback, destruction components, equipment and
shared siege/naval resources. No blanket replacement or new 3D art set was made.

The old replacement pack retained 128 stock basenames; 123 also retained their
stock PBG IDs. Owner namespace alone does not prove these collide. However, the
current official `cardinal.scar` extracts `BP_GetName(bp)` and passes that short
name back into native race-membership accessors when filling its entity/squad
caches. Stock/private copies with the same basename are ambiguous on this path.
Trial.2 logged missing springald/villager/horseman/archer/monk cache results and
no Wonder EBP; the actual callers were traced in current official source.
Trial.3 removes the short-name ambiguity. The next native test must confirm
whether this also resolves the observed art and generic cache warnings.

## Implemented changes

- 128 imported stock-named definitions now have unique `ber_` names and native
  generated IDs. The public derive/cook path allocated the IDs; full original
  custom records were retained. Typed references, every compiled variant,
  SCAR blueprint literals, voice aliases and numeric voice maps were translated.
- The RaceBP catalogue now points to Tuareg/Masmuda/available Berber cavalry
  entries and clears unavailable donor squad slots. This catalogue correction
  does not change the original build, production or research menus.
- Tent/Funduq predicates, Tent-panel sorting/labels and Mehari landmark checks
  now compare documented short names. Blueprint resolution keeps full owner names.
  Influence training events are restricted to the exact owned Berber race, and
  its Tent predicate no longer accepts another civ's shared Spirit Way type tag.
- Native flags now resolve under `ui/images`, whereas bonus icons resolve under
  `ui/icons`. Ten original vector surfaces were cooked into both required roots,
  with correct sizes, one mip and player-card alpha. `icon_small` uses the documented
  blank/native fallback. Garrison's outer package also contains a new cover.
- Real Berber dates, three-star difficulty, civilization description and bonuses
  replace implementation placeholders. Native traits 1–6 populate the Overview;
  trait 0 remains the lobby summary. Enduring Generations says the implemented
  flat +5% Health from Feudal onward, rather than the outdated stacking claim.
- Both native Codex representations now follow actual construction, production
  and upgrade records: 152 reachable records,
  23 producer branches, 7 unique-unit cards.
  Alliance conditions remain on original records; layout still needs native review.
  Horizontal coordinates are local to each native group, matching the stock layout.
  Indirect field construction remains a distinct review surface; valid Ram/Siege
  Tower catalogue references are retained even when no building directly spawns
  their SBPs. Production menus are preserved independently of this display.
- Passive bonuses now reset between matches and clean their modifier handles;
  alliance modifier tracking and first-choice state reset as well. Existing
  Core startup paths, local speech/music scope and disabled scripted AI remain.
- Bounded starter diagnostics print actual private names/IDs and expected IDs.
- The original long-description credit block is carried in [CREDITS.md](../CREDITS.md)
  and the packaged player instructions, including hossein81, marcokistan, Karyu,
  lammet and ForsakenCryz. The new native description replaces the obsolete
  lobby instructions; it does not replace this attribution record.

## Verification and preservation

Real native carrier cook completed, followed by the supported civilization
assembler and a reviewed RaceBP/catalogue-hash graft. The final archive has 2,868 members;
all TOCs and every extracted SHA-256 were checked. Native archive CRC/SHA-1
verification and the archive-owner check passed. Own `info` metadata is retained.

All 2,478 original pilot art/audio
members are byte-identical to trial.2. Across imported non-core records,
65,763 gameplay numeric/Boolean
leaves are unchanged, excluding PBG identity. Every private reference resolves,
family/ID uniqueness passes and no old owner remains in typed attributes/scripts.
The final recipe's stock references remain drawn from the previously verified
current-stock closure and existing production records.

All 25 SCAR files pass real Lua syntax loading.
The actual old Funduq predicate fails the short-name regression, and the new
Funduq/Tent predicates pass. Both passive modules pass duplicate-start,
end/setup and second-match tests against a stubbed engine boundary. This does
not simulate native mechanics. The old shared-type predicate accepts a foreign
Chinese Spirit Way in a focused regression; the new predicate rejects it, and
a foreign training event returns before touching squad/cost/group state.
All ten BC7 image surfaces were decoded and checked
for dimensions, one mip, source-pixel error, orientation and expected alpha.

ZIP CRC and packaged SGA SHA-256 verification passed. ZIP size exceeds the older
600 MB target; the owner explicitly waived size for this test. No runtime memory,
frame-time or performance claim follows from package size.

| Artifact | SHA-256 |
| --- | --- |
| Trial.3 playable ZIP | `bdb8c23531f12e0ad356abec1c91c8f2f0e9f0a7fc0f191da61ef52270752b01` |
| Trial.3 final SGA (770,805,980 bytes) | `c4e6639a1be24225f670eb0b1b3650246974e9ee592baaa0f385f6df11d40cf6` |
| Preserved trial.2 SGA | `13d6bb024aa7f60b01a0cc94c0d0e74beca292e5c9fce318122d3f6b48fd6b4d` |

Native trial.3 import, dropdown, art, actual training/age-ups/Tents, audio,
second matches, save/load, AI, multiplayer and performance remain separate gates.
No mod was installed, launched, committed or pushed during this work. Original
E:/F: workspaces, previous ZIPs and the composed 1.0.5 input remain unchanged.

## Editable inputs and reproduction

Current SCAR: `source/trial3/scar`. Original banner SVG/PNG sources:
`source/presentation/trial3`; recipe: `tools/make_trial3_banner.py`.
Native allocation authoring records are in `authoring-library/Mods/berbers`;
the precise identity map is `output/trial3-audit/private-identities.json`.
This is still a local pilot with preserved external rebuild inputs, not a
self-contained future-modder source release. Do not mistake compiled RGDs for
complete editable geometry/audio masters.

Use Python 3.13 with the installed Garrison compiled modules plus Pillow/Lupa.
The local verified interpreter is
`C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe`.
Run from this workspace:

```text
python tools/make_trial3_banner.py
python tools/allocate_trial3_identities.py
python tools/prepare_trial3.py
python tools/check_trial3.py
garrison-core civilization validate trial3-build-recipe.json
garrison-core civilization build trial3-build-recipe.json --output FRESH_BUILD
```

The native carrier's `project/source/ui/images/garrison/berbers/presentation`
PNGs and imported `ui/icons` PNGs are retained, so its ordinary native cook
recreates the correct resource names. Never copy an icon RRTEX into the image
root without checking its internal name.

After intentionally editing a banner PNG, update both retained native source
roots before the carrier cook. The first import used `ui_assets.add_image` for
the icon root and the same PNGs under native `project/source/ui/images` for the
race images. `allocate_trial3_identities.py` reuses existing derived records and
cooks that carrier; it does not reimport changed external PNGs automatically.

Current output is `output/trial3/current`, verified with
`python tools/verify_reviewed_trial3.py`. `tools/finalize_reviewed_archetypes.py`
records the RaceBP/declaration and influence-isolation graft after the supported reviewed
build; the receipt verifies the declaration's hashes too. The lifecycle and
local-coordinate corrections are included. The earlier `build`, `finalized`,
`build-reviewed`, `delivery` and `delivery-final` folders are intermediate receipts,
superseded by `current` and `delivery-ready`. `tools/finalize_trial3.py` records the historical four-SCAR graft
and refuses to overwrite its evidence. Do not rerun that graft on a fresh build
where those changes already exist. The package writer accepts `--build`, `--delivery`,
`--version 0.1.0-trial.3 --trial3`; require a matching full verification receipt
before packaging. Keep protected prior artifacts; use a new output only for an
explicitly requested later test.

The Garrison skill was updated through the Skill Creator workflow and validates.
Its independent-civilizations reference documents metadata discovery, native image
roots, short-name/stock-override pitfalls, gameplay preservation and gate boundaries.
