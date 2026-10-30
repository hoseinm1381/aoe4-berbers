from pathlib import Path
p=Path('art/buildings/wall_tower/build_wall_tower.py');t=p.read_text();t=t.replace('for x in [-2.64,-1.76,1.76,2.64]:','for x in [-1.76,1.76]:')
t=t.replace("# Cut real arrow slots in front upper chamber.","""# Actual recessed rear chamber access from the elevated wall walk.
    chamber=bpy.data.objects['front_upper_chamber']
    cutter=prism('TEMP_chamber_door',portal_outline(0,7.01,1.15,2.45),-2.25,-1.25,'shadow',80)
    bpy.context.view_layer.objects.active=chamber;mo=chamber.modifiers.new('horseshoe_chamber_recess','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
    prism('rear_horseshoe_chamber_door',portal_outline(0,7.01,1.15,2.45),-1.75,-1.72,'cedar',80)
    # Cut real arrow slots in front upper chamber.""")
p.write_text(t)
