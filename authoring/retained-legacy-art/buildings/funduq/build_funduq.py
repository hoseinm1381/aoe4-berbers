"""Original grand Sijilmasa caravan inn, ages II-IV. No mod edits."""
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
  im=bpy.data.images.new('Funduq_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
 floor=.16;low=1.80;upper=1.62+(age-2)*.12;deck=floor+low;top=deck+.12+upper;mat='earth' if age==2 else 'lime'
 box('foundation',(0,0,.08),(7.70,7.70,.16),'stone',0)
 # Grand four-wing inn with a real 3.5-square open trading court.
 for side,x in [('west',-3.56),('east',3.56)]:
  wall=box(side+'_outer_wall',(x,0,floor+(top-floor)/2),(.24,6.88,top-floor),mat,40);contact(wall.name,'foundation')
 for side,y in [('south',-3.56),('north',3.56)]:
  wall=box(side+'_outer_wall',(0,y,floor+(top-floor)/2),(7.36,.24,top-floor),mat,40);contact(wall.name,'foundation')
  if side=='south':arch(wall,0,y,2.10,2.82)
 # Continuous inward arcades support the upper galleries; stock room door recesses cut out.
 for side,x in [('west',-1.90),('east',1.90)]:
  arcade=box(side+'_ground_arcade',(x,0,floor+low/2),(.20,5.48,low),mat,40);contact(arcade.name,'foundation')
  for y in [-1.8,-.6,.6,1.8]:arch(arcade,y,-x,.92,1.66,side=True)
  deckob=box(side+'_gallery_floor',((x+(-3.56 if x<0 else 3.56))/2,0,deck+.06),(1.90,7.36,.12),'cedar',60);contact(deckob.name,arcade.name)
  outerroom=box(side+'_merchant_room_front',(x+(-.66 if x<0 else .66),0,deck+.12+upper/2),(.16,6.94,upper),mat,60);contact(outerroom.name,deckob.name)
  for y in [-2.4,-1.2,0,1.2,2.4]:arch(outerroom,y,-(x+(-.66 if x<0 else .66)),.46,1.20,base=deck+.12,side=True)
  for y in [-3,-1.8,-.6,.6,1.8,3]:
   part=box(side+'_room_divider',((x+(-3.56 if x<0 else 3.56))/2+(-.20 if x<0 else .20),y,deck+.12+upper/2),(1.16,.10,upper),mat,60);contact(part.name,deckob.name)
  roof(side+'_roof',(-2.73 if x<0 else 2.73),0,1.90,7.36,top,age);contact(side+'_roof',outerroom.name)
  # Gallery balustrade: seated on the continuous floor, never a floating stripe.
  for y in [-2.4,-1.2,0,1.2,2.4]:
   post=box(side+'_gallery_post',(x,y,deck+.12+.34),(.09,.09,.68),'cedar',80);contact(post.name,deckob.name)
  box(side+'_gallery_rail',(x,0,deck+.12+.68),(.10,5.48,.08),'cedar',80)
 for side,y in [('north',2.78),('south',-2.78)]:
  arcade=box(side+'_ground_arcade',(0,y+(-.80 if y>0 else .80),floor+low/2),(3.64,.20,low),mat,40);contact(arcade.name,'foundation')
  if side=='south':arch(arcade,0,-1.98,2.10,2.82)
  else:
   for x in [-1.2,0,1.2]:arch(arcade,x,1.98,.86,1.66)
  slab=box(side+'_gallery_floor',(0,y,deck+.06),(3.64,1.76,.12),'cedar',60);contact(slab.name,arcade.name)
  front=box(side+'_merchant_rooms',(0,y+.30,deck+.12+upper/2),(3.64,.18,upper),mat,60);contact(front.name,slab.name)
  for x in [-1.2,1.2]:arch(front,x,y+.30,.48,1.2,base=deck+.12)
  if side=='north':arch(front,0,y+.30,.48,1.2,base=deck+.12)
  else:
   arch(front,0,y+.30,2.10,2.82)
   c=box('TEMP_gate_gallery_void',(0,y,deck+.06),(2.18,2.1,.30),'shadow',60)
   bpy.context.view_layer.objects.active=slab;mo=slab.modifiers.new('caravan gateway through upper deck','BOOLEAN');mo.operation='DIFFERENCE';mo.object=c;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(c,do_unlink=True);g.PARTS.pop()
  roof(side+'_roof',0,y,3.56,1.80,top,age);contact(side+'_roof',front.name)
  for x in ([-1.45,-.75,0,.75,1.45] if side=='north' else [-1.45,1.45]):
   post=box(side+'_gallery_post',(x,y+(-.76 if y>0 else .76),deck+.12+.34),(.09,.09,.68),'cedar',80);contact(post.name,slab.name)
  if side=='north':box(side+'_gallery_rail',(0,y-.76,deck+.12+.68),(3.56,.10,.08),'cedar',80)
  else:
   for x in [-1.46,1.46]:box(side+'_gallery_rail',(x,y+.76,deck+.12+.68),(.64,.10,.08),'cedar',80)
 # Actual external shutter recesses punctuate the upper guest-room facade.
 for side,x in [('west',-3.56),('east',3.56)]:
  wall=bpy.data.objects[side+'_outer_wall'];sign=-1 if x<0 else 1
  for y in [-2.4,-1.2,0,1.2,2.4]:
   zz=deck+.12+upper*.56
   c=box('TEMP_shutter_recess',(sign*3.65,y,zz),(.18,.40,.58),'shadow',60)
   bpy.context.view_layer.objects.active=wall;mo=wall.modifiers.new('actual guest room shutter recess','BOOLEAN');mo.operation='DIFFERENCE';mo.object=c;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(c,do_unlink=True);g.PARTS.pop()
   box(side+'_fitted_room_shutter',(sign*3.60,y,zz),(.04,.38,.56),'cedar',80)
   box(side+'_window_sill',(sign*3.67,y,zz-.32),(.20,.48,.06),'stone',80)
 for y in [-3.56,3.56]:
  wall=bpy.data.objects['south_outer_wall' if y<0 else 'north_outer_wall'];sign=-1 if y<0 else 1
  for x in [-2.75,-1.4,1.4,2.75]:
   zz=deck+.12+upper*.56
   c=box('TEMP_shutter_recess',(x,sign*3.65,zz),(.40,.18,.58),'shadow',60)
   bpy.context.view_layer.objects.active=wall;mo=wall.modifiers.new('actual guest room shutter recess','BOOLEAN');mo.operation='DIFFERENCE';mo.object=c;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(c,do_unlink=True);g.PARTS.pop()
   box('fitted_room_shutter',(x,sign*3.60,zz),(.38,.04,.56),'cedar',80)
   box('window_stone_sill',(x,sign*3.67,zz-.32),(.48,.20,.06),'stone',80)
 # Broad loaded-animal entry: actual arch cut through both wall/arcade, clear center route.
 for x in [-1.22,1.22]:
  pier=box('gateway_stone_pier',(x,-3.71,1.58),(.30,.20,2.84),'stone',40);contact(pier.name,'foundation')
  box('gateway_owner_hanging_cloth',(x,-3.825,2.28),(.22,.024,1.04),'owner_cloth',100)
 box('gateway_carved_head',(0,-3.72,3.17),(2.76,.18,.28),'earth' if age==2 else 'lime',80)
 # Permanent cloth awnings cover only the side unloading bays, leave court open to sky.
 for x in [-1.78,1.78]:
  for y in [-1.42,1.42]:
   p=box('awning_post',(x,y,floor+.70),(.08,.08,1.40),'cedar',20);contact(p.name,'foundation')
  box('unloading_owner_awning',(x,0,1.59),(.60,2.92,.055),'owner_cloth',80)
  box('awning_crossbeam',(x,0,1.55),(.09,2.94,.08),'cedar',60)
 # Physical steps against north arcade connect court to upper gallery.
 for i in range(8):
  height=(deck+.12-floor)*(i+1)/8
  step=box('gallery_access_stair',(-1.08,1.28+i*.17,floor+height/2),(.62,.17,height),'stone',60);contact(step.name,'foundation')
 # Merchant logistics: storage stacks, bale loading pads and tether rails seated to ground.
 for x in [-2.85,2.85]:
  for y in [-2.0,-.8,.4,1.6]:
   crate=box('warehouse_crate',(x,y,floor+.27),(.48,.58,.54),'cedar',80);contact(crate.name,'foundation')
   if age>=3:box('stacked_trade_bale',(x,y,floor+.69),(.40,.50,.30),'straw',100);contact(bpy.context.object.name,crate.name)
 for x in [-1.20,1.20]:
  p=box('court_loading_pallet',(x,.70,floor+.05),(.52,.72,.10),'cedar',60);contact(p.name,'foundation')
  bale=box('unloaded_court_bale',(x,.70,floor+.27),(.43,.64,.34),'straw',80);contact(bale.name,p.name)
 for x in [-1.36,1.36]:
  p=box('animal_tether_post',(x,-.70,floor+.38),(.11,.11,.76),'cedar',60);contact(p.name,'foundation')
  box('tether_crossbar',(x,-.40,floor+.65),(.08,.72,.08),'cedar',80)
 if age>=3:
  for x in [-3.56,3.56]:box('lime_gateway_corner_course',(x,-3.58,.46),(.30,.32,.60),'lime',40)
 if age==4:
  for x in [-.90,-.60,-.30,0,.30,.60,.90]:
   o=box('geometric_gateway_inlay',(x,-3.818,3.17),(.105,.025,.105),'clay',100);o.rotation_euler.y=math.pi/4
  for y in [-2,0,2]:
   for x in [-3.7,3.7]:box('roof_timber_drain',(x,y,top+.06),(.30,.10,.09),'cedar',80)
 finalize(age)

def finalize(age):
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
 col=bpy.data.collections.new('BER_Funduq_Age'+str(age));bpy.context.scene.collection.children.link(col)
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
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'parts':g.PARTS,'assignment':'cumulative first visible percentage','construction_age':1 if age==2 else None,'construction_age1_source':'completed age2','game_binding_status':'pending'},indent=2))
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Funduq_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
 sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 bpy.ops.object.camera_add(location=(8,-10,13));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=11.3;target=Vector((0,0,2.3));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-8,-12,20));bpy.context.object.data.energy=3000;bpy.context.object.data.size=10
 bpy.ops.object.light_add(type='AREA',location=(0,0,13));bpy.context.object.data.energy=1800;bpy.context.object.data.size=7
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Funduq_Age{age}.blend'));sc.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
 sc.render.resolution_x=384;sc.render.resolution_y=384
 for name,loc in [('front',(0,-12,1.5)),('back',(0,12,1.5)),('left',(-12,0,1.5)),('right',(12,0,1.5)),('top',(0,0,12)),('bottom',(0,0,-12))]:
  cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 print('FUNDUQ_AGE_DONE',age,flush=True)
def donor():
 ctx=g.reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());groups=[]
 for group in d['geometry']['groups']:
  vs=group['positions'];fs=group.get('triangles',group.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched decoded Malian landmark 1b positions/topology';groups.append({'name':o.name,'bounds':bounds(o)})
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Malian_Landmark1b_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':groups,'geometry_reused':False,'render_bounds_are_footprint':False},indent=2))
try:
 donor()
 for age in [2,3,4]:build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'cook':False,'native_owner_colour':'blocked integration pending'}))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

