import bpy
for mat in bpy.data.materials:
 if mat.use_nodes and (node:=mat.node_tree.nodes.get('GARRISON Material Controls')):
  print(mat.name,[s.name for s in node.inputs])
