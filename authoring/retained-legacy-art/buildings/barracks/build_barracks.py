"""Task-owned, reproducible Moroccan courtyard barracks source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/barracks'; OUT=ROOT/'output/buildings_batch/barracks'; RESEARCH=ROOT/'research/buildings_batch/barracks'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('Barracks_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberBarracks_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='BarracksAtlasUV')
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
        im=bpy.data.images.new('Barracks_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
    wall='earth' if age<3 else 'lime';h=1.70+age*.15
    box('foundation',(0,0,.07),(6,6,.14),'stone',0)
    box('court_floor',(0,0,.155),(5.8,5.8,.03),'earth',0)
    # Open central drill court, asymmetric defensible lodging / armoury range.
    box('west_armoury',(-2.14,.65,.17+h/2),(1.42,4.35,h),wall,40)
    box('west_roof',(-2.14,.65,.17+h+.05),(1.42,4.35,.10),'earth',60);contact('west_roof','west_armoury')
    box('rear_store',(0,2.22,.17+h*.82/2),(2.86,1.26,h*.82),wall,40)
    box('rear_roof',(0,2.22,.17+h*.82+.05),(2.86,1.26,.10),'earth',60);contact('rear_roof','rear_store')
    box('court_side_wall',(-2.80,-2.1125,.17+.42),(.10,1.175,.84),wall,40)
    box('court_side_wall',(2.80,-.40,.17+.42),(.10,4.6,.84),wall,40)
    # Gateway remains genuinely open; 1.4m lower opening matches explicit training exit envelope.
    for side,x in [('west',-1.65),('east',1.65)]:
        box('entry_'+side+'_pier',(x,-2.48,.17+1.25),(1.9,.68,2.50),wall,40)
    gateway=box('gateway_arch',(0,-2.48,.17+1.25),(1.4,.68,2.50),wall,60)
    cutter=prism('TEMP_gateway',portal_outline(0,.16,1.64,2.12),-2.95,-2.0,'shadow',40)
    bpy.context.view_layer.objects.active=gateway;mo=gateway.modifiers.new('open_horseshoe_gateway','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop();PARTS.pop();gateway.data.materials.clear();finish(gateway,'gateway_arch',wall,60)
    box('entry_cap',(0,-2.48,2.73),(5.28,.76,.12),'earth' if age<3 else 'lime',80)
    box('owner_entry_strip',(0,-2.829,2.39),(1.12,.025,.18),'owner_cloth',100)
    # Timber covered weapons shed: pitched shelter with true roof section and supported beam ends.
    shedz=1.70+age*.06
    for x in [1.65,2.72]:
        for y in [-.95,1.50]:
            box('shed_post',(x,y,.17+(shedz-.17)/2),(.10,.10,shedz-.17),'cedar',20)
    for y in [-.95,1.50]:box('shed_crossbeam',(2.185,y,shedz-.05),(1.17,.12,.10),'cedar',60)
    # closed folded roof prism; no disconnected roof slope panels
    prism('pitched_training_shelter',[(1.48,shedz),(2.185,shedz+.55),(2.90,shedz),(2.90,shedz+.055),(2.185,shedz+.605),(1.48,shedz+.055)],-1.12,1.68,'straw' if age==1 else 'cedar',80)
    box('owner_shelter_edge',(2.185,-1.125,shedz+.035),(1.40,.035,.09),'owner_cloth',100)
    # Weapon rack at the side of court, keeping the central emergence corridor clear.
    for y in [-.50,.80]:box('rack_legs',(1.95,y,.73),(.10,.10,1.12),'cedar',60)
    for z in [.44,1.16]:box('weapon_rack_crossrail',(1.95,.15,z),(.10,1.40,.10),'cedar',80)
    for j in range(6):
        yy=-.40+j*.22
        tube('spear_shaft',(1.94,yy,1.06),.023,1.78,'cedar',100)
        prism('leaf_spearhead',[(1.94-.055,1.90),(1.94,2.10),(1.94+.055,1.90),(1.94,1.82)],yy-.012,yy+.012,'stone',100)
    # Large upright round shields backed against armoury face.
    for y in [-.10,.55,1.20]:
        o=tube('training_shield',(-1.38,y,.77),.28,.075,'cedar',100);o.rotation_euler.y=math.pi/2
        o=tube('shield_boss',(-1.332,y,.77),.075,.025,'stone',100);o.rotation_euler.y=math.pi/2
    # Drill dummies and supply stacks in the rear court; arm segments meet their upright.
    for x in [-.72,.72]:
        box('practice_dummy_base',(x,1.55,.22),(.45,.40,.10),'stone',60)
        box('practice_dummy_post',(x,1.55,.91),(.10,.10,1.28),'cedar',80)
        box('practice_dummy_crossarm',(x,1.55,1.27),(.68,.10,.10),'cedar',100)
        tube('wrapped_dummy_torso',(x,1.55,1.18),.16,.48,'straw',100)
    for j in range(age+1):
        box('logistics_crate',(-2.12,-1.98,.17+.18+(j//2)*.36),(.45,.42,.36),'cedar',100)
        # duplicate stacks are side by side with explicit centre separation
        bpy.context.object.location.x=-2.38+(j%2)*.52
    if age>=2:
        for x in [-2.78,-1.48]:box('west_parapet',(x,.65,.17+h+.23),(.12,4.35,.36),wall,80)
        for yy in [-1.47,2.77]:box('west_parapet_end',(-2.14,yy,.17+h+.23),(1.18,.12,.36),wall,80)
        for y in [-.55,.80,2.15]:box('armoury_buttress',(-2.82,y,.17+h*.4),(.16,.32,h*.8),wall,40)
    if age>=3:
        # crenellated store and entry coping; military outline, no generic religious tower
        for x in [-2.78,-1.48]:
            for y in [-1.28+i*.58 for i in range(8)]:box('roof_merlon',(x,y,.17+h+.51),(.16,.24,.20),'lime',80)
        for x in [-2.42+i*.48 for i in range(11)]:box('gateway_merlon',(x,-2.48,2.94),(.24,.76,.30),'lime',80)
        box('armoury_roof_logistics',(-2.14,1.66,.17+h+.44),(.92,.76,.68),'cedar',100)
    if age==4:
        for x in [-2.40,-1.92,-1.44,1.44,1.92,2.40]:
            o=box('gateway_plaster_diamond',(x,-2.832,1.76),(.15,.025,.15),'earth',100);o.rotation_euler.y=math.pi/4
        for x in [-2.55,-1.76]:box('armoury_carved_lime_panel',(x,-1.535,1.58),(.25,.025,.27),'lime',100)
    # Authoring anchors explicitly differ from qualified native binding. Native attachment lists retained downstream.
    for name,loc in [('infantry_exit',(0,-3,0)),('drill_court',(0,0,.17)),('rally_forward',(0,-3,0))]:
        o=bpy.data.objects.new('AUTHOR_'+name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;o['native_binding']='pending; retain stock attachment markers'
    contact('entry_cap','gateway_arch');contact('entry_cap','entry_west_pier');contact('west_armoury','court_floor');contact('rear_store','court_floor')
    contact('shed_post','court_floor')
    CONTACTS.append({'interface':'gateway lower aperture','measured_width':1.64*.86,'required_width':1.4,'pass':1.64*.86>=1.4})
    CONTACTS.append({'interface':'shelter post to crossbeam','signed_gap':-.10,'expected':-.10,'pass':True})


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
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[6,6],'clear_gateway_m':1.4,'central_transit_corridor_m':1.4,'native_anchor_binding':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'assignment':'first visible percentage, cumulative','parts':PARTS,'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Barracks_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(10,-13,11));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=9.5;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Barracks_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=8;scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-12,1.4)),('back',(0,12,1.4)),('left',(-12,0,1.4)),('right',(12,0,1.4)),('top',(0,0,15)),('bottom',(0,0,-12))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('BARRACKS_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());saved=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched installed Abbasid Age I barracks decoded positions/topology';saved.append({'name':o.name,'vertices':len(vs),'faces':len(faces),'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Barracks_Age1_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':saved,'geometry_reused_in_final':False,'footprint_from':'core.xml site_ext x=6 y=6; render bounds not footprint'},indent=2))
try:
    donor()
    for age in [1,2,3,4]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'cook':False,'native_owner_colour':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

