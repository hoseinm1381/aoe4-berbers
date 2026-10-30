"""Edit/export disposable building and unit copies; never save source scenes."""
import bpy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/berber_update_1_0_5')
sources=[ROOT/'art/building_remix_0_2_6/house/Berber_House_Age1_0_2_6.blend',ROOT/'art/unit_remix_0_5_0/mounted/zenata_age03/zenata_age03.blend']
rows=[]
for source in sources:
 before=hashlib.sha256(source.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
 meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.data.vertices]
 assert meshes
 meshes[0].data.vertices[0].co.x+=0.001
 bpy.ops.object.select_all(action='DESELECT')
 for obj in meshes:obj.hide_set(False);obj.hide_viewport=False;obj.select_set(True)
 bpy.context.view_layer.objects.active=meshes[0]
 target=OUT/'work/blender-edit-probes'/(source.stem+'.fbx');target.parent.mkdir(parents=True,exist_ok=True)
 status=bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'MESH'},bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
 assert 'FINISHED' in status and target.stat().st_size>0
 assert hashlib.sha256(source.read_bytes()).hexdigest()==before
 rows.append({'source':str(source),'source_sha256':before,'disposable_fbx_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'meshes':len(meshes),'memory_vertex_edit':True,'source_unchanged':True})
(OUT/'blender-edit-probes.json').write_text(json.dumps({'status':'passed','blender':bpy.app.version_string,'examples':rows,'scope':'Blender source edit and FBX export; native geometry composition has separate evidence'},indent=2))
