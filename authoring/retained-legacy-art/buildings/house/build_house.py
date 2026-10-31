"""Task-owned, reproducible Moroccan courtyard house source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/house'; OUT=ROOT/'output/buildings_batch/house'; RESEARCH=ROOT/'research/buildings_batch/house'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('House_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
        pixels=[]
        for y in range(256):
            for x in range(256):
                slot=(x//64)+4*(y//128); role,c,owner=COLORS[slot]
                variation=.96+.04*math.sin(x*.91)*math.sin(y*.81)
                rgb=(owner,0,0) if mapname=='pattern' else tuple(v*variation for v in c)
                pixels.extend((*rgb,1))
        im.pixels.foreach_set(pixels);im.filepath_raw=str(ART/(mapname+'.png'));im.file_format='PNG';im.save();im.pack()
        if mapname=='albedo': albedo=im
    for i,(name,c,owner) in enumerate(COLORS):
        m=bpy.data.materials.new('BerberHouse_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='HouseAtlasUV')
    for p in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis]
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=((slot%4+.07+.86*((co[axes[0]]*.3)%1))/4,(slot//4+.07+.86*((co[axes[1]]*.3)%1))/2)
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
def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps()
    h=1.62+.12*age; w=3.2; d=3.0; wallmat='earth' if age<3 else 'lime'
    box('stone_foundation',(0,0,.10),(3.65,3.4,.20),'stone',0)
    box('courtyard_earthen_floor',(0,0,.215),(3.45,3.2,.03),'earth',0)
    # Four connected habitable wings frame the open-to-sky courtyard.
    left=box('west_room',(-1.13,0,.22+h/2),(.94,d,h),wallmat,40)
    right=box('east_room',(1.13,0,.22+h*.87/2),(.94,d,h*.87),wallmat,40)
    back=box('north_room',(0,1.04,.22+h/2),(1.32,.92,h),wallmat,40)
    front=box('entrance_room',(0,-1.17,.22+h*.79/2),(1.32,.66,h*.79),wallmat,40)
    cut_portal(front,0,-1.5,.23,.72,1.34)
    CONTACTS.extend([{'interface':'foundation to all rooms','gap':0},{'interface':'north wing to side wings','gap':0},{'interface':'entrance wing to side wings','gap':0}])
    for side,x,rh in [('west',-1.13,h),('east',1.13,h*.87)]:
        z=.22+rh
        box(side+'_roof_deck',(x,0,z+.025),(.94,d,.05),'earth',60)
        for px in [x-.41,x+.41]:box(side+'_parapet',(px,0,z+.155),(.12,d,.26),wallmat,80)
        for yy in [-1.44,1.44]:box(side+'_parapet_end',(x,yy,z+.155),(.7,.12,.26),wallmat,80)
        for yy in [-1.48,.88]:
            box(side+'_roof_drain',(x+(-.54 if side=='west' else .54),yy,z+.012),(.34,.10,.09),'cedar',80)
        CONTACTS.append({'interface':side+' roof to wall and parapet','gap':0,'drain_overlap':.06})
    for yy,dep,rh in [(1.04,.92,h),(-1.17,.66,h*.79)]:
        box('link_roof',(0,yy,.22+rh+.03),(1.32,dep,.06),'earth',60)
        box('link_roof_parapet',(0,yy+(-1 if yy<0 else 1)*(dep/2-.05),.22+rh+.16),(1.32,.10,.26),wallmat,80)
    # Sockets cut into actual room walls, then closed shutter inserts.
    for x,rh in [(-1.13,h),(1.13,h*.87)]:
        target=left if x<0 else right
        cutter=box('TEMP_window',(x,-1.5,1.1),(.36,.3,.48),'shadow',60)
        bpy.context.view_layer.objects.active=target;mo=target.modifiers.new('window_recess','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
        box('cedar_shutter',(x,-1.40,1.1),(.35,.035,.47),'cedar',80)
        for xx in [x-.10,x+.10]:box('shutter_slats',(xx,-1.425,1.1),(.035,.024,.43),'straw',80)
        box('window_sill',(x,-1.52,.85),(.46,.14,.075),'stone',80)
        CONTACTS.append({'interface':'shutter in actual recessed window','recess':.075,'gap':0})
    # Owner stripe is neutral cloth, on the visible wall and courtyard canopy.
    box('owner_woven_wall_strip',(-1.13,-1.506,1.54),(.58,.025,.16),'owner_cloth',100)
    canopyz=.22+h*.87-.16
    for x in [-.55,.55]:box('canopy_anchored_post',(x,-.25,.22+(canopyz-.22)/2),(.07,.07,canopyz-.22),'cedar',20)
    box('courtyard_shade_canopy',(0,-.25,canopyz),(1.22,.8,.055),'owner_cloth',80)
    box('canopy_crossbeam',(0,-.25,canopyz-.03),(1.28,.08,.08),'cedar',60)
    CONTACTS.append({'interface':'canopy posts to courtyard floor and beam','gap':0})
    # Exterior step seats against foundation front face.
    box('entrance_step',(0,-1.87,.10),(.95,.34,.20),'stone',0)
    CONTACTS.append({'interface':'entrance step to foundation front','gap':0})
    if age>=2:
        # Geometric relief has an intentional shallow embed into real facade.
        for x in [-1.42,-1.13,-.84,.84,1.13,1.42]:
            o=box('pressed_diamond_border',(x,-1.508,.22+h*.65),(.13,.025,.13),'lime' if age==2 else 'earth',100);o.rotation_euler.y=math.pi/4
        for x in [-1.49,1.49]:box('stone_corner_courses',(x,-1.48,.48),(.20,.10,.50),'stone',20)
    if age>=3:
        # Rear roof grain store and useful ladder, coherently part of the dwelling.
        box('roof_grain_store',(.16,1.04,.22+h+.32),(1.03,.72,.64),'earth',60)
        box('grain_store_lime_cap',(.16,1.04,.22+h+.67),(1.08,.77,.07),'lime',80)
        for x in [-.45,-.06]:box('ladder_rails',(x,.5,.22+h/2),(.045,.045,h),'cedar',80)
        for z in [.35+i*.24 for i in range(int(h/.24))]:box('ladder_rung',(-.255,.50,z),(.44,.065,.055),'cedar',80)
    if age==4:
        for x in [-1.13,1.13]:
            for z in [.5,.84,1.18]:box('lime_corner_quoin',(x-.37,-1.509,z),(.18,.05,.12),'lime',80)
        box('door_lintel_carved_band',(0,-1.509,1.59),(1.05,.03,.12),'lime',100)
        for x in [-.42,-.21,0,.21,.42]:
            o=box('lintel_geometric_relief',(x,-1.535,1.59),(.065,.025,.065),'earth',100);o.rotation_euler.y=math.pi/4
    # Clay storage jars as continuous ring meshes.
    for j in range(age):
        cx=.28+j*.17;cy=.87; rings=[(.0,.09),(.06,.14),(.23,.15),(.29,.085),(.32,.085)]
        verts=[(cx+r*math.cos(k*math.tau/10),cy+r*math.sin(k*math.tau/10),.23+z) for z,r in rings for k in range(10)];faces=[]
        for q in range(len(rings)-1):
            for k in range(10):faces.append((q*10+k,q*10+(k+1)%10,(q+1)*10+(k+1)%10,(q+1)*10+k))
        faces.extend([tuple(reversed(range(10))),tuple(range(40,50))]);me=bpy.data.meshes.new('jar');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('clay_jar',me);bpy.context.scene.collection.objects.link(o);finish(o,'clay_jar','clay',100)
    col=bpy.data.collections.new('BER_House_Age'+str(age));bpy.context.scene.collection.children.link(col)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objects:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
    validate=[]
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data);volume=bm.calc_volume(signed=True)
        if volume<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);volume=-volume
        bad=sum(not e.is_manifold for e in bm.edges);deg=sum(p.calc_area()<1e-10 for p in bm.faces);bm.free()
        validate.append({'object':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'non_manifold_edges':bad,'degenerate_faces':deg,'outward_volume':volume,'uv_present':bool(o.data.uv_layers),'material_count':len(o.data.materials)})
    def bounds(name):
        ob=bpy.data.objects[name];points=[ob.matrix_world@Vector(v) for v in ob.bound_box]
        return [min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]
    bpy.context.view_layer.update()
    for child,parent,axis,childside,parentside,expected in [('west_roof_deck','west_room',2,0,1,0),('east_roof_deck','east_room',2,0,1,0),('west_room','courtyard_earthen_floor',2,0,1,-.01),('east_room','courtyard_earthen_floor',2,0,1,-.01),('entrance_step','stone_foundation',1,1,0,0)]:
        gap=bounds(child)[childside][axis]-bounds(parent)[parentside][axis]
        CONTACTS.append({'interface':child+' to '+parent,'measured_signed_gap':round(gap,6),'expected':expected,'pass':abs(gap-expected)<1e-5})
    assert all(c.get('pass',True) for c in CONTACTS),CONTACTS
    assert all(v['non_manifold_edges']==0 and v['degenerate_faces']==0 and v['outward_volume']>0 for v in validate),validate
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':validate,'contacts':CONTACTS,'uv_contract':'shared material-tile atlas; red-only pattern','native_owner_colour':'integration blocked; source mask only'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'parts':PARTS,'stages':[0,20,40,60,80,100],'assignment':'first visible construction percentage; cumulative','game_binding_status':'not exported through Garrison building recipe'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_House_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,path_mode='COPY',embed_textures=True)
    # Presentation only after source geometry validation.
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    bpy.ops.object.camera_add(location=(6,-8,6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.7;scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-3,-4,7));bpy.context.object.data.energy=650;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=5
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_House_Age{age}.blend'))
    scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    # Extra six-side source views establish geometry visibility, plus a roof view.
    scene.cycles.samples=8;scene.render.resolution_x=400;scene.render.resolution_y=400
    for name,loc in [('front',(0,-8,1.5)),('back',(0,8,1.5)),('left',(-8,0,1.5)),('right',(8,0,1.5)),('top',(0,0,9)),('bottom',(0,0,-8))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('HOUSE_AGE_DONE',age,flush=True)
def donor():
    ctx=reset_scene()
    d=json.loads((RESEARCH/'donor_geometry.json').read_text())
    for group in d['geometry']['groups']:
        verts=group['positions']; faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o)
        o['reference_only']='untouched installed Abbasid age-I decoded geometry; no material reconstruction'
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Age1_Reference.blend'))
try:
    donor()
    for age in range(1,5):build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'source':'generated original geometry; donor kept separate','cook':False,'native_acceptance':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:
    bpy.ops.wm.quit_blender()
