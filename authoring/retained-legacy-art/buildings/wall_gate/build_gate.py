"""Task-owned, reproducible Moroccan courtyard wall_gate source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/wall_gate'; OUT=ROOT/'output/buildings_batch/wall_gate'; RESEARCH=ROOT/'research/buildings_batch/wall_gate'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.50,.42,.31),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern'):
        im=bpy.data.images.new('StoneGate_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberStoneGate_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='StoneGateAtlasUV')
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
HINGES=[(-2.06,-.60,0),(2.06,-.60,0)]
def parent_keep(o,p):
    m=o.matrix_world.copy();o.parent=p;o.matrix_world=m;return o

def stake(name,x,zheight=4.578125,depth=.682861328125):
    o=box(name,(x,0,(zheight-.3)/2),(.38,depth,zheight-.3),'cedar',40)
    # Continuous shaft-to-point mesh, no disconnected spike.
    vs=[(-.19,-depth/2,-.3),(.19,-depth/2,-.3),(.19,depth/2,-.3),(-.19,depth/2,-.3),(-.19,-depth/2,zheight-.3),(.19,-depth/2,zheight-.3),(.19,depth/2,zheight-.3),(-.19,depth/2,zheight-.3),(0,0,zheight)]
    me=o.data;me.clear_geometry();me.from_pydata([(vx+x,vy,vz) for vx,vy,vz in vs],[],[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,8),(5,6,8),(6,7,8),(7,4,8)]);me.update();o.location=(0,0,0);o.data.materials.clear();PARTS.pop();finish(o,name,'cedar',40);return o


def prism(name,poly,y0,y1,mat,stage):
    vs=[(x,y,z) for y in [y0,y1] for x,z in poly];n=len(poly)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,stage)

def build(age):
    global PARTS
    ctx=reset_scene();PARTS=[];MATS.clear();setup_maps()
    for name,color in [('roughness',(.84,.84,.84)),('normal',(.5,.5,1)),('metal',(0,0,0))]:
        im=bpy.data.images.new(name,width=64,height=64);im.use_fake_user=True;im.pixels.foreach_set(list((*color,1))*4096);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack()
    # Architecture: full-through horseshoe opening, seated twin rampart towers.
    masonry='earth' if age==2 else 'lime'
    for side,sign in [('left',-1),('right',1)]:
        x=sign*3.65
        box(side+'_rubble_plinth',(x,0,.2),(2.7,4.2,.4),'stone',0)
        box(side+'_tower_pier',(x,0,3.45),(2.7,4.2,6.9),masonry,20)
        for y in [-2.1,2.1]:
            box(side+'_projecting_tower_face',(x,y+(.20 if y>0 else -.20),3.1),(2.7,.40,6.2),masonry,20)
            box(side+'_tower_ledge',(x,y+(.18 if y>0 else -.18),6.35),(2.7,.44,.3),'stone',60)
            box(side+'_battered_toe',(x,y,.5),(2.7,.35,1),masonry,20)
            box(side+'_owner_facade_band',(x,y+(.412 if y>0 else -.412),5.8),(2.05,.045,.34),'owner_cloth',100)
            if age>=3:
                for z in [1.1,4.3,6.1]:box(side+'_lime_belt',(x,y+(.412 if y>0 else -.412),z),(2.7,.04,.13),'lime',80)
            for z in [2.8,4.8]:
                box(side+'_arrow_slit',(x,y+(.412 if y>0 else -.412),z),(.10,.03,.65),'shadow',80)
                box(side+'_slit_sill',(x,y+(.445 if y>0 else -.445),z-.35),(.28,.1,.08),'stone',80)
        # side-to-wall end plane x=+/-5, full level deck.
    # Extruded spandrel strips follow real opening; no shadow-filled fake doorway.
    r=2.30;cz=3.60;angles=[math.radians(-25+230*i/28) for i in range(29)]
    arc=[(r*math.cos(t),cz+r*math.sin(t)) for t in angles]
    inner=arc[0][0]
    for side,sign in [('left',-1),('right',1)]:
        box(side+'_gateway_jamb',(sign*(inner+2.30)/2,0,arc[0][1]/2),(2.30-inner,4.2,arc[0][1]),masonry,40)
    # One continuous nonconvex U-section preserves the horseshoe undercut.
    outline=[(inner,0),(2.30,0),(2.30,6.5),(-2.30,6.5),(-2.30,0),(-inner,0)]+list(reversed(arc))
    prism('continuous_horseshoe_gateway',outline,-2.1,2.1,masonry,40)
    for i in range(28):
        x1,z1=arc[i];x2,z2=arc[i+1]
        if age>=3:
            t1=angles[i];t2=angles[i+1]
            prism('front_voussoir_'+str(i),[(x1,z1),(x2,z2),(2.52*math.cos(t2),cz+2.52*math.sin(t2)),(2.52*math.cos(t1),cz+2.52*math.sin(t1))],-2.17,-2.10,'stone' if age==3 else 'lime',80)
    box('continuous_rampart_deck',(0,0,6.75),(10,4.2,.5),'stone',60)
    for y in [-1.85,1.85]:
        box('walkway_parapet',(0,y,7.38),(10,.70,.76),masonry,60)
        for i in range(16):box('crenellation',( -4.68+i*.624,y,7.97),(.38,.7,.46),masonry,80)
        box('parapet_owner_band',(0, y+(.36 if y>0 else -.36),7.38),(8.6,.026,.15),'owner_cloth',100)
    if age==4:
        for y in [-2.18,2.18]:
            for x in [-1.5,-.75,0,.75,1.5]:
                o=box('geometric_portal_panel',(x,y,6.35),(.20,.04,.20),'stone',100);o.rotation_euler.y=math.pi/4
    root=bpy.data.objects.new('bone_root',None);bpy.context.scene.collection.objects.link(root)
    gate=bpy.data.objects.new('bone_gate',None);bpy.context.scene.collection.objects.link(gate);gate.parent=root;gate.location=(0,0,0)
    gate['source_reference']='decoded native bone_gate origin; original rigid lifting blade. Source +Z travel not decoded native clip'
    for x in [-2.22,2.22]:
        box('portcullis_guide_track',(x,-2.34,5.95),(.18,.20,11.9),'shadow',80)
        for z in [.8,3.0,5.7]:box('guide_anchor',(x,-2.28,z),(.32,.28,.14),'stone',80)
    pivots=[gate];leafparts=[]
    for i,(side,pivot) in enumerate(zip(['left','right'],HINGES)):
        p=gate; pivot=(pivot[0],-2.35,0)
        sign=1 if i==0 else -1;length=abs(pivot[0])-.015;cx=pivot[0]+sign*length/2;owned=[]
        for j in range(9):
            xa=pivot[0]+sign*(j*length/9+.003);xb=pivot[0]+sign*((j+1)*length/9-.003)
            za=cz+math.sqrt(r*r-xa*xa)-.025;zb=cz+math.sqrt(r*r-xb*xb)-.025
            owned.append(prism(side+'_door_plank_'+str(j),[(xa,.08),(xb,.08),(xb,zb),(xa,za)],pivot[1]-.10,pivot[1]+.10,'cedar',40))
        for z in [.48,2.75,4.25]:
            owned.append(box(side+'_door_crossbeam',(cx,pivot[1]+.14,z),(length,.15,.18),'cedar',60))
            owned.append(box(side+'_forged_strap',(cx,pivot[1]-.12,z),(length-.1,.06,.12),'shadow',80))
            for k in range(5):owned.append(box(side+'_strap_rivet',(pivot[0]+sign*(.12+k*(length-.24)/4),pivot[1]-.16,z),(.055,.035,.055),'stone',80))
        for z in [.48,4.25]:owned.append(box(side+'_hinge_knuckle',(pivot[0],pivot[1],z),(.14,.28,.22),'shadow',80))
        owned.append(box(side+'_owner_leaf_stripe',(cx,pivot[1]-.125,3.6),(length-.15,.05,.30),'owner_cloth',100))
        owned.append(box(side+'_lifting_handle',(pivot[0]+sign*(length-.24),pivot[1]-.20,2.3),(.10,.12,.28),'shadow',100))
        for o in owned:parent_keep(o,p)
        leafparts.append(owned)
    for frame,lift in [(1,0),(40,6.0),(70,6.0),(110,0)]:gate.location.z=lift;gate.keyframe_insert(data_path='location',frame=frame)
    gate.animation_data.action.name='Portcullis_LiftClose_SOURCE';gate.animation_data.action.use_fake_user=True
    for side,x in [('left',-5),('right',5)]:
        p=bpy.data.objects.new('SOURCE_socket_'+side,None);bpy.context.scene.collection.objects.link(p);p.location=(x,0,7);p['binding_status']='authored plane matching wall; native marker/stamp remains separate'
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
    closed=[bounds(a) for a in leafparts];closed_planks=[bounds([o for o in a if '_door_plank_' in o.name]) for a in leafparts];closed_gap=closed_planks[1][0][0]-closed_planks[0][1][0];assert abs(closed_gap-.036)<1e-5,closed_gap;scene.frame_set(40);bpy.context.view_layer.update();opened=[bounds(a) for a in leafparts]
    open_clear=2*inner;assert min(b[0][2] for b in opened)>5.9
    audit={'age':age,'objects':validation,'native_pivot':[0,0,0],'lift_travel_source':6.0,'closed_leaf_bounds':closed,'open_leaf_bounds':opened,'open_clear_width':open_clear,'source_closed_centre_gap':closed_gap,'passage_headroom':5.9,'wall_socket_height':7,'wall_socket_depth':4.2,'source_connector_span':10,'native_socket_status':'source planes x+/-5 deck z7 width4.2; native stamp/markers pending','contacts':{'tower_to_deck_overlap':.4,'arch_top_deck_overlap':.0,'walk_y_interval':[-1.5,1.5],'crest_z':8.2,'deck_y_interval':[-2.1,2.1],'owner_bands_to_leaves_overlap':.0},'native_animation':'not qualified','native_player_colour':'source red mask only; integration blocked'}
    (OUT/f'age{age}_validation.json').write_text(json.dumps(audit,indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'parts':PARTS,'assignment':'cumulative source first-visible percentage','native_binding':'pending'},indent=2))
    (ART/f'age{age}_states.json').write_text(json.dumps({'closed_frame':1,'open_frame':40,'hold_open_frame':70,'closed_again_frame':110,'native_pivot':[0,0,0],'lift_travel_source':6.0,'translation_axis':'Blender Z','lift_source_m':6.0,'mechanism':'rigid portcullis lift','native_motion_amplitude':'not decoded or qualified','state_actions':[p.animation_data.action.name for p in pivots],'native_playback':'pending'},indent=2))
    scene.frame_set(1);bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_StoneGate_Age{age}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=True,bake_anim_use_all_actions=False,path_mode='COPY',embed_textures=True)
    scene.frame_set(40);bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_StoneGate_Age{age}_Open.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene.frame_set(1)
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.62,.69,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
    bpy.ops.object.camera_add(location=(13,-18,12));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=17;scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-7,12));bpy.context.object.data.energy=1800;bpy.context.object.data.size=8
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_StoneGate_Age{age}.blend'))
    for state,frame in [('closed',1),('open',40)]:
        scene.frame_set(frame);cam.location=(13,-18,12);cam.rotation_euler=(Vector((0,0,5.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{state}.png');bpy.ops.render.render(write_still=True)
    scene.frame_set(1);scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-15,3)),('back',(0,15,3)),('left',(-15,0,3)),('right',(15,0,3)),('top',(0,0,18)),('bottom',(0,0,-18))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,5.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('GATE_AGE_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads((RESEARCH/'stock/eec27ceeab31b6f50309/decoded-static.json').read_text())
    for g in d['geometry']['groups']:
        me=bpy.data.meshes.new(g['name']);fs=g.get('triangles',g.get('indices',[]));fs=[fs[k:k+3] for k in range(0,len(fs),3)] if fs and isinstance(fs[0],int) else fs;me.from_pydata(g['positions'],[],fs);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched decoded installed stock donor, no materials reconstructed'
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTOUCHED_Malian_StoneGate_Reference.blend'))
try:
    donor()
    for age in range(2,5):build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'native_status':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

