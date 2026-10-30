"""Independent field-boundary checks for surgical stock windmill encoding."""
import sys,os,json,struct,hashlib,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'output/berber_update_0_2_6/authors/windmill';A=R/'art/building_remix_0_2_6/windmill';G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(G));from garrison_shared import relic_chunky as rc
s=json.loads(next((O/'stock').glob('*/decoded-static.json')).read_text());report=json.loads((O/'geometry-validation.json').read_text());old=Path(s['geometry']['source']['path']).read_bytes();new=(A/'native-remix.rrgeom').read_bytes();aa=list(rc.walk(rc.parse(old).roots));bb=list(rc.walk(rc.parse(new).roots));assert len(old)==len(new) and len(aa)==len(bb)
oldgeob=[c for c in aa if c.tag==b'GEOB'];newgeob=[c for c in bb if c.tag==b'GEOB'];p=oldgeob[2].payload;q=newgeob[2].payload;changed={e['vertex'] for e in report['edits']};n,_,stride,_=struct.unpack_from('<4I',p);assert n==11592 and stride==24
for a,b in zip(aa,bb):
 assert (a.kind,a.tag,a.name,a.version)==(b.kind,b.tag,b.name,b.version)
 if a.kind==b'DATA' and a.offset!=oldgeob[2].offset:assert a.payload==b.payload
errors=[];maxdot=0
for i in range(n):
 at=16+i*24
 if i not in changed:assert p[at:at+24]==q[at:at+24]
 else:
  assert p[at+6:at+8]==q[at+6:at+8] # opaque pos w
  assert p[at+11]==q[at+11] and p[at+15]==q[at+15] # normal/tangent w
  assert p[at+16:at+24]==q[at+16:at+24] # both UV sets/selector bytes
  v=struct.unpack_from('<4e',q,at);assert all(math.isfinite(x) for x in v)
  nn=struct.unpack_from('<3b',q,at+8);tt=struct.unpack_from('<3b',q,at+12);l=lambda v:math.sqrt(sum(x*x for x in v));assert l(nn)>100 and l(tt)>100
  dot=abs(sum(x*y for x,y in zip(nn,tt))/(l(nn)*l(tt)));maxdot=max(maxdot,dot);assert dot<.025,(i,dot)
assert oldgeob[0].payload==newgeob[0].payload # fans
result={'status':'passed','vertices_checked':n,'changed_vertices':len(changed),'fans_vertices_protected':720,'native_chunk_structure_equal':True,'nonvertex_native_chunks_exact':True,'unmodified_vertex_records_exact':True,'positions_w_normal_tangent_w_uv_selectors_exact':True,'edited_normals_tangents_valid':True,'max_normal_tangent_dot':maxdot,'source_sha256':hashlib.sha256(old).hexdigest(),'encoded_sha256':hashlib.sha256(new).hexdigest()}
(O/'encoding-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
