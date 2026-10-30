"""Supported Garrison construction export of the full source batch, on copies."""
import bpy,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_3_0';ART=OUT/'exports'
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison')
sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison import building_panel,material_adoption
batch=json.loads((ROOT/'Design/asset_overhaul/BUILDINGS_BATCH.json').read_text(encoding='utf-8'))
previous=json.loads((OUT/'export-report.json').read_text()) if (OUT/'export-report.json').exists() else None
report={'status':'running','assets':previous['assets'] if previous else [],'failures':[]}
completed={(x['key'],x['age']) for x in report['assets']}
for row in batch['rows']:
    if row['id']=='building.tent':continue
    for source in row['sources']:
        path=ROOT/source['path'];age=next((a for a in row['ages'] if 'age'+str(a) in path.name.lower()),None)
        if age is None:
            report['failures'].append({'source':str(path),'error':'Age cannot be resolved from source filename'});continue
        key=row['key']
        if (key,age) in completed:continue
        dest=OUT/'exports_final'/f'{key}_age{age}' if previous else ART/f'{key}_age{age}'
        try:
            bpy.ops.wm.open_mainfile(filepath=str(path))
            window=bpy.context.window_manager.windows[0]
            with bpy.context.temp_override(window=window):
                scene=bpy.context.scene
                scene.garrison.asset_library_root='E:/b30'
                scene.garrison.game_asset_connection=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json'
                scene.garrison.game_asset_index=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3'
                manifest=ROOT/f'art/buildings/{key}/age{age}_construction.json'
                document=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
                parts=document.get('parts',[])
                stages={p.get('object',p.get('name')):p.get('first_stage',p.get('stage')) for p in parts if isinstance(p,dict)}
                objects=[o for o in scene.objects if o.type=='MESH' and (o.name in stages if stages else not o.hide_render)]
                assert objects,('No primary construction objects',key,age)
                maps=ROOT/f'art/buildings/{key}'
                albedo=maps/'albedo.png';assert albedo.exists(),albedo
                # The batch uses shared UV atlas images across its role materials.
                material=bpy.data.materials.new('Berber_'+key+'_Atlas');material.use_nodes=True
                bsdf=material.node_tree.nodes.get('Principled BSDF')
                bsdf.inputs['Roughness'].default_value=.85
                atlas_size=tuple(bpy.data.images.load(str(albedo),check_existing=True).size)
                def matching_image(imagepath,role):
                    image=bpy.data.images.load(str(imagepath),check_existing=True)
                    if tuple(image.size)!=atlas_size:
                        image=image.copy();image.scale(*atlas_size)
                        folder=OUT/'normalized_maps'/f'{key}_age{age}';folder.mkdir(parents=True,exist_ok=True)
                        image.filepath_raw=str(folder/(role+'.png'));image.file_format='PNG';image.save()
                        image=bpy.data.images.load(image.filepath_raw,check_existing=False)
                    if role!='albedo':image.colorspace_settings.name='Non-Color'
                    return image
                uv=material.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map=objects[0].data.uv_layers.active.name
                for role,socket in [('albedo','Base Color'),('roughness','Roughness'),('metalness','Metallic')]:
                    imagepath=maps/(role+'.png')
                    if not imagepath.exists():continue
                    image=matching_image(imagepath,role)
                    tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
                    material.node_tree.links.new(uv.outputs['UV'],tex.inputs['Vector']);material.node_tree.links.new(tex.outputs['Color'],bsdf.inputs[socket])
                normalpath=maps/'normal.png'
                if normalpath.exists():
                    image=matching_image(normalpath,'normal')
                    tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
                    normal=material.node_tree.nodes.new('ShaderNodeNormalMap');normal.uv_map=uv.uv_map
                    material.node_tree.links.new(uv.outputs['UV'],tex.inputs['Vector']);material.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);material.node_tree.links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
                collection=bpy.data.collections.new('RELEASE_'+key+'_'+str(age));scene.collection.children.link(collection)
                for obj in objects:
                    clone=obj.copy();clone.data=obj.data.copy();collection.objects.link(clone)
                    world=obj.matrix_world.copy();clone.parent=None;clone.matrix_world=world
                    clone.hide_viewport=False;clone.hide_render=False;clone.hide_set(False)
                    clone.data.materials.clear();clone.data.materials.append(material)
                    for face in clone.data.polygons:face.material_index=0
                    clone.data.uv_layers.active.name=uv.uv_map
                    stage=stages.get(obj.name,obj.get('garrison_building_first_stage'))
                    assert stage is not None,('Missing explicit stage',obj.name)
                    stage=int(stage);assert stage in (0,20,40,60,80,100),(obj.name,stage)
                    clone['garrison_building_first_stage']=stage
                bpy.context.view_layer.update();scene.garrison.author_collection=collection
                collection['garrison_building_profile']='english-house';material_adoption.adopt_material(material)
                result=building_panel.export_building(bpy.context,collection,dest)
                report['assets'].append({'key':key,'age':age,'source':str(path),'export':str(dest),'name':f'{key}_age{age}','parts':len(result['parts'])})
                print('EXPORTED',key,age,flush=True)
        except Exception:
            error=traceback.format_exc();report['failures'].append({'key':key,'age':age,'source':str(path),'error':error});print('EXPORT_FAILED',key,age,error,flush=True)
        (OUT/'export-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
report['status']='passed' if not report['failures'] and len(report['assets'])==92 else 'failed'
(OUT/'export-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('EXPORT_BATCH_FINISHED',len(report['assets']),len(report['failures']),flush=True)
bpy.ops.wm.quit_blender()
