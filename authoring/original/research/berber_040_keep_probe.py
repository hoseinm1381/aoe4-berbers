import bpy,json,sys
from pathlib import Path
p=Path('art/building_remix_0_3_1/marrakech/Dar_al_Jihad_Marrakech_Age3_0_3_1.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(p))
rows=[]
for o in bpy.data.objects:
 if o.type=='MESH': rows.append({'name':o.name,'hidden':o.hide_render,'viewport':o.hide_get(),'vertices':len(o.data.vertices),'properties':dict(o.items()),'materials':[m.name for m in o.data.materials if m]})
print('INVENTORY',json.dumps(rows,default=str))
print('IMAGES',[(i.name,i.filepath) for i in bpy.data.images][:8])
