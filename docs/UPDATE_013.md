# Berbers 0.1.3 player color

The game now has more owner-color surface to work with on the audited Berber
buildings and units. Colors are selected by the owner in-game. The unit material
uses the red pattern channel; structure materials use the native team layer.
No fixed red or blue team color was added to the base textures.

- The 53 measured private unit resources sample at 10.54–44.83% across their
  three LODs. The 22 adjusted materials cover Tuareg, Mehari, Scout, Villager,
  Zenata, Sanhaja, Masmuda and one Trader variant. The other measured units
  already satisfied the target. Rigs, animations, mesh buffers and LOD
  selectors are preserved. 49 unit resources reduce triangle count across
  their LODs; the four Tuareg bodies retain their existing three skin LODs
  with the same triangle count. Original skin and hair source channels were copied
  into the revised masks before BC3 compression.
- 53 measured building resources sample at 8.94–19.31%. The update expands
  existing team layers on stock-derived structures, and adds a team layer to
  four Tribal Tent ages and five private landmarks. The 337 packaged custom
  building mesh groups each have one detail level. Construction, damage and
  ruin selectors remain intact.
- The four Tribal Tents were recooked with the structure shader in the
  Content Editor. Their original geometry, UV0 and indices match after
  accounting for the added UV2 lane. The native-cook geometry matches the
  released geometry byte for byte. For five landmarks the same stream
  conversion retains their mesh data, selectors and RGO without a new cook.
- Gameplay, voices, civilization identity, and archive members outside the
  explicit art allowlist are preserved against 0.1.2.

Coverage is a mesh-area estimate sampled from decoded texture masks, with four
samples per triangle. It is not screen coverage or proof of native color.
Structure collection measurements include inactive lifecycle pieces. Shared
stock models, building props and structure bindings without a verified team
layer (including the outpost base and stone upgrade) are outside the measured
target. See the per-resource receipts in [update_013](update_013).

Check two colors in a fresh Standard match with Player Colors set to Unique,
including unit distance transitions, tent construction and ruin, and landmark
damage. Native appearance, performance and multiplayer are pending.

The normal source build consumes the pinned native files and verifies the
exact archive delta from the 0.1.2 manifest. The art recipes in
`tools/owner_color.py`, `tools/structure_color.py`, `tools/tent_color_probe.py`
and `tools/convert_owner_buildings.py` work in an isolated staging directory.
To regenerate, set `BERBER_COLOR_BASELINE` to a fresh extraction of the exact
0.1.2 archive. Use Python 3.13, Pillow, NumPy, SciPy, the installed Garrison
SDK and its native Content Editor. Run the tent cook, extract its art output,
then run the three overlay generators against that baseline. The normal mod
build needs only the tracked native files and Garrison SDK.
