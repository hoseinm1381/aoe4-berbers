"""Installed native Garrison source export; isolated factory process avoids other compiled-addon loader collision."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/landmarks_0_2_7/ribat'
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison');sys.path.insert(0,str(EXT));sys.path.insert(0,str(EXT.parent))
import garrison_shared
sys.modules['garrison.garrison_shared']=garrison_shared
import garrison;garrison.register()
from garrison import building_panel,material_adoption,model_preflight_ui
bpy.ops.wm.open_mainfile(filepath=str(ART/'ribat_of_sanhaja.blend'))
scene=bpy.context.scene;scene.garrison.asset_library_root=str(ART/'library027');scene.garrison.game_asset_connection=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json';scene.garrison.game_asset_index=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3'
mat=bpy.data.materials['BerberRibat_OriginalAtlas2048'];material_adoption.adopt_material(mat)
reports={}
for lod in range(3):
 lc=bpy.data.collections[f'Ribat_LOD{lod}'];lc.hide_viewport=False;lc.hide_render=False;lc['garrison_building_profile']='english-house'
 for col in bpy.data.collections:
  if col.name.startswith('Ribat_LOD') and col!=lc:col.hide_viewport=True;col.hide_render=True
 for ob in lc.objects:ob.hide_set(False)
 bpy.context.view_layer.update();scene.garrison.author_collection=lc
 preflight=model_preflight_ui.require_valid(list(lc.objects),bpy.context)
 manifest=building_panel.export_building(bpy.context,lc,ART/f'export_lod{lod}')
 reports[str(lod)]={'source':str(ART/f'export_lod{lod}'),'manifest':manifest,'preflight':preflight,'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in lc.objects)}
 lc.hide_viewport=True;lc.hide_render=True
bpy.data.collections['Ribat_LOD0'].hide_viewport=False;bpy.data.collections['Ribat_LOD0'].hide_render=False
(ART/'export.json').write_text(json.dumps({'project_name':'br027_ribat','route':'installed building_panel.export_building','bootstrap':'factory-startup avoids compiled addon loader collision; garrison_shared alias','LODs':reports,'native_owner_flags_excluded':True},indent=2))
validation=json.loads((ART/'source-validation.json').read_text());validation['export_manifests']=[reports[str(i)]['manifest'] for i in range(3)];validation['source_preflight']='passed all3LODs';(ART/'source-validation.json').write_text(json.dumps(validation,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'ribat_of_sanhaja.blend'))
print('RIBAT_GARRISON_EXPORT_PASSED',json.dumps({k:v['triangles'] for k,v in reports.items()}));bpy.ops.wm.quit_blender()
