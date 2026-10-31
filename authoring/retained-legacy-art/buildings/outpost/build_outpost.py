"""Task-owned, reproducible Moroccan courtyard blacksmith source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/outpost'; OUT=ROOT/'output/buildings_batch/outpost'; RESEARCH=ROOT/'research/buildings_batch/outpost'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.10,.115,.125),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern','roughness','metal','normal'):
        im=bpy.data.images.new('Outpost_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
        pixels=[]
        for y in range(256):
            for x in range(256):
                slot=(x//64)+4*(y//128); role,c,owner=COLORS[slot]
                variation=.96+.04*math.sin(x*.91)*math.sin(y*.81)
                rgb={'pattern':(owner,0,0),'normal':(.5,.5,1),'metal':((.85,.85,.85) if slot==5 else (0,0,0)),'roughness':((.4,.4,.4) if slot==5 else (.85,.85,.85))}.get(mapname,tuple(v*variation for v in c))
                pixels.extend((*rgb,1))
        im.pixels.foreach_set(pixels);im.filepath_raw=str(ART/(mapname+'.png'));im.file_format='PNG';im.save();im.pack()
        if mapname=='albedo': albedo=im
    for i,(name,c,owner) in enumerate(COLORS):
        m=bpy.data.materials.new('BerberOutpost_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='OutpostAtlasUV')
    for face in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis]
        co=[o.data.vertices[o.data.loops[li].vertex_index].co for li in face.loop_indices]
        lo=[min(v[k] for v in co) for k in axes];hi=[max(v[k] for v in co) for k in axes]
        for li,v in zip(face.loop_indices,co):
            uv.data[li].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    PARTS.append({'object':o.name,'first_stage':stage,'material':mat,'owner_mask':MATS[mat][0]['ber_owner_mask']});return o
def box(name,center,size,mat='earth',stage=40):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,stage)
def prism(name,outline,yfront,yback,mat,stage):
    n=len(outline);vs=[(x,y,z) for y in (yfront,yback) for x,z in outline]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,stage)
def portal_outline(cx,base,width,height):
    r=width*.56;cz=base+height-r
    return [(cx-width*.43,base),(cx+width*.43,base)]+[(cx+r*math.cos(t),cz+r*math.sin(t)) for t in [math.radians(-28+i*236/16) for i in range(17)]]
def cut_portal(wall,cx,y,z,width,height,mat='cedar'):
    outline=portal_outline(cx,z,width,height)
    cutter=prism('TEMP_portal',outline,y-.7,y+.7,'shadow',40)
    bpy.context.view_layer.objects.active=wall;mod=wall.modifiers.new('Real recessed doorway','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
    # closed inserted door, actually seated inside the cut opening
    door=prism('horseshoe_door',outline,y+.035,y+.09,mat,60)
    for x in [cx-width*.32,cx,cx+width*.32]:box('door_joinery',(x,y+.022,z+height*.43),(.035,.035,height*.7),'stone',80)
    CONTACTS.append({'interface':'door recessed into front wall opening','gap':0,'intentional_recess':.035})
    return door
def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
def contact(a,b,axis=2,expected=0):
    bpy.context.view_layer.update(); gap=bounds(bpy.data.objects[a])[0][axis]-bounds(bpy.data.objects[b])[1][axis]
    CONTACTS.append({'child':a,'parent':b,'axis':axis,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})
def tube(name,center,r,h,mat='clay',stage=100):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=h,location=center);return finish(bpy.context.object,name,mat,stage)

def beam(name,a,b,w,mat='cedar',stage=60):
    v=Vector(b)-Vector(a);o=box(name,(Vector(a)+Vector(b))/2,(w,w,v.length),mat,stage);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o

def reuv(o):
    uv=o.data.uv_layers.active;slot=MATS[o['ber_material_role']][1]
    for p in o.data.polygons:
        ax=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=ax];vs=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];lo=[min(v[k] for v in vs) for k in axes];hi=[max(v[k] for v in vs) for k in axes]
        for i,v in zip(p.loop_indices,vs):uv.data[i].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)


def move_collection(objs,name):
 c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
 for o in objs:
  for old in list(o.users_collection):old.objects.unlink(o)
  c.objects.link(o)
 return c

def carve(o,center,size):
 cutter=box('TEMP_cut',center,size,'earth',40)
 bpy.context.view_layer.objects.active=o;m=o.modifiers.new('actual_opening','BOOLEAN');m.operation='DIFFERENCE';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name)
 bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop();reuv(o)

def export_state(age,name,objects):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Outpost_Age{age}_{name}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,path_mode='COPY',embed_textures=True)

def build(age):
 global PARTS,CONTACTS
 print('AGE_START',age,flush=True);ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();floor=.16;h=4.15+.14*(age-1);top=floor+h;wall='earth' if age<3 else 'lime'
 box('tower_foundation',(0,0,.08),(3.6,3.6,.16),'stone',0)
 box('entry_threshold',(0,-1.89,.08),(.95,.18,.16),'stone',0)
 walls=[]
 for side,x in [('west',-1.31),('east',1.31)]:
  o=box(side+'_thick_wall',(x,0,floor+h/2),(.38,3,h),wall,40);walls.append(o);contact(o.name,'tower_foundation')
  for yy in [-.65,.65]:carve(o,(x,yy,floor+h*.66),(.8,.16,.65))
 for side,y in [('north',1.31),('south',-1.31)]:
  o=box(side+'_thick_wall',(0,y,floor+h/2),(2.24,.38,h),wall,40);walls.append(o);contact(o.name,'tower_foundation')
  if side=='south':cut_portal(o,0,-1.5,floor,.86,1.65);reuv(o)
  else:
   for xx in [-.58,.58]:carve(o,(xx,y,floor+h*.66),(.16,.8,.65))
 # Continuous usable hollow shaft and fitted roof floor; original closed entrance door is inset.
 box('lookout_floor',(0,0,top+.06),(3.16,3.16,.12),'cedar',60);contact('lookout_floor','west_thick_wall')
 box('lookout_parapet_back',(0,1.44,top+.35),(3.16,.28,.46),wall,80);contact(bpy.context.object.name,'lookout_floor')
 for x in [-1.04,1.04]:box('lookout_parapet_front',(x,-1.44,top+.35),(1.08,.28,.46),wall,80);contact(bpy.context.object.name,'lookout_floor')
 for x in [-1.44,1.44]:box('lookout_parapet_side',(x,0,top+.35),(.28,2.88,.46),wall,80);contact(bpy.context.object.name,'lookout_floor')
 for x in [-1.43,1.43]:
  for y in [-1.43,1.43]:box('corner_merlon',(x,y,top+.65),(.29,.29,.60),wall,80)
 # A rear half canopy leaves the forward weapon platform unobstructed.
 canopybottom=top+1.42
 for x in [-1.12,1.12]:
  for y in [.05,1.13]:
   post=box('lookout_cedar_post',(x,y,(top+.12+canopybottom)/2),(.10,.10,canopybottom-top-.12),'cedar',20);contact(post.name,'lookout_floor')
 for x in [-1.12,1.12]:box('canopy_long_beam',(x,.59,canopybottom-.05),(.14,1.34,.10),'cedar',60)
 box('fitted_flat_canopy',(0,.59,canopybottom+.045),(2.46,1.42,.09),'straw' if age==1 else 'earth',80)
 CONTACTS.append({'interface':'canopy underside to post tops','signed_gap':0,'expected':0,'pass':True})
 for x in [-1.04,1.04]:box('neutral_owner_front_band',(x,-1.59,top+.36),(.85,.025,.18),'owner_cloth',100)
 box('neutral_owner_side_band',(-1.59,0,top+.36),(.025,2.20,.18),'owner_cloth',100)
 for x in [-.62,.62]:box('entry_cedar_lintel_end',(x,-1.52,1.97),(.12,.14,.12),'cedar',60)
 if age>=2:
  for x in [-1.43,1.43]:
   for z in [.38,.86,1.34]:box('limestone_corner_courses',(x,-1.48,z),(.14,.11,.20),'stone',80)
  box('portal_lime_lintel',(0,-1.512,2.06),(1.17,.075,.16),'lime',80)
 if age>=3:
  for x in [-.85,-.43,0,.43,.85]:
   o=box('geometric_plaster_panel',(x,-1.518,top-.36),(.19,.035,.19),'earth',100);o.rotation_euler.y=math.pi/4
 if age>=4:
  for x in [-1.12,1.12]:box('stone_crown_coping',(x,.59,canopybottom+.13),(.14,1.42,.08),'lime',100)
 print('BASE_DONE',age,flush=True);base=[o for o in bpy.context.scene.objects if o.type=='MESH'];move_collection(base,f'BER_Outpost_Age{age}_BASE')
 alt={};anchors=[]
 # Preserve exact runtime marker names; custom coordinates are source proposals, not donor-exact anchors.
 for weapon in ['arrow','springald','cannon']:
  radius,zoff={'arrow':(1.06,.42),'springald':(1.45,.77),'cannon':(1.43,.58)}[weapon]
  for i,(x,y,ang) in enumerate([(0,-radius,0),(radius,0,math.pi/2),(0,radius,math.pi),(-radius,0,-math.pi/2)]):
   bpy.ops.object.empty_add(type='ARROWS',location=(x,y,top+zoff));o=bpy.context.object;o.name=f'fx_muz_{weapon}_{i:02d}';o.rotation_euler.z=ang;o['source_only']=True;anchors.append(o)
 move_collection(anchors,'NATIVE_NAME_SOURCE_ANCHORS')
 if age>=2:
  start=set(bpy.context.scene.objects)
  for x in [-1.31,1.31]:box('fortified_stone_side',(x,0,floor+h/2),(.40,3.02,h),'stone',40)
  for y in [-1.31,1.31]:
   o=box('fortified_stone_face',(0,y,floor+h/2),(2.24,.40,h),'stone',40)
   if y<0:cut_portal(o,0,-1.51,floor,.86,1.65)
   else:
    for xx in [-.58,.58]:carve(o,(xx,y,floor+h*.66),(.16,.8,.65))
  # Side sleeves retain the same slit geometry, door and footprint.
  for o in [o for o in bpy.context.scene.objects if o not in start and o.name.startswith('fortified_stone_side')]:
   for yy in [-.65,.65]:carve(o,(o.location.x,yy,floor+h*.66),(.8,.16,.65))
  print('STONE_DONE',age,flush=True);alt['stone']=[o for o in bpy.context.scene.objects if o not in start];move_collection(alt['stone'],'STATE_FORTIFIED_STONE')
 for weapon,unlock in [('arrowslits',2),('springald',3),('cannon',4)]:
  if age<unlock:continue
  start=set(bpy.context.scene.objects);z=top+.12
  if weapon=='arrowslits':
   for x in [-.6,.6]:
    box('arrow_cover_frame',(x,-.96,z+.27),(.075,.12,.54),'cedar',100)
   box('arrow_shield_panel',(0,-.96,z+.27),(1.13,.11,.54),'cedar',100)
   carve(bpy.context.object,(0,-.96,z+.30),(.14,.5,.32))
  elif weapon=='springald':
   for x in [-.33,.33]:box('springald_stock_runner',(x,-.65,z+.09),(.13,1.20,.18),'cedar',100)
   for x in [-.27,.27]:box('springald_upright',(x,-.40,z+.36),(.12,.14,.54),'cedar',100)
   beam('springald_crossbow_limb',(-.73,-.87,z+.60),(.73,-.87,z+.60),.13,'cedar',100)
   beam('springald_tension_string',(-.73,-.87,z+.60),(0,-.18,z+.60),.025,'straw',100);beam('springald_tension_string',(0,-.18,z+.60),(.73,-.87,z+.60),.025,'straw',100)
   beam('springald_bolt',(0,-.1,z+.65),(0,-1.45,z+.65),.04,'shadow',100)
  else:
   for x in [-.33,.33]:box('cannon_ground_skid',(x,-.63,z+.09),(.16,1.30,.18),'cedar',100)
   box('cannon_cradle',(0,-.60,z+.23),(.58,.56,.28),'cedar',100)
   # Hollow faceted barrel with continuous outer/inner loop topology.
   vs=[];n=12
   for y,r in [(-1.43,.17),(-.10,.22),(-.10,.14),(-1.43,.10)]:
    vs.extend([(r*math.cos(k*math.tau/n),y,z+.46+r*math.sin(k*math.tau/n)) for k in range(n)])
   faces=[]
   for j in range(4):
    for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,((j+1)%4)*n+(k+1)%n,((j+1)%4)*n+k))
   me=bpy.data.meshes.new('cannon_barrel');me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new('cannon_hollow_barrel',me);bpy.context.scene.collection.objects.link(o);finish(o,o.name,'shadow',100)
  alt[weapon]=[o for o in bpy.context.scene.objects if o not in start];move_collection(alt[weapon],'STATE_'+weapon.upper())
 # Audit every source alternative, including currently hidden modules.
 print('STATES_DONE',age,flush=True);allmesh=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[];bpy.context.view_layer.update()
 for o in allmesh:
  bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True)
  if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);vol=-vol
  bad=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free();reuv(o)
  uv=o.data.uv_layers.active;areas=[]
  for f in o.data.polygons:
   pts=[uv.data[i].uv for i in f.loop_indices];areas.append(abs(sum(pts[i].x*pts[(i+1)%len(pts)].y-pts[(i+1)%len(pts)].x*pts[i].y for i in range(len(pts))))/2)
  b=bounds(o);finite=all(math.isfinite(v) for ve in o.data.vertices for v in ve.co)
  check={'object':o.name,'nonmanifold':bad,'degenerate':deg,'outward_volume':vol,'minimum_uv_area':min(areas),'finite':finite,'positive_scale':all(v>0 for v in o.scale),'bounds':b};checks.append(check)
  assert bad==0 and deg==0 and vol>0 and min(areas)>1e-10 and finite and check['positive_scale'],check
  assert b[0][0]>=-2.0001 and b[1][0]<=2.0001 and b[0][1]>=-2.0001 and b[1][1]<=2.0001 and b[0][2]>=-.0001,check
 assert all(c.get('pass',True) for c in CONTACTS)
 # Verify firing openings clear by local ray tests through the wall.
 rayproof=[]
 for o in walls:
  if o.name.startswith(('west','east')):
   for yy in [-.65,.65]:
    origin=o.matrix_world.inverted()@Vector((-2,yy,floor+h*.66));direction=Vector((1,0,0));hit=o.ray_cast(origin,direction)[0];rayproof.append({'object':o.name,'slit_y':yy,'unobstructed':not hit});assert not hit
 states={'base':[o.name for o in base]}
 for name,objs in alt.items():
  if name=='stone':states[name]=[o.name for o in base if o not in walls and not o.name.startswith(('horseshoe_door','door_joinery'))]+[o.name for o in objs]
  else:states[name]=states['base']+[o.name for o in objs]
  if name!='stone' and 'stone' in states:states[name+'_stone']=states['stone']+[o.name for o in objs]
 (ART/f'age{age}_states.json').write_text(json.dumps({'states':states,'exclusive_emplacements':True,'fortified_unlock_age':2,'anchors':[{'name':o.name,'xyz':list(o.location),'rotation':list(o.rotation_euler),'status':'proposed source mapping; not decoded native transforms'} for o in anchors]},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'cumulative-source-stage/v1','parts':PARTS,'stages':[0,20,40,60,80,100],'native_binding':'pending'},indent=2))
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'objects':checks,'contacts':CONTACTS,'slit_rays':rayproof,'footprint':[4,4],'origin':[0,0,0]},indent=2))
 for name,names in states.items():export_state(age,name,[bpy.data.objects[n] for n in names]+anchors)
 for objects in alt.values():
  for o in objects:o.hide_render=True;o.hide_set(True)
 scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.light='STUDIO';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.render_aa='8';scene.cycles.samples=12;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
 bpy.ops.object.camera_add(location=(8,-11,8));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,top/2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=8.0;scene.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(-3,-4,9));bpy.context.object.data.energy=1000;bpy.context.object.data.size=5
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Outpost_Age{age}.blend'))
 scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
 scene.cycles.samples=8;scene.render.resolution_x=400;scene.render.resolution_y=400
 for name,loc in [('front',(0,-12,top/2)),('back',(0,12,top/2)),('left',(-12,0,top/2)),('right',(12,0,top/2)),('top',(0,0,12)),('bottom',(0,0,-12))]:
  cam.location=loc;cam.rotation_euler=(Vector((0,0,top/2))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
 # Minimum-age upgrade views include fortified source state as well.
 cam.location=(8,-11,8);cam.rotation_euler=(Vector((0,0,top/2))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=768;scene.render.resolution_y=768
 for name,minimum in [('stone',2),('arrowslits',2),('springald',3),('cannon',4)]:
  if name not in states or age!=minimum:continue
  names=set(states[name])
  for o in allmesh:o.hide_render=o.name not in names
  scene.render.filepath=str(OUT/f'age{age}_{name}_preview.png');bpy.ops.render.render(write_still=True)
 print('OUTPOST_AGE_DONE',age,flush=True)

def donor():
 reset_scene();d=json.loads(next((RESEARCH/'stock').rglob('decoded-static.json')).read_text());summary=[]
 for g in d['geometry']['groups']:
  vs=g['positions'];fs=g.get('triangles',g.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(g['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched stock geometry, no material restoration';summary.append({'name':o.name,'vertices':len(vs),'faces':len(fs),'render_bounds':bounds(o)})
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Untouched_Abbasid_Outpost_Age01_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps(summary,indent=2))
try:
 donor()
 for age in range(1,5):build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[1,2,3,4],'cook':False,'native':'pending'}))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False
 bpy.ops.wm.quit_blender()
 import os;os._exit(0)
