import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'art/unit_remix_0_5_0/mounted/mehari_age02/mehari_age02.blend'))
c=bpy.data.objects['Berber candidate textured']
for o in c.children_recursive:
 if o.type=='MESH' and o.get('garrison_lod_level')==1:
  pts=[o.matrix_world@Vector(v) for v in o.bound_box]
  print('BOUNDS',o.name,[(s,min(getattr(v,s) for v in pts),max(getattr(v,s) for v in pts)) for s in ['x','y','z']],flush=True)
