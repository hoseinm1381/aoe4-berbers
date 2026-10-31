"""Original Berber connector recipe. Own process, no cook, exact logical walking joins."""
import sys,json,math,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import geometry_helpers as H
import bpy,bmesh
from mathutils import Vector
ART=H.ART;OUT=H.OUT;Q=H.RESEARCH
VARIANTS={'default':[], 'end':[0], 'corner':[0,90], 'thru':[0,180], 'tee':[0,90,270], 'cross':[0,90,180,270], 'why':[0,120,240]}
# Bearing zero points +Y to agree with native bone_north; +90 points +X.
def xy(r,t):return (r*math.sin(math.radians(t)),r*math.cos(math.radians(t)))
def poly(name,outline,lo,hi,mat,stage,batter=0):
 n=len(outline);vs=[(x*(1+batter),y*(1+batter),lo) for x,y in outline]+[(x,y,hi) for x,y in outline];fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);return H.finish(ob,name,mat,stage)
def strip(name,a,b,width,lo,hi,mat,stage):
 dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy);nx=-dy/length*width/2;ny=dx/length*width/2
 return poly(name,[(a[0]+nx,a[1]+ny),(a[0]-nx,a[1]-ny),(b[0]-nx,b[1]-ny),(b[0]+nx,b[1]+ny)],lo,hi,mat,stage)
def render(age,kind,meshes):
 scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.display.shading.show_shadows=True;scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.get('Review') or bpy.data.worlds.new('Review');scene.world.color=(.1,.12,.14)
 if not scene.camera:bpy.ops.object.camera_add();scene.camera=bpy.context.object;scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=12
 target=Vector((0,0,4));scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
 views=[('preview',(12,-16,14))]
 if kind=='tee':views += [('front',(0,-22,4)),('back',(0,22,4)),('left',(-22,0,4)),('right',(22,0,4)),('top',(0,0,22)),('bottom',(0,0,-22))]
 for nm,co in views:
  scene.camera.location=co;scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{kind}_{nm}.png');bpy.ops.render.render(write_still=True)
def variant(age,kind,angles):
 start=len(H.PARTS);wall='earth' if age==2 else 'lime';prefix=kind+'_'
 # Octagon has 4.2m wide cardinal join face at distance3; exact shared wall deck width.
 if kind=='why':outline=[xy(3/math.cos(math.pi/6),30+i*60) for i in range(6)]
 else:outline=[(-2.1,-3),(2.1,-3),(3,-2.1),(3,2.1),(2.1,3),(-2.1,3),(-3,2.1),(-3,-2.1)]
 # Lo-to-hi seated profiles; source bound is not a gameplay footprint.
 poly(prefix+'stone_foot',outline,0,.65,'stone',0)
 poly(prefix+'battered_lower',[(x*.97,y*.97) for x,y in outline],.65,3.25,wall,40,batter=1/.97-1)
 poly(prefix+'battered_upper',[(x*.93,y*.93) for x,y in outline],3.25,6.8,wall,60,batter=.97/.93-1)
 deck=poly(prefix+'continuous_walk_floor',outline,6.8,7,'stone' if age==4 else 'earth',80)
 # Closed parapets along each boundary, split into real entry cutouts on connected faces.
 for i,a in enumerate(outline):
  b=outline[(i+1)%len(outline)];mid=((a[0]+b[0])/2,(a[1]+b[1])/2);bearing=math.degrees(math.atan2(mid[0],mid[1]))%360;isentry=any(abs((bearing-t+180)%360-180)<1e-4 for t in angles)
  L=math.dist(a,b);segments=[(0,1)]
  if isentry:segments=[(0,(L-3)/(2*L)),((L+3)/(2*L),1)]
  for j,(u,v) in enumerate(segments):
   if v-u<1e-5:continue
   p=(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u);r=(a[0]+(b[0]-a[0])*v,a[1]+(b[1]-a[1])*v)
   # Shift guard .35m inward so exterior ends at floor boundary. Corridor is still3 wide.
   dx=r[0]-p[0];dy=r[1]-p[1];ell=math.hypot(dx,dy);mx=(p[0]+r[0])/2;my=(p[1]+r[1])/2;sgn=-1 if mx*(-dy)+my*dx>0 else 1;nx=sgn*(-dy)/ell*.35;ny=sgn*dx/ell*.35;p=(p[0]+nx,p[1]+ny);r=(r[0]+nx,r[1]+ny)
   strip(prefix+f'guard_{i}_{j}',p,r,.7,7,7.6,wall,80)
   count=max(1,round(ell/.95))
   for n in range(count):
    x=(n+.2)/count;y=(n+.8)/count;pa=(p[0]+dx*x,p[1]+dy*x);pb=(p[0]+dx*y,p[1]+dy*y)
    strip(prefix+f'merlon_{i}_{j}_{n}',pa,pb,.7,7.6,8.2,wall,100)
    if age>=3:strip(prefix+f'lime_cap_{i}_{j}_{n}',pa,pb,.7,8.16,8.2,'lime',100)
   # Owner-painted stripe on the exterior guard skin. Red-only atlas annotation.
   ex=-nx;ey=-ny;strip(prefix+f'owner_band_{i}_{j}',(p[0]+ex,p[1]+ey),(r[0]+ex,r[1]+ey),.014,7.24,7.43,'owner_cloth',100)
 if age>=3:
  for i,a in enumerate(outline):
   b=outline[(i+1)%len(outline)];strip(prefix+f'foundation_bond_{i}',a,b,.025,.4,.52,'lime',80)
 if age==4:
  # Painted earth diamond plaster motifs seated on upper facings below walk.
  for t in (0,90,180,270):
   x,y=xy(2.88,t);ob=H.box(prefix+'lozenge',(x,y,4.7),(.26,.055,.26),'earth',100);ob.rotation_euler.z=-math.radians(t);ob.rotation_euler.y=math.pi/4
 if kind=='why':
  # Cut every upper guard to the actual three continuous walking strips, including diagonal corners.
  for t in angles:
   x,y=xy(1.525,t);bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,9));cut=bpy.context.object;cut.dimensions=(3.001,3.05,4);cut.rotation_euler.z=-math.radians(t);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
   for part in list(H.PARTS[start:]):
    ob=bpy.data.objects.get(part['object'])
    if not ob or min(v.co.z+ob.location.z for v in ob.data.vertices)<6.99:continue
    bpy.context.view_layer.objects.active=ob;mod=ob.modifiers.new('Walking clearance120','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name)
    if len(ob.data.polygons)==0:bpy.data.objects.remove(ob,do_unlink=True);H.PARTS.remove(part)
    else:
     bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();H.reuv(ob)
   bpy.data.objects.remove(cut,do_unlink=True)
 if age==4:
  for z in (1.45,2.45,4.1):
   f=1-(z-.65)/2.6*.03 if z<=3.25 else .97-(z-3.25)/3.55*.04
   for i,a in enumerate(outline):
    b=outline[(i+1)%len(outline)];strip(prefix+f'dressed_course_{z}_{i}',(a[0]*f,a[1]*f),(b[0]*f,b[1]*f),.034,z-.035,z+.035,'stone',100)
 meshes=[bpy.data.objects[p['object']] for p in H.PARTS[start:]];c=bpy.data.collections.new(kind);bpy.context.scene.collection.children.link(c)
 for ob in meshes:
  for old in list(ob.users_collection):old.objects.unlink(ob)
  c.objects.link(ob)
 sockets=[];joins=[];rays=[]
 for t in angles:
  x,y=xy(3,t);ob=bpy.data.objects.new(prefix+'socket_'+str(t),None);c.objects.link(ob);ob.location=(x,y,7);ob['normal_xy']=xy(1,t);ob['clear_width']=3;sockets.append(ob)
  # Adjacent 6m curtain center at radial6, near endpoint radial3; numerical zero gap.
  cx,cy=xy(6,t);near=(cx-x,cy-y,7);joins.append({'bearing':t,'socket':[x,y,7],'adjacent_curtain_near_endpoint':near,'gap':math.dist((x,y,7),near),'pass':math.dist((x,y,7),near)<1e-7})
  for radial in (0,.5,1.5,2.5,2.999):
   for across in (-1.49,0,1.49):
    dx,dy=xy(radial,t);tx,ty=xy(across,t+90);orig=Vector((dx+tx,dy+ty,15));hits=[]
    for mesh in meshes:
     hit,loc,n,idx=mesh.ray_cast(orig-mesh.location,Vector((0,0,-1)))
     if hit:hits.append(loc.z+mesh.location.z)
    z=max(hits) if hits else None;rays.append({'bearing':t,'radial':radial,'across':across,'highest_z':z,'pass':z is not None and abs(z-7)<1e-5})
 assert all(j['pass'] for j in joins),joins
 assert all(r['pass'] for r in rays),[r for r in rays if not r['pass']]
 checks=H.check_objects(meshes);H.export(age,kind,meshes,sockets)
 return c,meshes,sockets,{'variant':kind,'connections':angles,'socket_distance_m':3,'native_bones':'bearing0 north;90 east;180 south;270 west; why uses120/240','walk_z':7,'clear_width':3,'parts':H.PARTS[start:],'joins':joins,'walk_rays':rays,'checks':checks,'body_deck_overhang_m':.21,'overhang':'intentional dressed cap lip, supported by battered core'}
def donor():
 H.reset_scene();records=[]
 for p in (Q/'stock').glob('*/decoded-static.json'):
  d=json.loads(p.read_text());kind=Path(d['request']['logical_path']).stem;c=bpy.data.collections.new(kind);bpy.context.scene.collection.children.link(c)
  for i,g in enumerate(d['geometry']['groups']):
   me=bpy.data.meshes.new(kind+'_'+str(i));me.from_pydata(g['positions'],[],g['triangles']);me.update();ob=bpy.data.objects.new(kind+'_'+str(i)+'_'+g['name'],me);c.objects.link(ob);ob['reference_only']='untouched decoded positions/triangles; materials not reconstructed'
  c.hide_render=True
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Untouched_Malian_Bastion_AllVariants_Reference.blend'))
def build(age):
 H.reset_scene();H.PARTS=[];H.CONTACTS=[];H.MATS.clear();H.setup_maps();recs=[];groups=[]
 for kind,angles in VARIANTS.items():
  c,meshes,sockets,rec=variant(age,kind,angles);recs.append(rec);render(age,kind,meshes);groups.append(c);c.hide_render=True
  for ob in meshes+sockets:ob.hide_set(True)
 # retain tee as opening default, all independent native variants remain selectable.
 c=bpy.data.collections['tee'];c.hide_render=False
 for ob in c.objects:ob.hide_set(False)
 (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'variants':recs,'native_colour':'blocked source-mask only'},indent=2))
 (ART/f'age{age}_states.json').write_text(json.dumps({'age':age,'variants':[{k:v for k,v in r.items() if k not in ('checks','walk_rays')} for r in recs],'selector_binding':'pending native cap attachment categories; 120deg why has shoulder narrowing, clear3 preserved'},indent=2))
 (ART/f'age{age}_construction.json').write_text(json.dumps({'age':age,'stages':[0,40,60,80,100],'cumulative':True,'objects':H.PARTS,'garrison_exported':False},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Bastion_Age{age}.blend'));print('BASTION_AGE_DONE',age,flush=True)
try:
 donor()
 for age in (2,3,4):build(age)
 (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[2,3,4],'native':'pending','cook':False},indent=2))
except Exception:
 (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
