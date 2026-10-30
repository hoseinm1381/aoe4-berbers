from pathlib import Path
R=Path.cwd();A=R/'art/buildings/university';Q=R/'research/buildings_batch/university'
s=(R/'art/buildings/blacksmith/build_blacksmith.py').read_text();p=s[:s.index('def build(age):')].replace('/blacksmith','/university').replace('Blacksmith','University')
siege=(R/'art/buildings/siege/build_siege.py').read_text();p+=siege[siege.index('def bounds(o):'):siege.index('def tube(')]
body='''
def open_arch(name,cx,y,width,height,wallheight,depth=.22):
    o=box(name,(cx,y,.16+wallheight/2),(width+.26,depth,wallheight),'lime',40)
    cut=prism('TEMP_opening',portal_outline(cx,.15,width,height),y-depth,y+depth,'shadow',40)
    bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Through horseshoe void','BOOLEAN');m.operation='DIFFERENCE';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cut,do_unlink=True);PARTS.pop()
    # Re-project final cut faces, not the pre-boolean wall UV.
    o.data.materials.clear();PARTS.pop();finish(o,name,'lime',40)
    return o

def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();floor=.16
    box('scholar_court_foundation',(0,0,.08),(7.6,7.6,.16),'stone',0)
    # Solid outer enclosure encloses genuinely open ground-floor galleries.
    for side,x in [('west',-3.55),('east',3.55)]:
        box(side+'_outer_wall',(x,0,1.46),(.24,6.86,2.60),'earth',40);contact(side+'_outer_wall','scholar_court_foundation')
        for yy in [-2.35,-.9,.55,2.0]:
            o=open_arch(side+'_hollow_arcade',0,0,1.16,1.94,2.60)
            o.rotation_euler.z=math.pi/2;o.location=(x/abs(x)*1.78,yy,0);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
            contact(o.name,'scholar_court_foundation')
        box(side+'_gallery_roof',(x/abs(x)*2.68,0,2.81),(2.03,6.86,.10),'earth',60);contact(side+'_gallery_roof',side+'_outer_wall')
        for xx in [x/abs(x)*1.73,x]:
            box(side+'_parapet',(xx,0,3.04),(.18,6.86,.36),'lime',80);contact(bpy.context.object.name,side+'_gallery_roof')
        # Upper cells are articulated by recessed cedar shutters and stone lintels.
        for yy in [-2.1,-.65,.8,2.25]:
            box(side+'_owner_gallery_frieze',(x/abs(x)*1.65,yy,2.47),(.025,1.0,.16),'owner_cloth',100)
            box(side+'_cedar_shutter',(x/abs(x)*3.69,yy,1.66),(.04,.49,.62),'cedar',80)
            box(side+'_stone_sill',(x/abs(x)*3.69,yy,1.32),(.14,.66,.07),'stone',80)
    # Taller library across rear court: open study bay, closed rear wall.
    box('library_rear_wall',(0,3.38,1.83),(6.86,.25,3.34),'earth',40);contact('library_rear_wall','scholar_court_foundation')
    for x in [-1.2,0,1.2]:
        o=open_arch('library_open_reading_bay',x,2.35,.96,2.48,3.34);contact(o.name,'scholar_court_foundation')
    box('library_roof',(0,2.93,3.55),(3.56,1.16,.10),'earth',60);contact('library_roof','library_rear_wall')
    for yy in [2.35,3.45]:box('library_roof_parapet',(0,yy,3.79),(3.56,.14,.38),'lime',80);contact(bpy.context.object.name,'library_roof')
    # Carved entry surround has a genuinely open portal and an uninterrupted court.
    for x in [-2.53,2.53]:
        box('front_enclosure',(x,-3.35,1.46),(1.94,.24,2.60),'earth',40);contact(bpy.context.object.name,'scholar_court_foundation')
    portal=open_arch('carved_main_portal',0,-3.35,2.86,2.30,2.95,.30);contact(portal.name,'scholar_court_foundation')
    box('portal_cedar_lintel',(0,-3.35,3.19),(3.15,.40,.16),'cedar',60);contact('portal_cedar_lintel','carved_main_portal')
    for x in [-1.43,1.43]:box('portal_carved_stone_jamb',(x,-3.535,1.35),(.15,.07,2.38),'stone',80)
    for x in [-1.1,-.74,-.37,0,.37,.74,1.1]:
        o=box('portal_geometric_diamond',(x,-3.515,2.78),(.15,.04,.15),'stone',100);o.rotation_euler.y=math.pi/4
    box('portal_neutral_owner_band',(0,-3.563,3.19),(2.32,.025,.12),'owner_cloth',100)
    # Two wall-seated cedar bookcases; every book is seated on a shelf.
    for x in [-.8,.8]:
        name='library_bookcase'
        box(name+'_back',(x,3.215,1.24),(.66,.10,2.16),'cedar',60);contact(bpy.context.object.name,'scholar_court_foundation')
        for sx in [x-.33,x+.33]:box(name+'_upright',(sx,3.08,1.24),(.06,.30,2.16),'cedar',60);contact(bpy.context.object.name,'scholar_court_foundation')
        for z in [.22,.77,1.32,1.87]:
            shelf=box(name+'_shelf',(x,3.07,z),(.66,.36,.08),'cedar',80)
            for i in range(5):
                b=box('bound_manuscript',(x-.24+i*.12,3.075,z+.18),(.075,.23,.28),'clay' if i%2 else 'straw',100);contact(b.name,shelf.name)
    # Reading tables and slate lesson tablets live under the side galleries.
    for x in [-2.6,2.6]:
        for yy in [-1.6,.8]:
            for xx in [x-.35,x+.35]:
                leg=box('reading_table_leg',(xx,yy,.51),(.10,.55,.70),'cedar',60);contact(leg.name,'scholar_court_foundation')
            top=box('reading_table',(x,yy,.91),(.94,.76,.10),'cedar',80);contact(top.name,leg.name)
            slate=box('lesson_slate_tablet',(x,yy,.98),(.52,.39,.04),'shadow',100);contact(slate.name,top.name)
            # Geometric score marks are content props, not lettering.
            for dx in [-.12,0,.12]:box('chalk_score',(x+dx,yy,1.008),(.025,.21,.016),'lime',100)
    # Conservative clear source courtyard and entry route, not a navmesh.
    bpy.context.view_layer.update()
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name!='scholar_court_foundation']:
        lo,hi=bounds(o)
        assert not (hi[0]>-.9 and lo[0]<.9 and hi[1]>-3.1 and lo[1]<2.0 and lo[2]<2.0),(o.name,lo,hi)
    # Every fitted arcade has a measured ray-clear opening at ground and shoulder height.
    voids=[]
    from mathutils.bvhtree import BVHTree
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and ('hollow_arcade' in o.name or 'open_reading_bay' in o.name or 'main_portal' in o.name)]:
        bm=bmesh.new();bm.from_mesh(o.data);tree=BVHTree.FromBMesh(bm)
        for z in [.5,1.3]:
            world=Vector((o.location.x,o.location.y,z)) if 'hollow' in o.name else Vector((0,0,z))
            if 'hollow' in o.name: origin=o.matrix_world.inverted()@world;origin.y=-.8
            else:
                cx=0 if 'main_portal' in o.name else sum(bounds(o)[i][0] for i in [0,1])/2
                origin=Vector((cx,-4,z))
            hit=tree.ray_cast(origin,Vector((0,1,0)),8)[0];assert hit is None,(o.name,z)
            voids.append({'object':o.name,'height':z,'ray_clear':True})
        bm.free()
    (OUT/'void_checks.json').write_text(json.dumps(voids,indent=2))
'''
t=siege[siege.index('    bpy.context.view_layer.update();objects='):siege.index('def donor():')].replace('Siege','University').replace('SIEGE','UNIVERSITY').replace('siege','university')
t=t.replace('>=-3.001','>=-4.001').replace('<=3.001','<=4.001').replace("'footprint_m':[6,6]","'footprint_m':[8,8]").replace("'clear_gateway_m':4.54","'clear_gateway_m':2.46").replace("'central_transit_corridor_m':2.0","'central_transit_corridor_m':1.8").replace('ortho_scale=9.5','ortho_scale=11.5')
d=siege[siege.index('def donor():'):].replace('Siege','University').replace('siege','university').replace('SIEGE','UNIVERSITY').replace('Age III','Age IV').replace('Age3_Reference','Age4_Reference').replace('x=6 y=6','x=8 y=8').replace("for age in [int(n) for n in os.environ.get('BER_UNIVERSITY_AGES','3,4').split(',')]:build(age)","for age in [4]:build(age)").replace("'ages':[3,4]","'ages':[4]")
(A/'build_university.py').write_text(p+body+t+d)
run=(R/'research/buildings_batch/siege/run_hidden.py').read_text().replace('/siege','/university').replace('build_siege','build_university');(Q/'run_hidden.py').write_text(run)
