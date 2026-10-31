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

def beam(name,a,b,width,mat='cedar',stage=60):
 mid=(Vector(a)+Vector(b))/2;o=H.box(name,mid,(width,width,(Vector(b)-Vector(a)).length),mat,stage);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o

def hollow(name,xy,z,size,mat='stone'):
 x,y=xy;w,d,h=size;o=H.box(name,(x,y,z+h/2),size,mat,80);c=H.box('TEMP_pocket',(x,y,z+h*.72),(w-.12,d-.12,h*.70),'shadow',80)
 bpy.context.view_layer.objects.active=o;mo=o.modifiers.new('actual open basin','BOOLEAN');mo.operation='DIFFERENCE';mo.object=c;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(c,do_unlink=True);H.PARTS.pop();return o

def rock(name,xy,z,r):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(*xy,z+r*.48));o=bpy.context.object;o.scale=(r,r*.8,r*.65);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return H.finish(o,name,'stone',100)

def build(age):
 ctx=H.reset_scene();H.PARTS.clear();H.CONTACTS.clear();H.MATS.clear();H.setup_maps();b=H.box
 wall='earth' if age<3 else 'lime';h=1.2+age*.10
 b('courtyard_foundation',(0,0,.09),(3.8,3.8,.18),'stone',0);b('courtyard_floor',(0,0,.19),(3.7,3.7,.02),'earth',0)
 # Grounded rear ore/supply store with true door recess.
 b('store_backwall',(.25,1.61,.20+h/2),(2.5,.22,h),wall,40)
 for x in [-.94,1.44]:b('store_sidewall',(x,1.145,.20+h/2),(.12,.71,h),wall,40)
 w=b('store_front',(.25,.69,.20+h/2),(2.50,.20,h),wall,40);H.cut_portal(w,.25,.59,.20,.68,1.16)
 b('store_roof',(.25,1.15,.20+h+.04),(2.64,1.12,.08),'earth',60)
 if age>=2:
  for yy in [.63,1.67]:b('store_parapet',(.25,yy,.20+h+.17),(2.64,.12,.26),wall,80)
  b('store_plinth',(.25,.577,.32),(2.50,.025,.24),'stone',60)
 if age>=3:
  for x in [-.70,1.20]:b('store_timber_drain',(x,1.76,.20+h+.025),(.12,.28,.07),'cedar',80)
 if age==4:
  for x in [-.90,1.40]:
   for zz in [.36,.63,.90,1.17]:b('stone_quoin',(x,.583,zz),(.18,.035,.14),'stone',80)
  b('store_geometric_band',(.25,.578,1.53),(2.3,.025,.12),'earth',100)
  for x in [-.72,-.40,-.08,.24,.56,.88,1.20]:
   o=b('lime_diamond',(x,.558,1.53),(.075,.02,.075),'lime',100);o.rotation_euler.y=math.pi/4
 # Accessible open-sided pitched sorting shelter on west court; structure slopes from real beam anchors.
 cx=-1.03;cy=-.47; eave=1.55+.05*age;ridge=eave+.42
 for xx in [-1.70,-.36]:
  for yy in [-1.30,.36]:b('shelter_post',(xx,yy,.20+(eave-.20)/2),(.11,.11,eave-.20),'cedar',20)
 for yy in [-1.30,.36]:
  b('front_crossbeam' if yy<0 else 'back_crossbeam',(cx,yy,eave),(1.56,.12,.12),'cedar',60)
  for xx in [-1.70,-.36]:beam('triangular_rafter',(xx,yy,eave+.03),(cx,yy,ridge),.095)
 b('ridge_pole',(cx,cy,ridge),( .09,1.94,.09),'cedar',60)
 # Thick closed slopes, with no open plane geometry. Soft reed age I, timber/slatted ages II onward.
 for side in [-1,1]:
  yfront=cy-.98;yback=cy+.98;xedge=cx+side*.85
  poly=[(cx,ridge+.065),(xedge,eave-.015),(xedge,eave-.08),(cx,ridge)]
  H.prism('fitted_reed_roof' if age==1 else 'timber_shelter_roof',poly,yfront,yback,'straw' if age==1 else 'cedar',80)
 b('owner_valance',(cx,-1.371,eave-.05),(1.58,.025,.22),'owner_cloth',100)
 # Sorting table seats exactly on plinth; small graded stone fragments demonstrate function.
 b('sorting_plinth',(-1.02,-.38,.37),(.86,.63,.34),'stone',40)
 b('sorting_slab',(-1.02,-.38,.58),(1.0,.78,.08),'stone',80)
 for i in range(7):rock('sorted_ore',(-1.30+i*.085,-.35+.075*(i%2)),.60,.08)
 # Actual hollow washing trough on east side and development into two-stage wash bank.
 hollow('washing_trough',(1.21,-.69),.20,(.80,1.23,.33),'cedar' if age<3 else 'stone')
 b('trough_sediment',(1.21,-.69,.30),(.65,1.08,.05),'earth',100)
 if age>=2:
  hollow('settling_basin',(1.25,.22),.20,(.67,.51,.23),'stone')
  b('interbasin_spout',(1.25,-.10,.40),(.15,.20,.08),'cedar',80)
 # Ore heap is separate faceted closed boulders grounded on the west rear court.
 for i in range(7+age*2):
  x=-1.75+.15*(i%3);y=.77+.19*(i//3);r=.13+.02*(i%3);rock('ore_heap',(x,y),.20,r)
 # Pick rack seated on east rear store wall; pick heads visibly attached to handles.
 b('pick_wall_rack',(1.03,.565,.90),(.56,.08,.09),'cedar',80)
 for x in [.83,1.03,1.23]:
  b('pick_handle',(x,.515,.91),(.035,.035,.70),'cedar',100);b('pick_iron_head',(x,.515,1.23),(.28,.045,.055),'shadow',100)
 b('owner_store_stripe',(-.42,.572,1.2),(.55,.024,.14),'owner_cloth',100)
 # Grounded divided crates increase supply capacity by age; no generic religious tower.
 for j in range(age):
  x=.72+(j%2)*.36;y=1.10+(j//2)*.29
  hollow('supply_crate',(x,y),.20,(.31,.26,.30),'cedar')
 if age>=3:
  b('washbank_earth_retainer',(1.74,-.36,.37),(.14,1.83,.34),wall,40)
 if age==4:
  # Timber lifting jib mounted on grounded pedestal over settling bank. Source only, static operation.
  b('jib_stone_base',(1.72,.45,.35),(.27,.27,.30),'stone',20)
  b('lifting_jib_post',(1.72,.45,1.10),(.095,.095,1.20),'cedar',60)
  beam('lifting_jib_arm',(1.72,.45,1.68),(.90,.45,1.68),.085)
  beam('lifting_jib_brace',(1.72,.45,1.10),(1.18,.45,1.68),.07)
  beam('jib_rope',(.91,.45,1.65),(.91,.45,.73),.025,'straw',100)
  hollow('ore_lifting_box',(.91,.45),.54,(.23,.23,.19),'cedar')
  b('basket_lifting_crossbar',(.91,.45,.715),(.24,.04,.03),'cedar',100)
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
 for child,parent,axis,cs,ps,expected in [('shelter_post','courtyard_floor',2,0,1,0),('sorting_slab','sorting_plinth',2,0,1,0),('washing_trough','courtyard_floor',2,0,1,0),('store_backwall','courtyard_floor',2,0,1,0),('owner_valance','front_crossbeam',2,1,1,0)]:
  gap=bounds(bpy.data.objects[child])[cs][axis]-bounds(bpy.data.objects[parent])[ps][axis];contacts.append({'interface':child+' to '+parent,'signed_gap':round(gap,6),'expected':expected,'pass':abs(gap-expected)<1e-5})
 assert all(c['pass'] for c in contacts),contacts
 envelope=[[min(bounds(o)[0][k] for o in objs) for k in range(3)],[max(bounds(o)[1][k] for o in objs) for k in range(3)]]
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':contacts,'geometry_bounds':envelope,'gameplay_footprint':[4,4],'front_access_clear_corridor':{'x':[-.10,.55],'y':[-1.9,.40],'minimum_width':.65,'note':'measured unobstructed visual passage; inherited native drop-off/pathing pending integration'},'uv':'shared material-tile atlas, deliberate same-surface overlap'},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'cumulative':True,'parts':H.PARTS,'native_binding':'pending'},indent=2))
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Mining_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 presentation();render(f'age{age}_preview',(6,-8,6));bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Mining_Age{age}.blend'))
 for name,loc in [('front',(0,-8,1)),('back',(0,8,1)),('left',(-8,0,1)),('right',(8,0,1)),('top',(0,0,9)),('bottom',(0,0,-8))]:render(f'age{age}_{name}',loc,size=384)
 print('MINING_DONE',age,flush=True)

try:
 for age in range(1,5):build(age)
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
