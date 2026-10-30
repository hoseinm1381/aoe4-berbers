import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'art/unit_remix_0_5_0/mounted/zenata_age04/zenata_age04.blend'))
for m in bpy.data.materials:
 if m.use_nodes:
  print('MAT',m.name,[(n.name,n.image.name if n.type=='TEX_IMAGE' and n.image else '') for n in m.node_tree.nodes if n.type=='TEX_IMAGE'],flush=True)
