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
  im=bpy.data.images.new('Ribat_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
 floor=.15;h=1.65+(age-2)*.15;top=floor+h
 box('foundation',(0,0,.075),(5.8,5.8,.15),'stone',0)
 # Outer enclosure and open central court; inhabited cells instead of Keep mass.
 back=box('rear_devotional_hall',(0,2.53,floor+h/2),(5.45,.24,h),'earth',40);contact(back.name,'foundation')
 front=box('south_single_entry_wall',(0,-2.53,floor+h/2),(5.45,.24,h),'earth',40);arch(front,0,-2.53,.95,1.50);contact(front.name,'foundation')
 for x in [-2.60,2.60]:
  n='outer_cell_wall_'+str(x);box(n,(x,0,floor+h/2),(.24,4.82,h),'earth',40);contact(n,'foundation')
  inner=box('cell_arcade_'+str(x),(x*.53,0,floor+h/2),(.20,3.82,h),'lime' if age>2 else 'earth',40)
  for y in [-1.22,0,1.22]:arch(inner,y,-x*.53,.86,1.4,side=True)
  contact(inner.name,'foundation')
  for y in [-1.88,-.61,.61,1.88]:
   n='cell_partition_'+str((x,y));box(n,(x*.77,y,floor+h/2),(1.05,.12,h),'earth',40);contact(n,'foundation')
  roof('cells_flat_roof_'+str(x),x*.77,0,1.46,4.96,top,age)
  contact('cells_flat_roof_'+str(x),n)
 # Northern assembly hall arcade is connected to side rooms, roof has real supports.
 arcade=box('council_hall_arcade',(0,1.8,floor+h/2),(2.76,.20,h),'lime',40)
 for x in [-.88,0,.88]:arch(arcade,x,1.8,.66,1.4)
 contact(arcade.name,'foundation');roof('council_roof',0,2.17,2.544,.96,top,age);contact('council_roof',arcade.name)
 # Small attached square watchtower; no central donjon or Keep siege silhouette.
 tx,ty=2.0,-2.05;towerh=3.15+(age-2)*.35
 tower=box('attached_signal_watchtower',(tx,ty,floor+towerh/2),(1.12,1.15,towerh),'earth',40);contact(tower.name,'foundation')
 roof('watchtower_flat_cap',tx,ty,1.30,1.33,floor+towerh,age);contact('watchtower_flat_cap',tower.name)
 for z in [2.35,2.80]:box('tower_owner_stripe',(tx,ty-.585,z),(.74,.018,.16),'owner_cloth',100)
 for x in [-1.1,1.1]:box('entry_owner_stripe',(x,-2.655,1.12),(.22,.02,.64),'owner_cloth',100)
 # Courtyard well and seated council benches give use and scale.
 g.tube('courtyard_well',(0,0,.32),.29,.34,'stone',80);contact('courtyard_well','foundation')
 for x in [-.8,.8]:box('council_bench',(x,2.2,.31),(.65,.28,.32),'cedar',80);contact(bpy.context.object.name,'foundation')
 if age>=3:
  for x in [-2.61,2.61]:box('limestone_corner_coping',(x,1.95,top-.10),(.28,.56,.18),'lime',80)
  for x in [-1.05,1.05]:box('entry_stone_pier',(x,-2.68,.93),(.25,.12,1.56),'lime',80)
 if age==4:
  for y in [-1.2,0,1.2]:box('gallery_geometric_frieze',(-1.49,y,top-.2),(.045,.47,.16),'clay',100)
  for x in [-.95,.95]:box('carved_entry_panel',(x,-2.755,1.43),(.18,.03,.18),'clay',100)
  for x in [-2.67,2.67]:box('cedar_roof_drain',(x,1.1,top+.025),(.36,.09,.09),'cedar',80)
 finalize(age)
def finalize(age):
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
 col=bpy.data.collections.new('BER_Ribat_Age'+str(age));bpy.context.scene.collection.children.link(col)
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
 assert lo[0]>=-3 and lo[1]>=-3 and hi[0]<=3 and hi[1]<=3 and abs(lo[2])<1e-6,(lo,hi)
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':g.CONTACTS,'void_guards':GUARDS,'site_footprint':[6,6],'mesh_bounds':[lo,hi],'footprint_pass':True,'ground_z':lo[2]},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'parts':g.PARTS,'assignment':'cumulative first visible percentage','construction_age':1 if age==2 else None,'construction_age1_source':'completed age2','game_binding_status':'pending'},indent=2))
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Ribat_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
 sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 bpy.ops.object.camera_add(location=(8,-10,9));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=8.3;target=Vector((0,0,1.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-8,-12,20));bpy.context.object.data.energy=3000;bpy.context.object.data.size=10
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Ribat_Age{age}.blend'));sc.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
 sc.render.resolution_x=384;sc.render.resolution_y=384
 for name,loc in [('front',(0,-12,1.5)),('back',(0,12,1.5)),('left',(-12,0,1.5)),('right',(12,0,1.5)),('top',(0,0,12)),('bottom',(0,0,-12))]:
  cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 print('RIBAT_AGE_DONE',age,flush=True)
def donor():
 ctx=g.reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());groups=[]
 for group in d['geometry']['groups']:
  vs=group['positions'];fs=group.get('triangles',group.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched decoded Malian landmark 1a positions/topology';groups.append({'name':o.name,'bounds':bounds(o)})
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Malian_Landmark1a_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':groups,'geometry_reused':False,'render_bounds_are_footprint':False},indent=2))
try:
 donor()
 for age in [2,3,4]:build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'cook':False,'native_owner_colour':'blocked integration pending'}))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

