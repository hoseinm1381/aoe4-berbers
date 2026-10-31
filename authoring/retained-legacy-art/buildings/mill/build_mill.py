"""Original Maghrebi food courtyard. Task-owned GUI Blender only; no production cook."""
import sys,os,json,math,traceback,bmesh,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
import geometry_helpers as H
ART=H.ART;OUT=H.OUT;RES=H.RESEARCH

def cylinder(name,xy,z,r,h,mat,stage=80):
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=h,location=(*xy,z+h/2));return H.finish(bpy.context.object,name,mat,stage)
def render(name,loc,target=(0,0,1),scale=5.4,size=768):
 s=bpy.context.scene;c=s.camera;c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.resolution_x=size;s.render.resolution_y=size;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
def presentation():
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.world=bpy.data.worlds.new('Neutral studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.60,.66,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
 bpy.ops.object.camera_add();s.camera=bpy.context.object;s.camera.data.type='ORTHO'
 bpy.ops.object.light_add(type='AREA',location=(-3,-4,7));bpy.context.object.data.energy=700;bpy.context.object.data.size=5
def bounds(o):
 pts=[o.matrix_world@Vector(p) for p in o.bound_box];return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
def donor():
 ctx=H.reset_scene();d=json.loads((RES/'stock/302b5a88237b7349e9b3/decoded-static.json').read_text());allpts=[]
 for g in d['geometry']['groups']:
  vs=g['positions'];fs=g.get('triangles',g.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(g['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched decoded installed stock positions/indices';allpts.extend(vs)
 lo=[min(p[k] for p in allpts) for k in range(3)];hi=[max(p[k] for p in allpts) for k in range(3)];(RES/'donor_bounds.json').write_text(json.dumps({'bounds': [lo,hi],'warning':'all decoded parts/LODs; render geometry bounds are not gameplay footprint'},indent=2))
 presentation();target=tuple((a+b)/2 for a,b in zip(lo,hi));scale=max(hi[k]-lo[k] for k in range(3))*1.25
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTOUCHED_Malian_Mill_Age1_Reference.blend'));render('stock_donor',tuple(target[k]+(6,-8,6)[k] for k in range(3)),target,scale)
def build(age):
 ctx=H.reset_scene();H.PARTS.clear();H.CONTACTS.clear();H.MATS.clear();H.setup_maps();b=H.box
 wall='earth' if age<3 else 'lime';h=1.40+.13*age
 b('courtyard_foundation',(0,0,.09),(3.8,3.8,.18),'stone',0)
 b('courtyard_floor',(0,0,.19),(3.68,3.68,.02),'earth',0)
 # Rear grain cells flank a real opening; courtyard remains front-accessible.
 b('store_backwall',(0,1.62,.20+h/2),(3.5,.26,h),wall,40)
 b('store_westwall',(-1.62,1.07,.20+h/2),(.26,1.10,h),wall,40)
 b('store_eastwall',(1.62,1.07,.20+h/2),(.26,1.10,h),wall,40)
 b('store_divider',(0,1.08,.20+h/2),(.16,1.02,h),wall,40)
 for x in [-1.05,1.05]:
  w=b('store_front', (x,.53,.20+h/2),(1.4,.22,h),wall,40);H.cut_portal(w,x,.42,.20,.61,1.16)
  b('store_roof',(x,1.07,.20+h+.04),(1.73,1.42,.08),'earth',60)
  b('roof_back_parapet',(x,1.73,.20+h+.17),(1.73,.10,.26),wall,80)
  b('roof_front_parapet',(x,.41,.20+h+.17),(1.73,.10,.26),wall,80)
  b('grain_sill',(x,.35,.235),(.76,.16,.07),'stone',60)
 b('owner_granary_strip',(1.05,.398,.20+h-.13),(1.0,.025,.14),'owner_cloth',100)
 # Open-sided grinding shelter; stone seat and runner touch exact z=.63.
 base=cylinder('millstone_bed',(-.70,-.62),.20,.51,.43,'stone',40)
 runner=cylinder('rotary_runner',(-.70,-.62),.63,.45,.15,'stone',80)
 # Cut the feed eye into the runner, seat a fitted shallow hopper on it.
 cutter=cylinder('TEMP_feed_eye',(-.70,-.62),.60,.09,.23,'shadow',80)
 bpy.context.view_layer.objects.active=runner;mod=runner.modifiers.new('through feed eye','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True);H.PARTS.pop()
 b('mill_handle',(-.34,-.62,.865),(.055,.055,.17),'cedar',80)
 b('meal_trough',(-.70,-1.18,.28),(.70,.24,.16),'cedar',80)
 # Trough has actual open pocket, not a painted solid block.
 trough=bpy.data.objects['meal_trough'];cut=b('TEMP_trough',(-.70,-1.18,.34),(.60,.16,.15),'shadow',80);bpy.context.view_layer.objects.active=trough;mo=trough.modifiers.new('hollow collection trough','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cut;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cut,do_unlink=True);H.PARTS.pop()
 canopy=1.50+.08*age
 for x in [-1.40,.0]:
  for y in [-1.40,.15]:b('shade_post',(x,y,.20+(canopy-.20)/2),(.08,.08,canopy-.20),'cedar',20)
 for y in [-1.40,.15]:b('shade_crossbeam',(-.70,y,canopy-.035),(1.52,.10,.07),'cedar',60)
 b('woven_shade',(-.70,-.625,canopy+.02),(1.62,1.77,.04),'straw',80)
 b('owner_shade_valance',(-.70,-1.505,canopy-.095),(1.58,.025,.20),'owner_cloth',100)
 for x in [.73,1.34]:
  cylinder('grain_sack',(x,-.47),.20,.22,.47,'straw',100);cylinder('sack_tied_neck',(x,-.47),.67,.12,.06,'cedar',100)
 if age>=2:
  for x in [-1.62,1.62]:b('corner_stone',(x,1.05,.40),(.30,1.30,.40),'stone',20)
  for x in [.65,1.20]:b('raised_storage_bin',(x,-1.19,.40),(.45,.38,.40),'cedar',80)
 if age>=3:
  for x in [-1.05,1.05]:
   b('lime_roof_cap',(x,1.07,.20+h+.09),(1.76,1.45,.04),'lime',80)
   for xx in [x-.47,x,x+.47]:b('timber_roof_drain',(xx,1.84,.20+h+.02),(.09,.38,.075),'cedar',80)
 if age>=4:
  for x in [-1.60,1.60]:
   for z in [.53,.89,1.25]:b('stone_quoin',(x,.42,z),(.26,.055,.15),'stone',80)
  for x in [-1.45,-1.05,-.65,.65,1.05,1.45]:
   o=b('geometric_plaster_mark',(x,.394,.20+h-.40),(.115,.025,.115),'earth',100);o.rotation_euler.y=math.pi/4
 # Planar projection per face: positive UV triangle area without modulo seams.
 objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.context.view_layer.update();checks=[]
 for o in objs:
  uv=o.data.uv_layers.active;slot=H.MATS[o['ber_material_role']][1]
  for p in o.data.polygons:
   ax=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=ax];co=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];lo=[min(v[k] for v in co) for k in axes];hi=[max(v[k] for v in co) for k in axes]
   for i,v in zip(p.loop_indices,co):uv.data[i].uv=((slot%4+.06+.88*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.06+.88*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));vol=bm.calc_volume(signed=True)
  if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));vol=-vol
  nm=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.to_mesh(o.data);bm.free();o.data.calc_loop_triangles();uv=o.data.uv_layers.active;areas=[]
  for t in o.data.loop_triangles:
   a,c,d=[uv.data[i].uv for i in t.loops];areas.append(abs((c-a).cross(d-a))*.5)
  checks.append({'object':o.name,'non_manifold':nm,'degenerate':deg,'outward_signed_volume':vol,'finite':all(math.isfinite(v) for p in o.data.vertices for v in p.co),'positive_scale':all(v>0 for v in o.scale),'minimum_uv_triangle_area':min(areas),'triangles':len(areas)})
 assert all(c['non_manifold']==0 and c['degenerate']==0 and c['outward_signed_volume']>0 and c['finite'] and c['positive_scale'] and c['minimum_uv_triangle_area']>1e-10 for c in checks),checks
 contacts=[]
 for child,parent,axis,cs,ps,expected in [('millstone_bed','courtyard_floor',2,0,1,0),('rotary_runner','millstone_bed',2,0,1,0),('mill_handle','rotary_runner',2,0,1,0),('store_backwall','courtyard_floor',2,0,1,0),('woven_shade','shade_crossbeam',2,0,1,0),('shade_post','courtyard_floor',2,0,1,0)]:
  gap=bounds(bpy.data.objects[child])[cs][axis]-bounds(bpy.data.objects[parent])[ps][axis];contacts.append({'interface':child+' to '+parent,'signed_gap':round(gap,6),'expected':expected,'pass':abs(gap-expected)<1e-5})
 assert all(c['pass'] for c in contacts),contacts
 envelope=[[min(bounds(o)[0][k] for o in objs) for k in range(3)],[max(bounds(o)[1][k] for o in objs) for k in range(3)]]
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':contacts,'geometry_bounds':envelope,'gameplay_footprint':[4,4],'front_access_clear_corridor':{'x':[.18,.46],'y':[-1.9,.4],'minimum_width':.28,'note':'visual court passage; native drop-off/pathing unchanged pending integration'},'uv':'shared material-tile atlas, deliberate same-surface overlap'},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'cumulative':True,'parts':H.PARTS,'native_binding':'pending'},indent=2))
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Mill_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 presentation();render(f'age{age}_preview',(6,-8,6));bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Mill_Age{age}.blend'))
 for name,loc in [('front',(0,-8,1)),('back',(0,8,1)),('left',(-8,0,1)),('right',(8,0,1)),('top',(0,0,9)),('bottom',(0,0,-8))]:render(f'age{age}_{name}',loc,size=384)
 print('MILL_DONE',age,flush=True)
try:
 if not (ART/'UNTOUCHED_Malian_Mill_Age1_Reference.blend').exists():donor()
 for age in range(1,5):build(age)
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
