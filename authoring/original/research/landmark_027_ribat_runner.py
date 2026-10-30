"""Reusable deterministic Blender geometry helpers for measured landmark recipes."""
import bpy,bmesh,math
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
class Runner:
 def __init__(self,collection,material,prefix):
  self.col=collection;self.material=material;self.prefix=prefix;self.objects=[];self.contacts=[]
 def mesh(self,name,verts,faces,panel=0,stage=40):
  mesh=bpy.data.meshes.new(self.prefix+name);mesh.from_pydata(verts,[],faces);mesh.update()
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
  obj=bpy.data.objects.new(self.prefix+name,mesh);self.col.objects.link(obj);mesh.materials.append(self.material)
  obj['garrison_building_first_stage']=stage;obj['atlas_panel']=panel
  uv=mesh.uv_layers.new(name='AtlasUV');r,c=divmod(panel,4)
  for face in mesh.polygons:
   axis=max(range(3),key=lambda j:abs(face.normal[j]));a,b=[j for j in range(3) if j!=axis]
   vals=[v.co for v in mesh.vertices];low=[min(v[j] for v in vals) for j in range(3)];high=[max(v[j] for v in vals) for j in range(3)]
   for li in face.loop_indices:
    co=mesh.vertices[mesh.loops[li].vertex_index].co
    u=(co[a]-low[a])/max(high[a]-low[a],.0001);v=(co[b]-low[b])/max(high[b]-low[b],.0001)
    uv.data[li].uv=((c+.02+.96*u)/4,1-(r+.02+.96*v)/4)
  self.objects.append(obj);return obj
 def box(self,name,center,size,panel=0,stage=40,taper=0):
  x,y,z=center;a,b,h=[s/2 for s in size];t=1-taper
  vs=[(x+sx*a*f,y+sy*b*f,z+sz*h) for sz,f in [(-1,1),(1,t)] for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  return self.mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],panel,stage)
 def beam(self,name,start,end,width,panel=3,stage=60):
  start,end=Vector(start),Vector(end);delta=end-start
  obj=self.box(name,(0,0,0),(width,width,delta.length),panel,stage)
  rot=delta.to_track_quat('Z','Y').to_matrix()
  for v in obj.data.vertices:v.co=rot@v.co+(start+end)/2
  return obj
 def prism(self,name,profile,y0,y1,panel=0,stage=40):
  # Extrude a concave XZ elevation; triangulate faces from its actual boundary.
  n=len(profile);verts=[(x,y,z) for y in [y0,y1] for x,z in profile]
  vectors=[Vector((x,0,z)) for x,z in profile];idx={tuple(v):i for i,v in enumerate(vectors)}
  tris=[[(v if isinstance(v,int) else idx[tuple(v)]) for v in t] for t in tessellate_polygon([vectors])]
  faces=[tuple(t) for t in tris]+[tuple(i+n for i in reversed(t)) for t in tris]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  return self.mesh(name,verts,faces,panel,stage)
 def archwall(self,name,x,y,span,depth,height,radius,spring,panel=0,stage=40,segments=24):
  profile=[(x-span/2,0),(x-span/2,height),(x+span/2,height),(x+span/2,0),(x+radius,0),(x+radius,spring)]
  profile += [(x+radius*math.cos(a),spring+radius*math.sin(a)) for a in [math.pi*i/segments for i in range(1,segments+1)]]
  profile += [(x-radius,0)]
  return self.prism(name,profile,y-depth/2,y+depth/2,panel,stage)
 def contact(self,label,gap,tolerance=.035):
  self.contacts.append({'interface':label,'signed_gap':gap,'tolerance':tolerance,'passed':abs(gap)<=tolerance})


def remap_uv(obj,panel):
 mesh=obj.data;uv=mesh.uv_layers.active or mesh.uv_layers.new(name='AtlasUV');r,c=divmod(panel,4)
 for face in mesh.polygons:
  axis=max(range(3),key=lambda j:abs(face.normal[j]));a,b=[j for j in range(3) if j!=axis]
  vals=[v.co for v in mesh.vertices];low=[min(v[j] for v in vals) for j in range(3)];high=[max(v[j] for v in vals) for j in range(3)]
  for li in face.loop_indices:
   co=mesh.vertices[mesh.loops[li].vertex_index].co;u=(co[a]-low[a])/max(high[a]-low[a],.0001);v=(co[b]-low[b])/max(high[b]-low[b],.0001)
   uv.data[li].uv=((c+.02+.96*u)/4,1-(r+.02+.96*v)/4)

