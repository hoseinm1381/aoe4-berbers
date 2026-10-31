"""Original fortified devotional/council quadrangle, ages II-IV. No mod edits."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import geometry_helpers as g
from geometry_helpers import bpy,bmesh,math,json,traceback,Vector,ART,OUT,RESEARCH,box,prism,contact,bounds
GUARDS=[]
def arch(wall,cx,y,width,height,base=.15,side=False):
 c=prism('TEMP_arch',g.portal_outline(cx,base,width,height),y-1,y+1,'shadow',40)
 if side:c.rotation_euler.z=math.pi/2
 bpy.context.view_layer.objects.active=wall;m=wall.modifiers.new('Actual through opening','BOOLEAN');m.operation='DIFFERENCE';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True);g.PARTS.pop()
 origin=Vector((-y-1.1,cx,base+.3)) if side else Vector((cx,y-1.1,base+.3));direction=Vector((1,0,0)) if side else Vector((0,1,0));inv=wall.matrix_world.inverted();hit=wall.ray_cast(inv@origin,inv.to_3x3()@direction,distance=2.2)[0]
 GUARDS.append({'wall':wall.name,'clear_base_width':width*.86,'ray_hit':hit,'pass':not hit})
def atlas(o):
 slot=g.MATS[o['ber_material_role']][1];uv=o.data.uv_layers.active
 for p in o.data.polygons:
  axes=sorted(range(3),key=lambda k:abs(p.normal[k]))[:2];cs=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];mins=[min(v[a] for v in cs) for a in axes];spans=[max(v[a] for v in cs)-mins[j] for j,a in enumerate(axes)]
  for li,v in zip(p.loop_indices,cs):uv.data[li].uv=((slot%4+.08+.84*(v[axes[0]]-mins[0])/max(spans[0],1e-9))/4,(slot//4+.08+.84*(v[axes[1]]-mins[1])/max(spans[1],1e-9))/2)
def roof(name,cx,cy,w,d,z,age):
 box(name,(cx,cy,z+.06),(w,d,.12),'earth' if age==2 else 'lime',60)
 for x in [cx-w/2+.08,cx+w/2-.08]:box(name+'_parapet',(x,cy,z+.24),(.16,d,.24),'earth',80)
 for y in [cy-d/2+.08,cy+d/2-.08]:box(name+'_parapet',(cx,y,z+.24),(w-.32,.16,.24),'earth',80)
def build(age):
 ctx=g.reset_scene();g.PARTS.clear();g.CONTACTS.clear();g.MATS.clear();GUARDS.clear();g.setup_maps()
 for name,col in [('normal',(.5,.5,1)),('roughness',(.85,.85,.85)),('metal',(0,0,0))]:
  im=bpy.data.images.new('Marrakech_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
 floor=.15;h=2.30;top=floor+h
 box('foundation',(0,0,.075),(7.7,7.7,.15),'stone',0)
 # Closed-volume masonry forms a hollow enclosure: no solid cuboid court.
 for x in [-3.25,3.25]:
  wall=box('side_rampart_'+str(x),(x,0,floor+h/2),(.70,7.2,h),'earth',40);contact(wall.name,'foundation')
 for y in [-3.25,3.25]:
  if y<0:
   for x in [-2.025,2.025]:
    ob=box('front_rampart_'+str(x),(x,y,floor+h/2),(1.75,.70,h),'earth',40);contact(ob.name,'foundation')
  else:
   ob=box('rear_rampart',(0,y,floor+h/2),(5.8,.70,h),'earth',40);contact(ob.name,'foundation')
 # Grand stone horseshoe gateway, open all the way through its shell.
 gate=box('grand_kasbah_gateway',(0,-3.25,floor+3.15/2),(2.30,.70,3.15),'stone',40);arch(gate,0,-3.25,1.35,2.12);contact(gate.name,'foundation')
 frame=box('gateway_carved_alfiz',(0,-3.64,floor+2.73/2),(2.55,.10,2.73),'lime',80);arch(frame,0,-3.64,1.35,2.12);contact(frame.name,'foundation')
 for x in [-1.05,1.05]:box('gateway_owner_bands',(x,-3.701,1.28),(.22,.025,1.30),'owner_cloth',80)
 for x in [-.85,-.51,-.17,.17,.51,.85]:
  ob=box('gateway_geometric_carving',(x,-3.705,2.56),(.15,.035,.15),'stone',100);ob.rotation_euler.y=math.pi/4
 box('gateway_stepped_cornice',(0,-3.25,3.36),(2.55,.80,.12),'lime',80);contact('gateway_stepped_cornice',gate.name)
 # Continuous supported walks share exact corner contacts; gate crosses above clear arch.
 for x in [-3.25,3.25]:
  ob=box('side_wall_walk_'+str(x),(x,0,top+.06),(.70,7.2,.12),'lime',60);contact(ob.name,'side_rampart_'+str(x))
 for y in [-3.25,3.25]:
  ob=box('cross_wall_walk_'+str(y),(0,y,top+.06),(5.8,.70,.12),'lime',60)
  if y>0:contact(ob.name,'rear_rampart')
 # Outside parapets leave the courtyard side clear for soldiers.
 for x in [-3.52,3.52]:box('outer_walk_parapet',(x,0,top+.38),(.16,6.88,.52),'earth',80)
 for y in [-3.52,3.52]:
  for x in ([-2.375,2.375] if y<0 else [0]):box('cross_walk_parapet',(x,y,top+.38),(2.45 if y<0 else 7.20,.16,.52),'earth',80)
 for x in [-3.53,3.53]:
  for y in [-2.75,0,2.75]:box('rammed_earth_stone_footing',(x,y,.34),(.16,.44,.38),'stone',20)
 # Rear administrative hall is a hollow shell with real through arches.
 oh=1.90;oy=2.33
 fw=box('office_courtyard_arcade',(0,1.72,floor+oh/2),(5.72,.18,oh),'lime',40)
 for x in [-1.80,0,1.80]:arch(fw,x,1.72,.86,1.56)
 contact(fw.name,'foundation')
 for x in [-2.80,2.80]:
  ob=box('office_end_wall',(x,oy,floor+oh/2),(.16,1.10,oh),'lime',40);contact(ob.name,'foundation')
 box('office_flat_roof',(0,2.30,floor+oh+.06),(5.8,1.34,.12),'lime',60);contact('office_flat_roof',fw.name)
 box('office_roof_front_parapet',(0,1.68,floor+oh+.25),(5.8,.12,.26),'earth',80);contact('office_roof_front_parapet','office_flat_roof')
 # Court-side storage portico, fitted neutral cloth canopy, timber rack and sacks.
 canopyz=1.55
 for y in [-1.25,.90]:
  post=box('store_portico_post',(-2.15,y,floor+(canopyz-floor)/2),(.10,.10,canopyz-floor),'cedar',20);contact(post.name,'foundation')
 box('store_portico_crossbeam',(-2.15,-.175,canopyz-.04),(.14,2.35,.08),'cedar',60)
 box('store_owner_cloth_awning',(-2.51,-.175,canopyz+.025),(.86,2.35,.05),'owner_cloth',80);contact('store_owner_cloth_awning','store_portico_crossbeam')
 for x in [-2.68,-2.38]:
  for y in [-.90,-.35,.20]:
   ob=g.tube('provision_sack',(x,y,.35),.17,.40,'straw',100);contact(ob.name,'foundation')
 # Useful training equipment sits off the gate-to-office traffic axis.
 for y in [-1.40,-.10,1.12]:
  ob=box('training_target_post',(2.15,y,.82),(.10,.10,1.34),'cedar',80);contact(ob.name,'foundation')
  box('training_target_crossbar',(2.15,y,1.18),(.70,.10,.10),'cedar',100)
  ob=g.tube('woven_training_target',(2.15,y,1.25),.28,.10,'straw',100);ob.rotation_euler.x=math.pi/2
 box('office_record_chest',(-1.85,2.30,.38),(.70,.48,.46),'cedar',80);contact('office_record_chest','foundation')
 box('office_record_chest_lid',(-1.85,2.30,.64),(.73,.51,.06),'cedar',100);contact('office_record_chest_lid','office_record_chest')
 # Stairs run to the east walk; each upper tread touches the preceding body.
 for i in range(10):
  ht=(top+.12-floor)*(i+1)/10
  ob=box('walk_access_stair_'+str(i),(2.625,-2.65+i*.25,floor+ht/2),(.55,.25,ht),'stone',60);contact(ob.name,'foundation')
 if age==4:
  # More developed masonry and joinery, same functional footprint.
  for x in [-3.55,3.55]:
   for y in [-2.75,-1.40,0,1.40,2.75]:box('lime_stone_rampart_repair',(x,y,.68),(.14,.34,.52),'lime',100)
  for x in [-2.55,-1.8,-1.05,0,1.05,1.8,2.55]:box('office_alfiz_joinery',(x,1.611,1.87),(.42,.04,.13),'cedar',100)
  for x in [-1.12,1.12]:
   box('portal_lime_pier_cap',(x,-3.25,3.53),(.35,.76,.22),'lime',100);contact('portal_lime_pier_cap' if x<0 else 'portal_lime_pier_cap.001','gateway_stepped_cornice')
 # Measured empty space and walk join guards; downward courtyard rays stop only at floor.
 bpy.context.view_layer.update()
 for point in [(0,-1),(0,0),(0,1),(1,0),(-1,0)]:
  origin=Vector((point[0],point[1],8));hits=[]
  for ob in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name!='foundation']:
   inv=ob.matrix_world.inverted();hit=ob.ray_cast(inv@origin,inv.to_3x3()@Vector((0,0,-1)),distance=8)[0]
   if hit:hits.append(ob.name)
  GUARDS.append({'court_point':point,'above_floor_hits':hits,'pass':not hits})
 for side in ['-3.25','3.25']:
  b=bounds(bpy.data.objects['side_wall_walk_'+side]);c=bounds(bpy.data.objects['cross_wall_walk_3.25'])
  gap=(c[0][0]-b[1][0]) if side=='-3.25' else (b[0][0]-c[1][0])
  GUARDS.append({'walk_join':side,'signed_gap':gap,'pass':abs(gap)<1e-5})
 b=bounds(bpy.data.objects['walk_access_stair_9']);c=bounds(bpy.data.objects['side_wall_walk_3.25']);gap=c[0][0]-b[1][0]
 GUARDS.append({'access_stair_to_east_walk_signed_gap':gap,'pass':abs(gap)<1e-5})
 finalize(age)

def finalize(age):
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
 col=bpy.data.collections.new('BER_Marrakech_Age'+str(age));bpy.context.scene.collection.children.link(col)
 for o in objects:
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
  bm.to_mesh(o.data);bm.free();o.data.update();atlas(o);bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True);non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free();uv=o.data.uv_layers.active;areas=[]
  for p in o.data.polygons:
   a,b,c=[uv.data[i].uv for i in p.loop_indices];areas.append(abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2)
  checks.append({'object':o.name,'triangles':len(o.data.polygons),'non_manifold_edges':non,'degenerate_faces':deg,'signed_volume':vol,'minimum_uv_triangle_area':min(areas),'positive_transform':o.matrix_world.determinant()>0,'finite_geometry':all(math.isfinite(t) for v in o.data.vertices for t in v.co)})
 bpy.context.view_layer.update();bs=[bounds(o) for o in objects];lo=[min(b[0][k] for b in bs) for k in range(3)];hi=[max(b[1][k] for b in bs) for k in range(3)]
 assert all(c['non_manifold_edges']==0 and c['degenerate_faces']==0 and c['signed_volume']>0 and c['minimum_uv_triangle_area']>1e-10 and c['positive_transform'] and c['finite_geometry'] for c in checks),checks
 assert all(c['pass'] for c in g.CONTACTS),g.CONTACTS
 assert all(c['pass'] for c in GUARDS),GUARDS
 assert lo[0]>=-4 and lo[1]>=-4 and hi[0]<=4 and hi[1]<=4 and abs(lo[2])<1e-6,(lo,hi)
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':g.CONTACTS,'void_guards':GUARDS,'site_footprint':[8,8],'mesh_bounds':[lo,hi],'footprint_pass':True,'ground_z':lo[2]},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'parts':g.PARTS,'assignment':'cumulative first visible percentage','construction_age':2 if age==3 else None,'construction_age2_source':'completed age3','game_binding_status':'pending'},indent=2))
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Marrakech_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
 sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 bpy.ops.object.camera_add(location=(8,-10,9));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=11.5;target=Vector((0,0,2.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-8,-12,20));bpy.context.object.data.energy=3000;bpy.context.object.data.size=10
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Marrakech_Age{age}.blend'));sc.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
 sc.cycles.samples=2;sc.render.resolution_x=384;sc.render.resolution_y=384
 for name,loc in [('front',(0,-12,1.5)),('back',(0,12,1.5)),('left',(-12,0,1.5)),('right',(12,0,1.5)),('top',(0,0,12)),('bottom',(0,0,-12))]:
  cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 for o in objects:
  if 'roof' in o.name or 'parapet' in o.name:o.hide_render=True
 cam.location=(8,-10,11);cam.rotation_euler=(Vector((0,1,0.7))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age{age}_interior.png');bpy.ops.render.render(write_still=True)
 for o in objects:o.hide_render=False
 print('MARRAKECH_AGE_DONE',age,flush=True)
def donor():
 ctx=g.reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());groups=[]
 for group in d['geometry']['groups']:
  vs=group['positions'];fs=group.get('triangles',group.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched decoded Malian landmark 2b positions/topology';groups.append({'name':o.name,'bounds':bounds(o)})
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Malian_Landmark2b_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':groups,'geometry_reused':False,'render_bounds_are_footprint':False},indent=2))
try:
 donor()
 for age in [3,4]:build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[3,4],'cook':False,'native_owner_colour':'blocked integration pending'}))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

