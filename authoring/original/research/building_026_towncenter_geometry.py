"""Patch verified native vertex spans; preserve native topology, UVs and state data."""
import os,sys,json,struct,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/towncenter';OUT=ROOT/'output/berber_update_0_2_6/authors/towncenter'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(EXT));from garrison_shared import relic_chunky as rc
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def deform(p):
 x,y,z=p
 # Preserve native roof/flag mounts and ground; refine lower arch profiles.
 if z<=1.0 or z>=3.8:return p,1.0
 t=(z-1.0)/2.8
 return (x,y,z-.24*math.sin(math.pi*t)**2),1-.24*math.pi/2.8*math.sin(2*math.pi*t)
def norm(v):
 length=math.sqrt(sum(x*x for x in v));return tuple(x/length for x in v) if length else (0,0,1)
def project(v):return -v[0],-v[2],v[1]
def native(v):return -v[0],v[2],-v[1]
def main():
 recipe=json.loads((ART/'recipe.json').read_text());reports=[]
 for model in recipe['models']:
  d=json.loads(Path(model['decode']).read_text());raw=Path(d['geometry']['source']['path']).read_bytes();doc=rc.parse(raw);chunks=[c for c in rc.walk(doc.roots) if c.tag==b'GEOB'];changed={};groups=[];seen=set();all_changes=0
  for gi,g in enumerate(d['geometry']['groups']):
   if 'fence' in model['name']:continue
   assert g['stream']=='StructureCollectionPositionDataStream'
   count=len(g['positions']);matching=[]
   for c in chunks:
    if len(c.payload)!=16+24*count:continue
    n,_,stride,_=struct.unpack_from('<4I',c.payload)
    if n!=count or stride!=24:continue
    if all(project(struct.unpack_from('<4e',c.payload,16+i*24))==tuple(g['positions'][i]) for i in [0,count//2,count-1]):matching.append(c)
   assert len(matching)==1,(model['name'],gi,count,len(matching));c=matching[0];assert c.offset not in seen;seen.add(c.offset);data=bytearray(c.payload);edits=0;low_unchanged=0;max_delta=0
   for i,p in enumerate(g['positions']):
    at=16+i*24;original=struct.unpack_from('<4e',data,at);assert project(original)==tuple(p)
    q,sz=deform(tuple(p))
    if q!=tuple(p):
     data[at:at+8]=struct.pack('<4e',*native(q),original[3]);quantized=project(struct.unpack_from('<4e',data,at));g['positions'][i]=list(quantized)
     packed_normal=struct.unpack_from('<4b',data,at+8);nb=project(tuple(max(-1,v/127) for v in packed_normal[:3]));nb=norm((nb[0],nb[1],nb[2]/sz))
     packed_tangent=struct.unpack_from('<4b',data,at+12);tb=project(tuple(max(-1,v/127) for v in packed_tangent[:3]));tb=(tb[0],tb[1],tb[2]*sz);dot=sum(n*t for n,t in zip(nb,tb));tb=norm(tuple(t-n*dot for t,n in zip(tb,nb)))
     for offset,vector in [(8,nb),(12,tb)]:data[at+offset:at+offset+3]=struct.pack('<3b',*(max(-127,min(127,round(v*127))) for v in native(vector)))
     g['normals'][i]=list(norm(project(tuple(max(-1,v/127) for v in struct.unpack_from('<3b',data,at+8)))))
     edits+=1;max_delta=max(max_delta,p[2]-quantized[2]);assert quantized[:2]==tuple(p[:2]);assert quantized[2]<=p[2]+.002
    else:assert data[at:at+24]==c.payload[at:at+24];low_unchanged+=1
    assert data[at+16:at+24]==c.payload[at+16:at+24]
    assert data[at+11]==c.payload[at+11] and data[at+15]==c.payload[at+15]
   if edits:changed[c.offset]=bytes(data)
   all_changes+=edits;groups.append({'group':gi,'vertices':count,'changed_vertices':edits,'unchanged_vertices':low_unchanged,'max_z_reduction':max_delta,'uv_selectors_tangent_handedness_preserved':True})
  result=rc.rebuild(doc,lambda c:changed.get(c.offset));assert len(result)==len(raw)
  reread=rc.parse(result)
  for a,b in zip(rc.walk(doc.roots),rc.walk(reread.roots)):
   assert (a.tag,a.name,a.version)==(b.tag,b.name,b.version)
   if a.offset not in changed and not a.children:assert a.payload==b.payload
  nativefile=ART/(model['name']+'.rrgeom');nativefile.write_bytes(result);projection=ART/(model['name']+'-remix-projection.json');projection.write_text(json.dumps(d))
  model['native_geometry']=str(nativefile);model['remix_decode']=str(projection)
  reports.append({'model':model['name'],'age':model['age'],'source_sha256':sha(raw),'remix_sha256':sha(result),'changed_vertices':all_changes,'groups':groups,'geometry_policy':'Smooth lower arch/joinery refinement with Jacobian normals/tangents; all native roof and flag mounts preserved','topology_uv_collection_state_bytes_preserved':True,'ground_below_1m_roofs_above_3_8m_and_all_xy_preserved':True,'native_rgm_rgo_skeleton_state_contract':'retained, only supported private art-path remap','direct_binary_reencoder':'disabled by stock decoder; this is surgical verified-span mutation, not generic export'})
 (ART/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');(OUT/'geometry-validation.json').write_text(json.dumps({'status':'passed','models':reports},indent=2)+'\n');print('TC_GEOMETRY_READY',[(x['model'],x['changed_vertices']) for x in reports])
if __name__=='__main__':main()
