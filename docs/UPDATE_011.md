# Local 0.1.1 update

The owner tested the previous four packages and reported a Persia crash when
opening the tech tree. This update preserves their stable owner IDs, existing
gameplay, voices, art and music. No push, tag, publication or installation occurs.

## Changes

- Client card: civilization period, difficulty stars, tagline, introduction,
  bonuses and flag cover, using the installed Garrison civilization metadata.
- Native presentation: nine freshly cooked UI textures, including a 1920x1080
  loading background with a dark left side fading toward the right.
- Korea/Persia/Vietnam: six villagers and scout use official stock offsets.
  Berbers already had the stock formation; extra sheep/Buffalo, unit counts,
  resources and caps remain unchanged.
- All four Codex trees: replace invalid producer-index age columns and
  rows extending beyond the four native age bands with stock-compatible
  age columns -1..3 and rows 0..11. Retain Berbers' existing graph and row/branch layout while repairing its age columns and background height.

The actual old native Codex is retained in tests/fixtures. The regression rejects
the invalid old layout and accepts the corrected generated layout. The captured
Persia warnings log opens CodexModalPage.xaml immediately before an access
violation. These facts support the repair; native retesting is still required
to establish that the crash is resolved in game.

## Rebuilding editable presentation

The raster master is source/presentation/hd/flag.png; Korea also has an editable
vector flag.svg. The derived SVGs preserve the compositing and fade recipe.
Vietnam uses the exact locally cached Garrison catalog flag chosen by the owner.
Persia is a high-resolution remaster of its existing lion-and-sun flag.

Use Node with the sharp package (GARRISON_SHARP may identify its installed path):
`node tools/render_presentation.mjs .`

With installed Garrison and Python 3.13:
`python -B tools/cook_presentation.py --replace-current`
`python -B tools/inputs.py verify`
`python -B tools/build.py --replace-current`

The UI cook uses a fresh throwaway native carrier, verifies archive CRC/SHA1 and
texture dimensions, then promotes only the nine presentation textures. It never
promotes the carrier's gameplay, root, metadata or locale. Failed or foreign work folders remain protected diagnostics. Reuse the single
verified output/presentation-current location with --replace-current; the prior
compact receipt is retained before regenerable work is replaced.

The final build verifies every member against the previous package and allows
only the documented Army/Race/Codex/declaration changes and nine added textures.
The previous tested player ZIP and compact before snapshots are retained here.

## Owner's focused native retest

1. Close AoE4 before importing the new ZIP through Garrison. Enable only the
   intended independent civ; use native Standard and Tuning Pack=None.
2. Check its card flag, difficulty stars, tagline and description.
3. Start a fresh standard Dark Age match. Check villagers/scout, extra civ units,
   readable loading text and crisp background. Do not reuse an old save.
4. Open the tech tree from both menu and a fresh match; inspect all four ages,
   pan/zoom, select units/upgrades/buildings and close/reopen it. Repeat for all4.
5. Report acceptance. GitHub push still requires a separate manual instruction.

Runtime, save/load, AI, multiplayer and performance are separate gates; a cooked
texture, passing static test or readable ZIP is not native acceptance.
