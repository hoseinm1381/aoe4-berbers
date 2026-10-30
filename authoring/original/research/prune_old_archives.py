"""Retire old release packages while keeping build inputs and restore dependencies."""
import os,json,stat,hashlib,zipfile,collections
from pathlib import Path
ROOT=Path(__file__).absolute().parents[1]
EXTERNAL=Path(r'F:\aoe_4_temp\Berber_future_kingdom_ai_20261014')
REPORT=ROOT/'research/archive_cleanup_20261017'
MAP=ROOT/'research/cleanup_20261016/deletion-plan.json'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def files(root):
 stack=[root]
 while stack:
  with os.scandir(stack.pop()) as entries:
   for e in entries:
    if e.is_symlink():continue
    if e.is_dir(follow_symlinks=False):
     if e.name not in ('.git','_archive_cleanup_smoke') and not Path(e.path).is_junction():stack.append(Path(e.path))
    elif e.name.lower().endswith(('.zip','.sga')):
     s=e.stat(follow_symlinks=False)
     if not s.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:yield Path(e.path),s.st_size
def prepare():
 REPORT.mkdir(exist_ok=True)
 allfiles=list(files(ROOT))+list(files(EXTERNAL));sources=[]
 print('ARCHIVE INVENTORY',len(allfiles),flush=True)
 for folder,dirs,names in os.walk(ROOT/'research',followlinks=False):
  dirs[:]=[d for d in dirs if not (Path(folder)/d).is_junction() and not (Path(folder)/d).is_symlink()]
  for name in names:
   if not name.endswith('.py'):continue
   p=Path(folder)/name
   try:sources.append((str(p),p.read_text(encoding='utf-8-sig',errors='replace')))
   except OSError:pass
 text='\n'.join(s for _,s in sources)
 candidates=[];retained=[]
 for p,n in allfiles:
  suffix=p.suffix.lower()
  if suffix not in ('.zip','.sga'):continue
  reason=None
  if 'berber_update_0_7_3' in p.parts and p.name in ('Berber-0.7.3-MAIN-GARRISON.zip','Berber-0.7.3-VOICES-INSTALLER.zip'):reason='Current 0.7.3 delivery'
  elif suffix=='.zip' and any(t in p.name.lower() for t in ('rebuild','snapshot','sidecar','metadata','vgmstream','evidence')):reason='Source/rebuild evidence/tool archive, not an old delivery'
  elif suffix=='.sga':
   if 'shared_stock_cache' in p.parts or 'project' in p.parts and 'archives' in p.parts:reason='Source archive or shared stock input'
   elif p==ROOT/'archives/Berber_future_kingdom.sga':reason='Original project source archive'
   elif p==EXTERNAL/'output/berber_update_0_6_0/candidate.sga':reason='0.6.0 voice composition base for 0.6.1'
   elif p==EXTERNAL/'output/berber_update_0_6_1/Berber_future_kingdom.sga':reason='Current content base for 0.7.3 and future versions'
   elif p.parent.name=='package' and p.name=='Berber_future_kingdom.sga':
    # Older final SGAs are retained only when recipe code explicitly uses that
    # release's package as an input; preserve transitive art donor history.
    token=p.parent.parent.name+'/package/Berber_future_kingdom.sga'
    token2=p.parent.parent.name+'" / "package'
    if token in text or token2 in text or p.parent.parent.name in ('berber_update_0_2_6','berber_update_0_2_7','berber_update_0_2_7_1','berber_update_0_3_0','berber_update_0_3_1','berber_update_0_4_0','berber_update_0_5_0','berber_update_0_5_1'):
     reason='Historical patch-chain base retained for existing art rebuild recipes'
   if reason is None and (EXTERNAL not in p.parents and ROOT/'archives' not in p.parents):reason='Non-output source archive retained conservatively'
  if reason:retained.append({'path':str(p),'bytes':n,'reason':reason,'sha256':sha(p)})
  else:candidates.append({'path':str(p),'bytes':n,'sha256':sha(p),'kind':suffix[1:]})
 # Validate current inputs and both retained deliveries before any change.
 print('ARCHIVES HASHED',len(candidates),'candidates',len(retained),'retained',flush=True)
 from next_release import check
 current=check();(REPORT/'current-release-preflight.json').write_text(json.dumps(current,indent=2))
 removal={r['path'].lower() for r in candidates}
 # The previous cleanup restores some caches from old ZIPs. Redirect those
 # references to current ZIPs where possible; preserve other exact members as
 # deduplicated rebuild blobs before deleting their old archive containers.
 latest={}
 for row in retained:
  if row['reason']!='Current 0.7.3 delivery':continue
  with zipfile.ZipFile(row['path']) as z:
   for item in z.infolist():
    if item.is_dir():continue
    with z.open(item) as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    latest[digest]={'zip':row['path'],'member':item.filename,'sha256':digest}
 plan=json.loads(MAP.read_text());retired=[r for r in plan['files'] if Path(r['path']).suffix.lower() in ('.sga','.zip')]
 plan['files']=[r for r in plan['files'] if r not in retired]
 plan['archive_restore_entries_retired']=retired
 plan['logical_bytes']=sum(r['bytes'] for r in plan['files'])
 migrated=0;store=EXTERNAL/'rebuild_inputs/archive-member-blobs';store.mkdir(parents=True,exist_ok=True);cache={};added=[]
 for row in plan['files']:
  old=row['restore'];ref=old.get('zip',old.get('file',''))
  if ref.lower() not in removal:continue
  digest=row['sha256']
  if digest in latest:row['restore']=latest[digest]
  elif digest in cache:row['restore']=cache[digest]
  else:
   target=store/(digest+'.bin')
   if not target.exists():
    with target.open('xb') as w:
     if 'zip' in old:
      with zipfile.ZipFile(old['zip']) as z,z.open(old['member']) as f:
       while block:=f.read(1024*1024):w.write(block)
     else:
      with open(old['file'],'rb') as f:
       while block:=f.read(1024*1024):w.write(block)
    added.append({'path':str(target),'bytes':target.stat().st_size,'sha256':digest})
   if sha(target)!=digest:raise ValueError('Preserved restore blob differs')
   row['restore']={'file':str(target),'sha256':digest};cache[digest]=row['restore']
  migrated+=1
 # Preserve original compact record, atomically publish new restore sources.
 (REPORT/'previous-restore-map.json').write_bytes(MAP.read_bytes())
 temp=MAP.with_suffix('.migrated.tmp');temp.write_text(json.dumps(plan,indent=1));os.replace(temp,MAP)
 if any(r['restore'].get('zip',r['restore'].get('file','')).lower() in removal for r in plan['files']):raise ValueError('Dangling restore dependency')
 report={'status':'prepared','files':candidates,'retained':retained,'bytes_before':sum(r['bytes'] for r in candidates),'rebuild_blobs_added':added,'rebuild_blob_bytes_added':sum(r['bytes'] for r in added),'restore_references_migrated':migrated,'retired_temporary_archive_restore_entries':len(retired),'scope':'ZIP/SGA files only; current 0.7.3 deliveries and source/rebuild inputs retained. All other existing files remain in place.'}
 (REPORT/'deletion-plan.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('files','retained','rebuild_blobs_added')},indent=2),flush=True)
 print('RETAINED',[(Path(x['path']).name,x['reason']) for x in retained],flush=True)
def apply():
 report=json.loads((REPORT/'deletion-plan.json').read_text());rows=report['files'];retained=report['retained']
 for number,r in enumerate(rows):
  p=Path(r['path'])
  if p.suffix.lower() not in ('.zip','.sga') or p.resolve()!=p or not (ROOT in p.parents or EXTERNAL in p.parents):raise ValueError('Unsafe target')
  for node in (p,*p.parents):
   if node.is_junction() or node.is_symlink():raise ValueError('Linked target refused')
  if sha(p)!=r['sha256']:raise ValueError('Target changed')
  if number%40==0:print('ARCHIVE PREFLIGHT',number,'/',len(rows),flush=True)
 for r in retained:
  if sha(r['path'])!=r['sha256']:raise ValueError('Retained input changed')
 for r in report['rebuild_blobs_added']:
  if sha(r['path'])!=r['sha256']:raise ValueError('Rebuild blob changed')
 result={'status':'in_progress','removed':[],'bytes_removed_by_drive':{}}
 try:
  for number,r in enumerate(rows):
   p=Path(r['path']);p.unlink();result['removed'].append(r)
   result['bytes_removed_by_drive'][p.drive]=result['bytes_removed_by_drive'].get(p.drive,0)+r['bytes']
   if number%40==0:print('ARCHIVES REMOVED',number,'/',len(rows),flush=True)
  for r in retained:
   if sha(r['path'])!=r['sha256']:raise ValueError('Retained input changed after cleanup')
   if r['reason']=='Current 0.7.3 delivery':
    with zipfile.ZipFile(r['path']) as z:
     if z.testzip():raise ValueError('Delivery CRC failed')
  from next_release import check
  result['rebuild_preflight']=check();result['status']='passed';result['rebuild_blob_bytes_added']=report['rebuild_blob_bytes_added'];result['net_bytes_reclaimed']=sum(result['bytes_removed_by_drive'].values())-report['rebuild_blob_bytes_added']
 finally:(REPORT/'result.json').write_text(json.dumps(result,indent=2))
 print(json.dumps({k:v for k,v in result.items() if k!='removed'},indent=2),flush=True)
if __name__=='__main__':
 import sys
 {'prepare':prepare,'apply':apply}[sys.argv[1]]()
