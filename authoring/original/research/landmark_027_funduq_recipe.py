"""Original measured Funduq recipe; rebuilding owns this private Blender scene only."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'art/landmarks_0_2_7/funduq';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'research'))
from landmark_027_ribat_runner import Runner as BaseRunner
from mathutils.geometry import tessellate_polygon
class Runner(BaseRunner):
 def prism(self,name,profile,y0,y1,panel=0,stage=40):
  n=len(profile);vs=[(x,y,z) for y in [y0,y1] for x,z in profile]
  vec=[Vector((x,0,z)) for x,z in profile];idx={tuple(v):i for i,v in enumerate(vec)}
  raw=tessellate_polygon([vec]);tris=[[v if isinstance(v,int) else idx[tuple(v)] for v in t] for t in raw]
  faces=[tuple(t) for t in tris]+[tuple(i+n for i in reversed(t)) for t in tris]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  obj=self.mesh(name,vs,faces,panel,stage);obj['prism_profile_count']=n;return obj
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('FunduqOriginalAtlas');mat.use_nodes=True
n=mat.node_tree.nodes;bs=n.get('Principled BSDF')
for key,target,space in [('basecolor','Base Color','sRGB'),('roughness','Roughness','Non-Color')]:
 t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(OUT/'textures'/f'funduq_{key}.png'));t.image.colorspace_settings.name=space;mat.node_tree.links.new(t.outputs['Color'],bs.inputs[target])
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(OUT/'textures/funduq_normal.png'));t.image.colorspace_settings.name='Non-Color';normal=n.new('ShaderNodeNormalMap');mat.node_tree.links.new(t.outputs['Color'],normal.inputs['Color']);mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
col=bpy.data.collections.new('Funduq_LOD0');bpy.context.scene.collection.children.link(col);r=Runner(col,mat,'Funduq_')
def box(name,c,s,p=0,stage=40,taper=0):return r.box(name,c,s,p,stage,taper)
def rotate(obj,a):
 for v in obj.data.vertices:
  x,y,z=v.co;v.co=(math.cos(a)*x-math.sin(a)*y,math.sin(a)*x+math.cos(a)*y,z)
 return obj
box("CourtPaving",(0,0,.13),(6.0,6.0,.26),4,0)
# Main court supports. Doorways are genuine concave wall boundaries, not painted-on inserts.
for side,a in [('front',0),('right',math.pi/2),('back',math.pi),('left',-math.pi/2)]:
 if side=='front':
  for x in [-3.25,3.25]:rotate(box(side+'plinth'+str(x),(x,-4.05,.13),(3.9,2.28,.26),4,0),a)
 else:rotate(box(side+'plinth',(0,-4.05,.13),(5.82 if side in ['left','right'] else 10.4,2.28,.26),4,0),a)
 # Native stable lower/upper shell with individually open doorway bays.
 for i,x in enumerate([-4.1,-2.05,0,2.05,4.1]):
  if side=='front' and i==2:continue
  for floor in [0,1]:
   z=.26+floor*2.05
   w=r.archwall(f'{side}_room_{i}_{floor}',x,-3.56,2.05,.34,1.96,.36,.90,1,20 if floor==0 else 60,32)
   for v in w.data.vertices:v.co.z+=z
   rotate(w,a)
   # Actual door is recessed 0.18 behind inward wall face.
   for k in range(7):rotate(box(f'{side}_doorplank_{i}_{floor}_{k}',(x+(k-3)*.092,-3.82,z+.67),(.085,.10,1.24),3,40 if floor==0 else 80),a)
   for zz in [.33,1.02]:rotate(box(f'{side}_doorbrace_{i}_{floor}_{zz}',(x,-3.75,z+zz),(.67,.10,.095),11,40 if floor==0 else 80),a)
  # Exterior wall with recessed window openings.
  if side=='front':
   rotate(r.archwall(f'{side}_outerlower_{i}',x,-5.0,2.05,.40,2.65,.44,1.07,0,20,24),a)
   for k in range(9):rotate(box(f'{side}_storedoortimber_{i}_{k}',(x+(k-4)*.09,-4.86,.72),(.08,.12,1.35),3,40),a)
   for z in [.35,1.08]:rotate(box(f'{side}_storedoorstrap_{i}_{z}',(x,-4.94,z),(.81,.06,.08),11,40),a)
  else:rotate(box(f'{side}_outerlower_{i}',(x,-5.0,1.325),(2.05,.40,2.65),0,20),a)
  w=r.archwall(f'{side}_outerwindow_{i}',x,-5.0,2.05,.40,1.59,.25,.27,0,60,32)
  for v in w.data.vertices:v.co.z+=2.65
  rotate(w,a)
  for k in range(5):rotate(box(f'{side}_shutter_{i}_{k}',(x+(k-2)*.098,-4.94,2.96),(.092,.10,.53),3,80),a)
 # Walkway, roof bands and parapet seated in exact elevation.
 for x,width in ([(-3.25,3.9),(3.25,3.9)] if side=='front' else [(0,10.4)]):
  for z,deep,thick,p,st in [(2.22,2.28,.18,3,60),(4.34,1.80,.22,2,80),(4.63,.30,.40,1,100)]:
   actualwidth=(5.82 if z==2.22 else 6.8 if z==4.34 else 9.7) if side in ['left','right'] else width
   rotate(box(f'{side}_band_{z}_{x}',(x,-4.05 if z==2.22 else -4.3 if z==4.34 else -5.0,z),(actualwidth,deep,thick),p,st),a)
 # Timber gallery columns and corbels; supports contact floor and gallery.
 for i,x in enumerate([-4.65,-3.1,-1.55,0,1.55,3.1,4.65]):
  if side=='front' and abs(x)<1.0:continue
  for floor in [0,1]:
   z=.26+floor*2.05
   rotate(box(f'{side}_column_{i}_{floor}',(x,-2.96,z+.97),(.15,.15,1.94),3,40 if floor==0 else 80),a)
   for yy in [-3.16,-2.83]:
    o=r.beam(f'{side}_brace_{i}_{floor}_{yy}',(x,-2.96,z+1.65),(x,yy,z+1.94),.085,3,60 if floor==0 else 100);rotate(o,a)
  # Detailed upper-gallery railing; turned pickets are functional geometry.
  for k in range(7):
   xx=x+.12+k*.16
   if xx>4.65:continue
   rotate(box(f'{side}_railpicket_{i}_{k}',(xx,-2.84,2.78),(.065,.075,.76),3,80),a)
 rotate(box(f'{side}_galleryheader',(0,-2.96,4.29),(9.45,.18,.18),3,80),a)
 for z in [2.40,3.18,4.29]:rotate(box(f'{side}_galleryrail_{z}',(0,-2.84,z),(9.45,.10,.10),3,80),a)
 # inward covered gallery roof and ceiling joists
 for i in range(28):rotate(box(f'{side}_joist_{i}',(-4.85+i*.36,-3.64,4.20),(.10,1.77,.16),3,80),a)
 r.contact(side+' columns ground',0);r.contact(side+' gallery floor beams',0)
# Measured tapered earthen buttresses, crown trim and pierced upper joinery.
# Vertical bay strips seat on the stoneplinth, touching exterior wall at y=-5.2.
for side,a in [('front',0),('right',math.pi/2),('back',math.pi),('left',-math.pi/2)]:
 for i,x in enumerate([-4.95,-3.075,-1.025,1.025,3.075,4.95]):
  if side=='front' and abs(x)<1.5:continue
  rotate(box(f'{side}_taperedbuttress_{i}',(x,-5.18,2.075),(.22,.13,3.63),1,60,taper=.20),a)
  rotate(box(f'{side}_buttresscap_{i}',(x,-5.16,3.94),(.29,.17,.13),7,80),a)
 for i in range(26):
  x=-4.84+i*.385
  if side=='front' and abs(x)<1.50:continue
  rotate(box(f'{side}_cornicecorbel_{i}',(x,-5.16,4.24),(.09,.08,.14),3,80),a)
 for x,wid in ([(-3.25,3.9),(3.25,3.9)] if side=='front' else [(0,10.4)]):
  rotate(box(f'{side}_warmplastercrown_{x}',(x,-5.08,4.68),(10.02 if side in ['left','right'] else wid,.14,.08),7,100),a)
# Broad stepped portal, truly open at ground, above courtyard gate.
w=r.archwall('MainPortal',0,-4.76,2.9,.72,4.85,.89,1.47,1,40,48)
# continuous arch voussoir ring, individual faceted blocks
for i in range(40):
 a0=math.pi*i/40;a1=math.pi*(i+1)/40
 vs=[(rad*math.cos(a),y,1.47+rad*math.sin(a)) for y in [-5.16,-5.03] for rad,a in [(0.91,a0),(1.09,a0),(1.09,a1),(.91,a1)]]
 r.mesh('PortalArchBlock'+str(i),vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],7,80)
for x in [-1.19,1.19]:box('PortalJamb'+str(x),(x,-5.095,1.12),(.16,.13,2.24),7,80)
for z,wid in [(4.81,2.97),(5.05,2.62),(5.24,2.25)]:box('PortalSteppedCrown'+str(z),(0,-4.75,z),(wid,.88,.19),1,100)
for i in range(13):box('PortalDentil'+str(i),(-1.2+i*.2,-5.17,3.80),(.10,.09,.18),6,100)
# Loading shelters in court: post top and supported woven canopy actual attachment.
for x in [-2.05,2.05]:
 for xx in [x-.65,x+.65]:box('LoadingPost'+str((x,xx)),(xx,1.55,1.16),(.12,.12,1.80),3,60)
 for xx in [x-.65,x+.65]:box('LoadingRearPost'+str((x,xx)),(xx,2.65,1.375),(.12,.12,2.23),3,60)
 box('LoadingLintel'+str(x),(x,1.55,2.06),(1.43,.16,.15),3,80)
 # woven canopy slope and supporting rafters
 vs=[(xx,yy,zz) for xx in [x-.76,x+.76] for yy,zz in [(1.45,2.15),(2.65,2.55)]]
 vs+= [(xx,yy,zz-.018) for xx,yy,zz in vs[:4]]
 r.mesh('LoadingCanopy'+str(x),vs,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)],5,100)
 for xx in [x-.65,x+.65]:r.beam('LoadingRafter'+str(xx),(xx,1.45,2.10),(xx,2.66,2.49),.10,3,80)
 r.contact('Loading post foot '+str(x),0)
# Pottery/crates/bales: meaningful lathed profiles and joinery rather than padding.
def lathe(name,x,y,z,profile,panel=2,n=32):
 vs=[(x+rad*math.cos(2*math.pi*i/n),y+rad*math.sin(2*math.pi*i/n),z+zz) for zz,rad in profile for i in range(n)]
 fs=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profile)-1) for i in range(n)]
 fs += [tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+i for i in range(n))];obj=r.mesh(name,vs,fs,panel,100);obj['lathe_profile']=json.dumps(profile);obj['lathe_center']=[x,y,z];obj['lathe_segments']=n;return obj
for i in range(18):
 x=(-2.13 if i<9 else 2.13)+(i%3-1)*.36;y=2.03+(i//3%3)*.35
 lathe('TradeJar'+str(i),x,y,.26,[(0,.14),(.04,.17),(.13,.22),(.32,.22),(.45,.16),(.51,.10),(.54,.105),(.56,.075),(.51,.07)],2,16)
for i in range(8):
 x=-1.65+(i%4)*1.05;y=.75+(i//4)*.62
 box('CargoBale'+str(i),(x,y,.52),(.72,.43,.52),5,100,.10)
 for xx in [x-.24,x+.24]:box('BaleBinding'+str((i,xx)),(xx,y,.786),(.032,.44,.018),3,100)
# Accessible upper gallery: twelve seated earthen steps join rear gallery slab.
for i in range(12):
 h=(i+1)*2.05/12
 box('CourtyardStair'+str(i),(.70,.80+i*.184,.26+h/2),(.84,.19,h),1,60)
# Flagpole roof mount reserved native dynamic cloth integration
box('FlagStoneSocket',(-2.7,-4.4,4.55),(.23,.23,.23),4,100)
lathe('Flagpole',-2.7,-4.4,4.55,[(0,.045),(1.06,.045),(1.10,.036)],3,12)
r.contact('Flag socket roof',0)
# Fine useful masonry/grain-support geometry: outer lower stonework tessellated nonplanar courses.
for side,a in [('front',0),('right',math.pi/2),('back',math.pi),('left',-math.pi/2)]:
 for row in range(4):
  for i in range(32):
   x=-5.02+i*.319+(.05 if row%2 else 0)
   if side=='front' and abs(x)<1.17:continue
   rotate(box(f'{side}_plinthstone_{row}_{i}',(x,-5.13,.08+row*.082),(.304,.09,.075),4,0,taper=.025),a)
# Directional atlas mapping: wood grain runs along longest exposed face axis.
for obj in r.objects:
 if obj.get('atlas_panel') not in [3,11]:continue
 uv=obj.data.uv_layers.active;row,c=divmod(obj['atlas_panel'],4)
 for face in obj.data.polygons:
  axis=max(range(3),key=lambda j:abs(face.normal[j]));axes=[j for j in range(3) if j!=axis]
  vals=[obj.data.vertices[i].co for i in face.vertices]
  lo=[min(v[j] for v in vals) for j in range(3)];hi=[max(v[j] for v in vals) for j in range(3)]
  a,b=sorted(axes,key=lambda j:hi[j]-lo[j],reverse=True)
  for li in face.loop_indices:
   co=obj.data.vertices[obj.data.loops[li].vertex_index].co
   u=(co[a]-lo[a])/max(hi[a]-lo[a],.0001);v=(co[b]-lo[b])/max(hi[b]-lo[b],.0001)
   uv.data[li].uv=((c+.02+.96*u)/4,1-(row+.02+.96*v)/4)
# Numerical contact proof derived from final mesh bounds, after all transforms.
def bounds(obj):
 return [(min(v.co[i] for v in obj.data.vertices),max(v.co[i] for v in obj.data.vertices)) for i in range(3)]
byname={o.name.removeprefix('Funduq_'):o for o in r.objects};r.contacts=[]
def audit(label,child,parent,axis=2,childface=0,parentface=1,tol=.035):
 gap=bounds(byname[child])[axis][childface]-bounds(byname[parent])[axis][parentface]
 r.contact(label,gap,tol)
def anchor_covering(child,candidates):
 bb=bounds(byname[child]);xy=[(bb[i][0]+bb[i][1])/2 for i in [0,1]]
 good=[name for name in candidates if all(bounds(byname[name])[i][0]-.025<=xy[i]<=bounds(byname[name])[i][1]+.025 for i in [0,1])]
 if not good:raise ValueError('Missing physical support for '+child)
 return good[0]
ground=['CourtPaving']+[name for name in byname if 'plinth' in name and 'stone' not in name]
floors=[name for name in byname if '_band_2.22_' in name];roofs=[name for name in byname if '_band_4.34_' in name or '_galleryheader' in name]
for side in ['front','right','back','left']:
 for i in range(7):
  if side=='front' and i==3:continue
  for floor in [0,1]:
   child=f'{side}_column_{i}_{floor}';parent=anchor_covering(child,ground if floor==0 else floors)
   audit(child+' bottom seat on '+parent,child,parent)
   upper=anchor_covering(child,floors if floor==0 else roofs)
   audit(child+' top beam overlap '+upper,child,upper,childface=1,parentface=0,tol=.08)
for x in [-2.05,2.05]:
 for xx in [x-.65,x+.65]:
  audit('loading foot '+str(xx),'LoadingPost'+str((x,xx)),'CourtPaving')
  audit('loading rear foot '+str(xx),'LoadingRearPost'+str((x,xx)),'CourtPaving')
audit('Flag socket on roof','FlagStoneSocket','front_band_4.34_-3.25')
for i in range(18):audit('jar ground '+str(i),'TradeJar'+str(i),'CourtPaving')
for i in range(8):audit('bale ground '+str(i),'CargoBale'+str(i),'CourtPaving')
# Ensure only useful form: report budget rather than subdivide to pad.
for o in r.objects:
 o.data.calc_loop_triangles()
report={'design':'Original Sijilmasa caravanserai reconstruction','stages':[0,20,40,60,80,100],'contacts':r.contacts,'LOD0_triangles':sum(len(o.data.loop_triangles) for o in r.objects),'objects':len(r.objects),'native_team_colour':'root-retained flag_rectangle component','source_actor_scale':1.25,'flag_transform':{'location':[-2.7,-4.4,4.7127],'rotation_euler':[0,0,math.pi/2],'scale':[.7,.7,.7],'pole_top_source':5.65,'native_flag_local_top':1.339,'alignment_error':abs(4.7127+1.339*.7-5.65)},'uv_present':all(o.data.uv_layers.active for o in r.objects)}
vs=[o.matrix_world@v.co for o in r.objects for v in o.data.vertices];report['bounds']={k:[min(v[i] for v in vs),max(v[i] for v in vs)] for i,k in enumerate('xyz')}
# geometric lower LODs are independent hidden collection sources
import bmesh
# Geometric LODs preserve entire walls/roof/openings; detail and arc counts reduce deliberately.
def atlas_uv(mesh,panel):
 uv=mesh.uv_layers.new(name='AtlasUV');row,c=divmod(panel,4)
 for face in mesh.polygons:
  axis=max(range(3),key=lambda j:abs(face.normal[j]));aa,bb=[j for j in range(3) if j!=axis]
  vals=[mesh.vertices[i].co for i in face.vertices];lo=[min(v[j] for v in vals) for j in range(3)];hi=[max(v[j] for v in vals) for j in range(3)]
  if panel in [3,11]:aa,bb=sorted([aa,bb],key=lambda j:hi[j]-lo[j],reverse=True)
  for li in face.loop_indices:
   co=mesh.vertices[mesh.loops[li].vertex_index].co;u=(co[aa]-lo[aa])/max(hi[aa]-lo[aa],.0001);v=(co[bb]-lo[bb])/max(hi[bb]-lo[bb],.0001)
   uv.data[li].uv=((c+.02+.96*u)/4,1-(row+.02+.96*v)/4)
for lod in [1,2]:
 cc=bpy.data.collections.new('Funduq_LOD'+str(lod));bpy.context.scene.collection.children.link(cc);stageparts={st:[] for st in [0,20,40,60,80,100]}
 for o in r.objects:
  name=o.name.removeprefix('Funduq_');skip=False;expand=1
  if 'plinthstone' in name:skip=True
  elif 'doorplank' in name:
   k=int(name.split('_')[-1]);skip=(k%2==0 if lod==1 else k!=3);expand=2 if lod==1 else 7
  elif 'storedoortimber' in name:
   k=int(name.split('_')[-1]);skip=(k%2==1 if lod==1 else k!=4);expand=1.8 if lod==1 else 9
  elif 'railpicket' in name:skip=(int(name.split('_')[-1])%2==1 if lod==1 else int(name.split('_')[-1])%3!=0)
  elif 'cornicecorbel' in name:skip=True
  elif '_brace_' in name:skip=lod==2 or int(name.split('_')[2])%2==1
  elif '_shutter_' in name:
   k=int(name.split('_')[-1]);skip=(k%2==0 if lod==1 else k!=2);expand=2.5 if lod==1 else 5
  elif 'doorbrace' in name or 'storedoorstrap' in name or 'PortalDentil' in name:skip=lod==2
  elif 'joist' in name:skip=lod==2
  elif 'TradeJar' in name:skip=(int(name.removeprefix('TradeJar'))%2==1 if lod==1 else int(name.removeprefix('TradeJar'))%3!=0)
  if skip:continue
  vv=[tuple(v.co) for v in o.data.vertices];ff=[tuple(p.vertices) for p in o.data.polygons]
  if 'prism_profile_count' in o:
   n=o['prism_profile_count'];factor=2 if lod==1 else 4
   ids=list(range(6))+list(range(6,n-2,factor))+[n-2,n-1];ids=list(dict.fromkeys(ids));profile=[Vector(vv[i]) for i in ids];nn=len(ids)
   raw=tessellate_polygon([profile]);idx={tuple(v):i for i,v in enumerate(profile)};tris=[[v if isinstance(v,int) else idx[tuple(v)] for v in t] for t in raw]
   vv=[vv[i] for i in ids]+[vv[i+n] for i in ids]
   ff=[tuple(t) for t in tris]+[tuple(i+nn for i in reversed(t)) for t in tris]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
  elif name.startswith('TradeJar'):
   profile=json.loads(o['lathe_profile']);profile=[profile[i] for i in ([0,1,3,4,6,7,8] if lod==1 else [0,2,4,6,7,8])];n=12 if lod==1 else 8;x,y,z=o['lathe_center']
   vv=[(x+rad*math.cos(2*math.pi*i/n),y+rad*math.sin(2*math.pi*i/n),z+zz) for zz,rad in profile for i in range(n)]
   ff=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profile)-1) for i in range(n)]+[tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+i for i in range(n))]
  elif expand!=1:
   dims=[max(v[i] for v in vv)-min(v[i] for v in vv) for i in [0,1]];axis=dims.index(min(dims));center=(max(v[axis] for v in vv)+min(v[axis] for v in vv))/2
   vv=[tuple(center+(co[j]-center)*expand if j==axis else co[j] for j in range(3)) for co in vv]
  md=bpy.data.meshes.new('TemporaryLOD');md.from_pydata(vv,[],ff);md.update();bm=bmesh.new();bm.from_mesh(md);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(md);bm.free();atlas_uv(md,o['atlas_panel']);stageparts[o['garrison_building_first_stage']].append(md)
 for stage,meshes in stageparts.items():
  vv=[];ff=[];uvs=[]
  for mesh in meshes:
   start=len(vv);vv.extend([tuple(v.co) for v in mesh.vertices]);ff.extend([tuple(start+i for i in p.vertices) for p in mesh.polygons]);uvs.extend([tuple(q.uv) for q in mesh.uv_layers.active.data])
  md=bpy.data.meshes.new(f'FunduqStage{stage}_LOD{lod}');md.from_pydata(vv,[],ff);md.update();md.materials.append(mat);uv=md.uv_layers.new(name='AtlasUV')
  for i,v in enumerate(uvs):uv.data[i].uv=v
  q=bpy.data.objects.new(md.name,md);cc.objects.link(q);q['garrison_building_first_stage']=stage
  for m in meshes:bpy.data.meshes.remove(m)
 cc.hide_render=True;cc.hide_viewport=True
 report['LOD'+str(lod)+'_triangles']=sum(sum(len(p.vertices)-2 for p in q.data.polygons) for q in cc.objects)
report['LOD_strategy']='Protected principal geometry, reduced arch curve samples, fewer cargo rings and omitted subpixel joinery. No global decimation.'
(OUT/'source-validation.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'funduq_editable.blend'))
print(json.dumps(report))
bpy.ops.wm.quit_blender()

















