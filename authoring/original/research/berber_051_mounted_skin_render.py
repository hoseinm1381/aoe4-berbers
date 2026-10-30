import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]; O=R/'art/unit_skin_0_5_1/mounted'
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def render(name):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'art/unit_remix_0_5_0/mounted/{name}/{name}.blend'))
 s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.world.color=(.65,.65,.65)
 c=bpy.data.objects['Berber candidate textured']; d=bpy.data.objects['Official donor textured']
 for o in [d,*d.children_recursive]:o.hide_render=True
 for o in c.children_recursive:o.hide_render=o.type=='MESH' and o.get('garrison_lod_level')!=1
 cd=bpy.data.cameras.new('Private face camera');cam=bpy.data.objects.new('Private face camera',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.ortho_scale=1.05
 riders=[o for o in c.children_recursive if o.type=='MESH' and o.get('garrison_lod_level')==1 and 'rider' in o.name.lower()]
 pts=[o.matrix_world@Vector(v) for o in riders for v in o.bound_box]; z=max(v.z for v in pts)-.23;x=sum(v.x for v in pts)/len(pts);y=sum(v.y for v in pts)/len(pts)
 if name.startswith(('mehari','sanhaja')):
  for o in c.children_recursive:
   if o.type=='MESH' and 'rider' not in o.name.lower():o.hide_render=True
  z=1.42;cd.ortho_scale=1.45
 target=(x,y,z);cam.location=(x+1.5,y-4,z+.25);aim(cam,target)
 ld=bpy.data.lights.new('Private face light','AREA');ld.energy=600;ld.size=4;li=bpy.data.objects.new('Private face light',ld);s.collection.objects.link(li);li.location=(x+1.4,y-2,z+2);aim(li,target)
 nodes=[]
 for o in c.children_recursive:
  if o.type!='MESH':continue
  for slot in o.material_slots:
   m=slot.material
   if not m or not m.use_nodes:continue
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image and ((name=='zenata_age04' and n.image.name=='rider-albedo.png') or (name!='zenata_age04' and 'skin' in n.name.lower() and 'tint' in n.name.lower())):
     if n not in nodes:nodes.append(n)
 print('SWAP',name,[(n.name,n.image.name) for n in nodes],flush=True)
 before=[n.image for n in nodes];folder=O/name;folder.mkdir(exist_ok=True)
 s.render.filepath=str(folder/'skin-before-face.png');bpy.ops.render.render(write_still=True)
 for n,old in zip(nodes,before):
  path=O/'zenata_age04/rider-albedo.png' if name=='zenata_age04' else R/'output/berber_update_0_5_1/baseline-inputs/eng_skin_tinting_lut.dds'
  im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=old.colorspace_settings.name;n.image=im
 s.render.filepath=str(folder/'skin-after-face.png');bpy.ops.render.render(write_still=True)
for name in sys.argv[sys.argv.index('--')+1:]:render(name)

