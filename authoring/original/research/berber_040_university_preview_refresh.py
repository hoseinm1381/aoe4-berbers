import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'research'));from berber_040_university_geometry import review
art=root/'art/building_remix_0_4_0/university';bpy.ops.wm.open_mainfile(filepath=str(art/'Berber_University_Age4_040.blend'))
rows=[]
for mat in bpy.data.materials:
 if mat.node_tree and 'extra' in mat.name:
  for nd in mat.node_tree.nodes:
   if nd.type=='TEX_IMAGE' and ('normalMap2' in nd.name or 'normalMap3' in nd.name):
    nd.image=bpy.data.images.load(str(art/'normal_tiles.png'),check_existing=True);rows.append({'material':mat.name,'node':nd.name,'image':str(art/'normal_tiles.png')})
for ob in list(bpy.context.scene.objects):
 if ob.type=='LIGHT':bpy.data.objects.remove(ob,do_unlink=True)
review(art,'koutoubia_university_daylight',[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render])
(art/'normal-preview-check.json').write_text(json.dumps(rows,indent=2));print('NORMAL_PREVIEW_SLOTS',len(rows))
