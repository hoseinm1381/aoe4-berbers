"""Task-owned, reproducible Moroccan courtyard market source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/market'; OUT=ROOT/'output/buildings_batch/market'; RESEARCH=ROOT/'research/buildings_batch/market'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('Market_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberMarket_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='MarketAtlasUV')
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
    # Extra atlas source maps are flat physically meaningful inputs, not decoded packed game maps.
    for name,col in [('normal',(.5,.5,1)),('roughness',(.85,.85,.85)),('metal',(0,0,0))]:
        im=bpy.data.images.new('Market_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
    wall='earth' if age==2 else 'lime';h=2.20+(age-2)*.28
    box('foundation',(0,0,.08),(8,8,.16),'stone',0)
    box('court_floor',(0,0,.175),(7.8,7.8,.03),'earth',0)
    # U-shaped inhabited range, open trade court and clear south entrance; source origin Z=0.
    for side,x in [('west',-3.12),('east',3.12)]:
        box(side+'_warehouse',(x,.40,.19+h/2),(1.56,6.6,h),wall,40)
        box(side+'_roof',(x,.40,.19+h+.06),(1.56,6.6,.12),'earth',60)
        contact(side+'_roof',side+'_warehouse')
        for xx in [x-.71,x+.71]:box(side+'_parapet',(xx,.40,.19+h+.27),(.14,6.6,.30),wall,80)
        for yy in [-2.83,3.63]:box(side+'_parapet_end',(x,yy,.19+h+.27),(1.28,.14,.30),wall,80)
        # Exterior warehouse ventilation is carved into the mass, not floating facade decals.
        for yy in [-1.8,.15,2.1]:
            xx=x+(-.78 if x<0 else .78)
            cutter=box('TEMP_lower_window',(xx,yy,1.43),(.34,.68,.70),'shadow',80)
            target=bpy.data.objects[side+'_warehouse'];bpy.context.view_layer.objects.active=target;mo=target.modifiers.new('warehouse_opening','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
            box(side+'_lower_cedar_shutter',(xx+(.11 if x<0 else -.11),yy,1.43),(.05,.66,.68),'cedar',80)
            for dy in [-.21,0,.21]:box(side+'_shutter_joinery',(xx+(.08 if x<0 else -.08),yy+dy,1.43),(.035,.028,.60),'straw',100)
            box(side+'_window_sill',(xx,yy,1.03),(.18,.80,.10),'stone',80)
            box(side+'_drain_spout',(xx+(.09 if x<0 else -.09),yy,.19+h+.12),(.36,.10,.10),'cedar',80)
        for yy in [-2.77,3.55]:
            box(side+'_buttress',(x+(-.66 if x<0 else .66),yy,.19+h*.44),(.24,.24,h*.88),wall,40)
        # outward shutters are cut pockets; street goods are kept out of central transit lane.
        for yy in [-1.75,.1,1.95]:
            inner=x+(.78 if x<0 else -.78)
            box(side+'_stall_back',(inner,yy,1.0),(.025,1.24,1.45),'cedar',60)
            box(side+'_sales_counter',(inner+(.375 if x<0 else -.375),yy,.68),(.75,1.22,.14),'cedar',80)
            for j in range(3):tube(side+'_spice_bin',(inner+(.375 if x<0 else -.375),yy+(j-1)*.31,.86),.12,.22,'clay')
            for ypost in [yy-.65,yy+.65]:
                box(side+'_shade_post',(inner+(.99 if x<0 else -.99),ypost,1.29),(.085,.085,2.20),'cedar',20)
            canopy=box(side+'_stall_awning',(inner+(.53 if x<0 else -.53),yy,2.40),(1.16,1.40,.06),'straw',80)
            for offset in [-.41,0,.41]:box(side+'_owner_awning_stripe',(inner+(.53 if x<0 else -.53),yy+offset,2.434),(1.16,.14,.015),'owner_cloth',100)
            post=bpy.data.objects[side+'_shade_post'];bpy.context.view_layer.update();gap=bounds(canopy)[0][2]-bounds(post)[1][2];CONTACTS.append({'interface':side+' canopy to post','measured_signed_gap':gap,'expected':-.02,'pass':abs(gap+.02)<1e-5})
        if age>=3:
            # Real second storey mass with outward-facing recessed cedar shutters.
            box(side+'_upper_store',(x,1.3,.19+h+.47),(1.56,4.7,.7),wall,60)
            box(side+'_upper_cap',(x,1.3,.19+h+.865),(1.62,4.76,.09),'lime',80)
            contact(side+'_upper_cap',side+'_upper_store')
            for yy in [-.2,1.2,2.6]:
                xx=x+(-.78 if x<0 else .78)
                cutter=box('TEMP_window',(xx,yy,.19+h+.47),(.24,.52,.43),'shadow',80)
                obj=bpy.data.objects[side+'_upper_store'];bpy.context.view_layer.objects.active=obj;mo=obj.modifiers.new('cut_storage_window','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
                box(side+'_recessed_shutter',(xx+(.10 if x<0 else -.10),yy,.19+h+.47),(.04,.50,.41),'cedar',80)
        contact(side+'_warehouse','court_floor')
    box('rear_goods_hall',(0,3.12,.19+h/2),(4.68,1.56,h),wall,40)
    box('rear_hall_roof',(0,3.12,.19+h+.06),(4.68,1.56,.12),'earth',60);contact('rear_hall_roof','rear_goods_hall')
    box('rear_hall_parapet',(0,3.84,.19+h+.27),(4.68,.14,.30),wall,80)
    # An actual 1.8m open connected gateway between solid piers, no blocked fake door plane.
    for side,x in [('left',-1.58),('right',1.58)]:
        box('entry_'+side+'_pier',(x,-3.15,.19+1.22),(1.36,1.25,2.44),wall,40)
        box('entry_'+side+'_stone_base',(x,-3.15,.35),(1.40,1.29,.32),'stone',20)
    box('entry_lintel',(0,-3.15,2.80),(4.52,1.25,.34),wall,60)
    contact('entry_lintel','entry_left_pier')
    box('entry_coping',(0,-3.15,3.01),(4.62,1.34,.08),'lime' if age>=3 else 'earth',80);contact('entry_coping','entry_lintel')
    box('gate_owner_textile',(0,-3.80,2.80),(1.68,.03,.22),'owner_cloth',100)
    # Commodity stacks / cargo staging outside the through route.
    for side,x in [('west',-2.8),('east',2.8)]:
        for row in range(age):
            box(side+'_cargo_crate',(x,-3.23+(row%2)*.40,.19+.20+(row//2)*.4),(.46,.37,.4),'cedar',100)
            for zz in [.26+(row//2)*.4,.48+(row//2)*.4]:box(side+'_crate_band',(x,-3.42+(row%2)*.4,zz),(.46,.026,.035),'straw',100)
    # Measuring station in rear court: spindle, beam, rods and two thick metal/wood pans.
    box('balance_table',(0,1.7,.69),(1.18,.66,.10),'cedar',80)
    for x in [-.5,.5]:box('balance_table_leg',(x,1.7,.415),(.10,.52,.45),'cedar',60)
    box('balance_spindle',(0,1.7,1.10),(.065,.065,.72),'stone',100)
    box('balance_arm',(0,1.7,1.46),(.87,.055,.065),'cedar',100)
    for x in [-.37,.37]:
        box('balance_pan_rod',(x,1.7,1.28),(.018,.018,.3),'stone',100)
        tube('balance_pan',(x,1.7,1.12),.19,.035,'stone')
    if age==4:
        for x in [-1.86,-1.58,-1.30,1.30,1.58,1.86]:
            o=box('entry_diamond',(x,-3.788,2.25),(.16,.035,.16),'earth',100);o.rotation_euler.y=math.pi/4
        for x in [-3.1,3.1]:
            box('roof_cargo_cabinet',(x,2.9,.19+h+1.14),(1.10,.64,.50),'cedar',100)
            box('roof_cabinet_cap',(x,2.9,.19+h+1.42),(1.18,.72,.06),'lime',100)
    # Independent downstream author anchors; source only, do not pretend native marker binding.
    for name,loc in [('trade_entry',(0,-4,0)),('court_transit',(0,0,.19)),('trade_exit',(0,-4,0))]:
        o=bpy.data.objects.new('AUTHOR_'+name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;o['native_binding']='pending'
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
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[8,8],'clear_gateway_m':1.8,'central_transit_corridor_m':1.8,'native_anchor_binding':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'assignment':'first visible percentage, cumulative','parts':PARTS,'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Market_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(10,-13,11));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=12.2;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Market_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=4;scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-12,1.4)),('back',(0,12,1.4)),('left',(-12,0,1.4)),('right',(12,0,1.4)),('top',(0,0,15)),('bottom',(0,0,-12))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('MARKET_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());saved=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched installed Abbasid Age II market decoded positions/topology';saved.append({'name':o.name,'vertices':len(vs),'faces':len(faces),'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Market_Age2_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':saved,'geometry_reused_in_final':False,'footprint_from':'core.xml site_ext x=8 y=8; render bounds not footprint'},indent=2))
try:
    donor()
    for age in [2,3,4]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'cook':False,'native_owner_colour':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

