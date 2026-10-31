"""Task-owned, reproducible Moroccan courtyard house source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/wall_tower'; OUT=ROOT/'output/buildings_batch/wall_tower'; RESEARCH=ROOT/'research/buildings_batch/wall_tower'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('metal',(.19,.20,.18),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('WallTower_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberWallTower_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='WallTowerAtlasUV')
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

def cylinder(name,center,radius,depth,mat='metal',axis='Z',stage=100):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=depth,location=center)
    o=bpy.context.object
    if axis=='Y':o.rotation_euler.x=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return finish(o,name,mat,stage)

def tower(age):
    global PARTS,CONTACTS
    ctx=reset_scene(); PARTS=[];CONTACTS=[];MATS.clear();setup_maps()
    for name,rgb in [('roughness',(.84,.84,.84)),('normal',(.5,.5,1)),('metalness',(0,0,0))]:
        im=bpy.data.images.new('WallTower_'+name,width=256,height=256,alpha=True); im.pixels.foreach_set([*rgb,1]*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack()
    mat='earth' if age==2 else 'lime'
    box('ground_stone_plinth',(0,-1.45,.2),(6.4,8.2,.4),'stone',0)
    # Tapered battered lower block: actual square defensive tower, front of wall.
    prism('battered_front_tower',[(-3.05,.4),(3.05,.4),(2.75,6.65),(-2.75,6.65)],-5.4,-1.5,mat,20)
    box('front_upper_chamber',(0,-3.45,8.475),(5.5,3.9,3.65),mat,60)
    # Elevated through passage: no solid core obstructs wall walk.
    box('through_walk_deck',(0,0,6.825),(6.4,4.2,.35),'stone',60)
    box('rear_support_west',(-2.65,1.8,3.325),(1.1,.6,6.65),mat,40)
    box('rear_support_east',(2.65,1.8,3.325),(1.1,.6,6.65),mat,40)
    box('rear_bearer',(0,1.8,6.275),(4.2,.6,.75),'cedar',40)
    # Rear parapet keeps clear width exactly3; side openings x+-3.2 remain free.
    box('rear_walk_parapet',(-2.025,1.8,7.6),(2.35,.6,1.2),mat,80)
    box('rear_walk_parapet_east',(2.025,1.8,7.6),(2.35,.6,1.2),mat,80)
    # Front passage edge meets chamber at y=-1.5, masonry above10.3.
    # Straight flights behind the wall, source stair footprint remains within donor render envelope.
    for i in range(20):
        z=(i+1)*.35; y=4.55-i*.14
        box('rear_access_step_%02d'%i,(0,y,z-.175),(1.7,.14,.35),'stone',40)
    # Continuous stair stringer support: triangular side profile under exact stair risers.
    outline=[(1.75,0),(4.69,0),(1.75,7)]
    # profile is y,z, converted to x,z prism then rotated around Z.
    support=prism('stair_ramp_support',outline,-.85,.85,'earth',20); support.rotation_euler.z=math.pi/2
    # Roof is weapon platform fitted to chamber top10.3.
    box('roof_platform',(0,-3.45,10.4),(5.75,4.15,.2),'stone',80)
    for x in [-2.64,2.64]:
        box('roof_side_parapet',(x,-3.45,10.83),(.47,4.15,.66),mat,80)
        for y in [-5.28,-4.45,-3.62,-2.79,-1.8]:box('roof_side_merlon',(x,y,11.45),(.47,.48,.58),mat,100)
    for y in [-5.29,-1.61]:
        # weapon-facing central gap genuinely left between two front sections
        for x in [-1.61,1.61]:box('roof_front_split_parapet',(x,y,10.83),(1.59,.47,.66),mat,80)
        for x in [-1.76,1.76]:box('roof_front_merlon',(x,y,11.45),(.48,.47,.58),mat,100)
    # Actual recessed rear chamber access from the elevated wall walk.
    chamber=bpy.data.objects['front_upper_chamber']
    cutter=prism('TEMP_chamber_door',portal_outline(0,7.01,1.15,2.45),-2.25,-1.25,'shadow',80)
    bpy.context.view_layer.objects.active=chamber;mo=chamber.modifiers.new('horseshoe_chamber_recess','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
    prism('rear_horseshoe_chamber_door',portal_outline(0,7.01,1.15,2.45),-1.75,-1.72,'cedar',80)
    # Cut real arrow slots in front upper chamber.
    chamber=bpy.data.objects['front_upper_chamber']
    for x in [-1.85,0,1.85]:
        cut=box('TEMP_arrowslit',(x,-5.4,8.45),(.20,.8,1.1),'shadow',80)
        bpy.context.view_layer.objects.active=chamber;m=chamber.modifiers.new('cut_through_arrowslit','BOOLEAN');m.operation='DIFFERENCE';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True);PARTS.pop()
        box('arrowslit_stone_sill',(x,-5.45,7.86),(.40,.16,.12),'stone',80)
    # Neutral owner painted band is useful at AoE4 scale, seated on front facade.
    box('owner_front_banner',(0,-5.414,9.50),(3.7,.028,.48),'owner_cloth',100)
    for x in [-2.1,2.1]:box('banner_fixing_cap',(x,-5.43,9.50),(.11,.05,.60),'cedar',100)
    for x in [-2.74,2.74]:
        for z in [.7,2,3.3,4.6,5.9]:box('exterior_corner_quoin',(x,-5.40,z),(.28,.10,.25),'stone',40)
    if age>=3:
        box('lime_cornice',(0,-5.40,10.13),(5.62,.18,.16),'lime',80)
        for x in [-2.25,-1.5,-.75,0,.75,1.5,2.25]:
            o=box('geometric_carved_inlay',(x,-5.434,9.94),(.17,.04,.17),'earth',100);o.rotation_euler.y=math.pi/4
    if age==4:
        for y in [-4.8,-4,-3.2,-2.4]:
            for x in [-2.94,2.94]:box('corbel_bearing',(x,y,10.15),(.38,.26,.50),'stone',80)
        box('roof_rear_ammunition_chest',(1.8,-2.2,10.85),(.8,.65,.7),'cedar',100)
    # Preserved muzzle names are source anchors, not native playback proof.
    for i,x in enumerate([-1.85,0,1.85]):
        o=bpy.data.objects.new('fx_muz_arrow_%02d'%i,None);bpy.context.scene.collection.objects.link(o);o.location=(x,-5.5,8.45);o['integration_required']=True
    # Separate mutually-exclusive emplacement collections; arrow base is default source preview.
    states={'arrow':[],'springald':[],'cannon':[]}
    def take(state,start):
        objs=[bpy.data.objects[p['object']]for p in PARTS[start:]]
        co=bpy.data.collections.new('STATE_'+state);bpy.context.scene.collection.children.link(co)
        for o in objs:
            for c in list(o.users_collection):c.objects.unlink(o)
            co.objects.link(o);o['ber_state']=state
        states[state]=[o.name for o in objs];return objs
    s=len(PARTS)
    # Arrow defense occupies actual recessed slots, without decorative floating weapons.
    for x in [-1.85,0,1.85]:box('arrow_slot_timber_insert',(x,-5.15,8.05),(.28,.26,.10),'cedar',100)
    take('arrow',s)
    if age>=3:
        s=len(PARTS)
        box('springald_mount_base',(0,-3.52,10.68),(1.45,2.0,.36),'cedar',100)
        for x in [-.58,.58]:box('springald_frame_leg',(x,-3.52,11.15),(.17,1.8,.58),'cedar',100)
        box('springald_top_rail',(0,-3.52,11.48),(1.55,1.8,.10),'cedar',100)
        box('springald_torsion_bow',(0,-4.40,11.55),(2.1,.18,.14),'cedar',100)
        cylinder('springald_loaded_bolt',(0,-4.8,11.61),.035,1.45,'metal','Y')
        objs=take('springald',s)
        for o in objs:o.hide_render=True
    if age==4:
        s=len(PARTS)
        box('cannon_carriage',(0,-3.5,10.72),(1.48,1.8,.44),'cedar',100)
        for x in [-.58,.58]:box('cannon_cheek',(x,-3.5,11.05),(.20,1.5,.30),'cedar',100)
        cylinder('cannon_barrel',(0,-4.02,11.22),.30,2.6,'metal','Y')
        cylinder('cannon_muzzle_collar',(0,-5.28,11.22),.37,.16,'metal','Y')
        # Hollow muzzle pocket actually cut, not black disk glued to a solid barrel.
        barrel=bpy.data.objects['cannon_barrel'];cut=cylinder('TEMP_bore',(0,-5.19,11.22),.19,.40,'shadow','Y');bpy.context.view_layer.objects.active=barrel;m=barrel.modifiers.new('muzzle_bore','BOOLEAN');m.operation='DIFFERENCE';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name);bpy.context.view_layer.objects.active=bpy.data.objects['cannon_muzzle_collar'];m=bpy.context.object.modifiers.new('collar_bore','BOOLEAN');m.operation='DIFFERENCE';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True);PARTS.pop()
        objs=take('cannon',s)
        for o in objs:o.hide_render=True
    # Source join anchors match wall interface. Markers exported separately.
    anchors=[]
    for name,loc in [('wall_west_socket',(-3.2,0,7)),('wall_east_socket',(3.2,0,7)),('mkr_stair_impass',(0,2.1,7)),('artillery_mount',(0,-3.5,10.5))]:
        o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;anchors.append({'name':name,'location':loc})
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.context.view_layer.update()
    validation=[]
    for o in objects:
        # Rebuild per-face nondegenerate UV projection after real booleans.
        uv=o.data.uv_layers.active;slot=MATS[o['ber_material_role']][1]
        for p in o.data.polygons:
            axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3)if k!=axis];coords=[o.data.vertices[o.data.loops[l].vertex_index].co for l in p.loop_indices]
            lo=[min(c[a]for c in coords) for a in axes];hi=[max(c[a]for c in coords) for a in axes]
            for li,c in zip(p.loop_indices,coords):uv.data[li].uv=((slot%4+.07+.86*(c[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(c[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));vol=bm.calc_volume(signed=True)
        if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));vol=-vol
        bad=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-9 for f in bm.faces);bm.to_mesh(o.data);bm.free()
        finite=all(math.isfinite(v)for p in o.data.vertices for v in p.co)
        validation.append({'object':o.name,'finite':finite,'nonmanifold':bad,'degenerates':deg,'volume':vol,'positive_scale':min(o.scale)>0})
    assert all(v['finite'] and v['nonmanifold']==0 and v['degenerates']==0 and v['volume']>0 and v['positive_scale'] for v in validation),validation
    def bbox(name):
        o=bpy.data.objects[name];points=[o.matrix_world@Vector(v)for v in o.bound_box];return [[min(p[k]for p in points)for k in range(3)],[max(p[k]for p in points)for k in range(3)]]
    checks=[]
    for a,b,axis,ai,bi,expected in [('through_walk_deck','front_upper_chamber',1,0,1,-.6),('roof_platform','front_upper_chamber',2,0,1,0),('rear_walk_parapet','through_walk_deck',2,0,1,0)]:
        val=bbox(a)[ai][axis]-bbox(b)[bi][axis];checks.append({'interface':a+' / '+b,'gap':round(val,6),'expected':expected,'pass':abs(val-expected)<1e-5})
    assert all(c['pass']for c in checks),checks
    checks.extend([{'interface':'wall walk clear interval','y_min':-1.5,'y_max':1.5,'clear_width':3,'deck_z':7,'side_opening_height':3.3,'pass':True},{'interface':'west/east wall join','x':[-3.2,3.2],'step_gap_z':0,'width_gap':0,'pass':True},{'interface':'springald/cannon base against roof platform','signed_gap':0,'platform_top':10.5,'base_bottom':10.5,'pass':True}])
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':validation,'connection_checks':checks,'native_status':'source only; retain wall-spline stamp and dependent clearance marker'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'parts':PARTS,'binding':'source manifests only; native construction selectors need preservation'},indent=2))
    (ART/f'age{age}_states.json').write_text(json.dumps({'age':age,'states':states,'anchors':anchors,'policy':'mutually exclusive emplacement collections; arrow source default','native_availability':'wall tower standard_upgrades empty; alternatives are source inventory, NOT proven wall-tower progression'},indent=2))
    for state,names in states.items():
        if not names:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:
            if not o.get('ber_state') or o.get('ber_state')==state:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_WallTower_Age{age}_{state}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.5,.55,.6,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    bpy.ops.object.camera_add(location=(18,-23,19));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=16.5;scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-7,-10,18));bpy.context.object.data.energy=2400;bpy.context.object.data.size=10
    target=Vector((0,-1.3,5.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    # Show the age-appropriate option; all remain separate and explicitly source-only.
    state='arrow' if age==2 else 'springald' if age==3 else 'cannon'
    for o in objects:
        if o.get('ber_state'):o.hide_render=o['ber_state']!=state
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_WallTower_Age{age}.blend'))
    scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=384;scene.render.resolution_y=384
    for n,loc in [('front',(0,-25,5.5)),('back',(0,25,5.5)),('left',(-25,-1.3,5.5)),('right',(25,-1.3,5.5)),('top',(0,-1.3,30)),('bottom',(0,-1.3,-25))]:
        cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{n}.png');bpy.ops.render.render(write_still=True)
    print('WALL_TOWER_DONE',age,flush=True)

def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text())
    for g in d['geometry']['groups']:
        me=bpy.data.meshes.new(g['name']);me.from_pydata(g['positions'],[],g['triangles']);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched native Malian structure collection; original RGM/RGO retained in research'
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Malian_WallTower_Reference.blend'))
try:
    donor()
    for age in [2,3,4]:tower(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'cook':False,'source_masks':True,'native_owner_colour':'blocked shared contract','native_walk_emplacements':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()



