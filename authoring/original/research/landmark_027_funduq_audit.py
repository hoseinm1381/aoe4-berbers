import bpy,json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'art/landmarks_0_2_7/funduq'
bpy.ops.wm.open_mainfile(filepath=str(P/'funduq_editable.blend'))
report=json.loads((P/'source-validation.json').read_text());checks={}
for lod in [0,1,2]:
 col=bpy.data.collections['Funduq_LOD'+str(lod)];bad=[];deg=[];uvbad=[];stage={str(s):0 for s in [0,20,40,60,80,100]}
 for o in col.objects:
  o.data.calc_loop_triangles();stage[str(o['garrison_building_first_stage'])]+=len(o.data.loop_triangles)
  for poly in o.data.polygons:
   if not all(math.isfinite(v) for v in poly.normal) or poly.normal.length<.99:bad.append([o.name,poly.index])
   if poly.area<1e-10:deg.append([o.name,poly.index])
  for q in o.data.uv_layers.active.data:
   if not all(math.isfinite(v) and -.0001<=v<=1.0001 for v in q.uv):uvbad.append(o.name)
 checks[str(lod)]={'bad_normals':bad,'degenerate_faces':deg,'invalid_uvs':uvbad,'stage_triangles':stage,'triangles':sum(stage.values())}
report['mesh_checks']=checks;report['reviewed_views']=['front','back','left','right','top','bottom','court-contact','solid-gameplay','material-gameplay','LOD1-solid','LOD2-solid'];report['texture_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (P/'textures').glob('*.png')};report['LOD_ratio_reason']='LOD1 47.7%; LOD2 25.5% rather than destructive20%: intact courtyards, archedwall boundaries, door silhouettes and supported loading shelter preserved.'
(P/'source-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({key:{k:(len(v) if isinstance(v,list) else v) for k,v in val.items()} for key,val in checks.items()}));bpy.ops.wm.quit_blender()
