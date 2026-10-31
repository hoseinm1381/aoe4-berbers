import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ART=Path(__file__).parent;OUT=ROOT/'output/berber_update_0_2_5/authors/mill'
def inspect(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));rows={};points=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  data={'vertices':[tuple(v.co) for v in o.data.vertices],'polygons':[tuple(p.vertices) for p in o.data.polygons],'normals':[tuple(v.normal) for v in o.data.vertices],'uvs':{u.name:[tuple(x.uv) for x in u.data] for u in o.data.uv_layers}}
  rows[o.name]={'mesh_sha256':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),'dimensions':list(o.dimensions),'world_matrix':[list(r) for r in o.matrix_world]}
  points.extend(o.matrix_world@Vector(p) for p in o.bound_box)
 lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
 return {'objects':rows,'bounds_min':lo,'bounds_max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)]}
before=inspect(ART/'UNTOUCHED_Malian_Mill_Age1.blend');after=inspect(ART/'Berber_Mill_Age1_0_2_5.blend')
assert before==after,'Geometry, transforms, normals or UVs drifted'
(OUT/'dimension-validation.json').write_text(json.dumps({'status':'passed','stock':before,'remix':after,'geometry_uv_normals_transforms_identical':True,'ground_contact_unchanged':True,'scale_policy':'native donor 1.0; no old tiny 2x2 reference used'},indent=2)+'\n')
print('MILL_DIMENSIONS_AND_UVS_PASSED')
