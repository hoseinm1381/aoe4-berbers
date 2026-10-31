"""Task-owned full source pass and previews; safe in a separate hidden Blender."""
from pathlib import Path
import bpy,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tribal_tent/iteration001'
print('FRESH_SOURCE_STARTED',flush=True)
scope={'__file__':str(ROOT/'art/tribal_tent/build_source.py')};exec(compile(Path(scope['__file__']).read_text(),scope['__file__'],'exec'),scope)
scope['initialize']();scope['structural']()
(OUT/'structural-contacts.json').write_text(json.dumps(scope['CONTACTS'],indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'structural_checkpoint.blend'))
scope['detailed']();scope['validate_save']()
sys.argv.append('--authored')
scope={'__file__':str(ROOT/'art/tribal_tent/finish_source.py')};exec(compile(Path(scope['__file__']).read_text(),scope['__file__'],'exec'),scope)
print('FRESH_SOURCE_AND_PREVIEWS_COMPLETE',flush=True)
bpy.ops.wm.quit_blender()
