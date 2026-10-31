"""Task-owned, reproducible Moroccan courtyard stable source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/stable'; OUT=ROOT/'output/buildings_batch/stable'; RESEARCH=ROOT/'research/buildings_batch/stable'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('Stable_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberStable_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='StableAtlasUV')
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
def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
def contact(a,b,axis=2,expected=0):
    bpy.context.view_layer.update(); gap=bounds(bpy.data.objects[a])[0][axis]-bounds(bpy.data.objects[b])[1][axis]
    CONTACTS.append({'child':a,'parent':b,'axis':axis,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})
def tube(name,center,r,h,mat='clay',stage=100):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=h,location=center);return finish(bpy.context.object,name,mat,stage)
def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps()
    for name,col in [('normal',(.5,.5,1)),('roughness',(.85,.85,.85)),('metal',(0,0,0))]:
        im=bpy.data.images.new('Stable_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
    wall='earth' if age==2 else 'lime';h=2.0+(age-2)*.18
    box('foundation',(0,0,.055),(6,6,.11),'stone',0)
    box('court_floor',(0,0,.125),(5.8,5.8,.03),'earth',0)
    # Three real open-front stalls. Shared continuous rear and side walls bound the shelter.
    box('stall_rear_wall',(0,2.64,.14+h/2),(5.5,.24,h),wall,40);contact('stall_rear_wall','court_floor')
    for i,x in enumerate([-2.65,-.883333,.883333,2.65]):
        n=f'stall_partition_{i}';box(n,(x,1.605,.14+h*.64/2),(.22,1.83,h*.64),wall,40);contact(n,'court_floor')
        n=f'stall_front_post_{i}';box(n,(x,.69,.14+h/2),(.10,.12,h),'cedar',20);contact(n,'court_floor')
    bpy.context.view_layer.update()
    for i in range(4):
        gap=bounds(bpy.data.objects[f'stall_partition_{i}'])[0][1]-bounds(bpy.data.objects[f'stall_front_post_{i}'])[1][1]
        CONTACTS.append({'interface':f'stall partition {i} to front post','measured_signed_gap_m':gap,'intentional_overlap_m':.06,'pass':abs(gap+.06)<1e-5})
        gap=bounds(bpy.data.objects['stall_rear_wall'])[0][1]-bounds(bpy.data.objects[f'stall_partition_{i}'])[1][1]
        CONTACTS.append({'interface':f'stall partition {i} to rear wall','measured_signed_gap_m':gap,'pass':abs(gap)<1e-5})
    box('stall_front_beam',(0,.69,.14+h+.07),(5.60,.16,.14),'cedar',60);contact('stall_front_beam','stall_front_post_0')
    box('stall_rear_beam',(0,2.64,.14+h+.07),(5.60,.16,.14),'cedar',60);contact('stall_rear_beam','stall_rear_wall')
    # Timber rafters terminate on rear wall and front crossbeam.
    for i,x in enumerate([-2.54,-1.69,-.845,0,.845,1.69,2.54]):
        n=f'stall_roof_rafter_{i}';box(n,(x,1.68,.14+h+.18),(.09,2.12,.08),'cedar',60);contact(n,'stall_front_beam');contact(n,'stall_rear_beam')
    roof='straw' if age==2 else 'earth'
    box('stall_roof',(0,1.68,.14+h+.245),(5.66,2.16,.05),roof,80);contact('stall_roof','stall_roof_rafter_0')
    # White/neutral owner-colour woven strips both horizontal and camera-visible vertical.
    for x in [-1.767,0,1.767]:
        box('owner_roof_stripe',(x,1.68,.14+h+.275),(.25,2.16,.01),'owner_cloth',100);contact('owner_roof_stripe','stall_roof')
    box('owner_stall_valance',(0,.584,.14+h+.055),(5.58,.025,.23),'owner_cloth',100)
    # Feed mangers at rear of each stall: hollow open-top boxes composed of continuous seated sides.
    for i,x in enumerate([-1.767,0,1.767]):
        n=f'feed_manger_base_{i}';box(n,(x,2.17,.22),(1.18,.42,.16),'cedar',60);contact(n,'court_floor')
        for y in [1.98,2.36]:box(f'feed_manger_wall_{i}',(x,y,.39),(1.18,.04,.18),'cedar',80)
        for xx in [x-.57,x+.57]:box(f'feed_manger_end_{i}',(xx,2.17,.39),(.04,.34,.18),'cedar',80)
        box(f'feed_straw_{i}',(x,2.17,.31),(1.06,.30,.02),'straw',100)
    # Tack/feed room forms the west wing, hollow with an east-facing open doorway.
    roomh=1.72+(age-2)*.12
    for name,center,size in [ ('tack_west',(-2.67,-1.30,.14+roomh/2),(.22,2.65,roomh)),('tack_south',(-2.02,-2.515,.14+roomh/2),(1.08,.22,roomh)),('tack_north',(-2.02,-.085,.14+roomh/2),(1.08,.22,roomh)),('tack_east_front',(-1.48,-2.12,.14+roomh/2),(.22,.57,roomh)),('tack_east_back',(-1.48,-.63,.14+roomh/2),(.22,.87,roomh))]:
        box(name,center,size,wall,40);contact(name,'court_floor')
    box('tack_door_lintel',(-1.48,-1.52,.14+1.40+(roomh-1.40)/2),(.22,.95,roomh-1.40),wall,60)
    box('tack_roof',(-2.02,-1.30,.14+roomh+.045),(1.52,2.75,.09),'earth',60);contact('tack_roof','tack_west')
    box('tack_roof_owner_strip',(-2.02,-1.30,.14+roomh+.095),(.24,2.75,.01),'owner_cloth',100);contact('tack_roof_owner_strip','tack_roof')
    # Joined wooden tack rack with saddles and bridle lines, positioned inside room.
    for x in [-2.48,-1.78]:box('tack_rack_post',(x,-.65,.14+.50),(.07,.08,1.0),'cedar',60)
    box('tack_rack_crossbar',(-2.13,-.65,1.11),(.77,.09,.09),'cedar',80)
    for i,x in enumerate([-2.40,-2.14,-1.88]):
        box('saddle_pad',(x,-.65,1.18),(.20,.27,.07),'clay',100)
        box('bridle_line',(x,-.61,.87),(.018,.018,.44),'cedar',100)
    for y in [-2.20,-1.84]:box('feed_bale',(-2.06,y,.37),(.82,.28,.46),'straw',100)
    # East wing is a shaded watering/rest apron. Center lane stays 2.83 m wide.
    z=1.64+(age-2)*.10
    for i,x in enumerate([1.51,2.65]):
        for j,y in enumerate([-2.42,-.32]):
            n=f'water_shade_post_{i}_{j}';box(n,(x,y,.14+(z-.14)/2),(.10,.10,z-.14),'cedar',20);contact(n,'court_floor')
    for j,y in enumerate([-2.42,-.32]):
        n=f'water_shade_beam_{j}';box(n,(2.08,y,z+.045),(1.24,.14,.09),'cedar',60);contact(n,f'water_shade_post_0_{j}')
    box('water_shade_roof',(2.08,-1.37,z+.12),(1.36,2.26,.06),'straw',80);contact('water_shade_roof','water_shade_beam_0')
    box('water_owner_valance',(2.08,-2.51,z+.04),(1.36,.025,.18),'owner_cloth',100)
    # Trough basin is visibly hollow, water below rim; no solid box pretending to hold water.
    box('trough_bottom',(2.13,-1.19,.24),(.66,1.36,.20),'stone',60);contact('trough_bottom','court_floor')
    for x in [1.83,2.43]:box('trough_long_rim',(x,-1.19,.46),(.06,1.36,.24),'stone',80)
    for y in [-1.84,-.54]:box('trough_end_rim',(2.13,y,.46),(.54,.06,.24),'stone',80)
    box('trough_water',(2.13,-1.19,.365),(.54,1.24,.05),'shadow',100)
    if age>=3:
        for x in [-2.73,2.73]:box('stall_stone_corner',(x,2.58,.64),(.20,.34,1.0),'stone',20)
        box('stall_rear_parapet',(0,2.64,.14+h+.42),(5.66,.16,.30),'lime',80)
        contact('stall_rear_parapet','stall_roof')
        for x in [-2.65,2.65]:
            o=box('stall_timber_brace',(x,.92,.14+h-.22),(.06,.65,.06),'cedar',80);o.rotation_euler.x=math.pi/4
    if age==4:
        for y in [-2.36,-.22]:box('tack_corner_quoin',(-2.68,y,.50),(.24,.20,.72),'lime',80)
        box('tack_geometric_band',(-2.837,-1.30,1.54),(.02,2.0,.15),'earth',100)
        for y in [-2.08,-1.68,-1.28,-.88,-.48]:
            o=box('tack_geometric_relief',(-2.806,y,1.54),(.024,.08,.08),'lime',100);o.rotation_euler.x=math.pi/4
        # Developed joinery: connected horizontal rail defines rest apron without blocking south lane.
        for zrail in [.65,1.04]:box('east_rest_rail',(2.65,-1.37,zrail),(.07,2.20,.07),'cedar',80)
    for name,loc in [('cavalry_exit',(0,-3,0)),('stall_access',(0,.6,.14)),('tack_access',(-1.37,-1.52,.14))]:
        ob=bpy.data.objects.new('AUTHOR_'+name,None);bpy.context.scene.collection.objects.link(ob);ob.location=loc;ob['native_binding']='pending'
    bpy.context.view_layer.update()
    gap=bounds(bpy.data.objects['water_shade_post_0_0'])[0][0]-bounds(bpy.data.objects['tack_east_front'])[1][0]
    stall=bounds(bpy.data.objects['stall_partition_1'])[0][0]-bounds(bpy.data.objects['stall_partition_0'])[1][0]
    door=bounds(bpy.data.objects['tack_east_back'])[0][1]-bounds(bpy.data.objects['tack_east_front'])[1][1]
    CONTACTS.extend([{'interface':'center exit corridor clear','measured_m':gap,'pass':abs(gap-2.83)<1e-5},{'interface':'stall opening clear','measured_m':stall,'pass':stall>1.54},{'interface':'tack doorway clear','measured_m':door,'pass':abs(door-.77)<1e-5}])
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
    assert all(c['bounds'][0][0]>=-3.001 and c['bounds'][1][0]<=3.001 and c['bounds'][0][1]>=-3.001 and c['bounds'][1][1]<=3.001 and c['bounds'][0][2]>=-.001 for c in checks)
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[6,6],'south_exit_clear_width_m':2.83,'central_corridor_clear_width_m':2.83,'stall_opening_clear_width_m':1.546667,'native_anchor_binding':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'assignment':'first visible percentage, cumulative','parts':PARTS,'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Stable_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(10,-13,11));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=9.0;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Stable_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=4;scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-12,1.4)),('back',(0,12,1.4)),('left',(-12,0,1.4)),('right',(12,0,1.4)),('top',(0,0,15)),('bottom',(0,0,-12))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('STABLE_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());saved=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched installed Abbasid Age II stable decoded positions/topology';saved.append({'name':o.name,'vertices':len(vs),'faces':len(faces),'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Stable_Age2_Reference.blend'))
    # Gray donor overview shows all decoded construction groups; reference source remains untouched.
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
    sc.world=bpy.data.worlds.new('ReferenceStudio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[1].default_value=.8
    bpy.ops.object.camera_add(location=(14,-20,14));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=17;cam.rotation_euler=(Vector((0,-3,1))-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-8,14));bpy.context.object.data.energy=1600;bpy.context.object.data.size=8
    sc.render.filepath=str(OUT/'stock_donor_overview.png');bpy.ops.render.render(write_still=True)
    (RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':saved,'geometry_reused_in_final':False,'footprint_from':'core.xml site_ext x=6 y=6; render bounds not footprint'},indent=2))
try:
    if not (ART/"UNTouched_Abbasid_Stable_Age2_Reference.blend").exists(): donor()
    for age in [2,3,4]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'cook':False,'native_owner_colour':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()



