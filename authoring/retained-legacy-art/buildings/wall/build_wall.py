"""Task-owned, reproducible Moroccan courtyard wall source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/wall'; OUT=ROOT/'output/buildings_batch/wall'; RESEARCH=ROOT/'research/buildings_batch/wall'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.10,.115,.125),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override

def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern','roughness','metal','normal'):
        im=bpy.data.images.new('Wall_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
        pixels=[]
        for y in range(256):
            for x in range(256):
                slot=(x//64)+4*(y//128); role,c,owner=COLORS[slot]
                variation=.96+.04*math.sin(x*.91)*math.sin(y*.81)
                rgb={'pattern':(owner,0,0),'normal':(.5,.5,1),'metal':((.85,.85,.85) if slot==5 else (0,0,0)),'roughness':((.4,.4,.4) if slot==5 else (.85,.85,.85))}.get(mapname,tuple(v*variation for v in c))
                pixels.extend((*rgb,1))
        im.pixels.foreach_set(pixels);im.filepath_raw=str(ART/(mapname+'.png'));im.file_format='PNG';im.save();im.pack()
        if mapname=='albedo': albedo=im
    for i,(name,c,owner) in enumerate(COLORS):
        m=bpy.data.materials.new('BerberWall_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='WallAtlasUV')
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

WALK=7.; CLEAR=3.; DECK=4.2; BASE=5.8; CREST=8.2

def sweep(name,L,zb,zt,wb,wt,mat,stage,slope=0):
    # One closed battered prism. End sections remain exact socket planes.
    verts=[(x,y,z+slope*x/L) for x in (-L/2,L/2) for z,w in ((zb,wb),(zt,wt)) for y in (-w/2,w/2)]
    fs=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,stage)

def section(age,L,kind,slope=0):
    wall='earth' if age==2 else 'lime';prefix=kind+'_'
    start=len(PARTS)
    sweep(prefix+'battered_stone_foot',L,0,.65,BASE,5.5,'stone',0,slope)
    sweep(prefix+'rammed_curtain_lower',L,.65,3.25,5.5,4.85,wall,40,slope)
    sweep(prefix+'rammed_curtain_upper',L,3.25,6.8,4.85,DECK,wall,60,slope)
    sweep(prefix+'walk_deck',L,6.8,WALK,DECK,DECK,'stone' if age==4 else 'earth',80,slope)
    for y in (-1.85,1.85):
        o=box(prefix+'parapet',(0,y,7.3),(L,.7,.6),wall,80)
        for v in o.data.vertices:v.co.z+=slope*(v.co.x+o.location.x)/L
        reuv(o)
        count=max(1,round(L/1.0));pitch=L/count
        for i in range(count):
            x=-L/2+(i+.5)*pitch
            if kind=='damaged_6m' and i in (1,2,4):continue
            o=box(prefix+'merlon',(x,y,7.9+slope*x/L),(pitch*.58,.7,.6),wall,100)
            for v in o.data.vertices:v.co.z+=slope*v.co.x/L
            reuv(o)
            if age>=3:
                o=box(prefix+'merlon_lime_cap',(x,y,8.18+slope*x/L),(pitch*.58,.7,.04),'lime',100)
                for v in o.data.vertices:v.co.z+=slope*v.co.x/L
                reuv(o)
        # Owner stripe stays on the exterior face, away from the walk corridor.
        o=box(prefix+'owner_painted_band',(0,y+math.copysign(.353,y),7.35),(L,.012,.18),'owner_cloth',100)
        for v in o.data.vertices:v.co.z+=slope*v.co.x/L
        reuv(o)
    if age>=3:
        # Shallow lime bond courses seated in the massive battered foundation.
        for z,width in ((.38,5.62),(1.05,5.4)):
            for y in (-width/2,width/2):
                o=box(prefix+'lime_bond_course',(0,y,z),(L,.03,.10),'lime',80)
                for v in o.data.vertices:v.co.z+=slope*(v.co.x+o.location.x)/L
                reuv(o)
    if age==4:
        for side in (-1,1):
            for i in range(max(1,int(L))):
                x=-L/2+(i+.5)*L/max(1,int(L));y=side*2.316
                o=box(prefix+'lozenge_plaster',(x,y,4.5+slope*x/L),(.23,.05,.23),'earth',100);o.rotation_euler.y=math.pi/4
    meshes=[bpy.data.objects[p['object']] for p in PARTS[start:]]
    c=bpy.data.collections.new(kind);bpy.context.scene.collection.children.link(c)
    for o in meshes:
        for old in list(o.users_collection):old.objects.unlink(o)
        c.objects.link(o)
    sockets=[]
    for end,x in [('left',-L/2),('right',L/2)]:
        o=bpy.data.objects.new(kind+'_socket_'+end,None);c.objects.link(o);o.location=(x,0,WALK+slope*x/L);o['socket_normal_x']=-1 if end=='left' else 1;o['clear_width']=CLEAR;sockets.append(o)
    return c,meshes,sockets,{'variant':kind,'length_m':L,'walk_clear_width_m':CLEAR,'walk_end_z':[WALK-slope/2,WALK+slope/2],'socket_centres':[[-L/2,0,WALK-slope/2],[L/2,0,WALK+slope/2]],'slope_rise_m':slope,'parts':PARTS[start:]}

def check_objects(objects):
    result=[]
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data);volume=bm.calc_volume(signed=True)
        bad=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free()
        uv=o.data.uv_layers.active;uvareas=[]
        for p in o.data.polygons:
            vs=[uv.data[i].uv for i in p.loop_indices]
            uvareas.append(abs(sum(vs[i].x*vs[(i+1)%len(vs)].y-vs[(i+1)%len(vs)].x*vs[i].y for i in range(len(vs)))/2))
        rec={'object':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'nonmanifold':bad,'degenerate':deg,'signed_volume':volume,'min_uv_area':min(uvareas),'finite':all(math.isfinite(v) for p in o.data.vertices for v in p.co),'positive_transform':o.matrix_world.determinant()>0}
        assert bad==0 and deg==0 and volume>0 and min(uvareas)>1e-9 and rec['finite'] and rec['positive_transform'],rec
        result.append(rec)
    return result

def export(age,kind,meshes,sockets):
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes+sockets:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Wall_Age{age}_{kind}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,path_mode='COPY',embed_textures=True)

def render_views(age,collection):
    scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_percentage=100
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Review');scene.world.color=(.10,.12,.14)
    bpy.ops.object.camera_add(location=(13,-18,14));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=13;scene.camera=cam
    target=Vector((0,0,4));scene.render.resolution_x=768;scene.render.resolution_y=768
    for name,loc in [('preview',(13,-18,14)),('front',(0,-22,4)),('back',(0,22,4)),('left',(-22,0,4)),('right',(22,0,4)),('top',(0,0,22)),('bottom',(0,0,-22))]:
        cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    cam.location=(13,-18,14);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()

def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();variants=[];allchecks=[];groups=[]
    for kind,L,slope in [('straight_1m',1,0),('straight_3m',3,0),('straight_6m',6,0),('gap_1m',1,0),('gap_2m',2,0),('gap_3m',3,0),('gap_4m',4,0),('slope_up_6m',6,1.2),('slope_down_6m',6,-1.2),('end_6m',6,0),('damaged_6m',6,0)]:
        c,meshes,sockets,record=section(age,L,kind,slope)
        if kind=='end_6m':
            o=box('end_6m_terminal_parapet',(2.65,0,7.3),(.7,3,.6),'earth' if age==2 else 'lime',80)
            for old in list(o.users_collection):old.objects.unlink(o)
            c.objects.link(o);meshes.append(o);record['closed_end']='right';record['open_socket']='left';record['parts'].append(PARTS[-1])
        allchecks.extend(check_objects(meshes));export(age,kind,meshes,sockets);variants.append(record);groups.append(c)
        c.hide_render=True
        for o in meshes+sockets:o.hide_set(True)
    # Curtain elbow is a continuous mitered profile; bastion family owns native branching caps.
    before=len(PARTS);kind='corner_90';wall='earth' if age==2 else 'lime'
    def corner_strip(name,wb,wt,zb,zt,mat,stage):
        # connected outline swept from a square L-shaped region; end planes x=-6 and y=6.
        outline=lambda w:[(-6,-w/2),(w/2,-w/2),(w/2,6),(-w/2,6),(-w/2,w/2),(-6,w/2)]
        a=outline(wb);b=outline(wt);vs=[(x,y,zb) for x,y in a]+[(x,y,zt) for x,y in b];n=6
        fs=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,stage)
    corner_strip('corner_foot',BASE,5.5,0,.65,'stone',0);corner_strip('corner_curtain',5.5,DECK,.65,6.8,wall,40);corner_strip('corner_walk',DECK,DECK,6.8,7,'stone',80)
    # Inner and outer guards follow mitered continuous strips with no rail across the socket.
    def outline_prism(name,outline,lo,hi,mat,stage):
        n=len(outline);vs=[(x,y,z) for z in (lo,hi) for x,y in outline];fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,stage)
    outline_prism('corner_outer_miter_guard',[(-6,-2.2),(2.2,-2.2),(2.2,6),(1.5,6),(1.5,-1.5),(-6,-1.5)],7,7.6,wall,80)
    outline_prism('corner_inner_miter_guard',[(-6,1.5),(-1.5,1.5),(-1.5,6),(-2.2,6),(-2.2,2.2),(-6,2.2)],7,7.6,wall,80)
    for y,xs in [(-1.85,[-5.5+i for i in range(8)]),(1.85,[-5.5+i for i in range(4)])]:
        for x in xs:box('corner_x_merlon',(x,y,7.9),(.58,.7,.6),wall,100)
    for x,ys in [(1.85,[-.5+i for i in range(7)]),(-1.85,[2.5+i for i in range(4)])]:
        for y in ys:box('corner_y_merlon',(x,y,7.9),(.7,.58,.6),wall,100)
    box('corner_owner_strip_x',(-2,-2.203,7.35),(8,.012,.18),'owner_cloth',100)
    box('corner_owner_strip_y',(2.203,1.9,7.35),(.012,8.2,.18),'owner_cloth',100)
    corner_meshes=[bpy.data.objects[p['object']] for p in PARTS[before:]];c=bpy.data.collections.new(kind);bpy.context.scene.collection.children.link(c)
    for o in corner_meshes:
        for old in list(o.users_collection):old.objects.unlink(o)
        c.objects.link(o)
    sockets=[]
    for side,co in [('west',(-6,0,7)),('north',(0,6,7))]:
        o=bpy.data.objects.new('corner_socket_'+side,None);c.objects.link(o);o.location=co;sockets.append(o)
    allchecks.extend(check_objects(corner_meshes));export(age,kind,corner_meshes,sockets);variants.append({'variant':kind,'socket_centres':[[-6,0,7],[0,6,7]],'walk_clear_width_m':3,'parts':PARTS[before:],'binding':'logical elbow only; native caps owned by wall_bastion'});c.hide_render=True
    for o in corner_meshes+sockets:o.hide_set(True)
    groups.append(c)
    before=len(PARTS);kind='destroyed_6m';c=bpy.data.collections.new(kind);bpy.context.scene.collection.children.link(c)
    sweep('destroyed_foot',6,0,.45,BASE,5.3,'stone',0)
    for i in range(7):
        x=-2.5+i*.8;y=(-1)**i*.85;h=.65+(i%3)*.22
        box('fallen_earth_blocks',(x,y,.45+h/2),(.92,1.12,h),wall,40)
    meshes=[bpy.data.objects[p['object']] for p in PARTS[before:]]
    for o in meshes:
        for old in list(o.users_collection):old.objects.unlink(o)
        c.objects.link(o)
    allchecks.extend(check_objects(meshes));export(age,kind,meshes,[]);variants.append({'variant':kind,'walk_surface':False,'parts':PARTS[before:],'binding':'source wreck visual only; native destruction and blockers pending'});c.hide_render=True
    for o in meshes:o.hide_set(True)
    # Numeric join, walk and clear corridor checks against actual mesh vertices.
    joins=[]
    for L in (1,3,6):
        o=bpy.data.objects[f'straight_{L}m_walk_deck'];b=bounds(o);joins.append({'module':L,'left_x':b[0][0],'right_x':b[1][0],'adjacent_translated_left':b[0][0]+L,'join_gap':b[0][0]+L-b[1][0],'walk_z':b[1][2],'pass':abs(b[0][0]+L-b[1][0])<1e-6 and abs(b[1][2]-7)<1e-6})
    bpy.context.view_layer.update()
    ray=[]
    # Source ray-cast from above establishes clear plane across 3m interior width.
    deck=bpy.data.objects['straight_6m_walk_deck']
    for x in (-2.99,-1.5,0,1.5,2.99):
        for y in (-1.49,0,1.49):
            hit,loc,n,idx=deck.ray_cast(Vector((x,y,20)),Vector((0,0,-1)));ray.append({'x':x,'y':y,'z':loc.z if hit else None,'pass':hit and abs(loc.z-7)<1e-5})
    assert all(j['pass'] for j in joins),joins
    assert all(j['pass'] for j in ray),ray
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':allchecks,'joins':joins,'walk_rays':ray,'uv':'positive per-face palette islands; repeating overlap intentional','owner_colour':'source mask only; native static structure route blocked'},indent=2))
    (ART/f'age{age}_states.json').write_text(json.dumps({'age':age,'variants':variants,'native_bindings':'pending wall segment/gap/cap/damage/destruction selectors and terrain conform'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,40,60,80,100],'parts':PARTS,'cumulative':True,'garrison_recipe_exported':False},indent=2))
    main=bpy.data.collections['straight_6m'];main.hide_render=False
    for o in main.objects:o.hide_set(False)
    render_views(age,main)
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Wall_Age{age}.blend'))
    print('WALL_AGE_DONE',age,flush=True)

def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text())
    rec=[]
    for index,g in enumerate(d['geometry']['groups']):
        name=str(index)+'_'+g['name'];me=bpy.data.meshes.new(name);me.from_pydata(g['positions'],[],g['triangles']);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched installed Malian 6m native geometry/states, no material reconstruction';rec.append({'name':name,'render_bounds':bounds(o),'vertices':len(g['positions']),'triangles':len(g['triangles'])})
    bpy.context.view_layer.update()
    (RESEARCH/'donor_geometry.json').write_text(json.dumps(rec,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Untouched_Malian_Wall_6m_Reference.blend'))

try:
    donor()
    for age in (2,3,4):build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'required_ages':[2,3,4],'cook':False,'native_acceptance':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()


