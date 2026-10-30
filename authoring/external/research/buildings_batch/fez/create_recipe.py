from pathlib import Path
R=Path.cwd(); A=R/'art/buildings/fez';Q=R/'research/buildings_batch/fez'
s=(R/'art/buildings/university/build_university.py').read_text()
s=s.replace('university','fez').replace('University','Fez').replace('UNIVERSITY','FEZ')
start=s.index('def build(age):');end=s.index('    # Every fitted arcade',start)
body='''def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();floor=.16
    box('scholar_court_foundation',(0,0,.08),(4.4,4.4,.16),'stone',0)
    # Scale-aware source envelope 4.4m, at live 130% animator scale =5.72m inside actual6m footprint.
    for side,x in [('west',-2.04),('east',2.04)]:
        wall=box(side+'_outer_wall',(x,0,1.31),(.20,4.0,2.30),'earth',40);contact(wall.name,'scholar_court_foundation')
        for yy in [-1.22,0,1.22]:
            o=open_arch(side+'_hollow_arcade',0,0,.90,1.75,2.30,.16)
            o.rotation_euler.z=math.pi/2;o.location.x=x/abs(x)*1.18;o.location.y=yy
            bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=False);contact(o.name,'scholar_court_foundation')
        roof=box(side+'_gallery_roof',(x/abs(x)*1.62,0,2.51),(1.04,4.0,.10),'cedar',60);contact(roof.name,wall.name)
        # Student-cell upper shell, divided into three actual chambers opening toward the court.
        cellwall=box(side+'_student_rear_wall',(x,0,2.96),(.20,4.0,.80),'lime',60);contact(cellwall.name,roof.name)
        for yy in [-2.0,-.64,.64,2.0]:
            div=box(side+'_cell_divider',(x/abs(x)*1.62,yy,2.96),(.84,.10,.80),'earth',60);contact(div.name,roof.name)
        for yy in [-1.25,0,1.25]:
            shutter=box(side+'_cell_cedar_shutter',(x/abs(x)*1.21,yy,2.98),(.12,.78,.76),'cedar',80)
            box(side+'_student_sleeping_platform',(x/abs(x)*1.72,yy,2.63),(.40,.70,.14),'straw',80)
            box(side+'_neutral_cell_owner_band',(x/abs(x)*1.137,yy,3.24),(.026,.76,.12),'owner_cloth',100)
        cap=box(side+'_cell_roof',(x/abs(x)*1.62,0,3.41),(1.04,4.10,.10),'earth',80);contact(cap.name,cellwall.name)
        for xx in [x/abs(x)*1.18,x]:
            para=box(side+'_lime_parapet',(xx,0,3.59),(.12,4.10,.26),'lime',80);contact(para.name,cap.name)
        # Fitted cedar lintel spans and shallow geometric plaster diamonds in the arcade spandrels.
        box(side+'_cedar_carved_frieze',(x/abs(x)*1.08,0,2.36),(.10,3.70,.14),'cedar',100)
        for yy in [-1.76,-.61,.61,1.76]:
            for z in [1.95,2.13]:
                o=box(side+'_plaster_geometric_carving',(x/abs(x)*1.08,yy,z),(.035,.10,.10),'stone',100);o.rotation_euler.x=math.pi/4
    rear=box('teaching_hall_rear',(0,2.03,1.56),(2.26,.18,2.80),'lime',40);contact(rear.name,'scholar_court_foundation')
    arch=open_arch('teaching_open_reading_bay',0,1.26,1.70,2.20,2.80,.18);contact(arch.name,'scholar_court_foundation')
    r=box('teaching_hall_roof',(0,1.64,3.01),(2.26,.98,.10),'cedar',60);contact(r.name,rear.name)
    para=box('teaching_hall_parapet',(0,2.08,3.19),(2.26,.12,.26),'lime',80);contact(para.name,r.name)
    entry=open_arch('carved_main_portal',0,-2.03,1.40,2.25,2.70,.20);contact(entry.name,'scholar_court_foundation')
    lintel=box('portal_cedar_carved_lintel',(0,-2.03,2.94),(1.75,.30,.16),'cedar',60);contact(lintel.name,entry.name)
    for xx in [-1.34,1.34]:
        wall=box('front_guest_cell_wall',(xx,-2.03,1.31),(.94,.20,2.30),'earth',40);contact(wall.name,'scholar_court_foundation')
        box('guest_cell_roof',(xx,-1.73,2.51),(.94,.80,.10),'cedar',60)
        box('front_neutral_owner_band',(xx,-2.145,2.17),(.74,.025,.16),'owner_cloth',100)
    # Facade carved star/diamond relief is geometric, no invented writing.
    for xx in [-.60,-.40,-.20,0,.20,.40,.60]:
        o=box('portal_carved_cedar_diamond',(xx,-2.192,2.94),(.085,.025,.085),'straw',100);o.rotation_euler.y=math.pi/4
    # Square central basin is hollow: bottom plus four edge blocks with measurable water seating.
    foot=box('fountain_plinth',(0,0,.22),(.90,.90,.12),'lime',20);contact(foot.name,'scholar_court_foundation')
    bed=box('fountain_basin_bottom',(0,0,.31),(.72,.72,.06),'stone',40);contact(bed.name,foot.name)
    for x,y,sx,sy in [(-.40,0,.08,.88),(.40,0,.08,.88),(0,-.40,.72,.08),(0,.40,.72,.08)]:
        box('fountain_basin_rim',(x,y,.41),(sx,sy,.26),'lime',60)
    water=box('fountain_water',(0,0,.345),(.70,.70,.01),'shadow',100);contact(water.name,bed.name)
    jet=tube('fountain_faceted_spout',(0,0,.50),.055,.30,'stone',100)
    # Ground-level tile inlays and scholarly desk are physically seated.
    for x in [-.78,.78]:
        for y in [-1.50,-1.0,-.5,0,.5,1.0]:
            tile=box('courtyard_geometric_inlay',(x,y,.165),(.15,.15,.01),'clay',100);tile.rotation_euler.z=math.pi/4;contact(tile.name,'scholar_court_foundation')
    desk=box('teaching_desk_pedestal',(0,1.68,.43),(.40,.36,.54),'cedar',80);contact(desk.name,'scholar_court_foundation')
    top=box('teaching_desk_top',(0,1.68,.74),(.74,.50,.08),'cedar',80);contact(top.name,desk.name)
    page=box('scholarly_open_book',(0,1.68,.80),(.38,.31,.04),'straw',100);contact(page.name,top.name)
    # Neutral banner hangs from measured cedar support and faces both front and court.
    box('banner_wall_bracket',(.94,-2.04,2.61),(.08,.08,.68),'cedar',80)
    box('banner_crossbar',(.73,-2.04,2.93),(.48,.08,.06),'cedar',80)
    box('neutral_owner_banner',(.73,-2.065,2.56),(.38,.035,.68),'owner_cloth',100)
'''
s=s[:start]+body+s[end:]
# Replace former ray routine with general world-space rays perpendicular to each actual arch facade.
start=s.index('    for o in [o for o in bpy.context.scene.objects');end=s.index('    (OUT/\'void_checks.json\')',start)
s=s[:start]+'''    for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and ('hollow_arcade' in o.name or 'open_reading_bay' in o.name or 'main_portal' in o.name)]:
        bm=bmesh.new();bm.from_mesh(o.data);tree=BVHTree.FromBMesh(bm)
        lo,hi=bounds(o);axis=0 if 'hollow_arcade' in o.name else 1
        for z in [.5,1.25]:
            world=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,z));world[axis]=lo[axis]-.1
            origin=o.matrix_world.inverted()@world;direct=Vector((1,0,0)) if axis==0 else Vector((0,1,0));direct=o.matrix_world.inverted().to_3x3()@direct
            hit=tree.ray_cast(origin,direct,hi[axis]-lo[axis]+.2)[0];assert hit is None,(o.name,z)
            voids.append({'object':o.name,'height':z,'ray_clear':True})
        bm.free()
''' +s[end:]
s=s.replace('-4.001','-2.3077').replace('4.001','2.3077').replace("'footprint_m':[8,8]","'footprint_m':[6,6],'animator_scale_percent':130,'scaled_source_envelope_m':[5.72,5.72]")
s=s.replace("'clear_gateway_m':2.46,'central_transit_corridor_m':1.8", "'clear_gateway_source_m':1.204")
s=s.replace('location=(10,-13,11)','location=(7,-9,8)').replace('ortho_scale=11.5','ortho_scale=7.0')
s=s.replace("    print('FEZ_DONE'", "    scene.render.resolution_x=768;scene.render.resolution_y=768;cam.location=(3,-4,5);cam.data.ortho_scale=4.5;cam.rotation_euler=(Vector((0,0,1.1))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'age4_interior.png');bpy.ops.render.render(write_still=True)\n    print('FEZ_DONE'")
s=s.replace('untouched installed Abbasid Age IV fez','untouched installed Abbasid Age IV university').replace('Untouched installed Abbasid Age IV fez','Untouched installed Abbasid Age IV university')
(A/'build_fez.py').write_text(s)
run=(R/'research/buildings_batch/blacksmith/run_hidden.py').read_text().replace('blacksmith','fez');(Q/'run_hidden.py').write_text(run)
audit=(R/'research/buildings_batch/university/audit_saved.py').read_text().replace('university','fez').replace('University','Fez').replace('-4.001','-2.3077').replace('4.001','2.3077');(Q/'audit_saved.py').write_text(audit)
