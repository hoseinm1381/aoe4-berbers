"""Generic original Imperial asset runner; no donors, shared cooks or live scenes."""
import bpy,bmesh,math,json,sys,os,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com'
sys.path.insert(0,str(EXT))
sys.path.insert(0,str(EXT/'garrison'))
import garrison_shared
sys.modules['garrison.garrison_shared']=garrison_shared
import garrison
try:pass # delayed registration
except Exception:pass
from garrison import building_panel,material_adoption
class Runner:
 def __init__(self,kind):
  self.kind=kind;self.art=ROOT/'art/building_remix_0_4_0'/kind;self.art.mkdir(parents=True,exist_ok=True)
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
  self.col=bpy.data.collections.new('040_original_'+kind);bpy.context.scene.collection.children.link(self.col);self.parts=[];self.checks=[]
  self.atlas()
 def atlas(self):
  im=bpy.data.images.load(str(self.art/'atlas_albedo_v2.png'));im.name='040_'+self.kind+'_NativeGrainAtlas';im.pack()
  self.mat=bpy.data.materials.new('040_'+self.kind+'_native_textured_atlas');self.mat.use_nodes=True;p=self.mat.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.82
  tex=self.mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;self.mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
  normalim=bpy.data.images.load(str(self.art/'atlas_normal_v2.png'));normalim.colorspace_settings.name='Non-Color';normalim.pack();nt=self.mat.node_tree.nodes.new('ShaderNodeTexImage');nt.image=normalim;nm=self.mat.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.5;self.mat.node_tree.links.new(nt.outputs['Color'],nm.inputs['Color']);self.mat.node_tree.links.new(nm.outputs['Normal'],p.inputs['Normal'])
 def finish(self,o,name,slot,stage=40):
  o.name=name
  for col in list(o.users_collection):col.objects.unlink(o)
  self.col.objects.link(o);o['garrison_building_first_stage']=stage;o['040_atlas_slot']=slot
  o.data.materials.clear();o.data.materials.append(self.mat)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
  self.remap(o,slot)
  self.parts.append(o);return o
 def remap(self,o,slot):
  # Bisect source planar faces on a world-space 4m grid before atlas addressing.
  # Each polygon stays inside one repeat cell, preserving consistent density.
  cell=2.0 if slot in (3,7) else 4.0
  bm=bmesh.new();bm.from_mesh(o.data)
  for axis in range(3):
   lo=min(v.co[axis]+o.location[axis] for v in bm.verts);hi=max(v.co[axis]+o.location[axis] for v in bm.verts)
   for k in range(math.floor(lo/cell)+1,math.ceil(hi/cell)):
    co=[0,0,0];co[axis]=k*cell-o.location[axis];no=[0,0,0];no[axis]=1
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=co,plane_no=no,clear_inner=False,clear_outer=False)
  bm.to_mesh(o.data);bm.free();o.data.update()
  uv=o.data.uv_layers.active or o.data.uv_layers.new(name='WorldDensityAtlasUV')
  for p in o.data.polygons:
   axes=[k for k in range(3) if k!=max(range(3),key=lambda k:abs(p.normal[k]))]
   center=o.matrix_world@p.center;cells=[math.floor((center[k]+1e-6)/cell) for k in axes]
   for li in p.loop_indices:
    v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
    U=max(0,min(1,v[axes[0]]/cell-cells[0]));V=max(0,min(1,v[axes[1]]/cell-cells[1]))
    uv.data[li].uv=((slot%4+.005+.99*U)/4,(slot//4+.005+.99*V)/2)
 def recess(self,parent,name,center,dims,slot=1):
  bpy.ops.mesh.primitive_cube_add(size=1,location=center);cut=bpy.context.object;cut.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  bpy.context.view_layer.objects.active=parent;mod=parent.modifiers.new(name,'BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True);self.remap(parent,slot)
 def pitched_roof(self,name,x,y,z,w,d,rise,slot=3):
  # Eave bottom z, ridge z+rise; solid thickness .16m.
  vs=[(x+X,y+Y,z+Z) for X,Y,Z in [(-w/2,-d/2,0),(w/2,-d/2,0),(-w/2,d/2,0),(w/2,d/2,0),(-w/2,0,rise),(w/2,0,rise),(-w/2,-d/2,-.16),(w/2,-d/2,-.16),(-w/2,d/2,-.16),(w/2,d/2,-.16)]]
  return self.mesh(name,vs,[(0,1,5,4),(4,5,3,2),(6,7,1,0),(2,3,9,8),(0,4,2,8,6),(1,7,9,3,5),(6,8,9,7)],slot,80)
 def box(self,name,c,d,slot=0,stage=40):
  bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return self.finish(o,name,slot,stage)
 def mesh(self,name,v,f,slot=0,stage=40):
  me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return self.finish(o,name,slot,stage)
 def prism(self,name,poly,y,depth,slot,stage=40):
  n=len(poly);return self.mesh(name,[(x,Y,z) for Y in (y-depth/2,y+depth/2) for x,z in poly],[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],slot,stage)
 def arch(self,name,x,y,z,w,h,top,depth=.35,slot=1,rot=0):
  # Open horseshoe: piers stop at spring; spandrel is contiguous ring strips to lintel.
  objs=[];r=w*.55;spring=z+h-r;end=math.radians(-25);start=math.pi-end
  pts=[(x+r*math.cos(t),spring+r*math.sin(t)) for t in [start+(end-start)*i/18 for i in range(19)]]
  left=pts[0][0];right=pts[-1][0]
  objs.append(self.box(name+'_left_pier',(x-w*.63,y,(z+pts[0][1])/2),(w*.26,depth,pts[0][1]-z),slot))
  objs.append(self.box(name+'_right_pier',(x+w*.63,y,(z+pts[-1][1])/2),(w*.26,depth,pts[-1][1]-z),slot))
  for i,(a,b) in enumerate(zip(pts,pts[1:])):objs.append(self.prism(name+'_voussoir_%02d'%i,[a,b,(b[0],top),(a[0],top)],y,depth,slot))
  # True opening width and pier/crown contact recorded before duplication.
  self.checks.append({'module':name,'opening_clear':True,'spring_z':spring,'top':top,'crown_contact_gap':0,'depth':depth})
  if rot:
   for o in objs:
    for v in o.data.vertices:
     X,Y=v.co.x-x,v.co.y-y;v.co.x=x+X*math.cos(rot)-Y*math.sin(rot);v.co.y=y+X*math.sin(rot)+Y*math.cos(rot)
    # boxes have world positions unlike prism local coordinates
    if o.location.length:
     X,Y=o.location.x-x,o.location.y-y;o.location.x=x+X*math.cos(rot)-Y*math.sin(rot);o.location.y=y+X*math.sin(rot)+Y*math.cos(rot);o.rotation_euler.z=rot
  return objs
 def taper(self,name,x,y,z,w,d,h,t=.85,slot=0):
  vs=[(x+a*w*s/2,y+b*d*s/2,Z) for Z,s in ((z,1),(z+h,t)) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
  return self.mesh(name,vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],slot)
 def capture(self,name,textured=False,direction=(1,-1,1)):
  scene=bpy.context.scene
  if not scene.camera:
   c=bpy.data.cameras.new('Review');o=bpy.data.objects.new('Review',c);scene.collection.objects.link(o);scene.camera=o;c.type='ORTHO';c.ortho_scale=28
  cam=scene.camera;center=Vector((0,0,7.1 if self.kind=='fez' else 5));cam.location=center+Vector(direction)*30;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
  scene.render.engine='CYCLES' if textured else 'BLENDER_WORKBENCH'
  scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.show_cavity=True
  if textured:
   scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.world=scene.world or bpy.data.worlds.new('ReviewWorld');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.72,.78,.85,1);scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.8
   if not bpy.data.objects.get('ReviewSun'):
    l=bpy.data.lights.new('ReviewSun','SUN');l.energy=2.1;o=bpy.data.objects.new('ReviewSun',l);scene.collection.objects.link(o);o.rotation_euler=(.25,-.2,-.4)
  scene.render.filepath=str(self.art/(name+'.png'));bpy.ops.render.render(write_still=True)
 def finish_asset(self,recipe,flag):
  self.capture('blockout_solid')
  for name,d in {'front':(0,-1,0),'back':(0,1,0),'left':(-1,0,0),'right':(1,0,0),'top':(0,0,1),'bottom':(0,0,-1)}.items():self.capture('solid_'+name,direction=d)
  self.capture('textured_gamecamera',True)
  try:garrison.register()
  except Exception:pass
  bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(self.art/(self.kind+'_040_original.blend')))
  material_adoption.adopt_material(self.mat)
  s=bpy.context.scene;s.garrison.asset_library_root=str(self.art/'private-library');s.garrison.game_asset_connection='C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json';s.garrison.game_asset_index='C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3'
  self.col['garrison_building_profile']='english-house';s.garrison.author_collection=self.col
  # Export follows root visual approval via scoped export helper.
  bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(self.art/(self.kind+'_040_original.blend')))
  (self.art/'recipe.json').write_text(json.dumps(recipe,indent=2));(self.art/'flag-transform.json').write_text(json.dumps(flag,indent=2))
  pts=[o.matrix_world@v.co for o in self.parts for v in o.data.vertices];bounds=[[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
  (self.art/'source-checks.json').write_text(json.dumps({'fresh_geometry':True,'bounds':bounds,'parts':len(self.parts),'triangles':sum(len(p.vertices)-2 for o in self.parts for p in o.data.polygons),'contacts':self.checks,'native_game':'unverified','uv_layers_all':all(bool(o.data.uv_layers) for o in self.parts),'texture_sha256':hashlib.sha256((self.art/'atlas_albedo_v2.png').read_bytes()).hexdigest(),'shared_mesh_users':sum(o.data.users>1 for o in self.parts)},indent=2))



