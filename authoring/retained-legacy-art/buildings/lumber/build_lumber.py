"""Original Maghrebi timber sorting yard. Source only, isolated Blender runner."""
import sys,json,math,traceback,bmesh,bpy
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
import geometry_helpers as H
ART=H.ART;OUT=H.OUT;RES=H.RESEARCH
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]
def render(name,loc,target=(0,0,1),scale=5.3,size=768):
 s=bpy.context.scene;c=s.camera;c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.resolution_x=size;s.render.resolution_y=size;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
def presentation():
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.world=bpy.data.worlds.new('Neutral studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.60,.66,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
 bpy.ops.object.camera_add();s.camera=bpy.context.object;s.camera.data.type='ORTHO'
 bpy.ops.object.light_add(type='AREA',location=(-3,-4,7));bpy.context.object.data.energy=700;bpy.context.object.data.size=5
def donor():
 ctx=H.reset_scene();d=json.loads(next((RES/'stock').glob('*/decoded-static.json')).read_text());pts=[]
 for g in d['geometry']['groups']:
  vs=g['positions'];fs=g.get('triangles',g.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(g['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched stock positions and indices; no reconstructed materials';pts.extend(vs)
 lo=[min(v[k] for v in pts) for k in range(3)];hi=[max(v[k] for v in pts) for k in range(3)];(RES/'donor_bounds.json').write_text(json.dumps({'bounds':[lo,hi],'scope':'render geometry not gameplay footprint'},indent=2))
 presentation();target=tuple((a+b)/2 for a,b in zip(lo,hi));scale=max(hi[k]-lo[k] for k in range(3))*1.4
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTOUCHED_Common_Lumber_Crane_Age1_Reference.blend'));render('stock_donor',tuple(target[k]+(6,-8,6)[k] for k in range(3)),target,scale)
def log(name,x,y,z,r,length,stage=100):
 bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=length,location=(x,y,z),rotation=(math.pi/2,0,0));o=bpy.context.object;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);H.finish(o,name,'cedar',stage)
 # seated pale cut-end disks make sawn timber legible at game distance
 for yy in [y-length/2-.002,y+length/2+.002]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r*.92,depth=.008,location=(x,yy,z),rotation=(math.pi/2,0,0));o=bpy.context.object;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);H.finish(o,'sawn_endgrain','straw',stage)
def build(age):
 ctx=H.reset_scene();H.PARTS.clear();H.CONTACTS.clear();H.MATS.clear();H.setup_maps();b=H.box
 # Foundation is a level datum; pit interior stays above z=0, no false terrain hole.
 b('yard_foundation',(0,0,.06),(3.8,3.8,.12),'earth',0)
 wall='earth' if age<3 else 'lime'; eave=1.6+.1*age
 # Rear open shelter, all posts seat on real foundation/pad surfaces.
 for x in [-1.55,1.55]:
  for y in [.60,1.55]:
   b('post_stone_pad',(x,y,.18),(.25,.25,.12),'stone',20)
   b('shelter_post',(x,y,.24+(eave-.24)/2),(.10,.10,eave-.24),'cedar',20)
 for y in [.60,1.55]:b('shelter_eave_beam',(0,y,eave+.05),(3.3,.13,.10),'cedar',60)
 # Closed pitched timber canopy, assembly ends touch eave top at eave+.10.
 roof=H.prism('covered_tool_roof',[(-1.75,eave+.10),(1.75,eave+.10),(1.75,eave+.16),(0,eave+.58),(-1.75,eave+.16)],.47,1.72,'straw' if age<3 else 'cedar',80)
 b('owner_front_roof_valance',(0,.455,eave+.04),(3.45,.025,.18),'owner_cloth',100)
 b('tool_rack_backrail',(0,1.58,1.1),(3.12,.07,.13),'cedar',60)
 for x in [-1.30,-.78,-.26,.26,.78,1.3]:
  b('hanging_tool_handle',(x,1.52,.83),(.045,.045,.54),'cedar',80)
  b('iron_adze_head',(x,1.485,1.075),(.17,.06,.085),'stone',80)
 b('tool_bench_top',(0,1.16,.65),(2.50,.49,.10),'cedar',60)
 for x in [-1.10,1.10]:
  for y in [.985,1.335]:b('bench_leg',(x,y,.36),(.085,.085,.48),'cedar',20)
 b('bench_owner_paint_band',(0,.909,.653),(2.4,.018,.045),'owner_cloth',100)
 # Sawpit: continuous raised masonry sides around a genuine empty interior.
 b('pit_bottom',(-.46,-.48,.135),(.96,1.65,.03),'shadow',0)
 for x in [-.94,.02]:b('pit_side',(x,-.48,.27),(.10,1.65,.30),wall,40)
 for y in [-1.255,.295]:b('pit_end',(-.46,y,.27),(.86,.10,.30),wall,40)
 # Plank walkways along rim; bridge log lies on cross-bearers exactly.
 for x in [-.94,.02]:b('pit_rim_plank',(x,-.48,.4475),(.22,1.85,.055),'cedar',60)
 for y in [-1.02,.10]:b('sawpit_cross_bearer',(-.46,y,.5125),(1.2,.12,.075),'cedar',60)
 log('sawpit_work_log',-.46,-.46,.68,.13,1.6)
 b('frame_saw_blade',(-.46,-.70,.565),(.018,.055,.23),'stone',100)
 for x in [-.73,-.19]:b('frame_saw_upright',(x,-.70,.75),(.045,.055,.48),'cedar',100)
 for z in [.525,.975]:b('frame_saw_crossbar',(-.46,-.70,z),(.58,.055,.045),'cedar',100)
 # Right side sorting rack; corridor between stack and pit stays clear.
 for y in [-1.15,-.10]:b('stack_dunnage',(1.22,y,.19),(1.13,.12,.14),'cedar',20)
 for level in range(2+age//2):
  for x in [1.0,1.30,1.60]:log('sorted_timber',x,-.59,.40+level*.28,.14,1.3)
 for x in [.82,1.78]:b('stack_retaining_post',(x,-.05,.62),(.075,.075,1.0),'cedar',60)
 # Offcut sorting ledge on left perimeter, grounded and open at front.
 b('offcut_sorting_bin',(-1.53,-.18,.22),(.42,1.0,.20),'cedar',40)
 for y in [-.52,-.25,.02]:b('offcut_board',(-1.53,y,.345),(.34,.12,.05),'straw',100)
 if age>=2:
  b('rear_low_masonry',(0,1.61,.42),(2.9,.17,.6),wall,40)
  for x in [-1.55,1.55]:b('developed_post_foot',(x,.60,.29),(.30,.30,.1),'stone',40)
 if age>=3:
  for x in [-1.55,1.55]:
   b('shelter_stone_pier',(x,1.55,.57),(.32,.32,.90),'lime',40)
  for x in [-1.10,1.10]:b('joinery_wedge',(x,.52,eave+.05),(.18,.05,.075),'straw',100)
 if age==4:
  b('carved_front_fascia',(0,.43,eave+.145),(3.30,.05,.07),'lime',100)
  for x in [-1.4,-1.0,-.6,.6,1.0,1.4]:
   o=b('restrained_diamond_joinery',(x,.399,eave+.145),(.047,.015,.047),'cedar',100);o.rotation_euler.y=math.pi/4
  for x in [-1.53]:
   for y in [.0,.25]:b('seasoned_board', (x,y,.42),(.35,.20,.06),'straw',100)
 # Independent closed-volume, finite, UV and positive-transform proof.
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
 for child,parent,axis,cs,ps,expected in [('post_stone_pad','yard_foundation',2,0,1,0),('shelter_post','post_stone_pad',2,0,1,0),('shelter_eave_beam','shelter_post',2,0,1,0),('covered_tool_roof','shelter_eave_beam',2,0,1,0),('tool_bench_top','bench_leg',2,0,1,0),('pit_side','yard_foundation',2,0,1,0),('pit_rim_plank','pit_side',2,0,1,0),('sawpit_cross_bearer','pit_rim_plank',2,0,1,0),('sawpit_work_log','sawpit_cross_bearer',2,0,1,0)]:
  gap=bounds(bpy.data.objects[child])[cs][axis]-bounds(bpy.data.objects[parent])[ps][axis];contacts.append({'interface':child+' to '+parent,'signed_gap':round(gap,6),'expected':expected,'pass':abs(gap-expected)<1e-5})
 assert all(c['pass'] for c in contacts),contacts
 envelope=[[min(bounds(o)[0][k] for o in objs) for k in range(3)],[max(bounds(o)[1][k] for o in objs) for k in range(3)]]
 assert envelope[0][2]>=-1e-6 and all(envelope[0][k]>=-2 and envelope[1][k]<=2 for k in range(2))
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':contacts,'geometry_bounds':envelope,'gameplay_footprint':[4,4],'front_apron':{'x':[-1.9,1.9],'y':[-1.9,-1.405],'depth':.495},'pit_sorting_corridor':{'x':[.14,.655],'minimum_width':.515,'scope':'visual passage only, inherited native pathing pending'},'fitted_openings':{'pit_interior':{'x':[-.89,-.03],'y':[-1.205,.245],'z':[.15,.42]},'access':'open sided shelter and open front yard; no door insert'},'uv':'per-face projection to shared repeating material tiles, deliberate overlap'},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'cumulative':True,'parts':H.PARTS,'native_binding':'pending'},indent=2))
 for name,rgb in [('roughness',(.85,.85,.85)),('normal',(.5,.5,1)),('metal',(0,0,0))]:
  im=bpy.data.images.new('Lumber_'+name,width=256,height=256,alpha=True);im.use_fake_user=True;im.colorspace_settings.name='Non-Color';im.pixels.foreach_set([*rgb,1]*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack()
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Lumber_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 presentation();render(f'age{age}_preview',(6,-8,6));bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Lumber_Age{age}.blend'))
 for name,loc in [('front',(0,-8,1)),('back',(0,8,1)),('left',(-8,0,1)),('right',(8,0,1)),('top',(0,0,9)),('bottom',(0,0,-8))]:render(f'age{age}_{name}',loc,size=384)
 print('LUMBER_DONE',age,flush=True)
try:
 donor()
 for age in range(1,5):build(age)
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

