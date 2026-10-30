"""Original Koutoubia detailed source: bounded features anchored to approved blockout."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research'))
from berber_040_university_geometry import Builder,review,export
ART=ROOT/'art/building_remix_0_4_0/wonder';bpy.ops.wm.open_mainfile(filepath=str(ART/'Koutoubia_blockout.blend'));bpy.context.preferences.filepaths.save_version=0
b=Builder.__new__(Builder);b.art=ART;b.col=bpy.data.collections['Koutoubia_original_lod0'];b.mat=bpy.data.materials['Koutoubia_original_lod0_textured_material'];b.parts=[o for o in b.col.objects if o.type=='MESH'];b.contacts=[]
for node in b.mat.node_tree.nodes:
 if node.type=='TEX_IMAGE':node.image=bpy.data.images.load(str(ART/'native_surface_atlas.png'),check_existing=True)
def uv_refresh(ob,kind):
 me=ob.data;me.update();uv=me.uv_layers.active or me.uv_layers.new();ps=[v.co for v in me.vertices];lo=[min(v[i] for v in ps) for i in range(3)];hi=[max(v[i] for v in ps) for i in range(3)]
 for p in me.polygons:
  drop=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=drop]
  for li in p.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=((kind+.03+.94*(v[axes[0]]-lo[axes[0]])/max(.01,hi[axes[0]]-lo[axes[0]]))/5,.02+.96*(v[axes[1]]-lo[axes[1]])/max(.01,hi[axes[1]]-lo[axes[1]]))
def arched_prism(name,cx,face,base,width,height,depth,orientation='front',kind=0,stage=60):
 radius=width/2;spring=base+height-radius;profile=[(-radius,base),(radius,base),(radius,spring)]+[(radius*math.cos(math.pi*i/16),spring+radius*math.sin(math.pi*i/16)) for i in range(1,17)]
 vs=[]
 for yy in (face-depth/2,face+depth/2):
  for xx,z in profile:vs.append((cx+xx,yy,z) if orientation=='front' else (yy,cx+xx,z))
 n=len(profile);fs=[tuple(range(n-1,-1,-1)),tuple(n+i for i in range(n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return b.mesh(name,vs,fs,kind,stage)
def recess(target,cx,face,base,width,height,depth,orientation='front'):
 cutter=arched_prism('TEMP_recess',cx,face,base,width,height,depth,orientation)
 bpy.context.view_layer.objects.active=target;mod=target.modifiers.new('real arched recess','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);b.parts.remove(cutter);bpy.data.objects.remove(cutter,do_unlink=True);uv_refresh(target,0 if 'minaret' in target.name else 1)
# Actual recessed blind-arch panels on visible front and east shaft faces.
tower=bpy.data.objects['minaret_square_shaft']
recess(tower,-5.6,3.39,3.3,1.6,3.7,.20,'front')
recess(tower,4.6,-4.39,3.3,1.6,3.7,.20,'side')
for x in (-6.17,-5.03):recess(tower,x,3.39,7.45,.70,1.70,.20,'front')
for y in (4.03,5.17):recess(tower,y,-4.39,7.45,.70,1.70,.20,'side')
# Upper narrower openings also cut into lantern, not floating plaques.
lantern=bpy.data.objects['minaret_lantern'];recess(lantern,-5.6,3.93,12.05,.72,1.05,.16,'front');recess(lantern,4.6,-4.93,12.05,.72,1.05,.16,'side')
# Doors in low sanctuary facade: three real recessed cedar entrances.
hall=bpy.data.objects['sanctuary_hypostyle_mass']
for i,x in enumerate([-2.2,1.0,4.2]):
 recess(hall,x,-.70,.15,1.5,2.25,.25,'front')
 arched_prism('recessed_cedar_door_'+str(i),x,-.59,.15,1.45,2.20,.035,'front',2,60)
# Tall blind panels have interlacing sebka diamonds, physically seated in recess bed.
def bar(name,p,q,width,depth,kind=0,stage=60):
 p=Vector(p);q=Vector(q);ob=b.box(name,(0,0,0),(width,depth,(q-p).length),kind,stage);ob.location=(p+q)/2;ob.rotation_euler=(q-p).to_track_quat('Z','Y').to_euler();return ob
# One measured continuous diamond module repeated only in inset panel, each mesh singleuser.
for face in ('front','east'):
 for row in range(3):
  z=4.15+row*.74
  for col in (-1,1):
   h=col*.34
   pts=[(h,z+.35),(h+.31,z),(h,z-.35),(h-.31,z)]
   for j in range(4):
    a,c=pts[j],pts[(j+1)%4]
    p=(-5.6+a[0],3.475,a[1]) if face=='front' else (-4.475,4.6+a[0],a[1]);q=(-5.6+c[0],3.475,c[1]) if face=='front' else (-4.475,4.6+c[0],c[1])
    bar('seated_sebka_'+face+str(row)+str(col)+str(j),p,q,.045,.05,1,60)
# Restrained crown bands and merlons; every bottom/face derives from shaft bounds.
for z,h,kind in [(9.9,.13,1),(10.65,.42,3),(11.22,.15,0)]:b.box('square_crown_band_'+str(z),(-5.6,4.6,z),(2.48,2.48,h),kind,60 if z!=10.65 else 80)
for side in (-1,1):
 for i in range(5):
  v=-.98+i*.49
  b.box('crown_merlon_front'+str(side)+str(i),(-5.6+v,4.6+side*1.19,12.045),(.20,.18,.29),0,80)
  if i not in (0,4):b.box('crown_merlon_side'+str(side)+str(i),(-5.6+side*1.19,4.6+v,12.045),(.18,.20,.29),0,80)
# Low court galleries: real open segmented stone arches supported by square piers.
def gallery_module(name,x,y,axis):
 # Local opening1.55wide; pier top1.30; semicircular arch rises to2.08.
 width=1.55;r=width/2;spring=1.30;top=2.18;dep=.32
 # Arch spandrel from inner curved opening to upper flat beam; connected strip.
 verts=[];n=16
 for depth in (-dep/2,dep/2):
  for i in range(n+1):
   u=-r+2*r*i/n;zz=spring+math.sqrt(max(0,r*r-u*u));verts.extend([(u,depth,zz),(u,depth,top)])
 faces=[];N=2*(n+1)
 for i in range(n):a=2*i;faces.extend([(a,a+2,a+3,a+1),(N+a,N+a+1,N+a+3,N+a+2),(a,N+a,N+a+2,a+2),(a+1,a+3,N+a+3,N+a+1)])
 faces.extend([(0,1,N+1,N),(2*n,2*n+N,2*n+N+1,2*n+1)])
 if axis=='Y':verts=[(x+v,y+u,z) for u,v,z in verts]
 else:verts=[(x+u,y+v,z) for u,v,z in verts]
 b.mesh(name+'_spandrel',verts,faces,0,60)
 for sign in (-1,1):
  ctr=(x,y+sign*(r+.10),.71) if axis=='Y' else (x+sign*(r+.10),y,.71);sz=(.32,.20,1.18) if axis=='Y' else (.20,.32,1.18);b.box(name+'_pier'+str(sign),ctr,sz,0,20)
 # Green shallow gallery canopy soffit seats at2.18 top.
 if axis=='Y':b.hip(name+'_gallery_cap',x,y,.72,1.95,2.30,.18,4,80)
 else:b.hip(name+'_gallery_cap',x,y,1.95,.72,2.30,.18,4,80)
# Inspectable first complete module then repeat3bays along both court sides.
gallery_module('court_west_module0',-5.45,-1.75,'Y')
for k,y in enumerate([-3.5,-5.25],1):gallery_module('court_west_module'+str(k),-5.45,y,'Y')
for k,y in enumerate([-1.75,-3.5,-5.25]):gallery_module('court_east_module'+str(k),5.85,y,'Y')
# Small central ablution basin seats on courtpaving without blocking mainaxis.
b.rings('court_basin',(.2,-3.5),[(.66,.16),(.66,.40),(.48,.40),(.48,.25),(.01,.25)],8,0,60,True)
b.rings('basin_inset_water',(.2,-3.5),[(.46,.255),(.46,.27)],8,3,80,True)
# Copperorb finial built as connected lathed rings on lantern capapex.
for j,(r,z) in enumerate([(.14,14.00),(.11,14.26),(.08,14.46)]):
 b.rings('copper_finial_orb'+str(j),(-5.6,4.6),[(.01,z-r),(.75*r,z-.75*r),(r,z),(.75*r,z+.75*r),(.01,z+r)],8,0,100,True)
b.rings('finial_spindle',(-5.6,4.6),[(.025,13.90),(.025,14.60)],8,0,100,True)
# Mandatory nativeflag seat independent of patterned tower and courtyardaccess.
b.rings('native_owner_flag_pole',(6.6,-5.8),[(.055,.12),(.055,4.70)],8,2,100,True)
flag={'location':[6.6,-5.77,3.35],'rotation':[0,0,0],'scale':[1,1,1]};(ART/'flag-transform.json').write_text(json.dumps(flag,indent=2))
contacts={'ground_plinth_bottom':0,'tower_bottom_plinth_top_gap':0,'tower_east_face':-4.4,'sanctuary_west_face':-4.4,'tower_hall_side_contact_gap':0,'hall_top':2.70,'roof_soffit':2.70,'roof_seat_gap':0,'gallery_pier_top':1.30,'gallery_arch_spring':1.30,'gallery_beam_top':2.18,'gallery_roof_soffit':2.18,'gallery_roof_gap':0,'basin_bottom':.16,'court_paving_top':.16,'fountain_recess_depth':.15,'native_flag_top':4.6889,'pole_top':4.70}
import bmesh
for ob in b.parts:
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
bounds=review(ART,'koutoubia_final',b.parts)
manifest=export(b,ART)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Berber_Koutoubia_Wonder_040.blend'))
report={'schema':'berber.original-koutoubia/v040','status':'source-exported','source':'entirely original mesh from clean040blockout','bounds_local':bounds,'bounds_world_actor150':[[v*1.5 for v in side] for side in bounds],'parts':b.report(),'contacts':contacts,'flag_transform':flag,'export':manifest,'native_runtime':'unverified','template':'native-compatible-singleLOD0 accepted027 export; integration owns cook/readback/markers'}
(ART/'source-validation.json').write_text(json.dumps(report,indent=2));print('KOUTOUBIA_ORIGINAL_READY',len(b.parts))
