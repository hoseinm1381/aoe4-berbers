"""Task-owned, reproducible Moroccan courtyard blacksmith source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/university'; OUT=ROOT/'output/buildings_batch/university'; RESEARCH=ROOT/'research/buildings_batch/university'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.10,.115,.125),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern','roughness','metal','normal'):
        im=bpy.data.images.new('University_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
        pixels=[]
        for y in range(256):
            for x in range(256):
                slot=(x//64)+4*(y//128); role,c,owner=COLORS[slot]
                variation=.96+.04*math.sin(x*.91)*math.sin(y*.81)
                rgb={'pattern':(owner,0,0),'normal':(.5,.5,1),'metal':(0,0,0),'roughness':((.4,.4,.4) if slot==5 else (.85,.85,.85))}.get(mapname,tuple(v*variation for v in c))
                pixels.extend((*rgb,1))
        im.pixels.foreach_set(pixels);im.filepath_raw=str(ART/(mapname+'.png'));im.file_format='PNG';im.save();im.pack()
        if mapname=='albedo': albedo=im
    for i,(name,c,owner) in enumerate(COLORS):
        m=bpy.data.materials.new('BerberUniversity_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='UniversityAtlasUV')
    for face in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis]
        co=[o.data.vertices[o.data.loops[li].vertex_index].co for li in face.loop_indices]
        lo=[min(v[k] for v in co) for k in axes];hi=[max(v[k] for v in co) for k in axes]
        for li,v in zip(face.loop_indices,co):
            uv.data[li].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    PARTS.append({'object':o.name,'first_stage':stage,'material':mat,'owner_mask':MATS[mat][0]['ber_owner_mask']});return o
def box(name,center,size,mat='earth',stage=40):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,stage)
def prism(name,outline,yfront,yback,mat,stage):
    n=len(outline);vs=[(x,y,z) for y in (yfront,yback) for x,z in outline]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,stage)
def portal_outline(cx,base,width,height):
    r=width*.56;cz=base+height-r
    return [(cx-width*.43,base),(cx+width*.43,base)]+[(cx+r*math.cos(t),cz+r*math.sin(t)) for t in [math.radians(-28+i*236/16) for i in range(17)]]
def cut_portal(wall,cx,y,z,width,height,mat='cedar'):
    outline=portal_outline(cx,z,width,height)
    cutter=prism('TEMP_portal',outline,y-.7,y+.7,'shadow',40)
    bpy.context.view_layer.objects.active=wall;mod=wall.modifiers.new('Real recessed doorway','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
    # closed inserted door, actually seated inside the cut opening
    door=prism('horseshoe_door',outline,y+.035,y+.09,mat,60)
    for x in [cx-width*.32,cx,cx+width*.32]:box('door_joinery',(x,y+.022,z+height*.43),(.035,.035,height*.7),'stone',80)
    CONTACTS.append({'interface':'door recessed into front wall opening','gap':0,'intentional_recess':.035})
    return door
def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
def contact(a,b,axis=2,expected=0):
    bpy.context.view_layer.update(); gap=bounds(bpy.data.objects[a])[0][axis]-bounds(bpy.data.objects[b])[1][axis]
    CONTACTS.append({'child':a,'parent':b,'axis':axis,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})
def tube(name,center,r,h,mat='clay',stage=100):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=h,location=center);return finish(bpy.context.object,name,mat,stage)

def beam(name,a,b,w,mat='cedar',stage=60):
    v=Vector(b)-Vector(a);o=box(name,(Vector(a)+Vector(b))/2,(w,w,v.length),mat,stage);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o

def reuv(o):
    uv=o.data.uv_layers.active;slot=MATS[o['ber_material_role']][1]
    for p in o.data.polygons:
        ax=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=ax];vs=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];lo=[min(v[k] for v in vs) for k in axes];hi=[max(v[k] for v in vs) for k in axes]
        for i,v in zip(p.loop_indices,vs):uv.data[i].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)

def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
def contact(a,b,axis=2,expected=0):
    bpy.context.view_layer.update(); gap=bounds(bpy.data.objects[a])[0][axis]-bounds(bpy.data.objects[b])[1][axis]
    CONTACTS.append({'child':a,'parent':b,'axis':axis,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})

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
            o.rotation_euler.z=math.pi/2;o.location=(x/abs(x)*1.78,yy,1.46);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
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
    # Two visible courtyard reading stations keep the central passage open.
    for x in [-1.20,1.20]:
        pedestal=box('court_reading_pedestal',(x,-1.65,.46),(.20,.38,.60),'cedar',60);contact(pedestal.name,'scholar_court_foundation')
        desk=box('court_reading_desk',(x,-1.65,.80),(.46,.72,.08),'cedar',80);contact(desk.name,pedestal.name)
        for dx in [-.095,.095]:
            page=box('open_manuscript_pages',(x+dx,-1.65,.862),(.18,.36,.044),'straw',100);contact(page.name,desk.name)
        box('manuscript_binding_spine',(x,-1.65,.858),(.03,.37,.036),'clay',100)
        for yy in [-1.0,-2.30]:
            stool=box('court_reader_stool',(x,yy,.34),(.30,.28,.36),'cedar',80);contact(stool.name,'scholar_court_foundation')
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
            if 'hollow' in o.name: origin=o.matrix_world.inverted()@world;origin.x=-.8;direction=Vector((1,0,0))
            else:
                cx=0 if 'main_portal' in o.name else sum(bounds(o)[i][0] for i in [0,1])/2
                origin=o.matrix_world.inverted()@Vector((cx,-4,z));direction=Vector((0,1,0))
            hit=tree.ray_cast(origin,direction,8)[0];assert hit is None,(o.name,z)
            voids.append({'object':o.name,'height':z,'ray_clear':True})
        bm.free()
    (OUT/'void_checks.json').write_text(json.dumps(voids,indent=2))
    bpy.context.view_layer.update();objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True)
        if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);vol=-vol
        non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free()
        uv=o.data.uv_layers.active;uvdeg=0
        for face in o.data.polygons:
            pts=[uv.data[i].uv for i in face.loop_indices];area=abs(sum(pts[i].x*pts[(i+1)%len(pts)].y-pts[(i+1)%len(pts)].x*pts[i].y for i in range(len(pts)))/2);uvdeg+=area<1e-10
        checks.append({'object':o.name,'non_manifold':non,'degenerate_faces':deg,'uv_zero_area_faces':uvdeg,'outward_signed_volume':vol,'finite':all(math.isfinite(v) for vert in o.data.vertices for v in vert.co),'positive_scale':all(v>0 for v in o.scale),'bounds':bounds(o)})
    assert all(c['non_manifold']==0 and c['degenerate_faces']==0 and c['uv_zero_area_faces']==0 and c['outward_signed_volume']>0 and c['finite'] and c['positive_scale'] for c in checks),checks
    assert all(c['pass'] for c in CONTACTS),CONTACTS
    assert all(c['bounds'][0][0]>=-4.001 and c['bounds'][1][0]<=4.001 and c['bounds'][0][1]>=-4.001 and c['bounds'][1][1]<=4.001 and c['bounds'][0][2]>=-.001 for c in checks)
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[8,8],'clear_gateway_m':2.46,'central_transit_corridor_m':1.8,'native_anchor_binding':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'assignment':'first visible percentage, cumulative','parts':PARTS,'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_University_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(10,-13,11));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=11.5;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
    bpy.ops.object.light_add(type='AREA',location=(0,-5,3));bpy.context.object.data.energy=420;bpy.context.object.data.size=4
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_University_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=8;scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-12,1.4)),('back',(0,12,1.4)),('left',(-12,0,1.4)),('right',(12,0,1.4)),('top',(0,0,15)),('bottom',(0,0,-12))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('UNIVERSITY_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());saved=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched installed Abbasid Age IV university decoded positions/topology';saved.append({'name':o.name,'vertices':len(vs),'faces':len(faces),'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_University_Age4_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':saved,'geometry_reused_in_final':False,'footprint_from':'core.xml site_ext x=8 y=8; render bounds not footprint'},indent=2))
try:
    donor()
    for age in [4]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[4],'cook':False,'native_owner_colour':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()


