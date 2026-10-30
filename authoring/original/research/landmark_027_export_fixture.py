"""Small new-topology building fixture; never touches the user's Blender process."""
import bpy,sys,json,traceback,inspect
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/berber_update_0_2_7/qualification'
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison')
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(EXT.parent))
import garrison
garrison.register()
from garrison import building_panel,material_adoption
report={'status':'running','source_route':'building_panel.export_building','new_geometry':True,'native_runtime':'pending'}
try:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 scene=bpy.context.scene
 scene.garrison.asset_library_root=str(OUT/'library')
 scene.garrison.game_asset_connection=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json'
 scene.garrison.game_asset_index=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3'
 material=bpy.data.materials.new('Earthen fixture');material.use_nodes=True
 bsdf=material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.43,.24,.12,1);bsdf.inputs['Roughness'].default_value=.83
 material_adoption.adopt_material(material)
 col=bpy.data.collections.new('NewGeometryFixture');scene.collection.children.link(col)
 parts=[]
 for stage,location,size in [(0,(0,0,.15),(4,4,.3)),(20,(0,0,1.0),(3.8,3.8,1.4)),(40,(0,0,1.9),(3.6,3.6,.4)),(60,(0,0,2.25),(3.8,3.8,.3)),(80,(0,0,2.6),(2,2,.4)),(100,(0,0,3.1),(1,1,.6))]:
  bpy.ops.mesh.primitive_cube_add(size=1,location=location);obj=bpy.context.object;obj.name=f'FixtureStage{stage}'
  obj.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  for c in list(obj.users_collection):c.objects.unlink(obj)
  col.objects.link(obj);obj.data.materials.append(material);obj['garrison_building_first_stage']=stage
  parts.append({'name':obj.name,'first_stage':stage,'triangles':12})
 col['garrison_building_profile']='english-house';scene.garrison.author_collection=col
 report['parts']=parts;report['manifest']=building_panel.export_building(bpy.context,col,OUT/'source')
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'fixture.blend'))
 report['api']={n:str(inspect.signature(v)) for n,v in vars(building_panel).items() if inspect.isfunction(v) and not n.startswith('_')}
 report['status']='source-export-passed'
except Exception:
 report['status']='failed';report['error']=traceback.format_exc();traceback.print_exc()
finally:
 (OUT/'export-evidence.json').write_text(json.dumps(report,indent=2))
 bpy.ops.wm.quit_blender()
