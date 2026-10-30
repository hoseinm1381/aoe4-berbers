"""Approved Berber cleanup: inventory -> plan -> bundle -> execute -> verify."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import collections,gzip,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import source_bundle as sb
from inventory import ROOT,EXTERNAL,REPORT,sha,save,walk,linked

BUNDLE=EXTERNAL/'rebuild_inputs/development_100/source-blobs.zip'
KEEP_FOLDERS=['berber_update_1_0_0','berber_update_0_11_0','berber_update_0_9_1','berber_update_0_8_1','berber_dark_age_music_test_2']
KEEP_ZIPS=[EXTERNAL/'output'/f/n for f,n in zip(KEEP_FOLDERS,['Berber-1.0.0.zip','Berber-0.11.0.zip','Berber-0.9.1.zip','Berber-0.8.1.zip','Berber-Dark-Age-Music-Test-2.zip'])]
RETIRE_ZIP=EXTERNAL/'output/berber_dark_age_music_test_1/Berber-Dark-Age-Music-Test-1.zip'
RETIRE_SGA=RETIRE_ZIP.parent/'Berber_future_kingdom.sga'
READBACK_PARTS={'baseline-readback','final-readback','cook-readback','readback','archive-readback','readback-final','garrison-cook-readback','garrison-readback','baseline-check'}
BINARY={'.rgd','.rrgeom','.rgm','.rgo','.rrmaterial','.rrtex','.dds','.wem','.wav','.xml'}

def inventory():
 with gzip.open(REPORT/'inventory.json.gz','rt',encoding='utf8') as f:return json.load(f)

def safe(p):
 p=Path(p).absolute()
 if not any(p.is_relative_to(root) and p!=root for root in (ROOT,EXTERNAL)):raise ValueError('Outside cleanup scope: '+str(p))
 for q in (p,*p.parents):
  if q.exists() and linked(q):raise ValueError('Reparse point: '+str(q))
 if p.resolve()!=p:raise ValueError('Not a canonical physical target')
 return p

def delivery(p):
 p=Path(p);archive=p.parent/'Berber_future_kingdom.sga'
 with zipfile.ZipFile(p) as z:
  if z.testzip() is not None:raise ValueError('ZIP CRC failed')
  sgas=[n for n in z.namelist() if n.lower().endswith('.sga')]
  if len(sgas)!=1:raise ValueError('Expected one SGA')
  with z.open(sgas[0]) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
  if digest!=sha(archive):raise ValueError('ZIP SGA differs from validated retained archive')
 return {'zip':str(p),'zip_sha256':sha(p),'sga':str(archive),'sga_sha256':digest,'zip_crc':'passed'}

def git_state():
 paths=[ROOT/'.git/index',ROOT/'.git/HEAD',ROOT/'.git/packed-refs']
 for folder in ('refs','logs','worktrees'):
  if (ROOT/'.git'/folder).is_dir():paths.extend(p for p in walk(ROOT/'.git'/folder) if p.is_file())
 return {str(p):sha(p) for p in paths if p.is_file()}

def plan():
 rows=inventory();byhash=collections.defaultdict(list)
 for r in rows:byhash[r['sha256']].append(r)
 selected=[]
 for r in rows:
  p=Path(r['path']);kind=None
  if p.name=='decoded-static.json':kind='decoded'
  elif p.suffix=='.json' and r['bytes']>1_000_000 and 'projection' in p.name.lower() and (p.is_relative_to(ROOT/'art') or p.is_relative_to(EXTERNAL/'output') or p.is_relative_to(EXTERNAL/'research')):kind='projection'
  elif '__pycache__' in p.parts and p.suffix=='.pyc':kind='bytecode'
  elif p==RETIRE_ZIP:kind='obsolete_delivery'
  elif p==RETIRE_SGA:kind='retired_test'
  elif p.suffix.lower() in BINARY and any(part.lower() in READBACK_PARTS for part in p.parts) and len(byhash[r['sha256']])>1:kind='duplicate_cache'
  elif p.suffix.lower() in ('.wem','.wav') and p.is_relative_to(EXTERNAL/'output') and p.relative_to(EXTERNAL/'output').parts[0] in ('berber_update_0_6_0','berber_update_0_7_0','berber_update_0_7_1','berber_update_0_7_3') and any(Path(other['path']).is_relative_to(ROOT/'art/voices_0_6_0') for other in byhash[r['sha256']]):kind='duplicate_cache'
  if kind:
   safe(p);selected.append(dict(r,kind=kind))
 # Native donor bytes, source archives, all Blender files/backups and originals
 # remain protected. No extension/name-only deletion of opaque cache folders.
 removed={r['path'] for r in selected}
 protected=[r for r in rows if r['path'] not in removed]
 dependencies=[]
 for r in rows:
  p=Path(r['path'])
  if p.suffix.lower() in ('.sga','.zip') and r['path'] not in removed:
   dependencies.append(dict(r,reason='checkpoint' if p.parent.name in KEEP_FOLDERS else 'retained source/build dependency; no removal without dependency migration'))
 save(REPORT/'deletion-plan.json',{'files':selected,'bytes':sum(r['bytes'] for r in selected),'kinds':dict(collections.Counter(r['kind'] for r in selected)),'protected_archives':dependencies,'protected_count':len(protected),'git_before':git_state()})
 with gzip.open(REPORT/'protected-inputs.json.gz','wt',encoding='utf8') as f:json.dump(protected,f)
 preflight=[delivery(p) for p in KEEP_ZIPS]
 save(REPORT/'delivery-preflight.json',preflight)
 print('PLAN',len(selected),sum(r['bytes'] for r in selected),dict(collections.Counter(r['kind'] for r in selected)),flush=True)

def bundle():
 record=json.loads((REPORT/'deletion-plan.json').read_text());rows=[r for r in record['files'] if r['kind'] not in ('bytecode','obsolete_delivery')]
 if BUNDLE.exists() or sb.INDEX.exists():raise FileExistsError('Existing bundle/index; inspect rather than overwrite')
 BUNDLE.parent.mkdir(parents=True,exist_ok=True);unique={}
 metadata=BUNDLE.parent/'retired-test1-metadata.zip'
 with zipfile.ZipFile(RETIRE_ZIP) as original,zipfile.ZipFile(metadata,'x',zipfile.ZIP_DEFLATED) as target:
  preserved={}
  for name in original.namelist():
   if not name.lower().endswith('.sga'):
    raw=original.read(name);target.writestr(name,raw);preserved[name]=hashlib.sha256(raw).hexdigest()
 with zipfile.ZipFile(metadata) as z:
  assert z.testzip() is None
  assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==preserved
 save(REPORT/'retired-test1-metadata.json',{'original_zip':str(RETIRE_ZIP),'original_sha256':sha(RETIRE_ZIP),'metadata_zip':str(metadata),'metadata_sha256':sha(metadata),'members':preserved,'sga':'retained losslessly in source-blobs.zip; old test is not a delivery checkpoint'})
 for r in rows:unique.setdefault(r['sha256'],r)
 with zipfile.ZipFile(BUNDLE,'x',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for i,(h,r) in enumerate(unique.items()):
   p=safe(r['path'])
   if sha(p)!=h:raise ValueError('Changed since inventory: '+str(p))
   z.write(p,h)
   if i%20==0:print('BUNDLED',i,'/',len(unique),flush=True)
 index={'schema':'berber-development-source-bundle/v1','bundle':str(BUNDLE),'bundle_sha256':sha(BUNDLE),'files':[dict(r,member=r['sha256'],scope='project' if Path(r['path']).is_relative_to(ROOT) else 'external',relative=Path(r['path']).relative_to(ROOT if Path(r['path']).is_relative_to(ROOT) else EXTERNAL).as_posix()) for r in rows]}
 # Physically extract every unique member to a short-lived probe and compare
 # full SHA256. This verifies real restoration, not just a ZIP listing.
 proof=[]
 with zipfile.ZipFile(BUNDLE) as z,tempfile.TemporaryDirectory(prefix='berber-source-verify-',dir=BUNDLE.parent) as tmp:
  if z.testzip() is not None:raise ValueError('Bundle CRC failed')
  if set(z.namelist())!=set(unique):raise ValueError('Bundle member set differs')
  for i,(h,r) in enumerate(unique.items()):
   probe=Path(tmp)/h
   with z.open(h) as src,probe.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
   if probe.stat().st_size!=r['bytes'] or sha(probe)!=h:raise ValueError('Extracted source differs')
   proof.append({'sha256':h,'bytes':r['bytes']});probe.unlink()
   if i%40==0:print('EXTRACT_VERIFIED',i,'/',len(unique),flush=True)
 save(sb.INDEX,index)
 save(REPORT/'bundle-verification.json',{'status':'passed','bundle_sha256':index['bundle_sha256'],'bundle_bytes':BUNDLE.stat().st_size,'original_paths':len(rows),'unique_blobs':len(unique),'unique_blob_bytes':sum(r['bytes'] for r in unique.values()),'all_members_extracted_sha256_checked':proof})
 print('BUNDLE_VERIFIED',BUNDLE.stat().st_size,flush=True)

def execute():
 plan=json.loads((REPORT/'deletion-plan.json').read_text());index=sb.load()
 if sha(BUNDLE)!=index['bundle_sha256']:raise ValueError('Bundle changed')
 before=json.loads((REPORT/'delivery-preflight.json').read_text())
 if [delivery(p) for p in KEEP_ZIPS]!=before:raise ValueError('Retained checkpoint changed')
 if git_state()!=plan['git_before']:raise ValueError('Git state changed concurrently; inspect before deletion')
 # A complete preflight precedes the first deletion; no partial surprise scan.
 rows=plan['files']
 with ThreadPoolExecutor(max_workers=24) as pool:
  ok=list(pool.map(lambda r:sha(safe(r['path']))==r['sha256'],rows))
 if not all(ok):raise ValueError('Candidate changed since inventory')
 save(REPORT/'deletion-preflight.json',{'status':'passed','candidates':len(rows),'bundle_sha256':sha(BUNDLE),'checkpoints':'passed','git':'unchanged'})
 removed=[];journal=(REPORT/'deletion-journal.jsonl').open('x',encoding='utf8')
 for i,r in enumerate(rows):
  p=safe(r['path']);s=p.stat()
  if s.st_size!=r['bytes'] or s.st_mtime_ns!=r['mtime_ns']:raise ValueError('File changed just before deletion: '+str(p))
  p.unlink();removed.append(r);journal.write(json.dumps(r)+'\n');journal.flush()
  if i%500==0:
   save(REPORT/'deletion-progress.json',{'removed':len(removed),'last':str(p)})
   print('REMOVED',i,'/',len(rows),flush=True)
 journal.close();save(REPORT/'removed.json',removed)
 # Remove only empty, non-linked cache directories owned by the selection.
 parents=sorted({Path(r['path']).parent for r in rows},key=lambda p:len(p.parts),reverse=True)
 for p in parents:
  if p.exists() and not linked(p) and not any(p.iterdir()) and p.name in ('__pycache__','baseline-readback','readback','cook-readback','final-readback'):p.rmdir()
 print('DELETION_COMPLETE',len(removed),flush=True)

def verify():
 removed=json.loads((REPORT/'removed.json').read_text());plan=json.loads((REPORT/'deletion-plan.json').read_text())
 assert len(removed)==len(plan['files'])
 assert all(not Path(r['path']).exists() for r in removed)
 with gzip.open(REPORT/'protected-inputs.json.gz','rt',encoding='utf8') as f:protected=json.load(f)
 # Documentation/restore readers deliberately revised by this cleanup are
 # enumerated in source-changes.json, with old and new hashes, never ignored.
 changes=json.loads((REPORT/'source-changes.json').read_text()) if (REPORT/'source-changes.json').exists() else {}
 def check(r):
  p=Path(r['path']);expected=changes.get(str(p),{}).get('after',r['sha256'])
  return None if p.is_file() and sha(p)==expected else str(p)
 with ThreadPoolExecutor(max_workers=24) as pool:errors=[e for e in pool.map(check,protected) if e]
 if errors:save(REPORT/'protected-errors.json',errors);raise ValueError(f'{len(errors)} protected inputs changed/missing')
 after=[delivery(p) for p in KEEP_ZIPS]
 assert after==json.loads((REPORT/'delivery-preflight.json').read_text())
 assert git_state()==plan['git_before']
 proof=json.loads((REPORT/'bundle-verification.json').read_text());assert sha(BUNDLE)==proof['bundle_sha256']
 bydrive={d:sum(r['bytes'] for r in removed if Path(r['path']).drive==d and r['links']==1) for d in ('E:','F:')}
 save(REPORT/'verification.json',{'status':'passed','protected_inputs_rehashed':len(protected),'removed_files':len(removed),'logical_bytes_removed':sum(r['bytes'] for r in removed),'single_link_bytes_removed_by_drive':bydrive,'bundle_bytes':BUNDLE.stat().st_size,'deliveries':after,'git':'refs, logs, index and worktree metadata unchanged','native_match':'not part of storage cleanup'})
 print('POSTFLIGHT_PASSED',len(protected),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
