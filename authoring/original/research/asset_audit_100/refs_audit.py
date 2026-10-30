"""Read-only native package dependency/texture audit. Only audit-owned temporary files."""
import os,sys,json,hashlib,platform,warnings,sqlite3,struct,re,collections,datetime,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'output/berber_update_1_0_0'; OWN=ROOT/'research/asset_audit_100'; ARCH=OUT/'Berber_future_kingdom.sga'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path[:0]=[str(EXT),str(ROOT/'research')]
from garrison_shared import relic_chunky as rc,rrtex_decoder as tx,rgd
from economy_025_native_stamp import NativeTree
from berber_040_integrate import active_visuals
platform.system=lambda:'Windows'
r=Path('E:/age of empires 4 mods/07_Subscribed_Mods/Subscribed_Mods/Current/subscribed_mods/.aoe4-sga-v10-runtime');sys.path[:0]=[str(r/'site-packages'),str(r/'SGA-V10/src')]
with warnings.catch_warnings():
 warnings.simplefilter('ignore');from relic.sga.v10 import EssenceFSHandler
from relic.sga.core.definitions import Version
norm=lambda s:s.replace('\\','/').lower().removeprefix('data:').lstrip('/')
def sha(p):
 with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
assert sha(ARCH)=='a96adced078ff7a1d97a7e22e6980165f723a1551abb8794b9a016738c68d42a'
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
stock={norm(x[0]) for x in c.execute('select logical_path from resolved_assets')}
providers=[{'path':p,'size_matches':Path(p).exists() and Path(p).stat().st_size==sz,'mtime_matches':Path(p).exists() and Path(p).stat().st_mtime_ns==mt} for p,sz,mt in c.execute('select path,size,mtime_ns from archives')]
metadata=dict(c.execute('select key,value from metadata'));c.close()
stockdata=json.loads(subprocess.check_output([str(EXT/'bin/sga-archiver.exe'),'list','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Data.sga'],text=True,encoding='utf8'));stockstamps={norm(x['path']) for x in stockdata['members']}
f=ARCH.open('rb');h=f.read(12);f.seek(0);EssenceFSHandler.version=Version(int.from_bytes(h[8:10],'little'),int.from_bytes(h[10:12],'little'));fs=EssenceFSHandler.read(f)
names={norm(n):n for n in fs.walk.files()};refs=[];errors=[];containers=[];textures=[];stamps=[];models=[];material_slots=[];affected=[]
def read(n):return fs.readbytes(names[n])
def ref(src,path,typ,field=None):
 path=norm(path);target=path
 if not path or path.startswith('__'):return
 suffix={'model':'.rgm','stamp':'.bin','texture':'.rrtex'}.get(typ)
 if suffix and not target.endswith(suffix):target+=suffix
 status='packaged' if target in names else 'official_stock_index' if target in stock else 'official_stock_Data_sga_metadata' if target in stockstamps else 'unresolved'
 refs.append(dict(source=src,path=path,target=target,type=typ,field=field,status=status))
def lp(b,p):
 n=struct.unpack_from('<I',b,p)[0];p+=4;assert p+n<=len(b);return b[p:p+n].decode('utf8'),p+n
for i,n in enumerate(sorted(n for n in names if n.startswith('art/') or n.endswith('.rrtex'))):
 raw=read(n);ext=Path(n).suffix
 try:
  d=rc.parse(raw); chunks=list(rc.walk(d.roots));containers.append({'path':n,'bytes':len(raw),'chunks':len(chunks)})
 except Exception as e:errors.append({'path':n,'layer':'chunky','error':str(e)});continue
 if ext=='.rrmaterial':
  for ch in chunks:
   if ch.tag==b'PbTe':
    b=ch.payload;count=struct.unpack_from('<I',b)[0];p=4
    try:
     for j in range(count):
      key,p=lp(b,p);v,p=lp(b,p);ref(n,v,'texture',key)
     assert p==len(b)
    except Exception as e:errors.append({'path':n,'layer':'material_PbTe','error':str(e)})
 if ext=='.rgm':
  stem=n[:-4];missing=[stem+ex for ex in ['.rrgeom','.rrmaterial'] if stem+ex not in names and stem+ex not in stock]
  models.append({'path':n,'missing_cook_companions':missing,'rgo_present':stem+'.rgo' in names or stem+'.rgo' in stock})
  for ch in chunks:
   if ch.tag==b'BANA':
    try:
     v,p=lp(ch.payload,0);ref(n,v,'model','BANA')
    except Exception as e:errors.append({'path':n,'layer':'BANA','error':str(e)})
 if ext=='.rrtex':
  tmp=OWN/'temp.rrtex';tmp.write_bytes(raw)
  try:res=tx.decode_rrtex(tmp,validate_stream=True);textures.append({'path':n,'status':'decoded_stream_validated','details':res})
  except Exception as e:textures.append({'path':n,'status':'unsupported_decoder' if 'unsupported' in str(e).lower() else 'decoder_error','error':str(e)})
  finally:tmp.unlink()
 if ext=='.bin':
  tmp=OWN/'temp.bin';tmp.write_bytes(raw)
  try:
   tree=NativeTree(tmp);vs=active_visuals(tree);stamps.append({'path':n,'objects':len(tree.objects),'active_visuals':vs})
   for v in vs:ref(n,v['model'],'model','active VisualStampBlueprint.m_blueprint')
  except Exception as e:errors.append({'path':n,'layer':'stamp_reflect','error':str(e)})
  finally:tmp.unlink()
 if i%150==0:print('read',i,n,flush=True)
# Exact actor links provide affected-unit/building evidence for custom stamp references.
for n in sorted(x for x in names if x.startswith('attrib/ebps/') and x.endswith('.rgd')):
 try:
  doc=rgd.read(read(n))
  for p,node in rgd.flatten(doc.nodes):
   if node.kind=='CString' and isinstance(node.value,str) and ('stamp' in p or 'animator' in p):
    v=norm(node.value)
    if v.startswith('art/stamps/'):
     affected.append({'actor':n,'field':p,'stamp':v if v.endswith('.bin') else v+'.bin'});ref(n,v,'stamp',p)
 except Exception as e:errors.append({'path':n,'layer':'actor_rgd','error':str(e)})
fs.close();f.close()
unresolved=[x for x in refs if x['status']=='unresolved'];confirmed=[];unknown=[]
for x in unresolved:
 # Official index intentionally excludes stamps, so absent stock stamp bindings are unknown.
 if x['target'].startswith(('art/scenario/','art/stamps/garrison/')):confirmed.append(x)
 else:unknown.append(x)
for x in confirmed:
 x['affected_actors']=[a['actor'] for a in affected if a['stamp']==x['source'] or any(s['path']==a['stamp'] and any(v['model']+'.rgm'==x['source'] or v['model']+'.rrmaterial'==x['source'] for v in s['active_visuals']) for s in stamps)]
report={'audit_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(ARCH),'archive_sha256':sha(ARCH),'counts':{'members':len(names),'chunky_containers_parsed':len(containers),'textures':len(textures),'texture_status':dict(collections.Counter(t['status'] for t in textures)),'models':len(models),'material_files':sum(n.endswith('.rrmaterial') for n in names),'stamps':len(stamps),'reference_edges':len(refs),'reference_status':dict(collections.Counter(x['status'] for x in refs)),'confirmed_broken_private_refs':len(confirmed),'unresolved_unclassified_refs':len(unknown),'parser_errors':len(errors)},'official_index':{'metadata':metadata,'providers':providers},'stock_stamp_provider':{'archive':stockdata['archive'],'method':'Fresh native sga-archiver list; metadata only, not extracted files','resolved_stamps':sorted({r['target'] for r in refs if r['status']=='official_stock_Data_sga_metadata'})},'confirmed_broken_private_refs':confirmed,'unresolved_unclassified_refs':unknown,'parser_errors':errors,'missing_model_companions':[m for m in models if m['missing_cook_companions']],'containers':containers,'textures':textures,'models':models,'stamps':stamps,'references':refs,'actors':affected,'limitations':['No game runtime, animation playback, visual quality, mip appearance or LOD transition proof.','RRTex unsupported_decoder is a decoder limitation, not a confirmed bad cook.','Official index excludes stamps; nonprivate absent stamp references remain unclassified.','Active stamp root-array visuals checked; dormant reflected records are not activated by this audit.','Graph/animation/rig reference semantics are not exhaustively validated by container parsing.']}
p=OUT/'refs-report.json';p.write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf8')
lines=['# Berber 1.0.0 read-only asset reference and cook audit','',f'Archive SHA256: `{report["archive_sha256"]}`','',json.dumps(report['counts'],indent=2),'','Confirmed broken private references:']
lines += [f'- {x["source"]}: {x["target"]}' for x in confirmed] or ['None detected by these checks.']
lines+=['','Limitations:']+['- '+x for x in report['limitations']]
(OUT/'refs-report.md').write_text('\n'.join(lines)+'\n',encoding='utf8');print(json.dumps(report['counts'],indent=2));print('ERRORS',errors[:8]);print('UNRESOLVED',unresolved[:20])
