from pathlib import Path
p=Path('art/buildings/tc/build_tc.py');s=p.read_text();needle="    for label,c,size,rh in [('hall'"
patch="""    # Hollow loggia behind the arch panel, leaving an outer wall and roof-bearing ends.
    west=bpy.data.objects['west_range']
    cavity=box('TEMP_gallery_hollow',(-3.34,0,floor+1.05),(1.00,3.15,2.10),'shadow',40)
    bpy.context.view_layer.objects.active=west;mo=west.modifiers.new('Covered civic loggia','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cavity;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cavity,do_unlink=True);PARTS.pop()
"""
assert needle in s;s=s.replace(needle,patch+needle);p.write_text(s)
