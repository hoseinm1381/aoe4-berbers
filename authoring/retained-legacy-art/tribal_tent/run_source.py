"""Separate source-authoring process; does not touch the live Blender session."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
scope={'__file__':str(ROOT/'art/tribal_tent/build_source.py')}
exec(compile(Path(scope['__file__']).read_text(),scope['__file__'],'exec'),scope)
scope['initialize']();scope['structural']()
import bpy,json,sys
out=ROOT/'output/tribal_tent/iteration001'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'structural_checkpoint.blend'))
(out/'structural-contacts.json').write_text(json.dumps(scope['CONTACTS'],indent=2))
print('STRUCTURE_CHECKPOINT_SAVED',flush=True)
if '--complete' in sys.argv:
    scope['detailed']();scope['validate_save']()
