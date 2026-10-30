from pathlib import Path
p=Path('art/buildings/tc/build_tc.py');s=p.read_text()
needle="    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']"
patch='''    # Rear council portal and windows are cut into the room, not pasted on the face.
    cut_portal(hall,0,1.73,floor+.01,1.32,2.28)
    for wx in [-2.75,2.75]:
        cutter=box('TEMP_hall_window',(wx,1.73,1.82),(.58,.60,.85),'shadow',40)
        bpy.context.view_layer.objects.active=hall;mo=hall.modifiers.new('Real council window','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
        box('council_shutter',(wx,1.91,1.82),(.56,.05,.83),'cedar',80)
        box('council_sill',(wx,1.68,1.38),(.76,.35,.12),'stone',80)
        for sx in [-.17,0,.17]:box('window_joinery',(wx+sx,1.87,1.82),(.035,.04,.80),'straw',100)
    # Original segmented arch voussoirs make the gate's horseshoe outline legible.
    if age>=2:
        r=1.05; zc=floor+gh-.55
        for k in range(13):
            t1=math.radians(-25+k*230/13);t2=math.radians(-25+(k+1)*230/13)
            outline=[(rr*math.cos(t),zc+rr*math.sin(t)) for rr,t in [(r,t1),(r+.25,t1),(r+.25,t2),(r,t2)]]
            prism('gate_arch_voussoir',outline,-3.88,-3.72,'stone' if age==2 else 'lime',80)
        for x in [-1.10,1.10]:box('arch_springer',(x,-3.8,floor+.90),(.25,.16,1.8),'stone',60)
    if age==1:
        for x in [-3.35,-2.4,-1.45,1.45,2.4,3.35]:
            box('earth_hall_timber_upright',(x,1.716,floor+h/2),(.12,.08,h),'cedar',20)
        box('hall_timber_plate',(0,1.70,floor+h-.12),(7.65,.12,.18),'cedar',60)
        for xx in [-3.65,3.65]:
            for yy in [-1.40,-.50,.40,1.3]:box('flat_roof_beam_ends',(xx,yy,floor+h-.47),(.13,.22,.15),'cedar',60)
    # Exterior side slit shutters, inset in the habitable wing.
    east=bpy.data.objects['east_range']
    for yy in [-.85,.85]:
        cutter=box('TEMP_side_window',(4.47,yy,1.55),(.45,.50,.70),'shadow',40)
        bpy.context.view_layer.objects.active=east;mo=east.modifiers.new('Side window cut','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
        box('side_inset_shutter',(4.30,yy,1.55),(.05,.48,.68),'cedar',80)
        box('side_sill',(4.48,yy,1.19),(.22,.67,.10),'stone',80)
'''
assert needle in s;s=s.replace(needle,patch+needle);p.write_text(s)
