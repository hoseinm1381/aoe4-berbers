"""Task-owned, reproducible Moroccan courtyard palisade_gate source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/palisade_gate'; OUT=ROOT/'output/buildings_batch/palisade_gate'; RESEARCH=ROOT/'research/buildings_batch/palisade_gate'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('PalisadeGate_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberPalisadeGate_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='PalisadeGateAtlasUV')
    for p in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis]
        coords=[o.data.vertices[o.data.loops[li].vertex_index].co for li in p.loop_indices]
        mn=[min(co[k] for co in coords) for k in axes];mx=[max(co[k] for co in coords) for k in axes]
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=((slot%4+.08+.84*(co[axes[0]]-mn[0])/max(mx[0]-mn[0],1e-8))/4,(slot//4+.08+.84*(co[axes[1]]-mn[1])/max(mx[1]-mn[1],1e-8))/2)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    PARTS.append({'object':o.name,'first_stage':stage,'material':mat,'owner_mask':MATS[mat][0]['ber_owner_mask']});return o
def box(name,center,size,mat='earth',stage=40):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,stage)
# Interface contract: exact donor hinges, provisional source connectors; rig contract remains pending.
HINGES=[(-2.05658977144858,-.15005000912143784,0),(2.0571998845716175,-.15005000912143784,0)]
def parent_keep(o,p):
    m=o.matrix_world.copy();o.parent=p;o.matrix_world=m;return o

def stake(name,x,zheight=4.578125,depth=.682861328125):
    o=box(name,(x,0,(zheight-.3)/2),(.38,depth,zheight-.3),'cedar',40)
    # Continuous shaft-to-point mesh, no disconnected spike.
    vs=[(-.19,-depth/2,-.3),(.19,-depth/2,-.3),(.19,depth/2,-.3),(-.19,depth/2,-.3),(-.19,-depth/2,zheight-.3),(.19,-depth/2,zheight-.3),(.19,depth/2,zheight-.3),(-.19,depth/2,zheight-.3),(0,0,zheight)]
    me=o.data;me.clear_geometry();me.from_pydata([(vx+x,vy,vz) for vx,vy,vz in vs],[],[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,8),(5,6,8),(6,7,8),(7,4,8)]);me.update();o.location=(0,0,0);o.data.materials.clear();PARTS.pop();finish(o,name,'cedar',40);return o

def build(age):
    global PARTS
    ctx=reset_scene();PARTS=[];MATS.clear();setup_maps()
    for name,color in [('roughness',(.84,.84,.84)),('normal',(.5,.5,1)),('metal',(0,0,0))]:
        im=bpy.data.images.new(name,width=64,height=64);im.use_fake_user=True;im.pixels.foreach_set(list((*color,1))*4096);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack()
    # Tall fitted portal preserves visual role while connecting to low defensive stakes.
    posttop=6.1+.18*(age-1); top=posttop+.5
    for side,x in [('left',-2.46),('right',2.46)]:
        box(side+'_stone_footing',(x,0,.10),(.85,1.05,.2),'stone',0)
        box(side+'_palm_gatepost',(x,0,posttop/2),(.65,.78,posttop),'cedar',20)
        for z in [.5,4.1,posttop-.3]:box(side+'_lashed_collar',(x,0,z),(.69,.83,.12),'straw' if age<3 else 'stone',60)
        for j in range(6):stake(side+'_palisade_stake_'+str(j),(-1 if x<0 else 1)*(2.94+j*.392))
        for z in [1.25,3.15]:box(side+'_flank_crossrail',((-1 if x<0 else 1)*3.96,.32,z),(2.2,.16,.2),'cedar',60)
        # owner stripe applied to substantial outer-facing timber, not hardware.
        box(side+'_owner_post_band',(x,-.408,4.85),(.52,.038,.45),'owner_cloth',100)
        if age>=2:
            box(side+'_earth_pier_base',(x,0,.58),(.79,.95,.95),'earth' if age==2 else 'lime',20)
    box('mortised_palm_lintel',(0,0,posttop-.12),(5.75,.95,.48),'cedar',60)
    box('lintel_earth_weather_cap',(0,0,posttop+.18),(5.88,1.08,.18),'earth' if age<3 else 'lime',80)
    for x in [-2.46,2.46]:
        box('lintel_tenon_peg',(x,-.5,posttop-.12),(.16,.12,.22),'straw',80)
    if age>=3:
        for x in [-1.65,-.82,0,.82,1.65]:
            o=box('carved_lintel_diamond',(x,-.498,posttop-.12),(.19,.04,.19),'lime',100);o.rotation_euler.y=math.pi/4
    if age==4:
        box('lintel_owner_woven_band',(0,-.558,posttop+.18),(2.6,.04,.12),'owner_cloth',100)
        for x in [-2.46,2.46]:box('pier_cap',(x,0,1.115),(.86,1.02,.12),'lime',60)
    pivots=[];leafparts=[]
    for i,(side,pivot) in enumerate(zip(['left','right'],HINGES)):
        p=bpy.data.objects.new('door_'+side+'_HINGE',None);bpy.context.scene.collection.objects.link(p);p.location=pivot;p.empty_display_type='ARROWS';p['source_only']='hinge transform preserved from decoded donor; native graph unqualified';pivots.append(p)
        sign=1 if i==0 else -1;length=abs(pivot[0])-.015;cx=pivot[0]+sign*length/2
        owned=[]
        for j in range(7):
            x=pivot[0]+sign*(j+.5)*length/7
            owned.append(box(side+'_door_plank_'+str(j),(x,pivot[1],2.65),(length/7-.002,.20,5.05),'cedar',40))
        for z in [.48,2.75,4.84]:
            owned.append(box(side+'_door_crossbeam',(cx,pivot[1]+.14,z),(length,.15,.18),'cedar',60))
            owned.append(box(side+'_forged_strap',(cx,pivot[1]-.115,z),(length-.10,.065,.105),'shadow',80))
            for k in range(4):owned.append(box(side+'_strap_rivet',(pivot[0]+sign*(.15+k*(length-.3)/3),pivot[1]-.15,z),(.055,.02,.06),'stone',80))
        # Diagonal brace seated on rear crossbeams.
        o=box(side+'_diagonal_brace',(cx,pivot[1]+.155,2.66),(.18,.13,math.sqrt(4.36**2+(length-.12)**2)),'straw',60);o.rotation_euler.y=sign*math.atan((length-.12)/4.36);owned.append(o)
        for z in [.48,4.84]:
            owned.append(box(side+'_hinge_knuckle',(pivot[0],pivot[1],z),(.22,.30,.20),'shadow',80))
        owned.append(box(side+'_owner_leaf_stripe',(cx,pivot[1]-.12,3.85),(length-.15,.05,.34),'owner_cloth',100))
        owned.append(box(side+'_lifting_handle',(pivot[0]+sign*(length-.24),pivot[1]-.21,2.4),(.10,.12,.28),'shadow',100))
        for o in owned:parent_keep(o,p)
        for frame,angle in [(1,0),(40,(-1 if i==0 else 1)*math.pi/2),(70,(-1 if i==0 else 1)*math.pi/2),(110,0)]:p.rotation_euler.z=angle;p.keyframe_insert(data_path='rotation_euler',frame=frame)
        p.animation_data.action.name=side+'_GateOpenClose_SOURCE';p.animation_data.action.use_fake_user=True
        leafparts.append(owned)
    for side,x in [('left',-5),('right',5)]:
        p=bpy.data.objects.new('SOURCE_socket_'+side,None);bpy.context.scene.collection.objects.link(p);p.location=(x,0,0);p['binding_status']='source join plane inferred from official gap_filler_length=5; native marker verification pending'
    scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=110;scene.frame_set(1);bpy.context.view_layer.update()
    validation=[]
    for o in [o for o in scene.objects if o.type=='MESH']:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data)
        volume=bm.calc_volume(signed=True);non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-9 for f in bm.faces);bm.free()
        uv=o.data.uv_layers.active;uvareas=[]
        for poly in o.data.polygons:
            pts=[uv.data[li].uv for li in poly.loop_indices];uvareas.append(abs(sum(pts[k].x*pts[(k+1)%len(pts)].y-pts[(k+1)%len(pts)].x*pts[k].y for k in range(len(pts)))/2))
        validation.append({'object':o.name,'closed_positive_volume':volume,'nonmanifold':non,'degenerate':deg,'min_uv_area':min(uvareas),'finite':all(math.isfinite(c) for v in o.data.vertices for c in v.co),'positive_scale':min(o.scale)>0})
    assert all(v['closed_positive_volume']>0 and v['nonmanifold']==0 and v['degenerate']==0 and v['min_uv_area']>0 and v['finite'] and v['positive_scale'] for v in validation),validation
    def bounds(objs):
        pts=[o.matrix_world@Vector(v) for o in objs for v in o.bound_box];return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
    closed=[bounds(a) for a in leafparts];closed_planks=[bounds([o for o in a if '_door_plank_' in o.name]) for a in leafparts];closed_gap=closed_planks[1][0][0]-closed_planks[0][1][0];assert abs(closed_gap-.032)<1e-5,closed_gap;scene.frame_set(40);bpy.context.view_layer.update();opened=[bounds(a) for a in leafparts]
    open_clear=opened[1][0][0]-opened[0][1][0];assert open_clear>3.4,open_clear
    audit={'age':age,'objects':validation,'hinges':HINGES,'closed_leaf_bounds':closed,'open_leaf_bounds':opened,'open_clear_width':open_clear,'source_closed_centre_gap':closed_gap,'passage_headroom':posttop-.36,'wall_socket_height':4.578125,'wall_socket_depth':.682861328125,'source_connector_span':10,'native_socket_status':'inferred source planes only; native stamp/markers pending','contacts':{'post_to_footing_overlap':.2,'tenon_lintel_overlap':.36,'flank_rail_to_stake_overlap':.1,'owner_bands_to_leaves_overlap':.005},'native_animation':'not qualified','native_player_colour':'source red mask only; integration blocked'}
    (OUT/f'age{age}_validation.json').write_text(json.dumps(audit,indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'parts':PARTS,'assignment':'cumulative source first-visible percentage','native_binding':'pending'},indent=2))
    (ART/f'age{age}_states.json').write_text(json.dumps({'closed_frame':1,'open_frame':40,'hold_open_frame':70,'closed_again_frame':110,'hinges':HINGES,'rotation_axis':'Blender Z','open_angles_degrees':[-90,90],'state_actions':[p.animation_data.action.name for p in pivots],'native_playback':'pending'},indent=2))
    scene.frame_set(1);bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_PalisadeGate_Age{age}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=True,bake_anim_use_all_actions=False,path_mode='COPY',embed_textures=True)
    scene.frame_set(40);bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_PalisadeGate_Age{age}_Open.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene.frame_set(1)
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.62,.69,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
    bpy.ops.object.camera_add(location=(11,-15,10));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=13;scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-7,12));bpy.context.object.data.energy=1800;bpy.context.object.data.size=8
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_PalisadeGate_Age{age}.blend'))
    for state,frame in [('closed',1),('open',40)]:
        scene.frame_set(frame);cam.location=(11,-15,10);cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{state}.png');bpy.ops.render.render(write_still=True)
    scene.frame_set(1);scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-15,3)),('back',(0,15,3)),('left',(-15,0,3)),('right',(15,0,3)),('top',(0,0,18)),('bottom',(0,0,-18))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('GATE_AGE_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text())
    for g in d['geometry']['groups']:
        me=bpy.data.meshes.new(g['name']);fs=g.get('triangles',g.get('indices',[]));fs=[fs[k:k+3] for k in range(0,len(fs),3)] if fs and isinstance(fs[0],int) else fs;me.from_pydata(g['positions'],[],fs);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched decoded installed stock donor, no materials reconstructed'
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTOUCHED_English_PalisadeGate_Reference.blend'))
try:
    donor()
    for age in range(1,5):build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'native_status':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
