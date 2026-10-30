import bpy
for m in bpy.data.materials:
 if m.use_nodes:
  print(m.name)
  for n in m.node_tree.nodes:
   if n.type=='RGB' or 'GARRISON' in n.name:print(n.name,n.type,[(s.name, getattr(s,'default_value',None)) for s in n.inputs],[(s.name,getattr(s,'default_value',None)) for s in n.outputs])
