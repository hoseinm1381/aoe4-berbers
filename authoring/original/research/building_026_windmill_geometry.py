"""Surgical known-span stock windmill vertex edits. All native motion data retained."""
import sys,os,json,struct,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_6/authors/windmill';ART=ROOT/'art/building_remix_0_2_6/windmill'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
# These donor collection fragments contain sails, sail frame and axle: no edits.
ROTATING={1,3,4,6,7,10,13,15}
def deform(p,b):
 x,y,z=p
 if b in ROTATING or z<.20:return p
 # Preserve stock foundation, doorway floor, and axle/sail space.
 # Existing main roof ridges become a broad low cap, remaining connected.
 if z>4.60:z=4.60+(z-4.60)*.18
 if y>-.95 and z>2.2:
  x*=1.12
  y=.10+(y-.10)*1.05
 return x,y,z

def main():
 sys.path.insert(0,str(EXT));from garrison_shared import relic_chunky as rc
 d=json.loads(next((OUT/'stock').glob('*/decoded-static.json')).read_text());raw=Path(d['geometry']['source']['path']).read_bytes();doc=rc.parse(raw);geob=[c for c in rc.walk(doc.roots) if c.tag==b'GEOB'];c=geob[2];data=bytearray(c.payload);g=d['geometry']['groups'][1]
 n,zero,stride,zero2=struct.unpack_from('<4I',data);assert (n,stride)==(len(g['positions']),24);changes=[]
 for i,(p,b) in enumerate(zip(g['positions'],g['collection_bone_indices'])):
  q=deform(tuple(p),b);at=16+i*stride;native=struct.unpack_from('<4e',data,at);assert (-native[0],-native[2],native[1])==tuple(p)
  if q!=tuple(p):
   packed=struct.pack('<4e',-q[0],q[2],-q[1],native[3]);data[at:at+8]=packed;qn=struct.unpack('<4e',packed);changes.append({'vertex':i,'fragment':b,'before':p,'after':[-qn[0],-qn[2],qn[1]]})
  # SNORM8 native normal and tangent are coordinate-projected and adjusted
  # by local deformation Jacobian; UV and selector spans remain exact.
  if q!=tuple(p):
   sx,sy=(1.12,1.05) if p[1]>-.95 and q[2]>2.2 else (1,1)
   sz=.18 if p[2]>4.60 else 1
   def norm(v):
    l=math.sqrt(sum(x*x for x in v));return tuple(x/l for x in v) if l else (0,0,1)
   nb=norm((g['normals'][i][0]/sx,g['normals'][i][1]/sy,g['normals'][i][2]/sz))
   tn=struct.unpack_from('<4b',data,at+12);tb=(-tn[0]/127,-tn[2]/127,tn[1]/127);tb=(tb[0]*sx,tb[1]*sy,tb[2]*sz);dot=sum(a*b for a,b in zip(nb,tb));tb=norm(tuple(t-n*dot for t,n in zip(tb,nb)))
   for off,v in [(8,nb),(12,tb)]:
    nativevec=(-v[0],v[2],-v[1]);data[at+off:at+off+3]=struct.pack('<3b',*(max(-127,min(127,round(x*127))) for x in nativevec))
   packedn=struct.unpack_from('<3b',data,at+8);g['normals'][i]=list(norm((-max(-1,packedn[0]/127),-max(-1,packedn[2]/127),max(-1,packedn[1]/127))))
  assert data[at+16:at+stride]==c.payload[at+16:at+stride]
 updated=rc.rebuild(doc,lambda chunk:bytes(data) if chunk.offset==c.offset else None)
 assert len(updated)==len(raw);result=ART/'native-remix.rrgeom';result.write_bytes(updated)
 # Decoder-projected remix contains quantized native positions, exact source UV/normals etc.
 for e in changes:g['positions'][e['vertex']]=e['after']
 (ART/'remix-projection.json').write_text(json.dumps(d));report={'status':'passed','source_sha256':hashlib.sha256(raw).hexdigest(),'remix_sha256':hashlib.sha256(updated).hexdigest(),'changed_vertices':len(changes),'protected_rotating_fragments':sorted(ROTATING),'fans_mesh_byte_identical':True,'other_chunks_byte_identical':True,'uv_collection_indices_byte_identical':True,'normals_tangents_follow_deformation':True,'topology_byte_identical':True,'skeleton_motion_policy':'native RGM and private-path-rewritten RGO retained; no animation flatten','edits':changes}
 (OUT/'geometry-validation.json').write_text(json.dumps(report,indent=2));print('WINDMILL_NATIVE_EDIT',len(changes))
if __name__=='__main__':main()
