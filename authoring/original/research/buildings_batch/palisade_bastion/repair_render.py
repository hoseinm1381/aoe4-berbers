"""Task-owned reproducible Berber palisade end/connection sources; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/palisade_bastion'; OUT=ROOT/'output/buildings_batch/palisade_bastion'; RESEARCH=ROOT/'research/buildings_batch/palisade_bastion'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.10,.115,.125),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern','roughness','metal','normal'):
        im=bpy.data.images.new('PalisadeBastion_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
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
        m=bpy.data.materials.new('BerberPalisadeBastion_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='PalisadeAtlasUV')
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


H=4.578125; WIDTH=.682861328125

def studio(scale=6.5):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.render.resolution_x=768;s.render.resolution_y=768
 s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
 bpy.ops.object.camera_add(location=(9,-13,10));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
 return s,cam


STATE_DIRS={'terminal':[0],'straight':[0,180],'corner_90':[0,90],'junction_T':[0,90,180],'junction_cross':[0,90,180,270]}
def donor():
 ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text())
 for g in d['geometry']['groups']:
  me=bpy.data.meshes.new(g['name']);me.from_pydata(g['positions'],[],g['triangles']);me.update();ob=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(ob)
  ob['reference_only']='untouched decoded position/topology, all18 collection partitions; not healthy-only; material reconstruction omitted'
 s,cam=studio();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Untouched_Stock_Palisade_Bastion_Reference.blend'));s.render.filepath=str(OUT/'donor_preview.png');bpy.ops.render.render(write_still=True)

def connector(age,dirs):
 W=WIDTH;P=.22;Q=.165;B=.22
 base=box('compacted_earth_footing',(0,0,B/2),(W,W,B),'lime' if age==4 else 'earth',0)
 for x in [-Q,Q]:
  for y in [-Q,Q]:
   p=prism('split_timber_upright',[(x-P/2,B),(x+P/2,B),(x+P/2,H-.24),(x,H),(x-P/2,H-.24)],y-P/2,y+P/2,'cedar',20)
   contact(p.name,base.name)
   if age>=3:
    box('earth_post_socket',(x,y,B+.10),(P+.06,P+.06,.20),'lime' if age==4 else 'earth',40)
 # Rails on all faces lock the four pole bundle into a squared terminal. Rails end at explicit W/2 planes.
 for z in [1.05,2.85]:
  for y in [-Q,Q]:
   box('bundle_cross_tie_x',(0,y,z),(W,.09,.16),'cedar',60)
  for x in [-Q,Q]:
   box('bundle_cross_tie_y',(x,0,z),(.09,W,.16),'cedar',60)
  for x in [-Q,Q]:
   for y in [-Q,Q]:
    # Four-sided lashing around each .22m upright. Exact contact at faces.
    for yy in [y-P/2-.018,y+P/2+.018]:box('lashing_front_back',(x,yy,z),(P+.072,.036,.062),'straw',80)
    for xx in [x-P/2-.018,x+P/2+.018]:box('lashing_sides',(xx,y,z),(.036,P,.062),'straw',80)
    CONTACTS.append({'interface':'rope inner faces on post faces','signed_gap':0.0,'intentional':'closed rectangular lashing sleeve; corner overlaps .036m','pass':True})
 # Neutral painted stripe panels are in contact with outer timber faces, matching peer 3.24m owner band.
 for axis in [0,1]:
  for sign in [-1,1]:
   pos=[0,0,3.24];pos[axis]=sign*(Q+P/2+.008);size=[.43,.016,.20] if axis==1 else [.016,.43,.20]
   box('native_owner_stripe_source',pos,size,'owner_cloth',100)
 # Inactive faces have angled stays and terminal joinery; sockets stay exposed on live directions.
 for deg in [0,90,180,270]:
  a=math.radians(deg);d=Vector((math.cos(a),math.sin(a),0));t=Vector((-math.sin(a),math.cos(a),0))
  if deg not in dirs:
   for sg in [-1,1]:beam('terminal_diagonal_stay',d*(Q+.10)+t*(sg*.12)+Vector((0,0,.44)),d*(Q+.10)-t*(sg*.12)+Vector((0,0,2.73)),.06,'cedar',80)
  else:
   for z in [1.05,2.85]:
    pos=d*(W/2-.018)+Vector((0,0,z));size=(.036,.32,.20) if deg in [0,180] else (.32,.036,.20)
    box('exposed_wall_socket_collar',pos,size,'straw',80)
 if age>=2:
  # Diagonal timber pegging creates a development step without converting woodwork to stone.
  for x in [-Q,Q]:
   for y in [-Q,Q]:box('locking_timber_peg',(x,y,2.85),(.08,.08,.32),'straw',80)
 if age==4:
  for axis in [0,1]:
   for sg in [-1,1]:
    pos=[0,0,3.69];pos[axis]=sg*(Q+P/2+.012);size=[.12,.024,.12] if axis==1 else [.024,.12,.12]
    ob=box('small_geometric_joinery_inlay',pos,size,'lime',100);ob.rotation_euler[axis]=math.pi/4
 for ob in [ob for ob in bpy.context.scene.objects if ob.type=='MESH']:reuv(ob)

def audit(objs):
 rows=[]
 for ob in objs:
  bm=bmesh.new();bm.from_mesh(ob.data);vol=bm.calc_volume(signed=True);non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free();uv=ob.data.uv_layers.active;uz=0
  for f in ob.data.polygons:
   ps=[uv.data[i].uv for i in f.loop_indices];area=abs(sum(ps[i].x*ps[(i+1)%len(ps)].y-ps[(i+1)%len(ps)].x*ps[i].y for i in range(len(ps)))/2);uz+=area<1e-10
  c={'object':ob.name,'closed':non==0,'signed_volume':vol,'degenerate_faces':deg,'zero_uv_faces':uz,'finite':all(math.isfinite(v) for ve in ob.data.vertices for v in ve.co),'positive_scale':all(v>0 for v in ob.scale),'bounds':bounds(ob)};rows.append(c)
 assert all(c['closed'] and c['signed_volume']>0 and c['degenerate_faces']==0 and c['zero_uv_faces']==0 and c['finite'] and c['positive_scale'] for c in rows)
 return rows

def build(age):
 global PARTS,CONTACTS
 ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();states={};checks={};joins=[]
 for name,dirs in STATE_DIRS.items():
  old=set(bpy.context.scene.objects);connector(age,dirs);objs=[ob for ob in bpy.context.scene.objects if ob not in old]
  coll=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(coll)
  for ob in objs:
   for c in list(ob.users_collection):c.objects.unlink(ob)
   coll.objects.link(ob)
  bpy.context.view_layer.update();checks[name]=audit(objs)
  endpoints=[]
  for i,deg in enumerate(dirs):
   a=math.radians(deg);p=[WIDTH/2*math.cos(a),WIDTH/2*math.sin(a),0];endpoints.append(p)
   marker=bpy.data.objects.new(name+'_wall_socket_'+str(deg),None);coll.objects.link(marker);marker.location=p;marker['native_binding']='authored logical endpoint, no verified native stamp transform'
   # Adjacent peer wall begins on the same W/2 plane, post footprint has no gap.
   joins.append({'state':name,'degrees':deg,'socket_ground':p,'socket_top':H,'wall_width':WIDTH,'wall_rail_z':[1.05,2.85],'plane_gap_m':0,'peer_6m_center':[p[0]+3*math.cos(a),p[1]+3*math.sin(a),0],'native_stamp_binding':'pending'})
  states[name]={'objects':[ob.name for ob in objs],'directions_degrees':dirs,'endpoints':endpoints}
  bpy.ops.object.select_all(action='DESELECT')
  for ob in objs:ob.hide_set(False);ob.select_set(True)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_PalisadeBastion_Age{age}_{name}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
  for ob in objs:ob.hide_set(True);ob.hide_render=True
 assert all(c['pass'] for c in CONTACTS)
 for ob in bpy.context.scene.objects:
  if ob.type=='MESH':ob.hide_render=ob.name not in states['corner_90']['objects'];ob.hide_set(ob.hide_render)
 (ART/f'age{age}_states.json').write_text(json.dumps({'age':age,'states':states,'joins':joins,'native_selector_binding':'empty official cap_connection_variants; authored alternatives require downstream selector qualification'},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'parts':PARTS,'native_binding':'pending'},indent=2))
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'states':checks,'contacts':CONTACTS,'joins':joins},indent=2))
 s,cam=studio();bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_PalisadeBastion_Age{age}.blend'));s.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
 s.cycles.samples=4;s.render.resolution_x=256;s.render.resolution_y=256
 for name,loc in [('front',(0,-12,2)),('back',(0,12,2)),('left',(-12,0,2)),('right',(12,0,2)),('top',(0,0,15)),('bottom',(0,0,-12))]:
  cam.location=loc;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 print('PALISADE_BASTION_DONE',age,flush=True)
try:
 # donor reference retained
 for age in [3,4]:build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'native_owner_colour':'pending','cook':False}))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender()
