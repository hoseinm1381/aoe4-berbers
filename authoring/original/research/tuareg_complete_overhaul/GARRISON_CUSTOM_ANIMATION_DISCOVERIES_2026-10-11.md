# Garrison and AoE4 custom-animation discoveries

**Recorded:** 2026-10-11, Asia/Tehran date.  
**Purpose:** Research handoff for a later update of `aoe4-garrison-blender`. This document does not update the skill.  
**Inspected installation:** Garrison Blender extension **0.1.3**, Blender **5.2.2 LTS**.  
**Project:** Berber/Tuareg spearman trials, project GUID `1d3145e8-f1b2-427f-8bb0-067851fcf0f1`.

## Main conclusion

Custom bone motion can be authored and previewed in Blender. Current Garrison game export admits a limited set of replacement clips. We have **not qualified a general private animation-library writer and an interruptible animation-graph/arm-layer route** for an immediate Tuareg Q shield pose while locomotion and combat continue normally.

The Tuareg Q gameplay signal works. Existing stock shield-wall motion can be selected, but the user observes immediate idle activation and a 3–5 second moving delay. More frequent ability polling or a better mesh does not establish a solution to native graph switching.

Do not describe the current models or stock guard trial as a complete custom animation set.

## Evidence rules

| Evidence | What it proves | What it does not prove |
|---|---|---|
| Installed guide/catalogue | Documented controls and admitted contracts | Native acceptance of a new candidate |
| Blender Action, retarget or pose preview | Candidate authoring and source motion | Game export, command binding or playback |
| Export/cook/archive readback | Generated resources and references | Correct appearance, timing, movement or combat |
| Lua fixtures | Tested controller logic under the fixture | Engine graph, blending or visual response |
| Successful Lua `pcall` | Call completed without a Lua error | Native acknowledgement that a branch played |
| User's fresh native observations/log | The observed fixture and recorded lifecycle | Untested ages/actions, exact graph causality or multiplayer |

Native observations in this investigation were supplied by the user. Do not claim independent review of an entire recording when only the report/log was examined. Recheck installation and resource fingerprints after updates; these findings are version- and fixture-specific.

## 1. Four separate parts of a custom animation feature

1. **Authoring:** bone poses, keyframes, Actions, retargeting and loop preparation.
2. **Native encoding:** motion resource, skeleton/binding compatibility, timing, root travel and related metadata.
3. **Graph integration:** selection, interruption, transitions, blending, layers and current-action phase.
4. **Gameplay signal/lifecycle:** actual ability activation, active effect, expiry and actor cleanup.

The Tuareg investigation has broad authoring capability and a working gameplay signal. Native export is limited through the public prototype route. Immediate moving graph integration remains unqualified.

## 2. Installed Garrison replacement catalogue

| Prototype | Skeleton / skeletal LOD counts | Admitted replacements | Boundary |
|---|---|---|---|
| `english-villager-1` | 73 / 50 / 32 | 16 full-body calm unarmed idles; six restricted calm walks | Walk replacement is vertical pelvis bounce only |
| `english-spearman-2` | 48 / 32 / 26 | `navigation\idle_calm_basic_01` | Other movement, attacks and deaths remain inherited |

No Donso, archer, cavalry or camel prototype was catalogued in these checks. `base_spearshield` is a real native animation owner, but querying it as a build prototype returned **Unknown game prototype**. That does not make the native asset invalid.

The 16 villager idle names are under `navigation\idles\`:

```text
idle_calm
idle_calm_yawn
idle_calm_wipe_nose
idle_calm_stretch
idle_calm_shift
idle_calm_scratch_side
idle_calm_scratch_head_lean
idle_calm_look_up
idle_calm_look_sun
idle_calm_look_right_02
idle_calm_look_right
idle_calm_look_left
idle_calm_look_around2
idle_calm_look_around
idle_calm_headscratch
idle_calm_adjust_clothing
```

The six villager walks are `navigation\walks\calm_walk_0N_f_fast_slide` for N = **1, 2, 3, 4, 5, 7**. Only vertical `metarig_pelvis` motion is admitted; other bones must remain at rest. This is not a complete custom arm/leg gait exporter.

Clip inventory labels such as Attack, Death or Cheer can be inferred from names. They are not proof of replacement admission, gameplay binding or a callable interface. The inspected default binding is verified separately from those inferred categories. Representative unsupported clip checks returned **replacement timing is not qualified**.

### Important owner difference

The supported English spearman prototype uses **`base_spearman`**; the current Tuareg uses **`base_spearshield`**. Their skeletons can be compatible without their libraries or graphs being interchangeable. An English prototype build recorded **182 untouched clips**, while the inspected spear/shield container has **222 entries**.

Do not replace the Tuareg animator wholesale with the prototype animator and assume shield-specific motions remain. The successful model integration can reuse compatible skin geometry while retaining the Tuareg's native animation owner and gameplay.

## 3. Blender authoring, fitting and retargeting

Available authoring operations include copying a stock clip to an editable Action, creating a rest Action, keyframing bones, importing compatible FBX animation, fitting a skinned character and retargeting external motion. Blender can author shield gestures, idle motion, gait, attacks and death sequences even when their native export contracts are absent.

- Character fitting and motion retargeting have **separate mappings**. Do not assume that fitting the character also maps an unrelated animation rig.
- Documented presets recognize Mixamo, Renderpeople and Mesh2Motion humanoids. Manual mapping is available; the documented manual route has **22 required body roles**, with optional finger roles.
- Retargeting is FK; automatic foot locking/IK is not supplied. Review foot slide, shoulders, elbows, wrists, grip and seams.
- Wrist mapping alone cannot fully resolve palm twist. Index and middle-finger landmarks help establish palm direction and roll; thumb/finger mapping also matters for grip.
- Keep Named Weights requires matching hierarchy, bind pose and placement. It does not retarget weights or automatically fit proportions.
- The documented fitting route normalizes the strongest four influences and folds appropriate unmapped descendants into mapped ancestors. Unmapped weighted roots are refused.
- Bone count alone is not a compatibility test. Check names, parents, rest transforms, root and required role chains.
- External solver constraints need an exportable baked Action. Auto-Rig Pro or another retarget tool does not extend Garrison's native clip admission.

Creating a `.blend` Action is an authoring result. It is not a native playback result.

## 4. Sampling, timing and export contracts

The inspected Action sampler accepts **1–240 FPS** and **2–10,000 samples**, with a valid selected bone Action/range. It refuses unsupported object-motion channels, NLA/drivers, shear and unsupported constraints, while supporting generated Garrison Pose Controls.

For qualified looping idle replacement:

- First/last poses must match.
- Keep `metarig_root` stationary and bone scale at one.
- Put authored jump height on the pelvis rather than moving the armature object.
- `repeat_idle_cycle` fills the original clip duration with whole Action cycles, adjusting cycle speed. One Action can therefore play at different speeds in different slots.

For the qualified villager walk profile, `fit_walk_cycle` fits one pelvis cycle to stock duration and retains native root travel/events. It does not admit a full-body gait.

The skin FBX exporter uses **`bake_anim=False`**. Animation samples are supplied separately to the unit builder/private library. Changing that flag does not qualify a general AoE4 FBX animation exporter.

**Export Unit Model** writes source FBX/rig/manifest files. It does not itself add a playable unit and is not automatically consumed by Cook. **Build Unit** is the documented supported unit route. Package does not rebuild edited source motion.

Original attack timing, hit events, audio, equipment changes and root travel must be preserved when qualifying broader motion. These can involve other native resources/graph tracks, not only the visible bone keys.

## 5. Skeleton, equipment and model-only changes

The Tuareg's current skeleton has **48 bones**. Its compatible prototype skeletal LOD counts are **48/32/26**. The model builds retained the hierarchy/rest pose and verified bind compatibility. Skeletal LOD folding is not automatic geometry decimation.

Confirmed equipment sockets:

```text
Shield: MetaRig_LArmPalmSocket
Spear:  MetaRig_RArmPalmSocket
```

The Donso left-hand socket recipe applies across the four ages. Geometry/origin/orientation still need individual contact checks.

A rigid shield or weapon mesh can follow an animated hand socket. It does not need an independent skeleton just to move with the hand. Conversely, a static remix of the whole character exports its pose without the character's skin/animation behavior.

Changing the shield body relative to its fixed grip changes fitting in inherited actions; it does not create motion or remove the graph delay. A longer spear similarly changes equipment geometry, not attack reach or animation events automatically.

## 6. Native spear/shield library and graph discoveries

The native `base_spearshield` container was read with **222 animation entries**. The reflected `anims_spearshield` tree inventory contains:

- **2,978 objects** within that root's ownership scope.
- **206 animation-related tracks**: 202 ordinary tracks, three synchronized non-entity-weapon tracks and one animation-matrix track.
- **163 distinct named clip candidates**.
- An unresolved constituent expansion for matrix reference **`strafe_tense_jog`**.

This is a candidate inventory, not a demonstrated complete reachability manifest for this Tuareg's weapons/equipment. Do not claim that all 163 named clips need or receive a tested replacement without resolving their conditions.

| Native clip | Stored duration | Frames |
|---|---:|---:|
| `navigation\idle_calm_basic_01` | 16.200 s | 487 |
| `navigation\idle_shieldwall_01` | 3.567 s | 108 |
| `navigation\idle_shieldwall_02` | 5.533 s | 167 |
| `navigation\jog_shieldwall_01` | 3.067 s | 93 |
| `navigation\walk_tense_f_01` | 5.500 s | 166 |
| `navigation\jog_shieldwall_to_idle_quick_01` | 0.833 s | 26 |
| `navigation\jog_shieldwall_to_idle_01` | 1.767 s | 54 |
| `attack\stab_center_middle_01` | 1.967 s | 60 |

These are stored durations. Engine play rate, desired speed and blending can change visible timing. Clip duration alone does not prove the cause of a delay.

### Graph-reading caution

The read-only reflected parser validates type checksums, object ranges and declared field layouts. Reference-wrapper targets must be read through the reflected **`m_objectID` offset**, rather than assuming the first word is the target. In the inspected layout that target field is at offset eight; the preceding word can be a placeholder. Do not generalize this offset to another build without reflection evidence.

The parser correction and layout regression are part of the provenance of the later graph inventory.

## 7. Tuareg Q signal and private stock guard control

The receiving ability is the project-owned `ber_spearman_ranged_damage_reduction`. The recorded expected source PBG was **1073741839**; identifiers here are project-specific, not universal constants for other mods.

The controller uses the actual ability event and confirms active effect state. It filters the four private Tuareg tiers, tracks individual entities/squads and cleans up the owned visual selector. PBG IDs identify definitions; they are not per-unit animation playback handles.

Confirmed stock visual selector:

```text
spearman_shield_wall_byz
```

`anims_spearshield` reads that selector. The private schema retains the Donso properties and adds the guard property. The source investigation separated the visual consumers from the Byzantine simulation **Mode_Chooser** branch, which was not installed on the Tuareg.

Do not activate/copy the actual Byzantine shield-wall ability to obtain this visual: its gameplay also changes movement/attack speed. The current Tuareg ability data was preserved; documented values are **50% ranged-damage reduction for 15 seconds**, with a **90-second recharge field**. Actual damage reduction is a separate native gameplay measurement, not something established by the pose or log alone.

The retained native feedback log records four starts ending approximately 15 seconds later. The selector remains true at movement/stop edges. The user's clarification is that normal body motion works; the issue is delayed guard switching, not a confirmed frozen walking/attack skeleton.

Relevant markers:

```text
TUAREG_Q_ART_GUARD1 START
TUAREG_Q_ART_GUARD1 MOTION_EDGE ... raised_selector=true effect_active=true
TUAREG_Q_ART_GUARD1 GUARD_REASSERT
TUAREG_Q_ART_GUARD1 STOP ... reason=effect_ended
```

Reassertion only repairs an owned selector if it is actually cleared. It does not establish an interruptible graph transition. The controller's 19 Lua fixtures are logic evidence, not visual acceptance.

## 8. Moving delay and stop-to-idle dip

**Native observations:** idle Q changes promptly; moving Q takes roughly 3–5 seconds; a brief normal-pose dip on stopping was also reported in earlier tests.

**Source finding:** six continuous opportunity checks were located around idle calm/tense/defensive transitions; no equivalent moving opportunity checks were found in the inspected inventory.

**Leading hypothesis:** locomotion retains a selected branch until a permitted transition/clip boundary, explaining why a promptly asserted Q flag does not immediately change the moving pose. The stored 3.067-second guarded jog and longer walking clips are consistent with loop-boundary behavior.

**Still unproven:** exact engine reevaluation/interruption causality, the precise cause of the stop dip, and whether a particular missing opportunity check alone is sufficient to repair it. A successful source interpretation is not an engine trace.

If the selector stays true while the visible pose changes late or dips, that distinguishes graph/playback behavior from a dropped controller signal. Faster PBG polling alone is not a demonstrated fix.

## 9. Shrek-style cheering trial

The native cheering mechanism was applied to the Tuareg through the existing Q signal. It grants the native cheer ability only when needed, issues its native command, then toggles off/removes only its owned grant during cleanup.

**User-confirmed native result:** victory/cheer motion played; movement was blocked during the approximately 15-second trial; movement returned afterward.

This proves a callable full-body native behavior/lifecycle for that fixture. It does **not** prove an upper-body overlay, uninterrupted combat, or arbitrary cheer-slot replacement through Garrison's panel. The historical Shrek custom cheer recipe is a separate experimental route.

Do not use that movement-blocking behavior as the final solution to the present requirement that Q preserve locomotion and combat.

## 10. Forced native leaf trial: failed to improve switching

The experimental call used exact inspected native branch names:

```lua
StateTree_QueueGlobalStateTreeEntity(
    false,
    "anims_spearshield\\Locomotion\\Walk\\defensive\\jog_shieldwall_01",
    entity
)
```

The trial also inspected a normal walk branch for restoration and avoided forced restart during attack, charge or brace.

The log's **`accepted_call=true` is a successful `pcall`**, not native acknowledgement of playback. The API returned no playback handle/acknowledgement in this trial. The user observed no useful moving improvement.

Root priority, interruption, lifetime, cancellation and preservation of gait/attack phase were not qualified. The forced requests were removed from the later guard controller. Do not repeat submissions or change keep-alive behavior without establishing cleanup and phase semantics.

Documented `Entity_SetAnimatorAction/State/Event/Variable` APIs for simple animations do not establish that arbitrary `base_spearshield` clip names are valid actions/states. Their receiving bindings still need proof.

## 11. Custom raise/hold/lower authoring preview

An earlier separate Blender source contains an authored left-arm shield motion on the unchanged skeleton:

- Raise over approximately **0.4 seconds**.
- Hold through the **15-second** interval.
- Lower over approximately **0.4 seconds**.
- Preserve the root and keep bone scale unchanged.

It demonstrates source authoring only. It was **not successfully exported and bound as the native Q animation**, and it does not meet the later next-update/0.2-second switching target by itself.

Source: `art/tuareg_shield/Tuareg_Shield_Q_RaiseHold_SOURCE_ONLY.blend`.

Assigning it to the supported calm idle would affect ordinary calm idle, not automatically connect it to Q or replace guarded running/attacking.

## 12. Native Havok read/write research

The inspected `.rhka` is a Havok binary tagfile with SDK identifier **`20180200`**. It uses a custom **HavokAnimSet-family root**, rather than the generic `hkRootLevelContainer`, and **`hkaPredictiveCompressedAnimation`** payloads.

An experimental adapter using local Soulstruct-Havok dependencies achieved reading of the actual container, skeletons, bindings, clip metadata and compressed payloads. Garrison's supported preview sampler also produced parent-local bone samples from stock clips. Parsing compressed data is distinct from proving a new motion encoder.

Compatibility work was needed for the native custom root/binding types and constant-character arrays. The Shift-JIS reader can represent native ASCII `0x5c` path separators as U+00A5; normalize for lookup carefully without needlessly altering serialized source names.

**Writer result: failed.** The round-trip test failed generating type metadata for **`hkFlags[hkUint32]`**, where **`tag_format_flags` was None**, leading to a TypeError. Therefore a general safe replacement-library writer was not qualified. No output from that failed codec was accepted for delivery.

Do not invent type flags, hashes or ABI layouts to turn this into a claimed export pass. First prove a native round-trip preserving clip names, durations, compressed payloads, track-to-bone mappings and skeleton metadata; then qualify authored replacement motion separately.

The exact installed CLI probe for **`src.core.state_tree_authoring`** returned **unknown core module**. Internal module names in bundled manifests do not establish callable public interfaces. This is an installed-route limitation, not proof that AoE4 can never support private graphs.

## 13. Presentation, ragdoll and multiplayer boundaries

Garrison presentation assemblies/adapters can manage scripted prop transforms and visibility. They do not supply a general native bone-pose channel or guarantee atomic render writes.

Garrison 0.1.3 describes a Jolt-backed prepared-rig cosmetic ragdoll facility with stock fallback. The inspected Lua helper exposes impact-direction selection; an end-to-end general ragdoll authoring/activation route was not qualified here. Backend availability does not admit authored attack/death replacements, nor provide a proven live arm layer for a moving combat unit.

Cosmetic death playback must remain separate from gameplay death. No general multiplayer acceptance follows from solo source/build/playback tests.

## 14. What can be added now, and what still needs qualification

| Goal | Current position |
|---|---|
| New skinned Tuareg model following native motion | Working route; each new model still needs native action/LOD review |
| New shield/spear following native hand sockets | Working route; grip, clearance and combat-state switching need review |
| Custom supported spearman calm idle | Documented public route on the English prototype; Tuareg owner integration is a separate gate |
| Qualified villager idle or restricted pelvis walk | Documented bounded route; each new result needs native review |
| Trigger native stock cheer from an ability | Tuareg fixture passed user observation, but blocks movement |
| Select native shield-wall posture | Partial native success: prompt idle, delayed moving selection |
| Custom shield-raise source Action | Authored preview, no qualified Q native binding |
| General custom running/attack/death export | Unqualified through the installed public contracts |
| Instant Q while preserving locomotion/attack phase | Unresolved |

Two technically relevant future approaches are:

1. A private arm/shield animation layer that switches promptly while locomotion and attack progress continue underneath.
2. Ordinary/guarded motion pairs with phase-preserving transitions, rather than whole-body restarts.

Both require a verified native resource/graph route. A Stop command, movement-blocking cheer, permanent raised calm idle or equipment-offset swap is not proof of the requested ability animation.

## 15. Acceptance requirements for a broader animation route

- Private scope: the four Tuareg tiers; preserve other stock units and shared resources.
- Exact actual ability activation/effect-end signal; no raw global Q-key interception.
- Visible activation/expiry target within **0.2 seconds** of confirmed signal, including movement/attack.
- Preserve gait phase, current attack progress, hit timing, root travel, audio/equipment events and queued orders.
- Test idle, walking/running, turns/stops, attacks, charge, brace, torch switching, reactions and death.
- Verify all ages, training/upgrades, mixed selections, ownership/conversion, removal, repeated activation, restore and game end.
- Clean up owned pose state on actual effect end, with the existing 15-second deadline cap.
- Compare travel speed, attack cadence, responsiveness and actual ranged-damage reduction separately from visual appearance.
- Native acceptance requires observed playback/gameplay; multiplayer remains a separate gate.

## 16. Guidance to carry into a later skill update

1. Keep authoring, export, graph integration and gameplay trigger as separate gates.
2. State the two current prototypes and exact replacement limits; keep version/fingerprint verification.
3. Explain the `base_spearman` / `base_spearshield` library difference even when rigs are compatible.
4. Record native cheer as a movement-blocking fixture, and native shield selection as partial success.
5. Correct the interpretation of `accepted_call=true`: no playback acknowledgement.
6. Record the continuous idle checks and delayed moving behavior as evidence plus a hypothesis, not proven engine causality.
7. Keep broad clip encoding/private graphs and the failed Havok writer explicitly provisional.
8. Do not edit admission flags, invent fingerprints or alter shared native clips to claim success.
9. Treat source-only Actions, pose previews, fixture passes and cooked packages as distinct from native acceptance.
10. Keep future per-motion coverage and lifecycle/gameplay tests explicit; do not silently shrink a full custom-animation request to one idle.

## Evidence and source index

Paths below are relative to the project root unless identified as installed files. Preserve complete supporting files, not only this summary. Reverify portable paths on another machine.

| Subject | Source/evidence |
|---|---|
| Installed guide | `%APPDATA%/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/guide/rig-and-animation.html` |
| Installed version | Same extension's `blender_manifest.toml` |
| Current skill references | `C:/Users/RS/.codex/skills/aoe4-garrison-blender/references/animations.md`; `scenario-tools.md` |
| Installed catalogue/contracts | `output/tuareg_complete_overhaul/installed-contracts.json`; `native-slot-export-probes.json` |
| Graph summary/coverage | `output/tuareg_complete_overhaul/native-graph-summary.json`; `motion-coverage-candidates.json` |
| Graph parser/layout regression | `research/tuareg_shield_posture/read_native_tree.py`; `research/tuareg_complete_overhaul/test_native_reference_layout.py` |
| Native animation catalogue | `output/tuareg_force_trial/native-animation-catalog.json` |
| Sampled current stock clips | `output/tuareg_refined_trial/clips/clip143.json`, `clip131.json`, `clip130.json`, `clip119.json`, `clip88.json`, `clip219.json`, `clip117.json` |
| Source-only raise/hold/lower | `art/tuareg_shield/Tuareg_Shield_Q_RaiseHold_SOURCE_ONLY.blend`; `prepare_ability_pose_source.py` |
| Native cheer controller | `art/tuareg_shield/tuareg_q_cheer_trial.scar`; retained native pass under `output/tuareg_shield_posture_test/native-cheer-pass/` |
| Failed force controller/trial | `art/tuareg_shield/tuareg_q_force_trial.scar`; `output/tuareg_art_guard_trial/native-force-failed/warnings.log` |
| Later guard controller/fixtures | `art/tuareg_overhaul/tuareg_q_art_guard_trial.scar`; `test_art_guard_trial.py`; `output/tuareg_art_guard_trial/controller-green.log` |
| Native selector/movement feedback | `output/tuareg_refined_trial/native-original-art-feedback.log` |
| Havok adapter/tests | `research/tuareg_complete_overhaul/native_havok_codec.py`; `test_native_havok_codec.py` |
| Failed writer/type metadata | `output/tuareg_force_trial/native-codec-roundtrip.log`; `codec-typeflags.log` |
| Private graph CLI probe | `output/tuareg_refined_trial/private-graph-interface-probe.log` |
| Source-only shield pose fitting | `output/tuareg_refined_trial/shield-fit.json`; `art/tuareg_refined/check_shield_fit.py` |

This file is a discovery record for later reconciliation into the skill. It is not an instruction to update the skill or resume the parent thread's implementation automatically.
