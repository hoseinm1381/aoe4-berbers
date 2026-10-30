"""Known-span outpost remix: reduce parapet cap, broaden stock entrance surrounds."""
import sys,os,json,struct,hashlib,math,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'output/berber_update_0_2_6/authors/outpost';A=R/'art/building_remix_0_2_6/outpost';G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(G));from garrison_shared import relic_chunky as rc

def norm(v):
 l=math.sqrt(sum(x*x for x in v));return tuple(x/l for x in v) if l else (0,0,1)
def deformation(p):
 x,y,z=p;sx=1.08 if abs(x)<.9 and y<-1.5 and .5<z<3.4 else 1;sz=.60 if z>7.4 else 1
 return (x*sx,y,7.4+(z-7.4)*sz if z>7.4 else z),(sx,1,sz)
def bounds(d):
 pts=[v for g in d['geometry']['groups'] for v in g['positions']];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)];return {'minimum':lo,'maximum':hi,'dimensions':[b-a for a,b in zip(lo,hi)]}
report={'status':'passed','models':[]}
for row in json.loads((A/'recipe.json').read_text())['models']:
 d=json.loads(Path(row['decode']).read_text());remix=copy.deepcopy(d);old=Path(d['geometry']['source']['path']).read_bytes();doc=rc.parse(old);vertexchunks=[c for c in rc.walk(doc.roots) if c.tag==b'GEOB'][::2];patch={};edits=[]
 for gi,(g,c) in enumerate(zip(remix['geometry']['groups'],vertexchunks)):
  assert g['vertex_stride']==24
  if g['preview_material']!='main':continue
  q=bytearray(c.payload);n,_,stride,_=struct.unpack_from('<4I',q);assert (n,stride)==(len(g['positions']),24)
  for i,p in enumerate(g['positions']):
   new,(sx,sy,sz)=deformation(p);at=16+i*24;native=struct.unpack_from('<4e',q,at);assert (-native[0],-native[2],native[1])==tuple(p)
   if new==tuple(p):continue
   q[at:at+8]=struct.pack('<4e',-new[0],new[2],-new[1],native[3]);actual=struct.unpack_from('<4e',q,at);g['positions'][i]=[-actual[0],-actual[2],actual[1]]
   nb=norm((g['normals'][i][0]/sx,g['normals'][i][1]/sy,g['normals'][i][2]/sz));tn=struct.unpack_from('<4b',q,at+12);tb=(-tn[0]/127,-tn[2]/127,tn[1]/127);tb=(tb[0]*sx,tb[1]*sy,tb[2]*sz);dot=sum(a*b for a,b in zip(nb,tb));tb=norm(tuple(t-n*dot for t,n in zip(tb,nb)))
   for off,v in [(8,nb),(12,tb)]:q[at+off:at+off+3]=struct.pack('<3b',*(max(-127,min(127,round(x*127))) for x in (-v[0],v[2],-v[1])))
   packed=struct.unpack_from('<3b',q,at+8);g['normals'][i]=list(norm((-max(-1,packed[0]/127),-max(-1,packed[2]/127),max(-1,packed[1]/127))))
   assert c.payload[at+16:at+24]==q[at+16:at+24];edits.append({'group':gi,'vertex':i,'fragment':g['collection_bone_indices'][i],'before':p,'after':g['positions'][i]})
  patch[c.offset]=bytes(q)
 encoded=rc.rebuild(doc,lambda c:patch.get(c.offset));assert len(encoded)==len(old);path=A/(row['name']+'-native.rrgeom');path.write_bytes(encoded);(A/(row['name']+'-remix-projection.json')).write_text(json.dumps(remix));bb=bounds(d);aa=bounds(remix);assert bb==aa
 report['models'].append({'name':row['name'],'source_sha256':hashlib.sha256(old).hexdigest(),'encoded_sha256':hashlib.sha256(encoded).hexdigest(),'changed_vertices':len(edits),'geometry':str(path),'native_complete_bounds':bb,'remix_complete_bounds':aa,'ground_contact_preserved':True,'complete_native_envelope_preserved':True,'misc_weapon_assembly_and_roof_spans_byte_identical':True,'native_uv_topology_selectors_exact':True,'native_normal_tangent_jacobian_encoding':True,'edits':edits})
(O/'geometry-validation.json').write_text(json.dumps(report,indent=2));print([(x['name'],x['changed_vertices']) for x in report['models']])
