# Berber0.9.0 retained sources and rebuild

Working0.8.1 remains the immutable binary input to the090 reproduction recipe.
Its complete voice integration is retained; do not reconstruct from an older
Content Editor cook. Future versions should instead start from final090SGA
and selectively apply new changes, so they retain this visual update too.

## Inputs and ownership

- `art/building_remix_0_9_0/fez/Madrasa_of_Fez_090.blend` and
  `wonder/Berber_Koutoubia_Wonder_090.blend` are packed editable sources. Original
  040 sources and their backups are unchanged. Fez generation reads the retained
  040Fez source/atlases and `research/berber_040_fez_runner.py`; Wonder uses its
  own090recipe/runner plus the retained040geometry helper. Keep those helpers.
- Both final `export_lod0` folders contain retained FBX, material maps and explicit
  stage lists. Native cook can run directly from these; Blender is not required
  unless changing/re-exporting the models. Editable parts1032/461 become6groups
  each, preserving triangles and stage thresholds0/20/40/60/80/100.
- Current installed Garrison compiled core/archiver and the prepared model-capable
  EssenceEditor are needed. Integration records exact editor/source/cook hashes.
  The prepared editor is under `%LOCALAPPDATA%/Garrison/Kit/tools/essence-object-editor`;
  it is a local tool dependency, not a Steam game-file modification.
- `output` resolves to `F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output`.
  Large generated cook/readbacks go there. New editable090art remains on E:.

## Recreate the cooked candidate

Run from the project root with Python3.13. The retained final exports avoid any
dependency on removed temporary exports or decoded readbacks.

```powershell
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/berber090/integrate.py audit
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/berber090/integrate.py prepare
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/berber090/integrate.py cook
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/berber090/integrate.py assemble
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/berber090/integrate.py compose
& 'C:/Users/RS/AppData/Local/Programs/Python/Python313/python.exe' -B research/berber090/integrate.py strong_verify
```

Use a separate version/output before reproducing a delivered release. These
commands regenerate the disposable090project/readbacks; preserve final delivered
ZIP/SGA before experimentation. The release script refuses to overwrite a ZIP.
`research/package_unified_release.py` can package a new validated candidate SGA
with a new three-part version. It reads081metadata/coverage only; always supply
the actual new SGA, never silently fall back to its default081archive.

## Re-authoring and presentation

Use a task-owned background Blender5.2 process, leaving live user work alone:

```powershell
& 'E:/Blender5.2/blender.exe' --factory-startup -b --python research/berber090/fez.py
& 'E:/Blender5.2/blender.exe' --factory-startup -b --python research/berber090/wonder.py
```

The renderer is separate from final source evaluation. `review_fez.py` captures
six solid views plus game/courtyard views; `review_pair.py` loads both collections
and compares them under one camera/light using actual actor scales1.3/1.5.
Dependencies must be updated before reading appended objects' world transforms.
Presentation cameras are not asset meshes.

`export_source.py` takes `-- ABSOLUTE_BLEND COLLECTION_NAME ABSOLUTE_NEW_EXPORT_DIR`.
Fez collection: `090_Marinid_College`; Wonder:
`090_Koutoubia_monumental_mosque`. Use a fresh directory: existing exports are
preserved/refused. After changing authoritative exports, repeat prepare and cook.
It invokes installed Garrison mesh preflight/parts contracts and exact material
snapshot helpers, with standard building FBX and UV conventions. This avoids
unrelated UI registration dependencies without editing the installed extension.

## Evidence and limits

Release-validation and cleanup reports retain delivery hashes. Composition and
full-member SHA proofs retain changed/unchanged members, source/cook evidence and
texture dependencies after decoded copies are removed. All voices/SCAR, native
RGO graphs, flags, stamps and tiers are preserved. Only two actor scale fields,
six model/geometry/material members and six new textures change.

Native visibility checks cover healthy/damage states and hiding completed meshes
in ruins, while retaining the existing lifecycle graphs. No new independently
qualified ruin geometry or lower-LOD activation is claimed. Garrison import and
in-game construction/damage/destruction, two player colours, entrances and voice
regression remain user acceptance checks, per the request to import personally.

No old voice installer, native loose-audio deployment or alternate launcher is
required. Keep081and090archives, all original voice/Blender assets, final source
exports, recipes and compact evidence; remove only inventoried generated caches.
