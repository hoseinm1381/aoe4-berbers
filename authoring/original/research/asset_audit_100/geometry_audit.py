"""Fresh archive geometry audit; learn UV lanes from native decoder projections."""
from pathlib import Path
import collections,hashlib,json,math,os,platform,struct,sys,warnings,zipfile,subprocess
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/berber_update_1_0_0'
sys.path.insert(0,str(ROOT/'research'));import source_bundle as sources
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT));from garrison_shared import relic_chunky as rc
READER=Path('E:/age of empires 4 mods/07_Subscribed_Mods/Subscribed_Mods/Current/subscribed_mods/.aoe4-sga-v10-runtime')
SGA=OUT/'Berber_future_kingdom.sga'

def sha(p):
 if not Path(p).exists():return hashlib.sha256(sources.read_bytes(p)).hexdigest()
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def groups(raw):
 result=[]
 for c in rc.walk(rc.parse(raw).roots):
  if c.tag!=b'GEOM':continue
  h=next(x for x in c.children if x.tag==b'GOHD');at=0;ss=[]
  for _ in range(4):s,at=rc.read_lp_string(h.payload,at);ss.append(s)
  bufs=[x for x in c.children if x.tag==b'GEOB']
  if len(bufs)!=2:raise ValueError('Expected2 vertex/index buffers')
  n,_,stride,_=struct.unpack_from('<4I',bufs[0].payload)
  if len(bufs[0].payload)!=16+n*stride:raise ValueError('Vertex buffer size mismatch')
  result.append(dict(stream=ss[3],vertices=n,stride=stride,vb=bufs[0].payload,ib=bufs[1].payload))
 return result

def learn():
 probes=('art/civilizations/abbasids/animals/abb_camel_combined_armor_age03/abb_camel_combined_armor_age03.rgm',
         'art/civilizations/malian/animals/mal_horse_combined_trade_age03/mal_horse_combined_trade_age03.rgm',
         'art/civilizations/common/flags/flag_rectangle/flag_rectangle.rgm')
 folder=OUT/'asset-audit-work/native-probe'
 present={json.loads(p.read_text())['request']['logical_path'] for p in folder.glob('*/decoded-static.json')}
 for logical in probes:
  if logical not in present:
   subprocess.run([str(EXT/'bin/core/garrison-core.exe'),'convert','decode-static','--logical-path',logical,
    '--config',str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.local.json'),
    '--index',str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.sqlite3'),
    '--output-root',str(folder)],check=True,capture_output=True)
 files=list((OUT/'asset-audit-work/native-probe').glob('*/decoded-static.json'))
 files+=sorted(sources.cached_paths(ROOT/'output/berber_update_0_2_6/authors','*/stock/*/decoded-static.json'),key=sources.size)
 layouts={};evidence=[]
 required={('ObjectDataStream',28),('ObjectCollectionDataStream',20),('SailsPositionDataStream',36),('StructureCollectionPositionDataStream',24),('StructurePositionDataStream',32),('ObjectLayeredCollectionPositionDataStream',24),('UnitDataStream',28)}
 for p in files:
  m=sources.read_json(p);rawpath=Path(m['geometry']['source']['path'])
  if not rawpath.exists():continue
  native=groups(rawpath.read_bytes());decoded=m['geometry']['groups']
  if len(native)!=len(decoded):raise ValueError('Native/projection group count mismatch')
  for g,d in zip(native,decoded):
   key=(g['stream'],g['stride']);n=g['vertices'];stride=g['stride'];vb=g['vb']
   if key not in required or key in layouts:continue
   if d['stream']!=g['stream'] or len(d['positions'])!=n:raise ValueError('Projection identity mismatch')
   sample=list(range(min(n,150)))
   # Positions are native half4 or float3, projected (-x,-z,y).
   pos=[]
   for fmt in ('<4e','<3f'):
    if struct.calcsize(fmt)>stride:continue
    if all(all(abs(a-b)<1e-6 for a,b in zip((-v[0],-v[2],v[1]),d['positions'][i])) for i in sample for v in [struct.unpack_from(fmt,vb,16+i*stride)]):pos.append(fmt)
   if len(pos)!=1:continue
   lanes={};ambiguous=False
   for layer,uv in d['uv_layers'].items():
    if len(uv)!=n:raise ValueError('DecodedUV count mismatch')
    if len({tuple(uv[i]) for i in sample})<4:ambiguous=True;break
    possible=[]
    for fmt in ('<2e','<2f'):
     for offset in range(0,stride-struct.calcsize(fmt)+1,2):
      if all(abs(v[0]-uv[i][0])<1e-6 and abs((1-v[1])-uv[i][1])<1e-6 for i in sample for v in [struct.unpack_from(fmt,vb,16+i*stride+offset)]):possible.append((fmt,offset))
    if len(possible)!=1:ambiguous=True;break
    lanes[layer]=possible[0]
   if not ambiguous and lanes:
    layouts[key]=dict(position_format=pos[0],uv_lanes=lanes)
    evidence.append(dict(stream=key[0],stride=key[1],layout=layouts[key],manifest=str(p),manifest_sha256=sha(p),native_source_sha256=sha(rawpath),sampled_vertices=len(sample)))
  del m
  if set(layouts)==required:break
 return layouts,evidence

def main():
 layouts,evidence=learn();print('VERIFIED_LAYOUTS',json.dumps(evidence),flush=True)
 sys.path[:0]=[str(READER/'site-packages'),str(READER/'SGA-V10/src')];platform.system=lambda:'Windows'
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');from relic.sga.v10 import EssenceFSHandler;from relic.sga.core.definitions import Version
 rows=[];errors=[];unsupported=[];streams=collections.Counter();bad_uv=bad_pos=bad_idx=verts=triangles=0
 legacy=json.loads((ROOT/'output/berber_update_0_9_1/model-postflight.json').read_text());legacy_names={r['member'] for r in legacy['models']};prior=json.loads((ROOT/'output/berber_update_0_9_1/member-sha256-proof.json').read_text())['after']
 with SGA.open('rb') as f:
  h=f.read(12);f.seek(0);EssenceFSHandler.version=Version(int.from_bytes(h[8:10],'little'),int.from_bytes(h[10:12],'little'));fs=EssenceFSHandler.read(f)
  for name in sorted(fs.walk.files()):
   if not name.endswith('.rrgeom'):continue
   raw=fs.readbytes(name);n=name.lstrip('/');record=dict(member=n,sha256=hashlib.sha256(raw).hexdigest(),groups=[])
   try:
    for g in groups(raw):
     key=(g['stream'],g['stride']);streams[str(key)]+=1;layout=layouts.get(key)
     if not layout:unsupported.append(dict(member=n,stream=g['stream'],stride=g['stride']));continue
     count=g['vertices'];stride=g['stride'];vb=g['vb'];ib=g['ib'];uvs={k:0 for k in layout['uv_lanes']};pos=0
     for i in range(count):
      at=16+i*stride
      if not all(math.isfinite(x) for x in struct.unpack_from(layout['position_format'],vb,at)[:3]):pos+=1
      for layer,(fmt,offset) in layout['uv_lanes'].items():
       if not all(math.isfinite(x) for x in struct.unpack_from(fmt,vb,at+offset)):uvs[layer]+=1
     ic,_,isz,_=struct.unpack_from('<4I',ib);assert isz in (2,4);assert len(ib)==16+ic*isz
     indices=struct.unpack_from('<'+str(ic)+('H' if isz==2 else 'I'),ib,16)
     invalid=sum(x>=count for x in indices);bad_idx+=invalid;bad_pos+=pos;bad_uv+=sum(uvs.values());verts+=count;triangles+=ic//3
     record['groups'].append(dict(stream=g['stream'],vertices=count,stride=stride,index_count=ic,index_stride=isz,invalid_indices=invalid,index_count_multiple3=ic%3==0,invalid_positions=pos,invalid_uv_by_layer=uvs))
    if n in legacy_names:record['matches_repaired091']=record['sha256']==prior[n]
   except Exception as e:errors.append(dict(member=n,error=str(e)))
   rows.append(record)
  fs.close()
 report=dict(status='passed' if not(errors or unsupported or bad_uv or bad_pos or bad_idx) else 'review_required',archive_sha256=sha(SGA),geometry_files=len(rows),geometry_groups=sum(streams.values()),vertices=verts,triangles=triangles,streams=dict(streams),layout_evidence=evidence,unsupported=unsupported,errors=errors,nonfinite_uv_coordinates_vertices=bad_uv,nonfinite_positions=bad_pos,out_of_range_indices=bad_idx,repaired22_match091=all(r.get('matches_repaired091') for r in rows if r['member'] in legacy_names),repaired22_seen=sum(r['member'] in legacy_names for r in rows),models=rows,scope='Checks actual finite declaredUVlayers/positions/indexbuffers after layout crosschecks against nativeGarrison decoder projections. UVtiling outside0..1 is legal. Does not prove unwrap appearance, deformation, animation or nativeLOD rendering.')
 (OUT/'geometry-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('models','layout_evidence')},indent=2))
if __name__=='__main__':main()
