"""Task-owned, reproducible Moroccan courtyard dock source; no cook or production edits."""
import bpy,bmesh,math,json,traceback,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/dock'; OUT=ROOT/'output/buildings_batch/dock'; RESEARCH=ROOT/'research/buildings_batch/dock'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('Dock_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberDock_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='DockAtlasUV')
    for p in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis]
        coords=[o.data.vertices[o.data.loops[li].vertex_index].co for li in p.loop_indices]
        lo=[min(c[a] for c in coords) for a in axes];hi=[max(c[a] for c in coords) for a in axes]
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=((slot%4+.07+.86*(co[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-9))/4,(slot//4+.07+.86*(co[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-9))/2)
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

def cylinder(name,center,radius,depth,mat='cedar',stage=80):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=depth,location=center)
    return finish(bpy.context.object,name,mat,stage)

def additional_maps():
    for name,rgb in [('normal',(.5,.5,1)),('roughness',(.84,.84,.84)),('metal',(0,0,0))]:
        im=bpy.data.images.new('Dock_'+name,width=256,height=256);im.pixels.foreach_set([*rgb,1]*65536);im.colorspace_settings.name='Non-Color';im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True

def roof_prism(name,x,y,w,d,z,h,mat):
    return prism(name,[(x-w/2,z),(x+w/2,z),(x+w/2,z+.10),(x,z+h),(x-w/2,z+.10)],y-d/2,y+d/2,mat,60)

def berth():
    # Explicit source convention: +Y land, -Y water, water plane Z=0. Not an engine marker claim.
    quay=box('quay_foundation',(0,.50,.10),(8,1.60,1.30),'stone',0)
    box('quay_deck',(0,.50,.80),(8,1.60,.10),'earth',20)
    for side,x in [('west',-3.2),('east',3.2)]:
        box(side+'_pier_deck',(x,-2.15,.80),(1.40,4.30,.10),'cedar',40)
        for yy in [-.5,-1.5,-2.5,-3.9]:
            box(side+'_crossbeam',(x,yy,.68),(1.48,.18,.14),'cedar',20)
            for xx in [x-.54,x+.54]:
                cylinder(side+'_pile',(xx,yy,-.415),.11,2.19,'cedar',0)
        # Plank seams and pile caps express construction at strategy camera distance.
        for yy in [-.4-i*.24 for i in range(17)]:box(side+'_plank_seam',(x,yy,.856),(1.39,.018,.012),'shadow',60)
        for yy in [-.7,-2.15,-3.55]:
            b=cylinder(side+'_bollard',(x,yy,1.035),.14,.37,'cedar',80)
            cylinder(side+'_bollard_cap',(x,yy,1.21),.185,.07,'stone',80)
        CONTACTS.extend([{'interface':side+' deck/crossbeam','expected_gap':0},{'interface':side+' piles/crossbeams','expected_overlap':.025}])
    # Side slip stays outside central 2.8m launch lane. Sloping connected prism, no floating boards.
    verts=[(x,y,z) for x in [-2.5,-1.5] for y,z in [(-.30,.85),(-1.8,.02),(-1.8,-.08),(-.30,.75)]]
    me=bpy.data.meshes.new('slipway');me.from_pydata(verts,[],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update();o=bpy.data.objects.new('west_slipway',me);bpy.context.scene.collection.objects.link(o);finish(o,'west_slipway','cedar',40)

def warehouse(age):
    z=.85;h=2.0+.15*age;wall='earth' if age<3 else 'lime'
    box('warehouse_land_plinth',(0,2.6,.38),(6.40,2.8,.94),'stone',0)
    front=box('warehouse_front',(0,1.30,z+h/2),(6.0,.20,h),wall,40)
    back=box('warehouse_back',(0,3.60,z+h/2),(6.0,.20,h),wall,40)
    for x in [-2.9,2.9]:box('warehouse_side',(x,2.45,z+h/2),(.20,2.10,h),wall,40)
    # Wide recessed storage portal and operable-looking joinery; no flat door stuck on an uncut wall.
    cut_portal(front,0,1.20,z,1.5,1.85)
    if age==1:
        for x in [-2.7,-1.8,-.9,.9,1.8,2.7]:box('timber_wall_frame',(x,1.16,z+h/2),(.11,.09,h),'cedar',20)
        roof_prism('pitched_reed_roof',0,2.45,6.30,2.70,z+h,.85,'straw')
        box('roof_ridge',(0,2.45,z+h+.87),(.12,2.75,.12),'cedar',80)
    else:
        box('warehouse_roof',(0,2.45,z+h+.06),(6.30,2.70,.12),'earth',60)
        for x in [-3.10,3.10]:box('roof_side_parapet',(x,2.45,z+h+.26),(.10,2.70,.40),wall,80)
        for yy in [1.15,3.75]:box('roof_end_parapet',(0,yy,z+h+.26),(6.10,.10,.40),wall,80)
        for x in [-2.5,2.5]:box('timber_roof_drain',(x,1.02,z+h+.08),(.12,.48,.10),'cedar',80)
    for x in [-1.8,1.8]:
        cut=box('TEMP_shutter',(x,1.30,2.35),(.62,.50,.7),'shadow',60)
        bpy.context.view_layer.objects.active=front;mod=front.modifiers.new('real_window_recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True);PARTS.pop()
        box('warehouse_shutter',(x,1.30,2.35),(.60,.055,.68),'cedar',80)
        box('shutter_stone_sill',(x,1.13,1.985),(.75,.30,.07),'stone',80)
        for xx in [x-.18,x,x+.18]:box('shutter_joinery',(xx,1.262,2.35),(.045,.03,.60),'straw',80)
    # Owner neutral cloth on front warehouse and supported harbour shade.
    box('owner_portal_stripe',(0,1.19,2.98),(1.65,.04,.20),'owner_cloth',100)
    for x in [1.8,3.50]:box('shade_post',(x,-.32,1.80),(.11,.11,1.90),'cedar',20)
    box('shade_crossbeam',(2.65,-.32,2.74),(1.80,.14,.14),'cedar',60)
    for x in [1.8,3.50]:box('shade_rear_post',(x,1.0,1.80),(.11,.11,1.90),'cedar',20)
    box('shade_rear_crossbeam',(2.65,1.0,2.74),(1.80,.14,.14),'cedar',60)
    box('harbour_shade',(2.65,.30,2.85),(1.95,1.55,.08),'straw',80)
    box('owner_canopy_stripe',(2.65,-.44,2.898),(1.94,.22,.016),'owner_cloth',100)
    if age>=3:
        store=box('upper_roof_storage',(-1.7,2.55,z+h+.77),(2.20,1.80,1.30),'earth',60)
        box('upper_storage_lime_cap',(-1.7,2.55,z+h+1.46),(2.35,1.95,.08),'lime',80)
        cutter=box('TEMP_store_recess',(-1.7,1.65,z+h+.77),(.72,.28,.57),'shadow',60)
        bpy.context.view_layer.objects.active=store;mod=store.modifiers.new('upper_store_actual_recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
        box('upper_store_recessed_louver',(-1.7,1.77,z+h+.77),(.70,.025,.55),'cedar',80)
        for xx in [-2.69,-2.40]:box('roof_ladder_rail',(xx,1.02,2.0),(.055,.06,2.30),'cedar',80)
        for zz in [1.0+i*.27 for i in range(8)]:box('roof_ladder_rung',(-2.545,1.02,zz),(.36,.08,.065),'cedar',80)
    if age==4:
        for x in [-2.92,2.92]:
            for zz in [1.15,1.70,2.25,2.80]:box('stone_corner_course',(x,1.18,zz),(.23,.12,.24),'stone',80)
        for xx in [-.60,-.30,0,.30,.60]:
            o=box('portal_geometric_panel',(xx,1.143,3.22),(.14,.045,.14),'lime',100);o.rotation_euler.y=math.pi/4
        # Useful winding hoist on eastern pier, clear of launch corridor.
        cylinder('hoist_pedestal',(3.2,-1.15,1.05),.32,.40,'stone',40)
        box('hoist_mast',(3.2,-1.15,2.25),(.18,.18,2.0),'cedar',60)
        box('hoist_davit',(2.87,-1.15,3.26),(.85,.18,.18),'cedar',80)
        cylinder('hoist_rope',(2.48,-1.15,2.45),.018,1.50,'straw',80)
        cylinder('hoist_winding_drum',(3.2,-1.15,1.42),.28,.20,'cedar',80)
    CONTACTS.append({'interface':'warehouse/plinth','expected_gap':0})

def cargo(age):
    for x,y in [(-2.90,.30),(-2.10,.40),(2.25,.70)]:
        box('cargo_crate',(x,y,1.12),(.55,.48,.54),'cedar',80)
        for zz in [.90,1.34]:box('crate_binding',(x,y-.25,zz),(.56,.03,.04),'straw',100)
    for i in range(age+1):
        cylinder('barrel',(-3.4+(i%2)*.46,.8+(i//2)*.45,1.13),.20,.56,'cedar',80)
    for x,y in [(-3.2,-2.65),(3.2,-3.15)]:
        bpy.ops.mesh.primitive_torus_add(major_radius=.22,minor_radius=.025,major_segments=16,minor_segments=6,location=(x,y,.881));finish(bpy.context.object,'rope_coil','straw',100)

def bounds(o):
    points=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)]]

def audit(age,objects):
    bpy.context.view_layer.update();records=[]
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));vol=bm.calc_volume(signed=True)
        if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));vol=-vol
        bm.to_mesh(o.data);non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free()
        uv=o.data.uv_layers.active;uvbad=0
        for p in o.data.polygons:
            pts=[uv.data[i].uv for i in p.loop_indices];area=abs(sum(pts[i].x*pts[(i+1)%len(pts)].y-pts[(i+1)%len(pts)].x*pts[i].y for i in range(len(pts))))/2
            if area<1e-10:uvbad+=1
        rec={'object':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'non_manifold_edges':non,'degenerate_faces':deg,'positive_volume':vol,'uv_zero_area_faces':uvbad,'finite_vertices':all(math.isfinite(v) for p in o.data.vertices for v in p.co),'positive_transforms':all(v>0 for v in o.scale),'bounds':bounds(o)};records.append(rec)
    # Check meaningful numeric contact and passage guards from final mesh bounds.
    checks=[]
    for c,p,axis,ci,pi,expected in [('quay_deck','quay_foundation',2,0,1,0),('warehouse_front','warehouse_land_plinth',2,0,1,0),('west_pier_deck','west_crossbeam',2,0,1,0),('east_pier_deck','east_crossbeam',2,0,1,0),('shade_post','quay_deck',2,0,1,0),('shade_crossbeam','shade_post',2,0,1,-.08),('shade_rear_post','quay_deck',2,0,1,0),('harbour_shade','shade_rear_crossbeam',2,0,1,0),('harbour_shade','shade_crossbeam',2,0,1,0)]:
        gap=bounds(bpy.data.objects[c])[ci][axis]-bounds(bpy.data.objects[p])[pi][axis];checks.append({'interface':c+'/'+p,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})
    lane=[]
    for o in objects:
        b=bounds(o)
        if b[0][0]<1.4-1e-6 and b[1][0]>-1.4+1e-6 and b[0][1]<-.30-1e-6 and b[1][1]>-4.30:lane.append(o.name)
    assert not lane,lane
    assert all(c['pass'] for c in checks),checks
    # Boolean UV is refreshed below by planar projection, therefore actual opening audit does not accept degenerate UV.
    assert all(r['non_manifold_edges']==0 and r['degenerate_faces']==0 and r['positive_volume']>0 and r['finite_vertices'] and r['positive_transforms'] and r['uv_zero_area_faces']==0 for r in records),[r for r in records if r['uv_zero_area_faces'] or r['non_manifold_edges'] or r['degenerate_faces']]
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':records,'contacts':checks,'footprint_envelope':{'authored_xy':[[-4,-4.3],[4,4]],'native_site_xy':[8,8],'pier_overhang_water_y':.30,'author_waterline':0,'deck_height':.85,'central_launch_lane_width':2.8,'between_pier_clear_width':5.0,'central_lane_obstacles':lane,'native_markers_bound':False},'native_owner_colour':'blocked source annotation only'},indent=2))

def reproject(o):
    # Regenerate UV after boolean cuts without re-registering stage entries.
    slot=MATS[o['ber_material_role']][1];uv=o.data.uv_layers.active
    for p in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis];coords=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];lo=[min(v[a] for v in coords) for a in axes];hi=[max(v[a] for v in coords) for a in axes]
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=((slot%4+.07+.86*(co[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-9))/4,(slot//4+.07+.86*(co[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-9))/2)

def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();additional_maps();berth();warehouse(age);cargo(age)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objects:reproject(o)
    audit(age,objects)
    col=bpy.data.collections.new('BER_Dock_Age'+str(age));bpy.context.scene.collection.children.link(col)
    for o in objects:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
    for name,pos in [('AUTHOR_WATER_DATUM',(0,0,0)),('AUTHOR_LAND_EDGE',(0,0,.85)),('AUTHOR_LAUNCH_CLEAR_CORRIDOR',(0,-2.3,0)),('AUTHOR_BERTH_MOUTH',(0,-4.3,0))]:
        o=bpy.data.objects.new(name,None);col.objects.link(o);o.location=pos;o['native_binding']='unqualified author reference, preserve original layout_docks'
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'parts':PARTS,'stages':[0,20,40,60,80,100],'assignment':'cumulative first visible percentage','native_selector_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Dock_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Harbour studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.49,.53,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(10,-13,12));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=13;cam.rotation_euler=(Vector((0,.0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,11));bpy.context.object.data.energy=1600;bpy.context.object.data.size=8
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Dock_Age{age}.blend'))
    scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=8;scene.render.resolution_x=400;scene.render.resolution_y=400
    for name,loc in [('front',(0,-14,2)),('back',(0,14,2)),('left',(-14,0,2)),('right',(14,0,2)),('top',(0,0,16)),('bottom',(0,0,-14))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('DOCK_AGE_DONE',age,flush=True)

def donor():
    ctx=reset_scene()
    for label,folder in [('Abbasid_Dock','stock'),('Common_Piers','piers_stock')]:
        d=json.loads(next((RESEARCH/folder).rglob('decoded-static.json')).read_text())
        col=bpy.data.collections.new('UNTouched_'+label);bpy.context.scene.collection.children.link(col)
        for group in d['geometry']['groups']:
            verts=group['positions'];faces=group.get('triangles',group.get('indices',[]))
            if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
            me=bpy.data.meshes.new(label+'_'+group['name']);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(label+'_'+group['name'],me);col.objects.link(o);o['reference_only']='untouched decoded geometry; material and native datum not reconstructed'
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Stock_Dock_and_Piers_Reference.blend'))

try:
    donor()
    for age in [int(x) for x in os.environ.get('DOCK_AGES','1,2,3,4').split(',')]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'cook':False,'native_acceptance':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:
    bpy.ops.wm.quit_blender()
