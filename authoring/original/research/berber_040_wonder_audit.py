import bpy,bmesh,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];art=root/'art/building_remix_0_4_0/wonder'
bpy.ops.wm.open_mainfile(filepath=str(art/'Berber_Koutoubia_Wonder_040.blend'));bpy.context.view_layer.update();parts=[o for o in bpy.data.collections['Koutoubia_original_lod0'].objects if o.type=='MESH'];rows=[];pts=[]
for o in parts:
 bm=bmesh.new();bm.from_mesh(o.data);rows.append({'name':o.name,'signed_volume':bm.calc_volume(signed=True),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'uv_layers':len(o.data.uv_layers),'mesh_users':o.data.users});bm.free();pts.extend(o.matrix_world@v.co for v in o.data.vertices)
bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
files=[p for p in art.rglob('*') if p.is_file() and p.suffix in ('.blend','.fbx','.json','.png') and not p.name.endswith('hashes.json')]
report={'bounds_local_evaluated':bounds,'triangles':sum(len(p.vertices)-2 for o in parts for p in o.data.polygons),'mesh_audit':rows,'nonmanifold_total':sum(r['nonmanifold_edges'] for r in rows),'native_runtime':'unverified'};(art/'geometry-audit.json').write_text(json.dumps(report,indent=2));(art/'source-hashes.json').write_text(json.dumps({str(p.relative_to(art)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2));print('WONDER_AUDIT',bounds,report['nonmanifold_total'])
