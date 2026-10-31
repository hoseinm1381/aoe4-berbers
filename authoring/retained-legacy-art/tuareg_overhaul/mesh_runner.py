"""Reusable, deterministic mesh construction with explicit skin weights and atlas UVs."""
import bpy, math
from mathutils import Vector
class MeshRecipe:
    def __init__(self,name):
        self.name=name;self.vertices=[];self.faces=[];self.weights=[];self.tiles=[];self.steps=[]
    def part(self,points,faces,weights,tile,label):
        offset=len(self.vertices);self.vertices.extend([tuple(p) for p in points])
        self.weights.extend(weights if isinstance(weights,list) else [weights.copy() for p in points])
        self.faces.extend([tuple(offset+i for i in f) for f in faces]);self.tiles.extend([tile]*len(faces))
        self.steps.append({'part':label,'vertices':len(points),'faces':len(faces)})
    def rings(self,rings,tile,label,cap=True):
        # Each ring is (centre, radiusX, radiusY, weights); horizontal continuous shell.
        n=16; points=[];weights=[];faces=[]
        for center,rx,ry,w in rings:
            for j in range(n):
                a=2*math.pi*j/n;points.append((center[0]+rx*math.cos(a),center[1]+ry*math.sin(a),center[2]));weights.append(w)
        for k in range(len(rings)-1):
            for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
        if cap:faces.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+j for j in range(n))])
        self.part(points,faces,weights,tile,label)
    def tube(self,centers,radii,weights,tile,label,sides=12):
        points=[];faces=[];vw=[]
        for k,c in enumerate(centers):
            c=Vector(c); direction=Vector(centers[min(k+1,len(centers)-1)])-Vector(centers[max(k-1,0)])
            direction.normalize();ref=Vector((0,1,0))
            if abs(direction.dot(ref))>.95:ref=Vector((1,0,0))
            u=direction.cross(ref).normalized();v=direction.cross(u).normalized()
            for j in range(sides):
                a=2*math.pi*j/sides;points.append(c+radii[k]*(math.cos(a)*u+math.sin(a)*v));vw.append(weights[k])
        for k in range(len(centers)-1):
            for j in range(sides):faces.append((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j))
        faces.extend([tuple(reversed(range(sides))),tuple((len(centers)-1)*sides+j for j in range(sides))])
        self.part(points,faces,vw,tile,label)
    def object(self,collection,material,rig=None):
        mesh=bpy.data.meshes.new(self.name);mesh.from_pydata(self.vertices,[],self.faces);mesh.update()
        obj=bpy.data.objects.new(self.name,mesh);collection.objects.link(obj);mesh.materials.append(material)
        uv=mesh.uv_layers.new(name='TuaregAtlas')
        for p,tile in zip(mesh.polygons,self.tiles):
            tx,ty=tile%4,tile//4
            for j,l in enumerate(p.loop_indices):
                a=2*math.pi*j/len(p.loop_indices)
                uv.data[l].uv=((tx+.5+.43*math.cos(a))/4,(ty+.5+.43*math.sin(a))/4)
        if rig:
            for name in sorted({name for w in self.weights for name in w}):obj.vertex_groups.new(name=name)
            for i,w in enumerate(self.weights):
                s=sum(w.values());assert s>0
                for name,value in w.items():obj.vertex_groups[name].add([i],value/s,'REPLACE')
            mod=obj.modifiers.new('Native 48 bone deformation','ARMATURE');mod.object=rig
            obj.parent=rig
        # Face winding is derived from connected shells then recalculated as a closed component.
        for o in bpy.context.selected_objects:o.select_set(False)
        obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
        obj['tuareg_recipe_parts']=str(self.steps)
        return obj
