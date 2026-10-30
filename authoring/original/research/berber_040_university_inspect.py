"""Read-only donor inspection; no production geometry."""
import bpy,json,sys,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_4_0/university';ART.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'research'))
from berber_040_integrate_cache import read_cached_json
sys.path.insert(0,str(Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com'))
from garrison.decode_projection import _apply_decoded_static
reports=[]
for directory in Path('F:/aoe_4_temp/berber_040_university_donors').iterdir():
 if not directory.is_dir():continue
 p=directory/'decoded-static.json'
 if not p.exists() and not (directory/'rebuild-cache.json').exists():continue
 bpy.ops.wm.read_factory_settings(use_empty=True); d=read_cached_json(p);label='abb' if 'abbasids' in d['request']['logical_path'] else 'mal'
 proxy=bpy.data.objects.new('reference_'+label,None);bpy.context.scene.collection.objects.link(proxy);proxy['garrison_decode_manifest']=str(p);proxy['garrison_logical_path']=d['request']['logical_path'];r=_apply_decoded_static(proxy,d,create_controls=False)
 meshes=[o for o in r.children_recursive if o.type=='MESH'];pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);center=(lo+hi)/2
 scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.render.resolution_x=1000;scene.render.resolution_y=900;scene.render.resolution_percentage=100
 camd=bpy.data.cameras.new('reference camera');cam=bpy.data.objects.new('reference camera',camd);scene.collection.objects.link(cam);scene.camera=cam;camd.type='ORTHO';camd.ortho_scale=max(hi-lo)*1.45
 paths=[]
 for view,offset in [('gamecamera',(1,-1,.95)),('top',(0,0,1)),('front',(0,-1,.1))]:
  cam.location=center+Vector(offset)*30;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ART/f'donor_{label}_{view}.png');bpy.ops.render.render(write_still=True);paths.append(scene.render.filepath)
 scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
 scene.world=bpy.data.worlds.new('reference world');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.8
 ld=bpy.data.lights.new('reference sun','SUN');ld.energy=3;ob=bpy.data.objects.new('reference sun',ld);scene.collection.objects.link(ob);ob.rotation_euler=(.4,-.3,-.5)
 cam.location=center+Vector((1,-1,.95))*30;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ART/f'donor_{label}_textured.png');bpy.ops.render.render(write_still=True);paths.append(scene.render.filepath)
 reports.append({'donor':d['request']['logical_path'],'decode':str(p),'bounds':[list(lo),list(hi)],'mesh_groups':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'source_geometry':d['geometry']['source'],'captures':paths,'native_runtime':'unverified'})
(ART/'donor-inspection.json').write_text(json.dumps(reports,indent=2));print('DONOR_INSPECTION_DONE')
