"""Original Almohad royal courtyard citadel. Source only, no cook/production writes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import geometry_helpers as g
from geometry_helpers import bpy,bmesh,math,json,traceback,Vector,ART,OUT,RESEARCH,box,prism,contact,bounds
GUARDS=[];STATE=[]

def atlas(o):
 slot=g.MATS[o['ber_material_role']][1];uv=o.data.uv_layers.active
 for p in o.data.polygons:
  axes=sorted(range(3),key=lambda k:abs(p.normal[k]))[:2];cs=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];mins=[min(v[a] for v in cs) for a in axes];spans=[max(v[a] for v in cs)-mins[j] for j,a in enumerate(axes)]
  for li,v in zip(p.loop_indices,cs):uv.data[li].uv=((slot%4+.08+.84*(v[axes[0]]-mins[0])/max(spans[0],1e-9))/4,(slot//4+.08+.84*(v[axes[1]]-mins[1])/max(spans[1],1e-9))/2)

def arch(wall,width,height,front,back,base=.16):
 cutter=prism('TEMP_gateway',g.portal_outline(0,base,width,height),front-.2,back+.2,'shadow',40)
 bpy.context.view_layer.objects.active=wall;m=wall.modifiers.new('Genuine through gateway','BOOLEAN');m.operation='DIFFERENCE';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True);g.PARTS.pop()

def battered(name,cx,cy,w,d,h):
 vs=[(cx+x*w/2,cy+y*d/2,.16) for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]+[(cx+x*(w-.32)/2,cy+y*(d-.32)/2,.16+h) for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 fs=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);g.finish(o,name,'earth',40);contact(name,'foundation');return o

def parapet(name,cx,cy,w,d,z):
 # Continuous crenellation base seats on the deck, merlons seat on that base.
 for side,x,y,sx,sy in [('W',cx-w/2+.10,cy,.20,d),('E',cx+w/2-.10,cy,.20,d),('S',cx,cy-d/2+.10,w-.4,.20),('N',cx,cy+d/2-.10,w-.4,.20)]:
  base=box(name+'_parapet_'+side,(x,y,z+.16),(sx,sy,.32),'earth',80)
  n=max(2,int((d if side in ['W','E'] else w)/.42))
  for i in range(n):
   along=(-.5+(i+.5)/n)*(d-.10 if side in ['W','E'] else w-.45)
   mer=box(name+'_merlon_'+side,(x+(along if side in ['S','N'] else 0),y+(along if side in ['W','E'] else 0),z+.49),(.23 if side in ['S','N'] else .20,.20 if side in ['S','N'] else .23,.34),'lime',100);contact(mer.name,base.name)

def build():
 ctx=g.reset_scene();g.PARTS.clear();g.CONTACTS.clear();g.MATS.clear();GUARDS.clear();g.setup_maps()
 for name,col in [('normal',(.5,.5,1)),('roughness',(.85,.85,.85)),('metal',(0,0,0))]:
  im=bpy.data.images.new('GrandKeep_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
 box('foundation',(0,0,.08),(7.8,7.8,.16),'stone',0)
 # Four battered towers; unequal south/north heights distinguish the royal citadel.
 for side,cx,cy,h in [('SW',-2.96,-2.96,5.1),('SE',2.96,-2.96,5.1),('NW',-2.96,2.96,5.7),('NE',2.96,2.96,5.7)]:
  t=battered(side+'_battered_tower',cx,cy,1.64,1.64,h)
  deck=box(side+'_roof_deck',(cx,cy,.16+h+.04),(1.32,1.32,.08),'stone',60);contact(deck.name,t.name)
  parapet(side,cx,cy,1.32,1.32,.16+h+.08)
  # Visible owner panel sits against the inward-tapering south tower face.
  if cy<0:
   panel=box(side+'_owner_standard',(cx,cy-.82+.16*(3.94-.16)/h-.008,3.94),(.48,.035,.94),'owner_cloth',100)
   panel.rotation_euler.x=-math.atan(.16/h)
   box(side+'_standard_hanger',(cx,cy-.82+.16*(4.43-.16)/h-.025,4.43),(.56,.10,.10),'cedar',80)
  # Arrow slits are real shallow cuts, dark beds seated inside each recess.
  for z in [1.3,2.3,3.3]:
   facey=cy-1.64/2+.16*(z-.16)/h
   cutter=box('TEMP_arrow_slit',(cx,facey+.06,z),(.10,.26,.47),'shadow',60)
   bpy.context.view_layer.objects.active=t;mo=t.modifiers.new('Arrow slit recess','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);g.PARTS.pop()
   box(side+'_slit_recess_bed',(cx,facey+.175,z),(.095,.018,.46),'shadow',80)
 # Thick curtain walls and broad top walks connect tower faces through shared edges.
 for side,cx in [('W',-2.96),('E',2.96)]:
  wall=box(side+'_curtain',(cx,0,1.78),(.88,4.60,3.24),'earth',40);contact(wall.name,'foundation')
  walk=box(side+'_walk',(cx,0,3.46),(1.00,4.60,.12),'stone',60);contact(walk.name,wall.name)
  outer=box(side+'_walk_battlement',(cx+(-.42 if cx<0 else .42),0,3.72),(.16,4.60,.40),'earth',80);contact(outer.name,walk.name)
  for y in [-1.92,-1.44,-.96,-.48,0,.48,.96,1.44,1.92]:
   mer=box(side+'_walk_merlon',(cx+(-.42 if cx<0 else .42),y,4.07),(.16,.24,.30),'lime',100);contact(mer.name,outer.name)
 # Gatehouse bridges the portal; court remains genuinely open sky and floor.
 gate=box('S_gatehouse',(0,-2.96,1.78),(4.60,1.00,3.24),'earth',40);contact(gate.name,'foundation');arch(gate,1.98,2.75,-3.46,-2.46)
 gatewalk=box('S_gate_walk',(0,-2.96,3.46),(4.60,1.0,.12),'stone',60);contact(gatewalk.name,gate.name)
 top=box('S_gate_battlement',(0,-3.38,3.72),(4.60,.16,.40),'earth',80);contact(top.name,gatewalk.name)
 for x in [-1.94,-1.46,-.98,-.5,0,.5,.98,1.46,1.94]:
  mer=box('S_gate_merlon',(x,-3.38,4.07),(.24,.16,.30),'lime',100);contact(mer.name,top.name)
 # Carved stone portal is a real hollow surround with matched arch cut.
 surround=box('carved_stone_portal',(0,-3.515,1.70),(2.90,.11,3.08),'stone',60);contact(surround.name,'foundation');arch(surround,1.98,2.75,-3.57,-3.46)
 trim=box('lime_portal_outer_frame',(0,-3.585,1.76),(3.14,.03,3.20),'lime',80);contact(trim.name,'foundation');arch(trim,2.85,3.04,-3.61,-3.57)
 # Sebka panels: interlaced diamonds above the portal, no invented script/emblems.
 for cx in [-1.76,1.76]:
  for z in [.72,1.24,1.76,2.28,2.80]:
   for dx in [-.13,.13]:
    o=box('sebka_carved_diagonal',(cx+dx,-3.53,z),(.035,.035,.38),'lime',100);o.rotation_euler.y=(-1 if dx<0 else 1)*.72
 box('carved_lintel_band',(0,-3.585,3.04),(2.60,.08,.15),'lime',100)
 # Rear royal barrack/residence mass; its flat upper hall does not cover central court.
 hall=box('N_royal_hall',(0,2.83,2.13),(4.60,1.26,3.94),'earth',40);contact(hall.name,'foundation')
 deck=box('N_hall_roof',(0,2.83,4.15),(4.60,1.26,.10),'stone',60);contact(deck.name,hall.name)
 parapet('N_hall',0,2.83,4.60,1.26,4.20)
 # Open smaller court-facing portal through hall and recessed wooden side shutters.
 cutter=prism('TEMP_hall_door',g.portal_outline(0,.16,1.14,2.14),2.10,3.60,'shadow',40)
 bpy.context.view_layer.objects.active=hall;mo=hall.modifiers.new('Hall through door','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);g.PARTS.pop()
 for cx in [-1.25,1.25]:
  cutter=box('TEMP_hall_window',(cx,2.23,2.44),(.44,.28,.66),'shadow',60)
  bpy.context.view_layer.objects.active=hall;mo=hall.modifiers.new('Real recessed shutter','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);g.PARTS.pop()
  box('cedar_hall_shutter',(cx,2.355,2.44),(.42,.035,.64),'cedar',80)
  box('hall_window_sill',(cx,2.19,2.10),(.53,.21,.07),'lime',80)
  box('hall_owner_strip',(cx,2.185,3.19),(.72,.03,.22),'owner_cloth',100)
 # Physical access stairs seat on foundation and meet west wall walk at its inner face.
 for i in range(10):
  height=(3.52-.16)*(i+1)/10
  stair=box('court_to_W_walk_stair',(-2.16,-1.87+i*.32,.16+height/2),(.60,.32,height),'stone',60);contact(stair.name,'foundation')
 # Open door leaves parked beside the gateway; retain closed/open native-independent Actions.
 for side,hinge,angle in [('left',-.85,math.pi/2),('right',.85,-math.pi/2)]:
  leaf=box('gateway_'+side+'_leaf',(hinge,-3.42,1.22),(.85,.075,2.10),'cedar',80)
  # Move local mesh to hinge, park leaf back into passage side; source origin is hinge.
  shift=.425 if side=='left' else -.425
  for v in leaf.data.vertices:v.co.x+=shift
  leaf.rotation_euler.z=0;leaf.keyframe_insert(data_path='rotation_euler',frame=1)
  leaf.rotation_euler.z=angle;leaf.keyframe_insert(data_path='rotation_euler',frame=30)
  leaf.animation_data.action.name='GrandKeep_'+side+'_gate_closed_to_open'
  STATE.append({'object':leaf.name,'hinge_design':[hinge,-3.42,1.22],'closed_rotation_z':0,'open_rotation_z':angle,'action':leaf.animation_data.action.name,'frames':[1,30],'native_playback':'unqualified'})
 bpy.context.scene.frame_set(30);bpy.context.view_layer.update()
 # Whole-model rays prove gateway and court emptiness before scale conversion.
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
 for z in [.42,2.05]:
  hits=[]
  for o in objects:
   inv=o.matrix_world.inverted()
   if o.ray_cast(inv@Vector((0,-3.9,z)),inv.to_3x3()@Vector((0,1,0)),distance=5.7)[0]:hits.append(o.name)
  GUARDS.append({'gateway_ray_design_z':z,'start_y':-3.9,'end_y':1.8,'hits':hits,'pass':not hits})
 for x,y in [(-1,0),(0,0),(1,0),(-1,1),(0,1),(1,1)]:
  hits=[]
  for o in objects:
   inv=o.matrix_world.inverted()
   if o.ray_cast(inv@Vector((x,y,.20)),inv.to_3x3()@Vector((0,0,1)),distance=8)[0]:hits.append(o.name)
  GUARDS.append({'court_vertical_ray_design':[x,y,.20],'hits':hits,'pass':not hits})
 assert all(v['pass'] for v in GUARDS),GUARDS
 finalize(objects)

def finalize(objects):
 checks=[]
 for o in objects:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
  bm.to_mesh(o.data);bm.free();o.data.update();atlas(o)
  # Preserve animator=125 by reducing all source metres by 0.8, including door pivots.
  for v in o.data.vertices:v.co*=.8
  o.location*=.8
  bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True);non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free();uv=o.data.uv_layers.active;areas=[]
  for p in o.data.polygons:
   a,b,c=[uv.data[i].uv for i in p.loop_indices];areas.append(abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2)
  checks.append({'object':o.name,'triangles':len(o.data.polygons),'non_manifold_edges':non,'degenerate_faces':deg,'signed_volume':vol,'minimum_uv_triangle_area':min(areas),'positive_transform':o.matrix_world.determinant()>0,'finite_geometry':all(math.isfinite(t) for v in o.data.vertices for t in v.co)})
 bpy.context.view_layer.update();bs=[bounds(o) for o in objects];lo=[min(b[0][k] for b in bs) for k in range(3)];hi=[max(b[1][k] for b in bs) for k in range(3)]
 assert all(c['non_manifold_edges']==0 and c['degenerate_faces']==0 and c['signed_volume']>0 and c['minimum_uv_triangle_area']>1e-10 and c['positive_transform'] and c['finite_geometry'] for c in checks),checks
 assert all(c['pass'] for c in g.CONTACTS),g.CONTACTS
 assert lo[0]*1.25>=-4 and lo[1]*1.25>=-4 and hi[0]*1.25<=4 and hi[1]*1.25<=4 and abs(lo[2])<1e-6,(lo,hi)
 joins=[]
 for walk,tower in [('W_walk','SW_battered_tower'),('E_walk','SE_battered_tower'),('S_gate_walk','SW_battered_tower')]:
  wb=bounds(bpy.data.objects[walk]);tb=bounds(bpy.data.objects[tower]);overlap=[min(wb[1][k],tb[1][k])-max(wb[0][k],tb[0][k]) for k in range(3)];joins.append({'walk':walk,'tower':tower,'bounds_overlap_source':overlap,'note':'Curtain end face intersects battered tower interior by explicit contact depth; walk continuous.'})
 validation={'age':4,'objects':checks,'contacts_design_metres':g.CONTACTS,'void_guards_design_metres':GUARDS,'walk_tower_interfaces':joins,'site_footprint':[8,8],'source_mesh_bounds':[lo,hi],'bounds_after_animator125':[[v*1.25 for v in lo],[v*1.25 for v in hi]],'footprint_pass':True,'ground_z':lo[2],'gateway_clear_width_source':1.98*.86*.8,'gateway_clear_width_rendered':1.98*.86,'walk_width_source':.8,'walk_width_rendered':1,'court_open_source_rect':[-.8,.8,-.8,.8]}
 (OUT/'age4_validation.json').write_text(json.dumps(validation,indent=2))
 (ART/'age4_construction.json').write_text(json.dumps({'age':4,'construction_age':3,'stages':[0,20,40,60,80,100],'parts':g.PARTS,'assignment':'cumulative first visible percentage','game_binding_status':'pending native integration'},indent=2))
 (ART/'construction_age3.json').write_text(json.dumps({'construction_age':3,'completed_age':4,'reuse':'age4_construction.json + Almohad_GrandKeep_Age4.blend','no_completed_age3':True},indent=2))
 for state in STATE:state['hinge_source']=[v*.8 for v in state['hinge_design']]
 (ART/'state_manifest.json').write_text(json.dumps({'default':'open frame30','gate_states':STATE,'walk_surfaces':'source mesh faces only; native surfaces/anchors pending'},indent=2))
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(ART/'Almohad_GrandKeep_Age4.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
 sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.65
 bpy.ops.object.camera_add(location=(9,-12,10));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=10.8;target=Vector((0,0,2.2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-8,-12,20));bpy.context.object.data.energy=3000;bpy.context.object.data.size=10
 bpy.ops.object.light_add(type='AREA',location=(0,0,13));bpy.context.object.data.energy=1800;bpy.context.object.data.size=7
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Almohad_GrandKeep_Age4.blend'));sc.render.filepath=str(OUT/'age4_preview.png');bpy.ops.render.render(write_still=True)
 sc.render.resolution_x=384;sc.render.resolution_y=384
 for name,loc in [('front',(0,-12,2.2)),('back',(0,12,2.2)),('left',(-12,0,2.2)),('right',(12,0,2.2)),('top',(0,0,12)),('bottom',(0,0,-12))]:
  cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age4_{name}.png');bpy.ops.render.render(write_still=True)

def donor():
 ctx=g.reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());groups=[]
 for group in d['geometry']['groups']:
  vs=group['positions'];fs=group.get('triangles',group.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched installed Abbasid keep decoded positions/topology';groups.append({'name':o.name,'bounds':bounds(o)})
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Keep_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':groups,'geometry_reused':False,'render_bounds_are_footprint':False},indent=2))
try:
 donor();build();(OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[4],'construction_age':3,'cook':False,'native_owner_colour':'blocked integration pending'}));print('GRAND_KEEP_DONE',flush=True)
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
