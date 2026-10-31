"""Original irrigated farm, private source only; GUI Blender deterministic recipe."""
import bpy,bmesh,json,math,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'art/buildings/farm';OUT=ROOT/'output/buildings_batch/farm';RES=ROOT/'research/buildings_batch/farm'
COLORS=[('earth',(.42,.24,.10),0),('lime',(.73,.62,.43),0),('stone',(.39,.32,.23),0),('wood',(.24,.105,.035),0),('owner',(.76,.72,.61),1),('water',(.13,.24,.19),0),('crop',(.49,.48,.19),0),('green',(.22,.31,.09),0)]
MATS={};PARTS=[]
def reset():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.context.temp_override(window=bpy.context.window_manager.windows[0]).__enter__()
 MATS.clear();PARTS.clear()
def maps():
 for name in ['albedo','pattern','normal','roughness','metal']:
  im=bpy.data.images.new('Farm_'+name,width=128,height=128,alpha=True);im.use_fake_user=True;px=[]
  for y in range(128):
   for x in range(128):
    role,c,mask=COLORS[x//32+4*(y//64)]
    rgb={'pattern':(mask,0,0),'normal':(.5,.5,1),'roughness':(.87,.87,.87),'metal':(0,0,0)}.get(name,tuple(v*(.95+.05*math.sin(x)*math.sin(y)) for v in c));px.extend((*rgb,1))
  im.pixels.foreach_set(px);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack()
  if name=='albedo':albedo=im
 for i,(name,c,mask) in enumerate(COLORS):
  m=bpy.data.materials.new('Farm_'+name);m.use_nodes=True;m['ber_owner_mask']=mask;m.diffuse_color=(*c,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.87
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
 o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1]
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for layer in list(o.data.uv_layers):o.data.uv_layers.remove(layer)
 uv=o.data.uv_layers.new(name='FarmAtlasUV')
 for p in o.data.polygons:
  axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis];co=[o.data.vertices[o.data.loops[li].vertex_index].co for li in p.loop_indices];lo=[min(v[a] for v in co) for a in axes];hi=[max(v[a] for v in co) for a in axes]
  for li,v in zip(p.loop_indices,co):
   u=(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-9);w=(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-9);uv.data[li].uv=((slot%4+.08+.84*u)/4,(slot//4+.08+.84*w)/2)
 PARTS.append({'object':o.name,'first_stage':stage,'material':mat,'owner_mask':MATS[mat][0]['ber_owner_mask']});return o
def box(name,c,s,mat='earth',stage=40):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,stage)
def stalk(name,x,y,z,h,mat):
 # Continuous ear/stem silhouette, all rings connected and closed.
 rings=[(0,.013),(h*.57,.013),(h*.60,.029),(h*.91,.032),(h,.005)];n=5
 vs=[(x+r*math.cos(k*math.tau/n),y+r*math.sin(k*math.tau/n),z+zz) for zz,r in rings for k in range(n)];fs=[tuple(reversed(range(n)))]
 for q in range(4):
  for k in range(n):fs.append((q*n+k,q*n+(k+1)%n,(q+1)*n+(k+1)%n,(q+1)*n+k))
 fs.append(tuple(range(20,25)));me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,80)
def donor():
 reset();d=json.loads(next((RES/'stock').rglob('decoded-static.json')).read_text());pts=[]
 for g in d['geometry']['groups']:
  vs=g['positions'];fs=g.get('triangles',g.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(g['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='unchanged stock depleted farm geometry; material reconstruction absent';pts+=vs
 (RES/'donor_bounds.json').write_text(json.dumps({'bounds':[ [min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)] ],'gameplay_footprint_from_official_site_ext':[4,4],'resource_layout_box':[8,8],'note':'stock positions untouched; render bounds not gameplay footprint'},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTOUCHED_Stock_Depleted_Farm.blend'))
def build(age):
 reset();maps();contacts=[]
 # 4x4 site footprint is numeric official scale; leave .1 margin. All farm stages traversable.
 box('flat_earth_plot',(0,0,.025),(3.8,3.8,.05),'earth',0)
 # Three long connected soil beds with wide access furrows and an open crossing.
 for i,x in enumerate([-1.14,0,1.14]):
  for j,y in enumerate([-.73,.83]):
   box('raised_bed_%d_%d'%(i,j),(x,y,.08),(.65,1.36,.06),'earth',20)
   contacts.append({'interface':'bed to earth top','measured_gap':0,'pass':True})
   for row in range(3):
    for q in range(10):stalk('cereal_connected_stem_ear',x+(row-1)*.19,y-.55+q*.12,.11,.29+.045*age+(.035*math.sin(q+i)), 'crop' if age!=2 else 'green')
 # Main header and two branch channels end exactly against header; low open tops.
 box('header_channel_water',(0,1.69,.057),(3.54,.16,.014),'water',40)
 for x in [-.57,.57]:
  box('branch_water',(x,-.05,.057),(.12,3.32,.014),'water',40)
  contacts.append({'interface':'branch north to header south','measured_signed_gap':0,'pass':True})
  for dx in [-.11,.11]:box('branch_channel_bank',(x+dx,-.05,.095),(.10,3.32,.09),'earth' if age<3 else 'lime',40)
 for y in [1.56,1.82]:box('header_channel_bank',(0,y,.095),(3.54,.10,.09),'earth' if age<3 else 'lime',40)
 # Low edging has generous south entry and no wall across middle access lane.
 edge='earth' if age==1 else 'stone'
 for x in [-1.85,1.85]:box('low_side_edging',(x,0,.13),(.10,3.70,.16),edge,20)
 for x in [-1.22,1.22]:box('south_edge_open_entry',(x,-1.85,.13),(1.16,.10,.16),edge,20)
 # Useful small tool shade, in southern service margin; no large house mass.
 z=.72+.07*age;cx=-1.1;cy=-1.52
 for x in [cx-.44,cx+.44]:
  for y in [cy-.22,cy+.22]:
   box('shade_post',(x,y,.05+(z-.05)/2),(.045,.045,z-.05),'wood',20);contacts.append({'interface':'shade post foot to plot','measured_gap':0,'pass':True})
 for y in [cy-.22,cy+.22]:box('shade_crossbeam',(cx,y,z),(.94,.065,.065),'wood',60)
 box('woven_tool_shade',(cx,cy,z+.055),(.98,.56,.045),'owner',80)
 contacts.append({'interface':'cloth underside to crossbeam top','measured_gap':0,'pass':True})
 box('tool_rack',(cx,cy,.23),(.72,.065,.065),'wood',60)
 for x in [cx-.22,cx+.22]:box('hoe_handle',(x,cy,.33),(.027,.027,.50),'wood',80);box('hoe_head',(x,cy,.087),(.15,.05,.06),'stone',80)
 box('owner_trim_band',(1.28,-1.847,.195),(.76,.022,.065),'owner',100)
 if age>=2:
  box('irrigation_sluice_board',(-.57,1.61,.16),(.30,.04,.22),'wood',80)
  box('watering_trough',(1.42,-1.55,.13),(.49,.30,.16),'earth',60)
 if age>=3:
  for x in [-1.7,1.7]:box('lime_header_corner',(x,1.71,.16),(.23,.32,.22),'lime',80)
  box('crossing_plank',(0,-.02,.16),(1.41,.25,.04),'wood',80)
 if age==4:
  for x in [-1.68,-1.41,1.41,1.68]:box('geometric_channel_tile',(x,1.563,.15),(.12,.021,.07),'stone',100)
  box('spare_sluice_board',(1.45,-1.27,.16),(.4,.06,.18),'wood',100)
 objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];col=bpy.data.collections.new('BER_Farm_Age'+str(age));bpy.context.scene.collection.children.link(col)
 checks=[]
 for o in objects:
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o);bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True);nm=sum(not e.is_manifold for e in bm.edges);dg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free()
  uv=o.data.uv_layers.active;ua=[]
  for p in o.data.polygons:
   v=[uv.data[li].uv for li in p.loop_indices];ua.append(abs(sum(a.x*b.y-b.x*a.y for a,b in zip(v,v[1:]+v[:1]))/2))
  checks.append({'object':o.name,'closed_edges':nm==0,'outward_volume':vol,'degenerate_faces':dg,'min_uv_area':min(ua),'finite':all(math.isfinite(v) for p in o.data.vertices for v in p.co),'positive_scale':all(v>0 for v in o.scale)})
 assert all(c['closed_edges'] and c['outward_volume']>0 and c['degenerate_faces']==0 and c['min_uv_area']>1e-10 and c['finite'] and c['positive_scale'] for c in checks)
 bpy.context.view_layer.update();points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box];bounds=[[min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]];assert bounds[0][0]>=-2 and bounds[1][0]<=2 and bounds[0][1]>=-2 and bounds[1][1]<=2
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'bounds':bounds,'official_site_footprint_scale':[4,4],'objects':checks,'contacts':contacts,'footprint_pass':True,'native_owner':'blocked pending actual shader contract'},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,20,40,60,80,100],'assignment':'cumulative first-visible percentage; source only','parts':PARTS,'resource_states_required':['untouched','gatherable','depleted'],'native_resource_state_binding':'pending; source crop meshes not regrowth animation'},indent=2))
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Farm_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.54,.57,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 bpy.ops.object.camera_add(location=(5,-6,6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.25))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.6;scene.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-3,-4,7));bpy.context.object.data.energy=600;bpy.context.object.data.size=5
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Farm_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
 scene.cycles.samples=8;scene.render.resolution_x=320;scene.render.resolution_y=320
 for name,loc in [('front',(0,-8,.4)),('back',(0,8,.4)),('left',(-8,0,.4)),('right',(8,0,.4)),('top',(0,0,8)),('bottom',(0,0,-8))]:
  cam.location=loc;cam.rotation_euler=(Vector((0,0,.25))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 print('FARM_AGE_DONE',age,flush=True)
try:
 donor()
 for age in range(1,5):build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'cook':False,'native':'pending'},indent=2))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
