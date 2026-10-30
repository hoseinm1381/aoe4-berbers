from pathlib import Path
r=Path.cwd();q=r/'research/buildings_batch/palisade';a=r/'art/buildings/palisade';o=r/'output/buildings_batch/palisade'
s=(r/'art/buildings/blacksmith/build_blacksmith.py').read_text();p=s[:s.index('def build(age):')].replace('/blacksmith','/palisade').replace('Blacksmith','Palisade')
body=r'''
H=4.578125; WIDTH=.682861328125

def studio(scale=9):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.render.resolution_x=768;s.render.resolution_y=768
 s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
 bpy.ops.object.camera_add(location=(9,-13,10));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
 return s,cam

def donor():
 ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text())
 for g in d['geometry']['groups']:
  me=bpy.data.meshes.new(g['name']);me.from_pydata(g['positions'],[],g['triangles']);me.update();ob=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(ob)
  ob.hide_render=g['name']!='mesh_11_group_00';ob['reference_only']='untouched decoded position/topology; no material reconstruction'
 s,cam=studio();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Untouched_English_Common_Palisade_6m_Reference.blend'));s.render.filepath=str(OUT/'donor_preview.png');bpy.ops.render.render(write_still=True)

def panel(age,L):
 # Long-axis sockets ±L/2, fence center Y0; picket profile shares datum across all lengths.
 base=box('earth_seat',(0,0,.12),(L,WIDTH,.24),'earth' if age<3 else 'stone',0)
 N=max(3,round(L/.24));pitch=L/N
 for i in range(N):
  x=-L/2+(i+.5)*pitch;top=H-(.10 if i%3 else 0)
  post=prism('palm_split_post',[(x-pitch*.46,.24),(x+pitch*.46,.24),(x+pitch*.46,top-.28),(x,top),(x-pitch*.46,top-.28)],-.17,.17,'cedar' if i%3 else 'straw',20+20*(i%4))
  CONTACTS.append({'child':post.name,'parent':base.name,'signed_gap':0,'pass':True})
  # Closed faceted lashing sleeves fit snugly around posts and through rear ties.
  for z in [1.05,2.85]:
   box('front_lashing',(x,-.192,z),(pitch*.97,.044,.055),'straw',100)
   box('back_lashing',(x,.25,z),(pitch*.97,.044,.055),'straw',100)
   for xx in [x-pitch*.44,x+pitch*.44]:box('lashing_side',(xx,.025,z),(.036,.49,.055),'straw',100)
  if age>=2:
   for y in [-.178,.178]:box('neutral_owner_band',(x,y,3.24),(pitch*.89,.016,.20),'owner_cloth',100)
  if age==1 and i%3==0:
   box('neutral_owner_painted_stripe',(x,-.178,3.24),(pitch*.89,.016,.26),'owner_cloth',100)
  if age>=3:
   box('post_earth_socket',(x,0,.34),(pitch*.97,.45,.20),'earth' if age==3 else 'lime',40)
  if age==4 and i%4==1:
   for y in [-.19,.19]:
    b=box('restrained_geometric_carving',(x,y,3.62),(.08,.024,.08),'lime',100);b.rotation_euler.y=math.pi/4
 for z in [1.05,2.85]:
  rail=box('continuous_rear_tie',(0,.205,z),(L,.07,.16),'cedar',60)
  CONTACTS.append({'interface':'rear tie front face seats to picket back face','signed_gap':.205-.035-.17,'pass':abs(.205-.035-.17)<1e-6})
 if age>=2:
  for x in [-L*.32,L*.32]:beam('back_diagonal_brace',(x-.25,.25,.65),(x+.25,.25,3.02),.085)
 for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:reuv(o)

def audit(objs):
 rows=[]
 for ob in objs:
  bm=bmesh.new();bm.from_mesh(ob.data);vol=bm.calc_volume(signed=True);non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free();uv=ob.data.uv_layers.active;uz=0
  for f in ob.data.polygons:
   ps=[uv.data[i].uv for i in f.loop_indices];area=abs(sum(ps[i].x*ps[(i+1)%len(ps)].y-ps[(i+1)%len(ps)].x*ps[i].y for i in range(len(ps)))/2);uz+=area<1e-10
  c={'object':ob.name,'closed':non==0,'volume':vol,'degenerate':deg,'uv_zero':uz,'finite':all(math.isfinite(v) for ve in ob.data.vertices for v in ve.co),'positive_scale':all(v>0 for v in ob.scale),'bounds':bounds(ob)};rows.append(c)
 assert all(c['closed'] and c['volume']>0 and c['degenerate']==0 and c['uv_zero']==0 and c['finite'] and c['positive_scale'] for c in rows),[c for c in rows if c['uv_zero']]
 return rows

def build(age):
 global PARTS,CONTACTS
 ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();states={};checks={};joins=[]
 for name,L,rise in [('straight_1m',1,0),('straight_3m',3,0),('straight_6m',6,0),('gapfill_1m',1,0),('gapfill_2m',2,0),('gapfill_3m',3,0),('gapfill_4m',4,0),('slope_up_6m',6,1),('slope_down_6m',6,-1),('corner_90',3,0),('end_socket',1,0)]:
  old=set(bpy.context.scene.objects);panel(age,L);objs=[ob for ob in bpy.context.scene.objects if ob not in old]
  if name=='corner_90':
   # Two panels share origin end and overlap intentionally through one post-width.
   for ob in objs:ob.location.x+=L/2
   second=[]
   for ob in objs:
    no=ob.copy();no.data=ob.data.copy();bpy.context.scene.collection.objects.link(no);no.name='corner_return_'+ob.name;no.location=Vector((-ob.location.y,ob.location.x,ob.location.z));no.rotation_euler.z+=math.pi/2;second.append(no)
    PARTS.append({'object':no.name,'first_stage':no['garrison_building_first_stage'],'material':no['ber_material_role'],'owner_mask':no.data.materials[0]['ber_owner_mask']})
   objs+=second
  if rise:
   # Affine terrain deformation preserves flat closed volumes; minimum terrain is zero.
   for ob in objs:
    mat=ob.matrix_world.copy()
    for ve in ob.data.vertices:
     co=mat@ve.co;co.z+=rise*co.x/L+abs(rise)/2;ve.co=co
    ob.location=(0,0,0);ob.rotation_euler=(0,0,0);ob.data.update();reuv(ob)
  coll=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(coll)
  for ob in objs:
   for c in list(ob.users_collection):c.objects.unlink(ob)
   coll.objects.link(ob)
  bpy.context.view_layer.update();checks[name]=audit(objs)
  sockets=[[-L/2,0,abs(rise)/2-rise/2],[L/2,0,abs(rise)/2+rise/2]] if name!='corner_90' else [[3,0,0],[0,3,0]]
  for i,pt in enumerate(sockets):
   marker=bpy.data.objects.new(name+'_end_'+str(i),None);coll.objects.link(marker);marker.location=pt;marker['native_binding']='source logical interface; stamp binding pending'
  joins.append({'state':name,'length':L,'terrain_rise':rise,'sockets':sockets,'connector_top_datum':H,'pitch_interface_error':0,'ground_rule':'local affine terrain z(x), ground is0 at low end','native_terrain_conform':'pending'})
  states[name]=[ob.name for ob in objs]
  bpy.ops.object.select_all(action='DESELECT')
  for ob in objs:ob.hide_set(False);ob.select_set(True)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Palisade_Age{age}_{name}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
  for ob in objs:ob.hide_set(True);ob.hide_render=True
 for c in CONTACTS:assert c['pass']
 for ob in bpy.context.scene.objects:
  if ob.type=='MESH':ob.hide_render=ob.name not in states['straight_6m'];ob.hide_set(ob.hide_render)
 (ART/f'age{age}_states.json').write_text(json.dumps({'age':age,'states':states,'joins':joins},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'parts':PARTS,'native_binding':'pending'},indent=2))
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'states':checks,'contacts':CONTACTS,'joins':joins},indent=2))
 s,cam=studio();bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Palisade_Age{age}.blend'));s.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
 s.cycles.samples=4;s.render.resolution_x=256;s.render.resolution_y=256
 for name,loc in [('front',(0,-12,2)),('back',(0,12,2)),('left',(-12,0,2)),('right',(12,0,2)),('top',(0,0,15)),('bottom',(0,0,-12))]:
  cam.location=loc;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 print('PALISADE_DONE',age,flush=True)
try:
 donor()
 for age in range(1,5):build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'native_owner_colour':'pending','cook':False}))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender()
'''
(a/'build_palisade.py').write_text(p+body)
s=(r/'research/buildings_batch/outpost/run_hidden.py').read_text().replace('/outpost','/palisade').replace('build_outpost','build_palisade');(q/'run_hidden.py').write_text(s)
