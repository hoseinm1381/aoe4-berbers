"""040 university-owned deterministic mesh/atlas helpers, reused by new Wonder."""
import bpy,math,json,random
from pathlib import Path
from mathutils import Vector
class Builder:
 def __init__(self,name,art):
  self.art=Path(art);self.art.mkdir(parents=True,exist_ok=True);self.contacts=[];self.parts=[]
  self.col=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(self.col)
  self.mat=self.atlas(name)
 def atlas(self,name):
  W=512;im=bpy.data.images.new(name+'_texture',width=W,height=W,alpha=True);pix=[]
  colors=[(.57,.39,.25),(.78,.67,.49),(.26,.11,.045),(.12,.31,.27),(.055,.27,.16)]
  for y in range(W):
   for x in range(W):
    k=min(4,x*5//W);u=(x/W*5)%1;v=y/W;noise=math.sin(x*73.13+y*19.71)*math.sin(x*9.1-y*56.3)*.035;c=colors[k];f=1+noise
    if k==0:
     row=int(v*18);joint=(u*8+(.5 if row%2 else 0))%1<.045 or v*18%1<.04;f*=.65 if joint else 1
    elif k==1:f+=.035*math.sin(x*.4+y*.1)
    elif k==2:f+=.13*math.sin(v*110+math.sin(u*15)*2)+.04*math.sin(v*700)
    elif k==3:
     a=abs((u*9)%1-.5)+abs((v*9)%1-.5);f*=1.5 if .30<a<.38 else .65 if a<.16 else 1
    else:
     joint=(u*9%1)<.045 or (v*17%1)<.04;f*=.5 if joint else 1+.08*math.sin(u*9*math.pi)
    pix.extend([max(0,min(1,c[0]*f)),max(0,min(1,c[1]*f)),max(0,min(1,c[2]*f)),1])
  im.pixels.foreach_set(pix);im.filepath_raw=str(self.art/'surface_atlas.png');im.file_format='PNG';im.save()
  mat=bpy.data.materials.new(name+'_textured_material');mat.use_nodes=True;nt=mat.node_tree;n=nt.nodes.new('ShaderNodeTexImage');n.image=im;nt.links.new(n.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);nt.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.77
  return mat
 def mesh(self,name,verts,faces,kind=0,stage=40):
  me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);self.col.objects.link(ob);me.materials.append(self.mat)
  uv=me.uv_layers.new(name='UVMap');lo=[min(v[i] for v in verts) for i in range(3)];hi=[max(v[i] for v in verts) for i in range(3)]
  for poly in me.polygons:
   normal=poly.normal;drop=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=drop]
   for li in poly.loop_indices:
    v=me.vertices[me.loops[li].vertex_index].co;u=(v[axes[0]]-lo[axes[0]])/max(.01,hi[axes[0]]-lo[axes[0]]);w=(v[axes[1]]-lo[axes[1]])/max(.01,hi[axes[1]]-lo[axes[1]])
    uv.data[li].uv=((kind+.03+.94*u)/5,.02+.96*w)
  ob['garrison_building_first_stage']=stage;self.parts.append(ob);return ob
 def box(self,name,center,size,kind=0,stage=40):
  x,y,z=center;a,b,c=[v/2 for v in size];verts=[(x+sx*a,y+sy*b,z+sz*c) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  return self.mesh(name,verts,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],kind,stage)
 def rings(self,name,center,rings,n=8,kind=0,stage=60,cap=True):
  x,y=center;vs=[(x+r*math.cos(2*math.pi*i/n+math.pi/n),y+r*math.sin(2*math.pi*i/n+math.pi/n),z) for r,z in rings for i in range(n)];fs=[]
  for j in range(len(rings)-1):
   for i in range(n):a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
  if cap:fs.extend([tuple(range(n-1,-1,-1)),tuple((len(rings)-1)*n+i for i in range(n))])
  return self.mesh(name,vs,fs,kind,stage)
 def hip(self,name,x,y,w,d,z,rise,kind=4,stage=80):
  # Closed solid hip roof, narrow exact eave overhang only.
  a=w/2;b=d/2;vs=[(x-a,y-b,z),(x+a,y-b,z),(x+a,y+b,z),(x-a,y+b,z),(x,y,z+rise),(x-a,y-b,z-.12),(x+a,y-b,z-.12),(x+a,y+b,z-.12),(x-a,y+b,z-.12)]
  return self.mesh(name,vs,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(5,6,1,0),(6,7,2,1),(7,8,3,2),(8,5,0,3),(8,7,6,5)],kind,stage)
 def report(self):return [{'name':o.name,'stage':o['garrison_building_first_stage'],'vertices':len(o.data.vertices),'faces':len(o.data.polygons)} for o in self.parts]
def review(art,name,parts):
 scene=bpy.context.scene;scene.render.resolution_x=1000;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new(name+' world');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.7
 pts=[o.matrix_world@Vector(v) for o in parts for v in o.bound_box];low=Vector([min(p[i] for p in pts) for i in range(3)]);high=Vector([max(p[i] for p in pts) for i in range(3)]);center=(low+high)/2
 cd=bpy.data.cameras.new(name+' camera');ca=bpy.data.objects.new(name+' camera',cd);scene.collection.objects.link(ca);scene.camera=ca;cd.type='ORTHO';cd.ortho_scale=max(high-low)*1.3
 for view,d in {'front':(0,-1,0),'back':(0,1,0),'left':(-1,0,0),'right':(1,0,0),'top':(0,0,1),'bottom':(0,0,-1),'gamecamera':(1,-1,.9)}.items():
  ca.location=center+Vector(d)*60;ca.rotation_euler=(center-ca.location).to_track_quat('-Z','Y').to_euler();scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.show_cavity=True
  if view=='gamecamera':
   cd.ortho_scale=max(high-low)*1.7
   scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;ld=bpy.data.lights.new(name+'sun','SUN');ld.energy=2.5;ob=bpy.data.objects.new(name+'sun',ld);scene.collection.objects.link(ob);ob.rotation_euler=(.4,-.4,-.5)
   if name.startswith('koutoubia'):
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.75,.82,1,1);scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.65;scene.view_settings.view_transform='Standard';scene.view_settings.exposure=-.3
    fill=bpy.data.lights.new(name+'fill','AREA');fill.energy=2200;fill.shape='DISK';fill.size=15;fo=bpy.data.objects.new(name+'fill',fill);scene.collection.objects.link(fo);fo.location=(6,-12,18);fo.rotation_euler=(center-fo.location).to_track_quat('-Z','Y').to_euler()
  scene.render.filepath=str(Path(art)/f'{name}_{view}.png');bpy.ops.render.render(write_still=True)
 return [list(low),list(high)]
def export(builder,art):
 import os,sys
 ext=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com';sys.path.insert(0,str(ext/'garrison'));sys.path.insert(0,str(ext));import importlib.util;spec=importlib.util.spec_from_file_location('garrison_shared',str(ext/'garrison/garrison_shared.cp313-win_amd64.pyd'));garrison_shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(garrison_shared);sys.modules['garrison_shared']=garrison_shared;sys.modules['garrison.garrison_shared']=garrison_shared;import garrison
 try:garrison.register()
 except Exception:pass
 from garrison import building_panel,material_adoption
 material_adoption.adopt_material(builder.mat);scene=bpy.context.scene;scene.garrison.asset_library_root='F:/aoe_4_temp/berber040_static_library';scene.garrison.game_asset_connection='C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json';scene.garrison.game_asset_index='C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3';builder.col['garrison_building_profile']='english-house';scene.garrison.author_collection=builder.col
 return building_panel.export_building(bpy.context,builder.col,Path(art)/'export_lod0')


