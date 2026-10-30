"""Native FBX naming trial, explicit geometric LODs rather than duplicated sources."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7/qualification'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'fixture.blend'))
sources=[o for o in bpy.data.objects if o.type=='MESH'];copies=[]
for obj in sources:
 stage=obj.get('garrison_building_first_stage');index=[0,100,20,40,60,80].index(stage)
 obj.name=f'garrison_part_{index:04}_lod1';obj.data.name=obj.name
 for lod in [2,3]:
  clone=obj.copy();clone.data=obj.data.copy();bpy.context.scene.collection.objects.link(clone)
  clone.name=f'garrison_part_{index:04}_lod{lod}';clone.data.name=clone.name;copies.append(clone)
  # Distinct reduced geometry, not only renamed copies.
  mod=clone.modifiers.new('Lower LOD','DECIMATE');mod.ratio=.5 if lod==2 else .25
  bpy.context.view_layer.objects.active=clone;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.object.select_all(action='DESELECT')
for obj in sources+copies:obj.select_set(True)
folder=OUT/'lod-source';folder.mkdir(exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(folder/'model.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y')
(folder/'source-check.json').write_text(json.dumps({'objects':[{ 'name':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in sources+copies]},indent=2))
bpy.ops.wm.quit_blender()
