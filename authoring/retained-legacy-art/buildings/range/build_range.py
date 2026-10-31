"""Task-owned, reproducible Moroccan courtyard range source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/range'; OUT=ROOT/'output/buildings_batch/range'; RESEARCH=ROOT/'research/buildings_batch/range'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('Range_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberRange_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='RangeAtlasUV')
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
        im=bpy.data.images.new('Range_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
    wall='earth' if age==2 else 'lime';h=1.85+(age-2)*.22
    box('foundation',(0,0,.055),(6,6,.11),'stone',0)
    box('court_floor',(0,0,.125),(5.8,5.8,.03),'earth',0)
    # Hollow store: actual ground-level access opening on east wall; no false door plane.
    box('store_floor',(-2.03,-.1,.175),(1.62,4.8,.07),'stone',0);contact('store_floor','court_floor')
    box('store_west_wall',(-2.76,-.1,.21+h/2),(.16,4.8,h),wall,40);contact('store_west_wall','store_floor')
    for name,yy in [('north',2.22),('south',-2.42)]:
        box('store_'+name+'_wall',(-2.03,yy,.21+h/2),(1.30,.16,h),wall,40);contact('store_'+name+'_wall','store_floor')
    bpy.context.view_layer.update();CONTACTS.append({'interface':'store north wall to west wall butt joint','signed_gap':bounds(bpy.data.objects['store_north_wall'])[0][0]-bounds(bpy.data.objects['store_west_wall'])[1][0],'pass':abs(bounds(bpy.data.objects['store_north_wall'])[0][0]-bounds(bpy.data.objects['store_west_wall'])[1][0])<1e-5})
    # East facing store entrance: 1.10m clear, 1.55m high.
    for name,yy,dep in [('front',-1.83,1.34),('rear',1.12,2.36)]:
        box('store_east_'+name,(-1.30,yy,.21+h/2),(.16,dep,h),wall,40);contact('store_east_'+name,'store_floor')
    box('store_door_lintel',(-1.30,-.61,.21+1.55+(h-1.55)/2),(.16,1.10,h-1.55),wall,60)
    box('store_roof',(-2.03,-.1,.21+h+.045),(1.62,4.8,.09),'earth',60);contact('store_roof','store_west_wall')
    for xx in [-2.78,-1.28]:box('store_roof_parapet',(xx,-.1,.21+h+.20),(.12,4.8,.22),wall,80)
    for yy in [-2.44,2.24]:box('store_end_parapet',(-2.03,yy,.21+h+.20),(1.38,.12,.22),wall,80)
    box('store_drain',(-2.87,1.95,.21+h+.08),(.24,.10,.08),'cedar',80)
    for j in range(age):box('arrow_storage_crate',(-2.03,-1.90+j*.72,.21+.22),(.65,.56,.44),'cedar',100)
    # South firing shelter faces north toward three targets. Large open front and side passage.
    shadez=1.90+.08*(age-2)
    for ix,x in enumerate([-.62,2.42]):
        for iy,y in enumerate([-2.33,-1.23]):
            n=f'shade_post_{ix}_{iy}';box(n,(x,y,.14+(shadez-.14)/2),(.10,.10,shadez-.14),'cedar',20);contact(n,'court_floor')
    for iy,y in enumerate([-2.33,-1.23]):
        n=f'shade_crossbeam_{iy}';box(n,(.90,y,shadez+.045),(3.14,.13,.09),'cedar',60);contact(n,f'shade_post_0_{iy}')
    for j in range(7):
        x=-.60+j*.50;n=f'shade_rafter_{j}';box(n,(x,-1.78,shadez+.13),(.07,1.35,.08),'cedar',60);contact(n,'shade_crossbeam_0')
    box('woven_shooting_roof',(.90,-1.78,shadez+.19),(3.24,1.36,.04),'straw',80);contact('woven_shooting_roof','shade_rafter_0')
    for x in [-.15,.90,1.95]:box('roof_owner_stripe',(x,-1.78,shadez+.215),(.24,1.36,.01),'owner_cloth',100)
    box('owner_front_valance',(.90,-2.46,shadez+.10),(3.24,.035,.20),'owner_cloth',100)
    # Target discs are vertical, continuous solids, with fitted concentric painted facing rings.
    for i,x in enumerate([-.48,.70,1.88]):
        n=f'target_post_{i}';box(n,(x,2.12,.14+.62),(.12,.14,1.24),'cedar',60);contact(n,'court_floor')
        box(f'target_foot_{i}',(x,2.12,.19),(.72,.48,.10),'cedar',60);contact(f'target_foot_{i}','court_floor')
        for role,r,y,depth in [('straw',.43,2.10,.16),('earth',.30,2.015,.025),('lime',.19,1.9975,.01),('clay',.08,1.990,.005)]:
            o=tube(f'target_{i}_{role}',(x,y,1.46),r,depth,role);o.rotation_euler.x=math.pi/2
        bpy.context.view_layer.update();CONTACTS.append({'interface':f'target {i} post overlaps target body','pass':bounds(bpy.data.objects[n])[1][2]>1.46-.43,'measured_overlap_m':round(1.38-(1.46-.43),3)})
        # Arrow seated into the target face, ends clear of pedestrian lane.
        o=box(f'arrow_shaft_{i}',(x+.10,1.73,1.50),(.019,.54,.019),'cedar',100)
        for xx in [x+.07,x+.13]:box('arrow_fletching',(xx,1.50,1.50),(.035,.08,.04),'lime',100)
    box('target_earth_backstop',(.61,2.71,.14+.55),(4.42,.24,1.10),wall,40);contact('target_earth_backstop','court_floor')
    # Low right boundary only at rear: south and east exit remain unobstructed.
    box('east_rear_boundary',(2.73,1.80,.14+.34),(.20,1.58,.68),wall,40);contact('east_rear_boundary','court_floor')
    if age>=3:
        for x in [-2.64,-1.42]:box('store_stone_corner',(x,-2.43,.21+.50),(.22,.21,1.0),'stone',20)
        box('store_carved_band',(-2.03,-2.514,1.61),(1.14,.027,.14),'lime',100)
        for x in [-2.39,-2.03,-1.67]:
            o=box('store_geometric_lozenge',(x,-2.532,1.61),(.07,.02,.07),'earth',100);o.rotation_euler.y=math.pi/4
        for x in [-.62,2.42]:
            o=box('shade_joinery_brace',(x,-1.46,shadez-.22),(.075,.62,.075),'cedar',80);o.rotation_euler.x=math.pi/4
    if age==4:
        # Modest taller arrow-making loft over store, rather than a generic tower/minaret.
        z=.21+h+.09
        box('arrow_workshop_loft',(-2.03,.90,z+.35),(1.34,2.00,.70),'earth',60);contact('arrow_workshop_loft','store_roof')
        box('loft_roof_cap',(-2.03,.90,z+.745),(1.46,2.12,.09),'lime',80);contact('loft_roof_cap','arrow_workshop_loft')
        # Simple true pocket + shutter in east-facing loft.
        loft=bpy.data.objects['arrow_workshop_loft'];cut=box('TEMP_loft_cut',(-1.36,.90,z+.37),(.25,.60,.40),'shadow',80)
        bpy.context.view_layer.objects.active=loft;mo=loft.modifiers.new('recessed_loft_shutter','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cut;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cut,do_unlink=True);PARTS.pop()
        box('loft_recessed_cedar_shutter',(-1.44,.90,z+.37),(.045,.58,.38),'cedar',100)
    for name,loc in [('range_exit_south',(.9,-3,0)),('range_exit_east',(3,-.6,0)),('store_door',(-1.3,-.61,.21))]:
        o=bpy.data.objects.new('AUTHOR_'+name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;o['native_binding']='pending'
    bpy.context.view_layer.update();south_gap=bounds(bpy.data.objects['shade_post_1_0'])[0][0]-bounds(bpy.data.objects['shade_post_0_0'])[1][0];east_gap=bounds(bpy.data.objects['east_rear_boundary'])[0][1]-bounds(bpy.data.objects['woven_shooting_roof'])[1][1];store_gap=bounds(bpy.data.objects['store_east_rear'])[0][1]-bounds(bpy.data.objects['store_east_front'])[1][1]
    CONTACTS.extend([{'interface':'south exit clear between posts','measured_m':south_gap,'pass':abs(south_gap-2.94)<1e-5},{'interface':'east exit boundary to shade edge','measured_m':east_gap,'pass':abs(east_gap-2.11)<1e-5},{'interface':'store doorway clear width','measured_m':store_gap,'pass':abs(store_gap-1.10)<1e-5}])
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
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[6,6],'south_exit_clear_width_m':2.94,'east_exit_clear_width_m':2.11,'store_door_clear_width_m':1.10,'store_door_clear_height_m':1.55,'native_anchor_binding':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'assignment':'first visible percentage, cumulative','parts':PARTS,'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Range_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(10,-13,11));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=9.0;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Range_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=4;scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-12,1.4)),('back',(0,12,1.4)),('left',(-12,0,1.4)),('right',(12,0,1.4)),('top',(0,0,15)),('bottom',(0,0,-12))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('RANGE_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());saved=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched installed Abbasid Age II archery range decoded positions/topology';saved.append({'name':o.name,'vertices':len(vs),'faces':len(faces),'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Range_Age2_Reference.blend'))
    # Gray donor overview shows all decoded construction groups; reference source remains untouched.
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
    sc.world=bpy.data.worlds.new('ReferenceStudio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[1].default_value=.8
    bpy.ops.object.camera_add(location=(14,-20,14));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=17;cam.rotation_euler=(Vector((0,-3,1))-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-8,14));bpy.context.object.data.energy=1600;bpy.context.object.data.size=8
    sc.render.filepath=str(OUT/'stock_donor_overview.png');bpy.ops.render.render(write_still=True)
    (RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':saved,'geometry_reused_in_final':False,'footprint_from':'core.xml site_ext x=6 y=6; render bounds not footprint'},indent=2))
try:
    donor()
    for age in [2,3,4]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'cook':False,'native_owner_colour':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

