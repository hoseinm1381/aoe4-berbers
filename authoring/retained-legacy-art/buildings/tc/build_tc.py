"""Task-owned, reproducible Moroccan courtyard tc source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/tc'; OUT=ROOT/'output/buildings_batch/tc'; RESEARCH=ROOT/'research/buildings_batch/tc'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('TC_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberTC_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='TCAtlasUV')
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
    ctx=reset_scene(); PARTS=[];CONTACTS=[];MATS.clear();setup_maps()
    wall='earth' if age<3 else 'lime';floor=.18;h=2.55+age*.3
    box('foundation',(0,0,.09),(9.6,8.8,.18),'stone',0)
    box('council_courtyard',(0,0,.20),(9.3,8.5,.04),'earth',0)
    # Hall and lateral inhabited ranges; the open centre reads clearly from game camera.
    hall=box('rear_council_hall',(0,2.78,floor+h/2),(7.8,2.1,h),wall,40)
    for x,label in [(-3.7,'west'),(3.7,'east')]:
        box(label+'_range',(x,0,floor+(h-.45)/2),(1.55,3.46,h-.45),wall,40)
    for x in [-2.9,2.9]:box('front_enclosure',(x,-3.45,floor+1.8/2),(3.5,.46,1.8),wall,40)
    for x in [-4.30,4.30]:box('side_enclosure_link',(x,-2.195,floor+.90),(.35,.93,1.80),wall,40)
    # Entry remains physically open for villagers; gate lintel seats on piers.
    gh=2.20+.23*age
    for x in [-1.21,1.21]:box('entry_pier',(x,-3.45,floor+gh/2),(.62,.8,gh),wall,40)
    box('entry_lintel',(0,-3.45,floor+gh+.22),(3.05,.82,.44),'cedar' if age==1 else 'stone',60)
    CONTACTS.extend([{'interface':'pier bottom/floor','gap_m':0},{'interface':'entry lintel/piers','gap_m':0}])
    # Covered side arcade, genuinely void arches through a wall panel.
    arcade=box('courtyard_arcade_wall',(-2.88,0,floor+(h-.50)/2),(.32,3.5,h-.50),wall,40)
    for cy in [-1.05,0,1.05]:
        cutter=prism('TEMP_arcade',portal_outline(cy,floor-.02,.80,1.95),-3.20,-2.55,'shadow',40)
        # prism local X/Z profile is rotated to Y/Z, with thickness in X.
        for v in cutter.data.vertices:
            x,y,z=v.co;v.co=(y,x,z)
        bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(cutter.data);bm.free();cutter.data.update();bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active=arcade;mo=arcade.modifiers.new('Open horseshoe arcade','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
    # Hollow loggia behind the arch panel, leaving an outer wall and roof-bearing ends.
    west=bpy.data.objects['west_range']
    cavity=box('TEMP_gallery_hollow',(-3.34,0,floor+1.04),(1.00,3.15,2.12),'shadow',40)
    bpy.context.view_layer.objects.active=west;mo=west.modifiers.new('Covered civic loggia','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cavity;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cavity,do_unlink=True);PARTS.pop()
    for label,c,size,rh in [('hall',(0,2.78),(7.8,2.1),h),('west',(-3.7,0),(1.55,3.46),h-.45),('east',(3.7,0),(1.55,3.46),h-.45)]:
        top=floor+rh;box(label+'_roof',(c[0],c[1],top+.06),(*size,.12),'earth',60)
        for s in [-1,1]:
            box(label+'_parapet_long',(c[0],c[1]+s*(size[1]/2-.08),top+.29),(size[0],.16,.46),wall,80)
            box(label+'_parapet_end',(c[0]+s*(size[0]/2-.08),c[1],top+.29),(.16,size[1]-.32,.46),wall,80)
        CONTACTS.append({'interface':label+' roof/deck','gap_m':0})
    # Small civic corner chambers, broad rather than religious towers.
    for x in [-3.7,3.7]:
        for y in [-3.38,3.0]:
            ch=2.25+age*.18
            box('corner_watch_room',(x,y,floor+ch/2),(1.55,1.45,ch),wall,40)
            box('corner_flat_cap',(x,y,floor+ch+.08),(1.70,1.60,.16),'earth' if age<3 else 'lime',60)
            if age>1:
                for q in [-.58,0,.58]:box('corner_merlon',(x+q,y-.63,floor+ch+.38),(.24,.27,.45),wall,80)
    # Neutral fitted awning with narrow owner zones; stone and wood remain unmasked.
    cz=2.05
    for x in [-1.65,1.65]:
        box('awning_post',(x,-1.8,(cz+floor)/2),(.13,.13,cz-floor),'cedar',20)
    box('awning_crossbeam',(0,-1.8,cz),(3.5,.15,.15),'cedar',60)
    box('market_council_awning',(0,-1.05,cz+.075),(3.45,1.65,.045),'straw',80)
    for x in [-1.20,0,1.20]:box('awning_owner_stripe',(x,-1.05,cz+.105),(.35,1.65,.020),'owner_cloth',100)
    # Banner attached to gate lintel, never floating.
    box('owner_banner',(0,-3.875,floor+gh+.06),(.90,.03,.42),'owner_cloth',100)
    # Council seat, work benches and amphorae/storage cargo make it a civic centre.
    box('council_dais',(0,1.25,.30),(2.50,.70,.24),'stone',20)
    box('council_bench',(0,1.25,.63),(2.10,.40,.42),'cedar',80)
    for x in [-2.1,2.1]:
        box('traders_table',(x,.15,.75),(.8,1.3,.12),'cedar',80)
        for yy in [-.4,.7]:box('table_leg',(x,yy,.45),(.12,.12,.6),'cedar',60)
        for j in range(3):box('grain_chest',(x+j*.19-.2,.15,1.03),(.18,.55,.43),'straw',100)
    if age>=2:
        for x in [-1.21,1.21]:box('gate_stone_foot',(x,-3.47,.47),(.72,.85,.60),'stone',20)
        for x in [-3.7,3.7]:box('woven_civic_badge',(x,-4.12,1.30),(.48,.035,.38),'earth' if age>=3 else 'lime',100)
    if age>=3:
        box('raised_council_roof_pavilion',(0,2.80,floor+h+.55),(3.3,1.6,1.1),wall,60)
        box('pavilion_cap',(0,2.80,floor+h+1.16),(3.55,1.82,.12),'earth',80)
        for x in [-1.55,1.55]:box('pavilion_end_parapet',(x,2.80,floor+h+1.42),(.20,1.82,.40),wall,80)
    if age==4:
        for x in [-1.16,-.58,0,.58,1.16]:
            o=box('gate_diamond_relief',(x,-3.874,floor+gh+.28),(.16,.035,.16),'earth',100);o.rotation_euler.y=math.pi/4
        for x in [-2.9,-1.9,-.9,.9,1.9,2.9]:box('council_roof_stone_band',(x,1.715,floor+h-.20),(.7,.04,.14),'stone',100)
    # Rear council portal and windows are cut into the room, not pasted on the face.
    cut_portal(hall,0,1.73,floor+.01,1.32,2.28)
    for wx in [-2.75,2.75]:
        cutter=box('TEMP_hall_window',(wx,1.73,1.82),(.58,.60,.85),'shadow',40)
        bpy.context.view_layer.objects.active=hall;mo=hall.modifiers.new('Real council window','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
        box('council_shutter',(wx,1.91,1.82),(.56,.05,.83),'cedar',80)
        box('council_sill',(wx,1.68,1.38),(.76,.35,.12),'stone',80)
        for sx in [-.17,0,.17]:box('window_joinery',(wx+sx,1.87,1.82),(.035,.04,.80),'straw',100)
    # Original segmented arch voussoirs make the gate's horseshoe outline legible.
    if age>=2:
        r=1.05; zc=floor+gh-.55
        for k in range(13):
            t1=math.radians(-25+k*230/13);t2=math.radians(-25+(k+1)*230/13)
            outline=[(rr*math.cos(t),zc+rr*math.sin(t)) for rr,t in [(r,t1),(r+.25,t1),(r+.25,t2),(r,t2)]]
            prism('gate_arch_voussoir',outline,-3.88,-3.72,'stone' if age==2 else 'lime',80)
        for x in [-1.10,1.10]:box('arch_springer',(x,-3.8,floor+.90),(.25,.16,1.8),'stone',60)
    if age==1:
        for x in [-3.35,-2.4,-1.45,1.45,2.4,3.35]:
            box('earth_hall_timber_upright',(x,1.716,floor+h/2),(.12,.08,h),'cedar',20)
        box('hall_timber_plate',(0,1.70,floor+h-.12),(7.65,.12,.18),'cedar',60)
        for xx in [-3.65,3.65]:
            for yy in [-1.40,-.50,.40,1.3]:box('flat_roof_beam_ends',(xx,yy,floor+h-.47),(.13,.22,.15),'cedar',60)
    # Exterior side slit shutters, inset in the habitable wing.
    east=bpy.data.objects['east_range']
    for yy in [-.85,.85]:
        cutter=box('TEMP_side_window',(4.47,yy,1.55),(.45,.50,.70),'shadow',40)
        bpy.context.view_layer.objects.active=east;mo=east.modifiers.new('Side window cut','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
        box('side_inset_shutter',(4.30,yy,1.55),(.05,.48,.68),'cedar',80)
        box('side_sill',(4.48,yy,1.19),(.22,.67,.10),'stone',80)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    # Inherited installed core site_ext is 8x8. Scale authored plan into that exact envelope.
    for o in objects:
        o.location.x*=8/9.6;o.location.y*=8/8.8
        for v in o.data.vertices:v.co.x*=8/9.6;v.co.y*=8/8.8
    col=bpy.data.collections.new('BER_TC_Age'+str(age));bpy.context.scene.collection.children.link(col)
    for o in objects:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
    # Actual contact gaps from world-space bounds, not visual assertions.
    bpy.context.view_layer.update()
    def bb(o):
        ps=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(p[k] for p in ps) for k in range(3)],[max(p[k] for p in ps) for k in range(3)]]
    for child,parent,expected in [('hall_roof','rear_council_hall',0),('entry_lintel','entry_pier',0),('awning_owner_stripe','market_council_awning',-.0025)]:
        g=bb(bpy.data.objects[child])[0][2]-bb(bpy.data.objects[parent])[1][2];CONTACTS.append({'interface':child+'/'+parent,'measured_signed_gap_m':g,'expected_m':expected,'pass':abs(g-expected)<1e-5})
    checks=[]
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True)
        if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);vol=-vol
        checks.append({'object':o.name,'vertices':len(bm.verts),'triangles':sum(len(f.verts)-2 for f in bm.faces),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-10 for f in bm.faces),'positive_volume':vol,'uv_present':bool(o.data.uv_layers),'uv_in_atlas':all(0<=q.uv.x<=1 and 0<=q.uv.y<=1 for q in o.data.uv_layers.active.data)});bm.free()
    arcade_volume=next(c['positive_volume'] for c in checks if c['object']=='courtyard_arcade_wall')
    uncut_arcade_volume=.32*3.5*(h-.50)*(8/9.6)*(8/8.8)
    assert arcade_volume<uncut_arcade_volume*.80,('arcade openings absent',arcade_volume,uncut_arcade_volume)
    assert all(c.get('pass',True) for c in CONTACTS),CONTACTS
    assert all(c['non_manifold_edges']==0 and c['degenerate_faces']==0 and c['positive_volume']>0 and c['uv_in_atlas'] for c in checks),checks
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[8,8],'clear_entry_width_m':1.50,'native_exit_anchor_status':'source origin retained; inherited native marker binding requires integration','owner_colour':'source semantic and red-only PNG; native pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'first_visible_cumulative_stages':[0,20,40,60,80,100],'parts':PARTS,'binding':'source-only; Garrison recipe/native stage binding pending'},indent=2))
    for name,pos in [('ber_entry_front',(0,-4.0,0)),('ber_origin',(0,0,0))]:
        o=bpy.data.objects.new(name,None);col.objects.link(o);o.location=pos;o['author_anchor_only']=True
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_TC_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=4;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.46,.53,.64,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.55
    bpy.ops.object.camera_add(location=(13,-17,14));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.8))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=13.6;scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-7,-8,13));bpy.context.object.data.energy=1700;bpy.context.object.data.size=9
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_TC_Age{age}.blend'))
    scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=1;scene.render.resolution_x=300;scene.render.resolution_y=300
    for name,loc in [('front',(0,-20,2)),('back',(0,20,2)),('left',(-20,0,2)),('right',(20,0,2)),('top',(0,0,20)),('bottom',(0,0,-20))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('TC_AGE_DONE',age,flush=True)
def donor():
    ctx=reset_scene()
    for path in (RESEARCH/'stock').rglob('decoded-static.json'):
        d=json.loads(path.read_text());stem='Control' if 'control' in d['request']['logical_path'] else 'Combined'
        if stem!='Control':continue
        for g in d['geometry']['groups']:
            me=bpy.data.meshes.new(g['name']);me.from_pydata(g['positions'],[],g['triangles']);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['untouched_reference']=d['request']['logical_path']
        bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Untouched_Abbasid_TC_Age1.blend'))
        (RESEARCH/'donor_summary.json').write_text(json.dumps({'path':d['request'],'bounds':[g.get('bounds') for g in d['geometry']['groups']],'building_boundary_binding':d.get('building_boundary_binding'),'entity_binding':d.get('entity_binding')},indent=2));break
try:
    donor()
    for age in range(1,5):build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'capital_start_nomad':[1,2,3,4],'additional':[2,3,4],'geometry':'original enclosed council courtyard','cook':False,'native':'pending','mask':'source PNG + ber_owner_mask'},indent=2))
except: (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()





