import bpy,bmesh,json,math
from pathlib import Path
P=Path(__file__).parent;O=P.parents[2]/'output/buildings_batch/mining'
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(P/f'Berber_Mining_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   rows=[]
   for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data);o.data.calc_loop_triangles();uv=o.data.uv_layers.active;areas=[]
    for t in o.data.loop_triangles:
     a,b,c=[uv.data[i].uv for i in t.loops];areas.append(abs((b-a).cross(c-a))*.5)
    rows.append({'object':o.name,'non_manifold':sum(not e.is_manifold for e in bm.edges),'degenerate':sum(f.calc_area()<1e-10 for f in bm.faces),'outward_signed_volume':bm.calc_volume(signed=True),'finite':all(math.isfinite(v) for p in o.data.vertices for v in p.co),'positive_scale':all(v>0 for v in o.scale),'minimum_uv_triangle_area':min(areas),'triangles':len(areas)});bm.free()
   assert all(c['non_manifold']==0 and c['degenerate']==0 and c['outward_signed_volume']>0 and c['finite'] and c['positive_scale'] and c['minimum_uv_triangle_area']>1e-10 for c in rows)
   packed=[{'name':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if im.name.startswith('Mining_')];assert all(v['packed'] for v in packed)
   path=O/f'age{age}_validation.json';d=json.loads(path.read_text());d['objects']=rows;d['final_saved_source_reaudit']=True;d['packed_images']=packed;path.write_text(json.dumps(d,indent=2));print(age,len(rows),sum(r['triangles'] for r in rows),flush=True)
finally:bpy.ops.wm.quit_blender()
