"""Isolated name-only authoring probe; preserves original release and geometry."""
import bpy,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'art/landmarks_0_2_7/ribat';ART=ROOT/'art/landmarks_0_2_7_1/ribat';ART.mkdir(parents=True,exist_ok=True)
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison');sys.path[:0]=[str(EXT),str(EXT.parent)]
import garrison_shared
sys.modules['garrison.garrison_shared']=garrison_shared
import garrison;garrison.register()
from garrison import building_panel,material_adoption,model_preflight_ui
bpy.ops.wm.open_mainfile(filepath=str(OLD/'ribat_of_sanhaja.blend'))
def geometry_digest():
 h=hashlib.sha256()
 for o in sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda o:o.name):
  h.update(o.name.encode());h.update(bytes(o.data.vertices.foreach_get('co',[0.0]*(len(o.data.vertices)*3)) or [])) if False else None
  h.update(repr([tuple(v.co) for v in o.data.vertices]).encode());h.update(repr([tuple(v.vertices) for v in o.data.polygons]).encode());h.update(repr([tuple(u.uv) for u in o.data.uv_layers.active.data]).encode());h.update(repr([tuple(row) for row in o.matrix_world]).encode())
 return h.hexdigest()
before=geometry_digest();m=bpy.data.materials['BerberRibat_OriginalAtlas2048'];m.name='BerberRibat'
scene=bpy.context.scene;scene.garrison.asset_library_root=str(ART/'library');scene.garrison.game_asset_connection=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json';scene.garrison.game_asset_index=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3'
material_adoption.adopt_material(m)
reports=[]
for lod in range(3):
 lc=bpy.data.collections[f'Ribat_LOD{lod}'];lc.hide_viewport=False;lc.hide_render=False;lc['garrison_building_profile']='english-house'
 for col in bpy.data.collections:
  if col.name.startswith('Ribat_LOD') and col!=lc:col.hide_viewport=True;col.hide_render=True
 for ob in lc.objects:ob.hide_set(False)
 bpy.context.view_layer.update();scene.garrison.author_collection=lc
 model_preflight_ui.require_valid(list(lc.objects),bpy.context)
 reports.append(building_panel.export_building(bpy.context,lc,ART/f'export_lod{lod}'))
 lc.hide_viewport=True;lc.hide_render=True
bpy.data.collections['Ribat_LOD0'].hide_viewport=False;bpy.data.collections['Ribat_LOD0'].hide_render=False
assert before==geometry_digest(),'Geometry/UV/placement changed during material rename'
validation=json.loads((OLD/'source-validation.json').read_text());validation['material_identifier_hotfix']='BerberRibat';(ART/'source-validation.json').write_text(json.dumps(validation,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'ribat_of_sanhaja.blend'))
(ART/'name-only-source-evidence.json').write_text(json.dumps({'geometry_uv_placement_sha256_before':before,'geometry_uv_placement_sha256_after':geometry_digest(),'material_name_before':'BerberRibat_OriginalAtlas2048','material_name_after':'BerberRibat','native_collection_name_expected':'berberribat_collection','geometry_changes':False,'texture_inputs':str(OLD/'textures'),'hypothesis':'Native material-name compatibility; runtime fix requires retest'},indent=2))
print('NAME_ONLY_SOURCE_EXPORTED')
