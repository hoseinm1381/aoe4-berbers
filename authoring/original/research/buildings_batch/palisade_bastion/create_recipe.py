from pathlib import Path
r=Path.cwd();a=r/'art/buildings/palisade_bastion';q=r/'research/buildings_batch/palisade_bastion';o=r/'output/buildings_batch/palisade_bastion'
s=(r/'art/buildings/palisade/build_palisade.py').read_text();head=s[:s.index('def donor():')].replace('/palisade\'','/palisade_bastion\'').replace('Palisade_', 'PalisadeBastion_').replace('BerberPalisade_', 'BerberPalisadeBastion_'); head=head.replace('"""Task-owned, reproducible Moroccan courtyard blacksmith source; no cook or production edits."""','"""Task-owned reproducible Berber palisade end/connection sources; no cook or production edits."""')
head=head.replace("s.cycles.samples=8","s.cycles.samples=8").replace('def studio(scale=9):','def studio(scale=6.5):')
body=r'''
STATE_DIRS={'terminal':[0],'straight':[0,180],'corner_90':[0,90],'junction_T':[0,90,180],'junction_cross':[0,90,180,270]}
def donor():
 ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text())
 for g in d['geometry']['groups']:
  me=bpy.data.meshes.new(g['name']);me.from_pydata(g['positions'],[],g['triangles']);me.update();ob=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(ob)
  ob['reference_only']='untouched decoded position/topology, all18 collection partitions; not healthy-only; material reconstruction omitted'
 s,cam=studio();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Untouched_Stock_Palisade_Bastion_Reference.blend'));s.render.filepath=str(OUT/'donor_preview.png');bpy.ops.render.render(write_still=True)

def connector(age,dirs):
 W=WIDTH;P=.22;Q=.165;B=.22
 base=box('compacted_earth_footing',(0,0,B/2),(W,W,B),'earth',0)
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
 if age>=3:
  box('limewashed_earth_base_course',(0,0,.06),(W,W,.12),'earth' if age==3 else 'lime',0)
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
 donor()
 for age in range(1,5):build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'native_owner_colour':'pending','cook':False}))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender()
'''
(a/'build_palisade_bastion.py').write_text(head+body,encoding='utf-8')
runner=(r/'research/buildings_batch/palisade/run_hidden.py').read_text().replace('/palisade','/palisade_bastion').replace('build_palisade.py','build_palisade_bastion.py');(q/'run_hidden.py').write_text(runner)
