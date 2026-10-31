# Berber house 0.2.2 implementation ledger

Authorized plan: remix Abbasid House Control A Ages I-IV; release only the house changes on the verified 0.2.1 archive. No replacement from primitives. Keep native owner colour and existing gameplay.

Baseline archive SHA256: 348378e6562cd5bc16bb9167a4e2596c9691209383a470d43e4273b21c3d800e.

Work is isolated in task-owned art/output paths on codex/berber-house-022. Existing uncommitted art, source and unrelated files are preserved; an ordinary worktree would omit the untracked baseline and asset work.

Ruling: use the native stock-model variant route, retaining original topology, masks, team-colour layers and construction/damage selectors. Apply earthen plaster, darker timber, geometric trim and uniform 0.46 visual stamp scale. The cultural changes are a surface remix; wall geometry is not remodeled. This departure from the generic Building exporter prevents loss of native team colour. Native selector consumption is pending game testing.

2026-10-13: all four stock families decoded; 40 repainted maps, four untouched .blend files, four editable surface-remix .blend files and 32 inspection captures saved. A final read-only reviewer found a cross-block native palette lookup bug and unbound readback caches. Both are corrected before final release assembly: tonal fields are collected across all material blocks and archive hashes bind readback directories.

Steps: decode all stock ages; inspect native parts/materials; author editable remixes and before/after views; fresh Garrison cook; private house-only bindings; archive readback and untouched-member checks; ZIP and user test guide.

Completed 2026-10-13: all steps passed. Fresh Garrison native texture/model-variant cook succeeded; four stamp RDOs compiled with the ordinary Steam Content Editor (stamp-build-v4, exit 0). The thin prepared-editor stamp fixture did not qualify and remains diagnostic evidence. Final stamp vectors are verified from native raw float bytes. Current cook source PNGs match all 40 authored PNG hashes.

Final archive: 400 actual members, comprising 335 byte-preserved baseline members, one changed house actor and 64 new private house resources. SHA256 5cdb9b2c264eecc1d0986c3c50899bf15ac9ea1aa653093c8c24697becd9fb38. Five material fixture tests passed. Final reviewer verified archive/ZIP hashes, payload readback, private tiers and main age requirements. Native acceptance remains pending.

Nonblocking rerun limitation: stages reuses a successful cook/stamp run for the same saved inputs. For a future revision, perform a fresh native cook and select a new stamp-run directory; do not treat this cached invocation as a revision build. Archive extraction itself is hash-bound. The current artifact's 40 staged PNGs and native stamp references/transforms were checked against authored inputs.

Native acceptance belongs to the user's test. No match, audio or multiplayer acceptance may be inferred from build success.

2026-10-13 native failure and repair: user reported completed houses invisible while the tent renders. Installed archive hash matches delivered 0.2.2; game logs confirm house completion/population. The four private house tier RGDs were mistakenly inserted in `data`, whereas native attribute loading requires `attrib`. Previous archive checks verified member bytes and paths but omitted TOC admission. Corrected the helper to split media/attribute insertion and added namespace regression validation. 0.2.3 preserves all 400 member bytes and moves only the four house tiers to attrib. Native retest pending. See `output/berber_update_0_2_3/DIAGNOSIS.md`.
