import bpy
bpy.ops.wm.open_mainfile(filepath=r'E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai/art/building_remix_0_4_0/university/Berber_University_Age4_040.blend')
for m in bpy.data.materials:
 if m.node_tree:print('MAT',m.name,[(n.name,n.image.name if n.image else None) for n in m.node_tree.nodes if n.type=='TEX_IMAGE'])
