"""Independently compare native geometry fields and opaque state spans."""
import os,sys,json,struct,hashlib,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'art/building_remix_0_2_6/barracks';O=R/'output/berber_update_0_2_6/authors/barracks';G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(G));from garrison_shared import relic_chunky as rc
rows=[]
for m in json.loads((A/'recipe.json').read_text())['models']:
 d=json.loads(Path(m['decode']).read_text());old=Path(d['geometry']['source']['path']).read_bytes();new=Path(m['native_geometry']).read_bytes();aa=list(rc.walk(rc.parse(old).roots));bb=list(rc.walk(rc.parse(new).roots));assert len(old)==len(new) and len(aa)==len(bb);count=0;verts=0;maxdot=0
 for a,b in zip(aa,bb):
  assert (a.kind,a.tag,a.name,a.version)==(b.kind,b.tag,b.name,b.version)
  if a.children:continue
  if a.payload==b.payload:continue
  assert a.tag==b'GEOB'
  n,_,stride,_=struct.unpack_from('<4I',a.payload);assert stride==24 and len(a.payload)==16+n*24;assert a.payload[:16]==b.payload[:16]
  for i in range(n):
   at=16+i*24;p=a.payload[at:at+24];q=b.payload[at:at+24];verts+=1
   if p==q:continue
   count+=1;op=struct.unpack_from('<4e',p);np=struct.unpack_from('<4e',q);assert op[0]==np[0] and op[2:]==np[2:] and np[1]<=op[1]+.002
   assert op[1]>2.15 and q[6:8]==p[6:8] and q[11]==p[11] and q[15]==p[15] and q[16:]==p[16:]
   nn=struct.unpack_from('<3b',q,8);tt=struct.unpack_from('<3b',q,12);l=lambda v:math.sqrt(sum(x*x for x in v));assert l(nn)>100 and l(tt)>100
   dot=abs(sum(x*y for x,y in zip(nn,tt))/(l(nn)*l(tt)));maxdot=max(dot,maxdot);assert dot<.025,(m['name'],i,dot)
 rows.append({'age':m['age'],'model':m['name'],'changed_vertices':count,'checked_vertex_records':verts,'source_sha256':hashlib.sha256(old).hexdigest(),'encoded_sha256':hashlib.sha256(new).hexdigest(),'max_normal_tangent_dot':maxdot,'native_chunk_structure_unchanged':True,'nonvertex_chunks_exact':True,'topology_uv_collection_indices_exact':True,'lower_2_15m_ground_and_all_xy_exact':True,'normal_tangent_handedness_exact':True})
result={'status':'passed','models':rows};(O/'encoding-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
