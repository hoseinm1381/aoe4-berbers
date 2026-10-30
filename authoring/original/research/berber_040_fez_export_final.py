import bpy,bmesh,sys,os,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ext=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com';sys.path.insert(0,str(ext/'garrison'));sys.path.insert(0,str(ext));import garrison_shared;sys.modules['garrison.garrison_shared']=garrison_shared;import garrison
try:garrison.register()
except:pass
from garrison import building_panel,material_adoption
kind=sys.argv[-1];art=ROOT/'art/building_remix_0_4_0'/kind;bpy.ops.wm.open_mainfile(filepath=str(art/(kind+'_040_original.blend')));col=bpy.data.collections['040_original_'+kind]
parts=[o for o in col.objects if o.type=='MESH']
from mathutils import Vector
def bounds(o):
 pts=[o.matrix_world@v.co for v in o.data.vertices];return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
mesh_checks=[]
for ob in parts:
 bm=bmesh.new();bm.from_mesh(ob.data);mesh_checks.append({'name':ob.name,'signed_volume':bm.calc_volume(signed=True),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)});bm.free()
def segment_hits(start,end):
 hits=[];start=Vector(start);end=Vector(end)
 for ob in parts:
  inv=ob.matrix_world.inverted();a=inv@start;b=inv@end;delta=b-a;hit,loc,norm,index=ob.ray_cast(a,delta.normalized(),distance=delta.length)
  if hit:hits.append(ob.name)
 return hits
opening_hits=segment_hits((0,-8,1.5),(0,-4,1.5)) if kind=='fez' else segment_hits((0,-7.2,1.5),(0,-6.03,1.5))
report={'normal_topology_checks':mesh_checks,'source_portal_masonry_segment_hits':opening_hits,'portal_opening_pass':not opening_hits,'parts':[{'name':o.name,'bounds':bounds(o),'stage':o.get('garrison_building_first_stage'),'uv':len(o.data.uv_layers),'mesh_users':o.data.users} for o in parts],'triangles':sum(len(p.vertices)-2 for o in parts for p in o.data.polygons),'native_game':'unverified','texture_sha256':hashlib.sha256((art/'atlas_albedo_v2.png').read_bytes()).hexdigest()}
(art/'geometry-audit.json').write_text(json.dumps(report,indent=2))

for mat in bpy.data.materials:
 if mat.use_nodes:material_adoption.adopt_material(mat)
if '--audit' not in sys.argv:
 building_panel.export_building(bpy.context,col,art/'export_lod0_v2');bpy.ops.wm.save_as_mainfile(filepath=str(art/(kind+'_040_original.blend')))
