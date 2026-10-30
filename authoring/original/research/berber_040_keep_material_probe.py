import bpy
bpy.ops.wm.open_mainfile(filepath=r'E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai/art/building_remix_0_4_0/keep/Berber_keep_Age3_040.blend')
for m in bpy.data.materials:
 if m.node_tree:
  print('MAT',m.name)
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':print('IMG',n.name,n.label,n.image.name if n.image else '')
