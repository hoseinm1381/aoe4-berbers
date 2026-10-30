"""Three explicit single-level construction FBXs with stable logical identities."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7/qualification'
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison')
sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison import building_panel
report=[]
for lod,segments in [(0,4),(1,2),(2,0)]:
 bpy.ops.wm.open_mainfile(filepath=str(OUT/'fixture.blend'))
 col=bpy.data.collections['NewGeometryFixture'];parts=[]
 for obj in sorted(col.all_objects,key=lambda o:o.name):
  if obj.type!='MESH':continue
  bpy.context.view_layer.objects.active=obj
  if segments:
   mod=obj.modifiers.new('Detail bevel','BEVEL');mod.width=.035;mod.segments=segments
   bpy.ops.object.modifier_apply(modifier=mod.name)
  points=[obj.matrix_world@v.co for v in obj.data.vertices]
  parts.append({'name':obj.name,'first_stage':obj['garrison_building_first_stage'],'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'bounds':[[min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)]]})
 folder=OUT/f'lod{lod}-source';manifest=building_panel.export_building(bpy.context,col,folder)
 report.append({'lod':lod,'parts':parts,'manifest':manifest,'triangles':sum(p['triangles'] for p in parts),'source':str(folder)})
(OUT/'independent-lod-source.json').write_text(json.dumps(report,indent=2))
print('INDEPENDENT_LOD_EXPORTS',[(r['lod'],r['triangles']) for r in report],flush=True)
bpy.ops.wm.quit_blender()
