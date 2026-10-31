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
  im=bpy.data.images.new('Tlemcen_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
 floor=.15;h=2.1+(age-3)*.12;top=floor+h
 box('foundation',(0,0,.075),(7.7,7.7,.15),'stone',0)
 # True open courtyard, hollow hypostyle hall, 13 compressed longitudinal aisles.
 back=box('qibla_wall',(0,3.59,floor+h/2),(7.1,.22,h),'lime',40);contact(back.name,'foundation')
 for x in [-3.50,3.50]:
  ob=box('outer_side_wall_'+str(x),(x,0,floor+h/2),(.22,7.1,h),'earth',40);contact(ob.name,'foundation')
 front=box('entry_enclosure',(0,-3.50,floor+h/2),(6.8,.22,h),'earth',40);arch(front,0,-3.50,1.13,1.78);contact(front.name,'foundation')
 facade=box('prayer_hall_courtyard_arcade',(0,.50,floor+h/2),(6.90,.16,h),'lime',40)
 for x in [-3,-2.5,-2,-1.5,-1,0,1,1.5,2,2.5,3]:arch(facade,x,.50,.34 if x else .84,1.6 if x else 1.94)
 contact(facade.name,'foundation')
 # Twelve parallel walls create thirteen aisles; six through arches each.
 for i in range(12):
  x=-3.0+i*6/11
  wall=box('hypostyle_aisle_'+str(i),(x,2.01,floor+h/2),(.085,2.85,h),'lime',40)
  for y in [.84,1.31,1.78,2.25,2.72,3.19]:arch(wall,y,-x,.30,1.66,side=True)
  contact(wall.name,'foundation')
 roof('prayer_hall_flat_roof',0,2.045,7.10,3.32,top,age);contact('prayer_hall_flat_roof',facade.name)
 # Real blind mihrab pocket, not a painted door on a solid prayer hall.
 cutter=prism('TEMP_mihrab',g.portal_outline(0,floor,.42,1.61),3.40,3.61,'shadow',40)
 bpy.context.view_layer.objects.active=back;mod=back.modifiers.new('Blind mihrab niche','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True);g.PARTS.pop()
 for x in [-.36,.36]:box('mihrab_stone_frame',(x,3.469,.99),(.16,.035,1.68),'earth',80)
 box('mihrab_alfiz',(0,3.469,1.88),(.88,.035,.16),'earth',80)
 # Small faceted lantern above the mihrab bay, with crossing interior ribs.
 profiles=[(0,.44),(.21,.40),(.37,.23),(.42,.09)];vs=[(r*math.cos(k*math.tau/12),3.03+r*math.sin(k*math.tau/12),top+.12+z) for z,r in profiles for k in range(12)];fs=[]
 for q in range(3):
  for k in range(12):fs.append((q*12+k,q*12+(k+1)%12,(q+1)*12+(k+1)%12,(q+1)*12+k))
 fs.extend([tuple(reversed(range(12))),tuple(range(36,48))]);me=bpy.data.meshes.new('mihrab_roof_cupola');me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('mihrab_roof_cupola',me);bpy.context.scene.collection.objects.link(ob);g.finish(ob,ob.name,'lime',80);contact(ob.name,'prayer_hall_flat_roof')
 box('mihrab_rib_crown_support',(0,3.03,2.19),(.70,.10,.04),'lime',80)
 for angle in [0,math.pi/2]:
  pts=[(-.40,1.66),(-.40,1.78),(-.28,2.01),(0,2.17),(.28,2.01),(.40,1.78),(.40,1.66),(.33,1.76),(.22,1.94),(0,2.09),(-.22,1.94),(-.33,1.76)]
  ob=prism('crossing_mihrab_rib',pts,-.03,.03,'lime',80);ob.rotation_euler.z=angle;ob.location.y=3.03
  contact('mihrab_rib_crown_support',ob.name)
 contact('mihrab_rib_crown_support','hypostyle_aisle_5',expected=2.17-top)
 # Side galleries leave a large genuine courtyard void.
 for x in [-2.65,2.65]:
  wall=box('courtyard_gallery_'+str(x),(x,-1.46,floor+h/2),(.16,3.78,h),'lime',40)
  for y in [-2.8,-1.95,-1.1,-.25]:arch(wall,y,-x,.61,1.69,side=True)
  contact(wall.name,'foundation');roof('gallery_roof_'+str(x),(x+(-3.50 if x<0 else 3.50))/2,-1.6125,1.10,3.995,top,age);contact('gallery_roof_'+str(x),wall.name)
 # An off-axis square minaret is a later medieval addition, not 1136 attribution.
 tx,ty=-2.80,-2.86;mh=5.85+(age-3)*.20
 for name,c,size in [('north',(tx,ty+.53,floor+mh/2),(1.20,.14,mh)),('south',(tx,ty-.53,floor+mh/2),(1.20,.14,mh)),('west',(tx-.53,ty,floor+mh/2),(.14,.92,mh)),('east',(tx+.53,ty,floor+mh/2),(.14,.92,mh))]:
  ob=box('minaret_shell_'+name,c,size,'earth',40)
  if name in ['north','south']:arch(ob,tx,ty+(.53 if name=='north' else -.53),.28,.64,base=floor+mh-.99)
  contact(ob.name,'foundation')
 roof('minaret_cornice',tx,ty,1.40,1.40,floor+mh,age);contact('minaret_cornice','minaret_shell_north')
 box('lantern_base',(tx,ty,floor+mh+.43),(.70,.70,.62),'lime',80);contact('lantern_base','minaret_cornice')
 roof('lantern_cap',tx,ty,.83,.83,floor+mh+.74,age);contact('lantern_cap','lantern_base')
 for z in [3.35,3.77]:box('minaret_owner_painted_stripe',(tx,ty-.607,z),(1.03,.012,.19),'owner_cloth',100)
 for x in [-.86,.86]:box('portal_owner_painted_stripe',(x,-3.617,1.13),(.22,.012,.80),'owner_cloth',100)
 # Carved stone/plaster register: restrained, attached surfaces and real recessed niche.
 for x in [-1.0,1.0]:box('portal_limestone_jamb',(x,-3.63,1.05),(.20,.14,1.8),'lime',80)
 box('entry_alfiz_lintel',(0,-3.64,2.05),(2.20,.12,.18),'lime',80)
 for x in [-3,-2,-1,1,2,3]:box('court_alfiz_panel',(x,.399,top-.14),(.33,.04,.17),'earth',100)
 if age==4:
  for j in range(3):
   for x in [tx-.34,tx,tx+.34]:
    ob=box('minaret_sebka_stone_relief',(x,ty-.613,4.35+j*.30),(.18,.020,.18),'lime',100);ob.rotation_euler.y=math.pi/4
  for x in [-2.5,-1.5,1.5,2.5]:box('court_cedar_screen_band',(x,.405,top-.43),(.27,.03,.11),'cedar',100)
  for x in [-3.63,3.63]:box('seated_cedar_roof_drain',(x,1.10,top+.035),(.32,.08,.08),'cedar',80)
 # Courtyard remains empty and legible, with a small ablution basin outside traffic axis.
 g.tube('ablution_basin',(1.05,-1.50,.31),.32,.32,'stone',80);contact('ablution_basin','foundation')
 finalize(age)

def finalize(age):
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
 col=bpy.data.collections.new('BER_Tlemcen_Age'+str(age));bpy.context.scene.collection.children.link(col)
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
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Tlemcen_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
 sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 bpy.ops.object.camera_add(location=(8,-10,9));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=11.5;target=Vector((0,0,2.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-8,-12,20));bpy.context.object.data.energy=3000;bpy.context.object.data.size=10
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Tlemcen_Age{age}.blend'));sc.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
 sc.render.resolution_x=384;sc.render.resolution_y=384
 for name,loc in [('front',(0,-12,1.5)),('back',(0,12,1.5)),('left',(-12,0,1.5)),('right',(12,0,1.5)),('top',(0,0,12)),('bottom',(0,0,-12))]:
  cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 for o in objects:
  if 'roof' in o.name or 'parapet' in o.name:o.hide_render=True
 cam.location=(8,-10,11);cam.rotation_euler=(Vector((0,1,0.7))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age{age}_interior.png');bpy.ops.render.render(write_still=True)
 for o in objects:o.hide_render=False
 print('TLEMCEN_AGE_DONE',age,flush=True)
def donor():
 ctx=g.reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());groups=[]
 for group in d['geometry']['groups']:
  vs=group['positions'];fs=group.get('triangles',group.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched decoded Malian landmark 2a positions/topology';groups.append({'name':o.name,'bounds':bounds(o)})
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Malian_Landmark2a_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':groups,'geometry_reused':False,'render_bounds_are_footprint':False},indent=2))
try:
 donor()
 for age in [3,4]:build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[3,4],'cook':False,'native_owner_colour':'blocked integration pending'}))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

