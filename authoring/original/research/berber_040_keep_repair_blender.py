"""Background-only editable native040 projection and bounded inspection captures.
Usage blender --background --python this.py -- keep (or marrakech/siege).
"""
import bpy,json,sys,os,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from berber_040_integrate_cache import read_cached_json
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com'
sys.path.insert(0,str(EXT))
from garrison.decode_projection import _apply_decoded_static
family=sys.argv[sys.argv.index('--')+1]
ART=ROOT/'art/building_remix_0_4_0'/family
recipe=json.loads((ART/'recipe.json').read_text())
reports=[]
for row in recipe['models']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
 before=json.loads(Path(row['decoded']).read_text());after=read_cached_json(Path(row['remix_projection']))
 proxy=bpy.data.objects.new('040 donor decode contract',None);bpy.context.scene.collection.objects.link(proxy)
 proxy['garrison_decode_manifest']=row['decoded'];proxy['garrison_logical_path']=before['request']['logical_path']
 root=_apply_decoded_static(proxy,before,create_controls=False)
 root.name=f'040_{row["name"]}_WHOLE_native_building'
 meshes=[o for o in root.children_recursive if o.type=='MESH'];used=set()
 for ob in meshes:
  choices=[(i,g) for i,g in enumerate(before['geometry']['groups']) if i not in used and len(g['positions'])==len(ob.data.vertices) and tuple(g['positions'][0])==tuple(ob.data.vertices[0].co)]
  assert len(choices)==1,(ob.name,len(choices))
  i,g=choices[0];used.add(i);new=after['geometry']['groups'][i]
  ob.data.vertices.foreach_set('co',[c for p in new['positions'] for c in p]);ob.data.update()
  ob.data.normals_split_custom_set_from_vertices(new['normals'])
  ob['040_source_group']=g['name'];ob['040_native_rrgeom']=row['native_geometry']
  ob['040_excludes']='No031 bastion/yard kit or inherited stamp architectural overlays'
 carriers={c['name']:c['image'] for c in row.get('texture_inputs',[])}
 for ob in meshes:
  slot=ob.get('garrison_material_slot','')
  spec=next((m for m in row.get('materials',[]) if m['name']==slot),None)
  if spec:
   for mat in ob.data.materials:
    if mat and mat.node_tree:
     for edit in spec['repaint']:
      node=mat.node_tree.nodes.get('Essence '+chr(183)+' '+edit['slot'])
      assert node is not None,(mat.name,edit['slot'])
      node.image=bpy.data.images.load(carriers[edit['carrier']],check_existing=True)
 assert len(used)==len(before['geometry']['groups'])
 scene=bpy.context.scene;scene['040_contract']='One coherent native donor; original native selectors and owner masks retained in game resources'
 scene['040_preview_limit']='Decoded partitions shown together. Native damage/construction/upgrade selector rendering requires game test.'
 scene['040_recipe']=str(ART/'recipe.json')
 scene.render.resolution_x=900;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG';scene.world=bpy.data.worlds.new('040 neutral world');scene.world.color=(.35,.35,.35)
 low,hi=row['bounds_m'];center=Vector([(a+b)/2 for a,b in zip(low,hi)])
 camd=bpy.data.cameras.new('040 review camera');cam=bpy.data.objects.new('040 review camera',camd);scene.collection.objects.link(cam);scene.camera=cam
 camd.type='ORTHO';camd.ortho_scale=max(b-a for a,b in zip(low,hi))*1.4
 scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.65,.65,.65);scene.display.shading.show_cavity=True
 paths=[]
 for name,d in {'front':(0,-1,0),'back':(0,1,0),'left':(-1,0,0),'right':(1,0,0),'top':(0,0,1),'bottom':(0,0,-1)}.items():
  cam.location=center+Vector(d)*35;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  scene.render.filepath=str(ART/f'{row["name"]}_solid_{name}.png');bpy.ops.render.render(write_still=True);paths.append(scene.render.filepath)
 cam.location=center+Vector((1,-1,.95))*25;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
 scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.65,.7,.8,1);scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.6
 sun=bpy.data.lights.new('040 sun','SUN');sun.energy=2.5;so=bpy.data.objects.new('040 sun',sun);scene.collection.objects.link(so);so.rotation_euler=(math.radians(30),math.radians(-20),math.radians(-30))
 scene.render.filepath=str(ART/f'{row["name"]}_textured_gamecamera.png');bpy.ops.render.render(write_still=True);paths.append(scene.render.filepath)
 missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()]
 assert not missing,missing
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=row['blend'])
 reports.append({'model':row['name'],'blend':row['blend'],'bounds_m':row['bounds_m'],'source_checks':row['source_checks'],'mesh_groups':len(meshes),'packed_images':len([im for im in bpy.data.images if im.packed_file]),'captures':paths,'native_runtime':'unverified','preview_limit':scene['040_preview_limit']})
 print('040_COHERENT_SOURCE_SAVED',row['name'],flush=True)
(ART/'source-review.json').write_text(json.dumps(reports,indent=2)+'\n')
