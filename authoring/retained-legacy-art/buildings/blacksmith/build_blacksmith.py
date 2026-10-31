"""Task-owned, reproducible Moroccan courtyard blacksmith source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/blacksmith'; OUT=ROOT/'output/buildings_batch/blacksmith'; RESEARCH=ROOT/'research/buildings_batch/blacksmith'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.10,.115,.125),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern','roughness','metal','normal'):
        im=bpy.data.images.new('Blacksmith_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
        pixels=[]
        for y in range(256):
            for x in range(256):
                slot=(x//64)+4*(y//128); role,c,owner=COLORS[slot]
                variation=.96+.04*math.sin(x*.91)*math.sin(y*.81)
                rgb={'pattern':(owner,0,0),'normal':(.5,.5,1),'metal':((.85,.85,.85) if slot==5 else (0,0,0)),'roughness':((.4,.4,.4) if slot==5 else (.85,.85,.85))}.get(mapname,tuple(v*variation for v in c))
                pixels.extend((*rgb,1))
        im.pixels.foreach_set(pixels);im.filepath_raw=str(ART/(mapname+'.png'));im.file_format='PNG';im.save();im.pack()
        if mapname=='albedo': albedo=im
    for i,(name,c,owner) in enumerate(COLORS):
        m=bpy.data.materials.new('BerberBlacksmith_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='BlacksmithAtlasUV')
    for face in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis]
        co=[o.data.vertices[o.data.loops[li].vertex_index].co for li in face.loop_indices]
        lo=[min(v[k] for v in co) for k in axes];hi=[max(v[k] for v in co) for k in axes]
        for li,v in zip(face.loop_indices,co):
            uv.data[li].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)
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

def beam(name,a,b,w,mat='cedar',stage=60):
    v=Vector(b)-Vector(a);o=box(name,(Vector(a)+Vector(b))/2,(w,w,v.length),mat,stage);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o

def reuv(o):
    uv=o.data.uv_layers.active;slot=MATS[o['ber_material_role']][1]
    for p in o.data.polygons:
        ax=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=ax];vs=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];lo=[min(v[k] for v in vs) for k in axes];hi=[max(v[k] for v in vs) for k in axes]
        for i,v in zip(p.loop_indices,vs):uv.data[i].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)

def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();wall='earth' if age==2 else 'lime';h=2.1+.25*(age-2)
    box('foundation',(0,0,.08),(8,8,.16),'stone',0);box('court_floor',(0,0,.175),(7.8,7.8,.03),'earth',0)
    # Hollow east workshop with a physically open doorway, separate store walls and roof.
    box('store_back',(1.95,3.18,.19+h/2),(3.5,.24,h),wall,40)
    for x in [.32,3.58]:box('store_side',(x,2.10,.19+h/2),(.24,1.92,h),wall,40)
    for x,w in [(.775,1.15),(3.00,1.40)]:box('store_front_jamb',(x,1.02,.19+.8),(w,.24,1.6),wall,40)
    box('store_open_lintel',(1.95,1.02,.19+1.6+(h-1.6)/2),(3.5,.24,h-1.6),wall,40)
    box('store_roof',(1.95,2.10,.19+h+.06),(3.74,2.40,.12),'earth',60);contact('store_roof','store_back')
    for yy in [.96,3.24]:box('store_parapet',(1.95,yy,.19+h+.30),(3.74,.12,.36),wall,80)
    for xx in [.14,3.76]:box('store_end_parapet',(xx,2.10,.19+h+.30),(.12,2.16,.36),wall,80)
    # Open forge mouth, hearth sides and back, hood with shaft void, chimney four shell walls.
    fx=-2.3;fy=1.35
    box('hearth_base',(fx,fy,.19+.27),(1.8,1.5,.54),'stone',40);contact('hearth_base','court_floor')
    for xx in [fx-.78,fx+.78]:box('forge_side',(xx,fy,1.26),(.24,1.5,1.06),wall,40)
    box('forge_back',(fx,fy+.63,1.26),(1.32,.24,1.06),wall,40)
    # hollow hood: four perimeter beams form real opening into square flue
    for xx in [fx-.68,fx+.68]:box('hood_side',(xx,fy,1.88),(.44,1.5,.18),'stone',60)
    for yy in [fy-.59,fy+.59]:box('hood_front_back',(fx,yy,1.88),(.92,.32,.18),'stone',60)
    ch=1.30+.35*(age-2);base=1.97
    for xx in [fx-.38,fx+.38]:box('chimney_side',(xx,fy,base+ch/2),(.16,.86,ch),wall,60)
    for yy in [fy-.35,fy+.35]:box('chimney_front_back',(fx,yy,base+ch/2),(.60,.16,ch),wall,60)
    # ring coping remains genuinely open; six side inspection exposes the flue
    for xx in [fx-.41,fx+.41]:box('chimney_coping',(xx,fy,base+ch+.05),(.20,1.00,.10),'stone',80)
    for yy in [fy-.40,fy+.40]:box('chimney_coping_cross',(fx,yy,base+ch+.05),(.62,.20,.10),'stone',80)
    for j in range(7):tube('cold_charcoal',(fx-.5+j*.15,fy-.15,.77),.075,.08,'shadow')
    # Bellows support stand and leather wedge; nozzle physically seats against forge side.
    box('bellows_stand',(-.92,fy,.64),(.70,.65,.90),'cedar',40);contact('bellows_stand','court_floor')
    prism('bellows_leather',[(-1.53,1.02),(-.38,.98),(-.38,1.36),(-1.53,1.16)],fy-.29,fy+.29,'clay',80)
    beam('bellows_handle',(-.38,fy,1.33),(-.12,fy,1.50),.06)
    box('bellows_nozzle',(-1.62,fy,1.08),(.20,.14,.14),'shadow',80)
    # Timber forge shelter with slopes seated on actual eaves; chimney outside rear roof edge.
    eave=2.15+.15*(age-2);ridge=eave+.42
    for xx in [-3.53,-.72]:
        for yy in [-2.9,.35]:box('shelter_post',(xx,yy,.19+(eave-.19)/2),(.14,.14,eave-.19),'cedar',20)
    for yy in [-2.9,.35]:box('shelter_crossbeam',(-2.125,yy,eave),(3.09,.16,.16),'cedar',60)
    for yy in [-2.9,.35]:
        for xx in [-3.53,-.72]:beam('roof_rafter',(xx,yy,eave+.08),(-2.125,yy,ridge),.11)
    for side in [-1,1]:prism('pitched_roof',[(-2.125,ridge+.10),(-2.125+side*1.65,eave+.02),(-2.125+side*1.65,eave-.05),(-2.125,ridge+.03)],-3.07,.47,'cedar',80)
    for xx in [-3.0,-2.12,-1.24]:box('owner_roof_stripe',(xx,-3.082,eave-.05),(.38,.026,.25),'owner_cloth',100)
    # Anvil integral silhouette with horn on a seated stump.
    tube('anvil_stump',(-2.1,-3.42,.54),.32,.70,'cedar',60);contact('anvil_stump','court_floor')
    prism('anvil',[(-2.65,.89),(-1.60,.89),(-1.82,1.01),(-1.78,1.12),(-1.45,1.14),(-1.26,1.25),(-2.62,1.25),(-2.52,1.05)],-3.60,-3.24,'shadow',80);contact('anvil','anvil_stump')
    # Actual open quenching trough assembled as floor plus four rim walls.
    tx=1.7;ty=-1.55
    box('trough_bottom',(tx,ty,.245),(1.35,1.9,.11),'stone',40);contact('trough_bottom','court_floor')
    for xx in [tx-.60,tx+.60]:box('trough_side',(xx,ty,.52),(.15,1.9,.44),'stone',80)
    for yy in [ty-.875,ty+.875]:box('trough_end',(tx,yy,.52),(1.05,.15,.44),'stone',80)
    box('quench_water',(tx,ty,.40),(1.05,1.60,.04),'shadow',100)
    # Tool bench/rack and stocked workshop; every bench foot grounded.
    for xx in [.58,3.12]:box('bench_leg',(xx,2.6,.595),(.12,.62,.81),'cedar',60)
    box('bench_top',(1.85,2.6,1.04),(2.84,.76,.08),'cedar',80);contact('bench_top','bench_leg')
    box('tool_rack',(1.85,3.04,1.58),(2.80,.10,.12),'cedar',80)
    for xx in [.65,1.2,1.75,2.3,2.85]:
        box('hammer_handle',(xx,2.96,1.36),(.045,.045,.47),'cedar',100);box('hammer_head',(xx,2.96,1.59),(.24,.10,.10),'shadow',100)
    for xx in [.8,1.3,1.8,2.3,2.8]:box('steel_billet',(xx,2.6,1.125),(.32,.12,.09),'shadow',100)
    box('owner_workshop_band',(1.95,.882,1.98),(2.9,.026,.18),'owner_cloth',100)
    if age>=3:
        for xx in [.38,3.52]:
            for zz in [.36,.70,1.04,1.38,1.72]:box('workshop_quoin',(xx,.882,zz),(.22,.035,.17),'stone',80)
        for xx in [.63,3.28]:box('roof_drain',(xx,3.44,.19+h+.1),(.13,.45,.09),'cedar',80)
        for i in range(4):box('charcoal_sack',(3.3,.1+i*.32,.40),(.46,.26,.42),'straw',100)
    if age==4:
        for xx in [.70,1.15,2.70,3.15]:
            o=box('geometric_inlay',(xx,.858,2.24),(.12,.025,.12),'earth',100);o.rotation_euler.y=math.pi/4
        for xx in [-3.55,-.75]:box('forge_masonry_post_base',(xx,-2.9,.36),(.30,.30,.34),'stone',40)
        box('workshop_roof_monitor',(2.75,2.30,.19+h+.39),(1.15,.94,.66),wall,80)
        box('monitor_cap',(2.75,2.30,.19+h+.77),(1.27,1.06,.10),'lime',80);contact('monitor_cap','workshop_roof_monitor')
        for xx in [2.4,2.75,3.1]:box('monitor_vent',(xx,1.819,.19+h+.40),(.15,.024,.26),'cedar',100)
    # Source markers only. Preserve inherited native placements during later integration.
    for name,loc in [('entry',(0,-4,0)),('forge_work',(-2.1,-1.8,.19)),('workshop_entry',(1.95,.88,.19))]:
        o=bpy.data.objects.new('AUTHOR_'+name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;o['native_binding']='pending'
    # Extra grounded tools sit on the exposed anvil so the role reads at game camera scale.
    box('anvil_hammer_handle',(-2.20,-3.42,1.275),(.44,.045,.05),'cedar',100)
    box('anvil_hammer_head',(-2.4,-3.42,1.325),(.12,.13,.10),'shadow',100)
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:reuv(o)
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
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[8,8],'store_clear_door_width_m':.95,'front_access_corridor_m':1.3,'flue_clear_m':[.60,.54],'forge_mouth_clear_m':[1.32,1.06],'native_anchor_binding':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'assignment':'first visible percentage, cumulative','parts':PARTS,'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Blacksmith_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(10,-13,11));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=12.2;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
    bpy.ops.object.light_add(type='AREA',location=(0,-5,3));bpy.context.object.data.energy=500;bpy.context.object.data.size=4
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Blacksmith_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=4;scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-12,1.4)),('back',(0,12,1.4)),('left',(-12,0,1.4)),('right',(12,0,1.4)),('top',(0,0,15)),('bottom',(0,0,-12))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('BLACKSMITH_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());saved=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched installed Abbasid Age II blacksmith decoded positions/topology';saved.append({'name':o.name,'vertices':len(vs),'faces':len(faces),'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Blacksmith_Age2_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':saved,'geometry_reused_in_final':False,'footprint_from':'core.xml site_ext x=8 y=8; render bounds not footprint'},indent=2))
try:
    donor()
    for age in [2,3,4]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'cook':False,'native_owner_colour':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

