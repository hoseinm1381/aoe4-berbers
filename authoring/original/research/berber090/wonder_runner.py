"""Reusable measured rigid-building runner; recipe owns anatomy and steps."""
import bpy,bmesh,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research'))
from berber_040_university_geometry import Builder,review,export

class Runner(Builder):
 def remap(self,o,kind):
  me=o.data;me.update();uv=me.uv_layers.active or me.uv_layers.new(name='UVMap')
  lo=[min(v.co[i] for v in me.vertices) for i in range(3)];hi=[max(v.co[i] for v in me.vertices) for i in range(3)]
  for p in me.polygons:
   drop=max(range(3),key=lambda i:abs(p.normal[i]));a=[i for i in range(3) if i!=drop]
   for li in p.loop_indices:
    v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=((kind+.03+.94*(v[a[0]]-lo[a[0]])/max(.001,hi[a[0]]-lo[a[0]]))/5,.02+.96*(v[a[1]]-lo[a[1]])/max(.001,hi[a[1]]-lo[a[1]]))
 def plane_prism(self,name,poly,face,depth,axis='Y',kind=0,stage=60):
  vs=[(u,d,z) if axis=='Y' else (d,u,z) for d in (face-depth/2,face+depth/2) for u,z in poly];n=len(poly)
  return self.mesh(name,vs,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],kind,stage)
 def arch(self,name,u,face,z,width,height,depth,axis='Y',kind=0,stage=60):
  r=width/2;s=z+height-r;poly=[(u-r,z),(u+r,z)]+[(u+r*math.cos(math.pi*i/16),s+r*math.sin(math.pi*i/16)) for i in range(17)]
  return self.plane_prism(name,poly,face,depth,axis,kind,stage)
 def recess(self,target,name,u,face,z,width,height,axis,depth=.26,kind=0):
  cutter=self.arch('TEMP_'+name,u,face,z,width,height,depth,axis)
  for ob in (target,cutter):
   bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
  bpy.context.view_layer.update()
  bpy.context.view_layer.objects.active=target;m=target.modifiers.new('true recessed '+name,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name)
  self.parts.remove(cutter);bpy.data.objects.remove(cutter,do_unlink=True);self.remap(target,kind)
 def bar(self,name,p,q,width,kind=1,stage=80):
  p=Vector(p);q=Vector(q);o=self.box(name,(0,0,0),(width,width,(q-p).length),kind,stage);o.location=(p+q)/2;o.rotation_euler=(q-p).to_track_quat('Z','Y').to_euler();return o
 def finalize_meshes(self):
  proof=[]
  for o in self.parts:
   if o.data.users>1:o.data=o.data.copy()
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data)
   row={'name':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)};proof.append(row)
   bm.free();o.data.update()
   assert o.data.uv_layers.active is not None
   assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
   assert all(p.area>1e-12 for p in o.data.polygons)
  assert not [p for p in proof if p['nonmanifold_edges'] or p['signed_volume']<-1e-6],proof
  return proof
