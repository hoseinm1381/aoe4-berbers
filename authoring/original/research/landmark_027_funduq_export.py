"""Isolated installed-Garrison source export: six merged stages per geometric LOD."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'art/landmarks_0_2_7/funduq'
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison');sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison import building_panel,material_adoption
bpy.ops.wm.open_mainfile(filepath=str(OUT/'funduq_editable.blend'))
s=bpy.context.scene;s.garrison.asset_library_root=str(OUT/'library');s.garrison.game_asset_connection=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json';s.garrison.game_asset_index=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3'
mat=bpy.data.materials.get('FunduqOriginalAtlas');material_adoption.adopt_material(mat)
reports={}
for lod in [0,1,2]:
 col=bpy.data.collections['Funduq_LOD'+str(lod)];col.hide_viewport=False;col.hide_render=False
 for other in bpy.data.collections:
  if other.name.startswith('Funduq_LOD') and other!=col:other.hide_viewport=True;other.hide_render=True
 stagecounts={}
 for stage in [0,20,40,60,80,100]:
  objs=[o for o in col.objects if o.type=='MESH' and o.get('garrison_building_first_stage')==stage]
  bpy.ops.object.select_all(action='DESELECT')
  for o in objs:o.hide_set(False);o.select_set(True)
  bpy.context.view_layer.objects.active=objs[0]
  if len(objs)>1:bpy.ops.object.join()
  merged=bpy.context.object;merged.name=f'FunduqStage{stage:03d}';merged['garrison_building_first_stage']=stage
  merged.data.calc_loop_triangles();stagecounts[str(stage)]=len(merged.data.loop_triangles)
 col['garrison_building_profile']='english-house';s.garrison.author_collection=col
 folder=OUT/f'export_lod{lod}';manifest=building_panel.export_building(bpy.context,col,folder)
 reports[str(lod)]={'folder':str(folder),'manifest':manifest,'stage_triangles':stagecounts,'triangles':sum(stagecounts.values())}
 col.hide_viewport=True;col.hide_render=True
(OUT/'export.json').write_text(json.dumps({'route':'installed building_panel.export_building','LODs':reports,'native_cook':'root pending'},indent=2));print(json.dumps(reports))
bpy.ops.wm.quit_blender()

