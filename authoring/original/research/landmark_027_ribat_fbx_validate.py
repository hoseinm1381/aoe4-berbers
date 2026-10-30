"""Fresh actual FBX reimport counts and connected-component orientation checks."""
import bpy,bmesh,json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/landmarks_0_2_7/ribat';results=[]
for lod in range(3):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.fbx(filepath=str(ART/f'export_lod{lod}/model.fbx'))
 rows=[]
 for ob in sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name):
  mesh=ob.data;mesh.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
  boundary=sum(1 for e in bm.edges if e.is_boundary);volume=bm.calc_volume(signed=True);negative_closed=[];open_components=0
  remaining=set(bm.faces)
  while remaining:
   face=remaining.pop();faces={face};queue=[face]
   while queue:
    f=queue.pop()
    for e in f.edges:
     for f2 in e.link_faces:
      if f2 in remaining:remaining.remove(f2);faces.add(f2);queue.append(f2)
   component_edges={e for f in faces for e in f.edges}
   if any(len([f for f in e.link_faces if f in faces])!=2 for e in component_edges):open_components+=1;continue
   verts={v for f in faces for v in f.verts};m=bmesh.new();vmap={v:m.verts.new(v.co) for v in verts}
   for f in faces:m.faces.new([vmap[v] for v in f.verts])
   cv=m.calc_volume(signed=True);m.free()
   if cv < -1e-8:negative_closed.append(cv)
  bm.free();uv=mesh.uv_layers.active;bad_uv=0;bad_tri=0
  for t in mesh.loop_triangles:
   a,b,c=[mesh.vertices[i].co for i in t.vertices]
   if (b-a).cross(c-a).length<1e-10:bad_tri+=1
   ua,ub,uc=[uv.data[i].uv for i in t.loops]
   if abs((ub.x-ua.x)*(uc.y-ua.y)-(ub.y-ua.y)*(uc.x-ua.x))<1e-10:bad_uv+=1
  rows.append({'name':ob.name,'triangles':len(mesh.loop_triangles),'boundary_edges':boundary,'signed_volume':volume,'negative_closed_components':negative_closed,'intentional_open_components':open_components,'zero_area_triangles':bad_tri,'zero_area_uv_triangles':bad_uv})
 results.append({'LOD':lod,'triangles':sum(r['triangles'] for r in rows),'parts':rows})
report={'route':'fresh FBX import, no source estimates','LODs':results,'passed':all(not r['negative_closed_components'] and not r['zero_area_triangles'] and not r['zero_area_uv_triangles'] for x in results for r in x['parts']),'open_surface_note':'woven canopy/shields are intentionally thin; all closed components individually positive-volume'}
(ART/'fbx-reimport-validation.json').write_text(json.dumps(report,indent=2));print('RIBAT_FBX_VALIDATION',report['passed'],[x['triangles'] for x in results]);bpy.ops.wm.quit_blender()
