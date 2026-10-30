from pathlib import Path
p=Path('art/buildings/palisade/build_palisade.py');s=p.read_text();s=s.replace("  if rise:\n", "  bpy.context.view_layer.update()\n  if rise:\n")
mark="  coll=bpy.data.collections.new(name);"
insert='''  # Collapse repeated modules by role/stage; keep reproducible anatomy in recipe.
  groups={}
  for ob in objs:
   key=(ob.name.split('.')[0].replace('corner_return_',''),ob['ber_material_role'],ob['garrison_building_first_stage'])
   groups.setdefault(key,[]).append(ob)
  merged=[]
  for key,group in groups.items():
   bpy.ops.object.select_all(action='DESELECT')
   for ob in group:ob.select_set(True)
   bpy.context.view_layer.objects.active=group[0]
   if len(group)>1:bpy.ops.object.join()
   merged.append(bpy.context.object)
  objs=merged
  PARTS=[p for p in PARTS if p['object'] in bpy.data.objects]
'''
s=s.replace(mark,insert+mark);p.write_text(s)
