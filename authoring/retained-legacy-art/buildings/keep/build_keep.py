"""Original Berber kasbah keep; task-owned reproducible source only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runner import *
import runner as R
def bounds(o):
    bpy.context.view_layer.update();p=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]
def cut(o,c):
    bpy.context.view_layer.objects.active=o;m=o.modifiers.new('true_void','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True);R.PARTS.pop()
def battered(name,x,y,h,mat):
    vs=[(x+sx*r,y+sy*r,z) for z,r in [(.18,1.05),(h,.86)] for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    fs=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,40)
def donor():
    reset_scene();d=json.loads(next((RESEARCH/'stock').rglob('decoded-static.json')).read_text());summary=[]
    for g in d['geometry']['groups']:
        f=g.get('triangles',g.get('indices',[]));f=[f[i:i+3] for i in range(0,len(f),3)] if f and isinstance(f[0],int) else f
        me=bpy.data.meshes.new(g['name']);me.from_pydata(g['positions'],[],f);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched Abbasid ageIII stock decode';summary.append({'name':o.name,'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTOUCHED_Abbasid_Keep_Age3_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps(summary,indent=2))
def build(age):
    reset_scene();R.PARTS.clear();R.CONTACTS.clear();MATS.clear();setup_maps();wall='earth' if age==3 else 'lime';H=4.35 if age==3 else 4.60;deck=H-.03
    foundation=box('foundation',(0,0,.09),(7.7,7.7,.18),'stone',0);box('courtyard_floor',(0,0,.20),(7.4,7.4,.04),'earth',0)
    towers=[]
    for x in [-2.65,2.65]:
      for y in [-2.65,2.65]:
        t=battered('battered_square_tower',x,y,H,wall);towers.append(t)
        # Narrow full-depth slits are real voids rather than painted marks.
        cut(t,box('TEMP_slit',(x,y,2.72),(.13,2.3,.75),'shadow',60))
        box('tower_roof',(x,y,H+.055),(1.72,1.72,.11),'stone',60)
        for a in [-.78,.78]:
          p=box('tower_parapet',(x+a,y,H+.30),(.16,1.72,.38),wall,80)
          if (x+a)*x<x*x:cut(p,box('TEMP_walk_access',(x+a,y,H+.30),(.30,.92,.6),'shadow',80))
          p=box('tower_parapet',(x,y+a,H+.30),(1.40,.16,.38),wall,80)
          if (y+a)*y<y*y:cut(p,box('TEMP_walk_access',(x,y+a,H+.30),(.92,.30,.6),'shadow',80))
        for a in [-.65,0,.65]:
          for b in [-.78,.78]:
            if not (a==0 and (y+b)*y<y*y):box('tower_merlon',(x+a,y+b,H+.60),(.28,.20,.26),wall,80)
    for x in [-3.0,3.0]:
        box('curtain_wall',(x,0,(.18+deck)/2),(.80,3.60,deck-.18),wall,40);box('rampart_walk',(x,0,deck+.07),(.90,3.60,.14),'stone',60)
        for yy in [-1.6+i*.4 for i in range(9)]:box('curtain_merlon',(x+(.35 if x>0 else -.35),yy,deck+.69),(.20,.22,.35),wall,80)
        box('curtain_parapet',(x+(.35 if x>0 else -.35),0,deck+.33),(.20,3.6,.52),wall,80)
    for y in [-3.0,3.0]:
        w=box('front_gate_wall' if y<0 else 'rear_wall',(0,y,(.18+deck)/2),(3.60,.80,deck-.18),wall,40)
        if y<0:
            cut(w,prism('TEMP_gate',portal_outline(0,.22,1.35,2.20),-3.6,-2.4,'shadow',40))
            for x in [-.46,.46]:
                door=box('gate_leaf_closed',(x,-3.02,1.17),(.88,.13,1.90),'cedar',60);door['state']='gate_closed';door['native_playback']='source Action only'
                hinge=-.90 if x<0 else .90
                for v in door.data.vertices:v.co.x+=x-hinge
                door.location.x=hinge
                door.keyframe_insert(data_path='rotation_euler',frame=1);door.rotation_euler.z=(-1 if x<0 else 1)*1.45;door.keyframe_insert(data_path='rotation_euler',frame=30);door.rotation_euler.z=0
        box('rampart_walk',(0,y,deck+.07),(3.60,.90,.14),'stone',60);box('curtain_parapet',(0,y+(.35 if y>0 else -.35),deck+.33),(3.60,.20,.52),wall,80)
        for xx in [-1.6+i*.4 for i in range(9)]:box('curtain_merlon',(xx,y+(.35 if y>0 else -.35),deck+.69),(.22,.20,.35),wall,80)
    # Barracks/store inside the court, open central manoeuvre zone and rear access stair.
    room=box('guard_store',(-1.38,.65,1.05),(.90,2.60,1.66),wall,40);cut(room,box('TEMP_store_entry',(-.90,.0,.94),(.3,.62,1.44),'shadow',40));box('guard_store_roof',(-1.38,.65,1.94),(1.04,2.72,.12),'cedar',60)
    for i in range(18):box('court_stair',(1.18,.35+i*.13,.22+(i+1)*(deck-.22)/36),(.70,.13,(i+1)*(deck-.22)/18),'stone',60)
    box('stair_landing',(1.18,2.60,deck+.07),(.70,.65,.14),'stone',60)
    for x in [-.8,.8]:box('supply_crate',(x,.80,.48),(.48,.48,.52),'cedar',80)
    # Neutral owner flags; poles seat on tower roof.
    for x,y in [(-2.65,-2.65),(2.65,2.65)]:
        box('flag_pole',(x,y,H+.90),(.055,.055,1.80),'cedar',80);box('neutral_owner_flag',(x+.32,y,H+1.47),(.64,.035,.45),'owner_cloth',100)
    # Explicit independent visual alternatives; defaults hidden so upgrades do not appear early.
    states=[]
    for key,agegate,gate in [('arrow',3,'default'),('springald',3,'upgrade_keep_springald'),('cannon',4,'upgrade_keep_cannon'),('oil',3,'upgrade_tech_university_murder_holes_4')]:
        names=[]
        for x in [-2.65,2.65]:
            p=box(key+'_mount',(x,-2.65,H+.19),(.7,.66,.16),'cedar',100);p['ber_state_gate']=gate;p.hide_render=key!='arrow';p.hide_viewport=key!='arrow';names.append(p.name)
            if key in ['springald','cannon']:
                b=box(key+'_source_barrel',(x,-2.85,H+.41),(.18,.84,.18),'stone' if key=='cannon' else 'cedar',100);b.hide_render=True;b.hide_viewport=True;b['ber_state_gate']=gate;names.append(b.name)
            if key=='oil':
                o=box('oil_drop_box',(x,-3.53,H-.04),(.55,.23,.25),'stone',100);o.hide_render=True;o.hide_viewport=True;o['ber_state_gate']=gate;names.append(o.name)
        states.append({'key':key,'minimum_age':agegate,'gate':gate,'objects':names,'binding':'source alternatives; native research/action apply/markers must be retained'})
    if age==4:
        for x in [-3.45,3.45]:box('lime_corner_course',(x,-3.47,1.70),(.16,.10,2.75),'stone',60)
        for x in [-.8,-.4,0,.4,.8]:
            o=box('gate_geometric_lintel',(x,-3.408,2.74),(.15,.035,.15),'stone',100);o.rotation_euler.y=math.pi/4
    bpy.context.scene.frame_set(1);objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));vol=bm.calc_volume(signed=True)
        if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));vol=-vol
        nm=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.to_mesh(o.data);bm.free()
        uv=o.data.uv_layers.active;ua=sum(abs((uv.data[p.loop_indices[1]].uv-uv.data[p.loop_indices[0]].uv).cross(uv.data[p.loop_indices[2]].uv-uv.data[p.loop_indices[0]].uv)) for p in o.data.polygons)
        checks.append({'object':o.name,'closed':nm==0,'degenerate_faces':deg,'volume':vol,'uv_area_sum':ua,'finite':all(math.isfinite(c) for v in o.data.vertices for c in v.co),'positive_scale':all(v>0 for v in o.scale)})
    assert all(c['closed'] and not c['degenerate_faces'] and c['volume']>0 and c['uv_area_sum']>0 and c['finite'] and c['positive_scale'] for c in checks)
    guards={'wall_walk_contact_gap':0.0,'tower_walk_plan_overlap_m':round(1.80-(2.65-(1.05-(1.05-.86)*(deck-.18)/(H-.18))),6),'tower_walk_top_gap_m':round((deck+.14)-(H+.11),6),'courtyard_clear_zone_m':[1.5,2.0],'wall_thickness_m':.80,'walk_width_m':.90,'gate_clear_width_m':1.16,'gate_top_m':2.42,'slit_width_m':.13,'tower_batter_top_halfwidth_m':.86,'ground_min_z':min(bounds(o)[0][2] for o in objects),'site_envelope_m':[8,8],'geometry_xy_max':max(max(abs(v) for v in bounds(o)[q][:2]) for o in objects for q in [0,1]),'gate_void_boolean':'applied','slit_void_boolean':'applied','native_walk_surface':'unqualified'}
    assert guards['ground_min_z']>=-1e-5 and guards['geometry_xy_max']<4
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'guards':guards},indent=2));(ART/f'age{age}_construction.json').write_text(json.dumps({'parts':R.PARTS,'stages':[0,20,40,60,80,100],'cumulative':True},indent=2));(ART/f'age{age}_states.json').write_text(json.dumps({'alternatives':states,'gate_actions':'closed frame1/open frame30; source only, not native gate playback'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.hide_viewport=False;o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Keep_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=True,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100;scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(12,-16,13));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=12;scene.camera=cam;cam.rotation_euler=(Vector((0,0,2.2))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.ops.object.light_add(type='AREA',location=(-5,-7,12));bpy.context.object.data.energy=1800;bpy.context.object.data.size=8
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Keep_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=400;scene.render.resolution_y=400
    for key,loc in [('front',(0,-15,2.3)),('back',(0,15,2.3)),('left',(-15,0,2.3)),('right',(15,0,2.3)),('top',(0,0,16)),('bottom',(0,0,-15))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,2.3))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{key}.png');bpy.ops.render.render(write_still=True)
try:
    if not (ART/'UNTOUCHED_Abbasid_Keep_Age3_Reference.blend').exists():donor()
    for a in [3,4]:build(a)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[3,4],'cook':False}))
except Exception:(OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
