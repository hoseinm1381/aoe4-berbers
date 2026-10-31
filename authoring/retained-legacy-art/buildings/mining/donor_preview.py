"""Original Maghrebi ore workyard. Task-owned GUI Blender only; no production cook."""
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
def donor():
 ctx=H.reset_scene();d=json.loads((RES/'stock/63c24366984eb66c461d/decoded-static.json').read_text());allpts=[]
 for g in d['geometry']['groups']:
  vs=g['positions'];fs=g.get('triangles',g.get('indices',[]))
  if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
  me=bpy.data.meshes.new(g['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(g['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='untouched decoded installed stock positions/indices';allpts.extend(vs)
 lo=[min(p[k] for p in allpts) for k in range(3)];hi=[max(p[k] for p in allpts) for k in range(3)];(RES/'donor_bounds.json').write_text(json.dumps({'bounds': [lo,hi],'warning':'all decoded parts/LODs; render geometry bounds are not gameplay footprint'},indent=2))
 presentation();target=tuple((a+b)/2 for a,b in zip(lo,hi));scale=max(hi[k]-lo[k] for k in range(3))*1.25
 bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTOUCHED_Common_Mining_Age1_Reference.blend'));render('stock_donor',tuple(target[k]+(6,-8,6)[k] for k in range(3)),target,scale)

try: donor()
finally: bpy.ops.wm.quit_blender()
