"""Run in BACKGROUND Blender on restored copies, never on the old project.

blender --background --factory-startup --python tools/relocate_blends.py -- AUTHORING
"""
import bpy
import json
import sys
from pathlib import Path

root=Path(sys.argv[sys.argv.index('--')+1]).resolve()
assert (root/'RESTORE_RECEIPT.json').is_file(),'Not a verified editable-master restoration'
index=json.loads((Path(__file__).resolve().parents[1]/'source/master-index.json').read_text())
by_original={x['original'].replace('\\','/').lower():x for x in index['files']}
prefixes=[('E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai',root/'original'),
          ('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014',root/'external')]
count=0
for path in sorted(root.rglob('*.blend')):
    assert path.resolve().is_relative_to(root)
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    changed=False
    for item in [*bpy.data.images,*bpy.data.libraries]:
        if isinstance(item,bpy.types.Image) and item.packed_file:
            continue
        if not item.filepath:continue
        current=item.filepath.replace('\\','/')
        for old,new in prefixes:
            if current.lower().startswith(old.lower()+'/'):
                target=new/current[len(old)+1:]
                if isinstance(item,bpy.types.Image) and len(str(target))>230:
                    row=by_original[current.lower()]
                    target=root/'_images'/(row['sha256']+target.suffix.lower())
                assert target.exists(),target
                item.filepath=str(target)
                changed=True
                break
    if changed:
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
        count+=1
print('RELOCATED_RESTORED_BLENDS',count,flush=True)
