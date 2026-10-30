"""Remove only old unreachable loose objects and abandoned Git temp objects.

Protects all refs/reflogs/indexed objects, including linked worktrees. Never
expires reflogs, resets an index, rewrites history, or touches project assets.
"""
import collections,hashlib,json,os,re,stat,subprocess,time
from pathlib import Path
ROOT=Path(__file__).absolute().parents[1]
GIT=ROOT/'.git'
REPORT=ROOT/'research/git_cleanup_20261017'
def git(*args):
 env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
 p=subprocess.run(['git','-c','core.fsmonitor=false',*args],cwd=ROOT,env=env,capture_output=True,text=True)
 if p.returncode:raise RuntimeError('Git check failed: '+str(args)+'\n'+p.stderr[-1500:]+p.stdout[-1000:])
 return p.stdout
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def metadata():
 paths=[GIT/'HEAD',GIT/'index',GIT/'packed-refs']
 for parent in (GIT/'refs',GIT/'logs',GIT/'worktrees'):
  if parent.exists():paths.extend(p for p in parent.rglob('*') if p.is_file() and not p.name.endswith('.lock'))
 return {str(p.relative_to(GIT)):sha(p) for p in paths if p.is_file()}
def protected():
 return set(git('rev-list','--objects','--all','--reflog','--indexed-objects','--no-object-names').splitlines())
def writer_check():
 cmd="@(Get-CimInstance Win32_Process -Filter \"Name='git.exe'\" | Where-Object { $_.CommandLine -match '(?i)\\b(add|commit|reset|checkout|switch|merge|rebase|gc|prune|repack|fetch|update-ref|stash)\\b' } | Select-Object ProcessId,CommandLine) | ConvertTo-Json -Compress"
 p=subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],capture_output=True,text=True)
 if p.returncode:raise RuntimeError('Cannot establish Git writer idle state')
 if p.stdout.strip():raise RuntimeError('Git writer active; retry when idle: '+p.stdout[:500])
def prepare():
 REPORT.mkdir(exist_ok=True);writer_check();before=metadata();reach=protected()
 print('CHECKING REACHABILITY (all history, reflogs and worktree indexes)',flush=True)
 output=git('fsck','--full','--connectivity-only','--unreachable','--cache','--no-progress')
 unreach={line.split()[2] for line in output.splitlines() if line.startswith('unreachable ') and len(line.split())==3}
 cutoff=time.time()-3600;rows=[];recent=0
 for folder in (GIT/'objects').iterdir():
  if not folder.is_dir() or not re.fullmatch('[0-9a-f]{2}',folder.name):continue
  for p in folder.iterdir():
   if not p.is_file() or p.is_symlink() or p.is_junction():continue
   temp=p.name.startswith('tmp_obj_');oid=folder.name+p.name
   if not temp and (not re.fullmatch('[0-9a-f]{40}',oid) or oid not in unreach or oid in reach):continue
   s=p.stat()
   if s.st_mtime>=cutoff:recent+=1;continue
   rows.append({'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'kind':'temporary' if temp else 'unreachable','oid':None if temp else oid})
 if metadata()!=before or protected()!=reach:raise RuntimeError('Git state changed during inventory; rerun')
 result={'status':'prepared','git_metadata_before':before,'protected_objects':sorted(reach),'files':rows,'bytes':sum(x['bytes'] for x in rows),'recent_objects_preserved':recent,'cutoff_unix':cutoff,'worktrees':git('worktree','list','--porcelain'),'scope':'Only unreachable loose Git objects and abandoned tmp_obj files older than one hour; packs/history/reflogs/indexes/project files untouched'}
 (REPORT/'plan.json').write_text(json.dumps(result,indent=1));print(json.dumps({'files':len(rows),'bytes':result['bytes'],'protected_objects':len(reach),'recent_preserved':recent,'kinds':dict(collections.Counter(r['kind'] for r in rows))}),flush=True)
def apply():
 plan=json.loads((REPORT/'plan.json').read_text());writer_check()
 if metadata()!=plan['git_metadata_before'] or protected()!=set(plan['protected_objects']):raise RuntimeError('Protected state changed; regenerate plan')
 indexes=[GIT/'index']+list((GIT/'worktrees').glob('*/index'))
 locks=[];result={'status':'in_progress','deleted_files':0,'bytes_removed':0}
 try:
  # Exclusive index locks prevent Git add/commit from replacing either staged
  # state during the short removal window. Never alter or remove foreign locks.
  for index in indexes:
   lock=index.with_name(index.name+'.lock');handle=lock.open('xb');locks.append((lock,handle))
  writer_check()
  if metadata()!=plan['git_metadata_before'] or protected()!=set(plan['protected_objects']):raise RuntimeError('Protected state changed before deletion')
  for row in plan['files']:
   p=Path(row['path'])
   if p.resolve()!=p or p.parent.parent!=GIT/'objects' or not re.fullmatch('[0-9a-f]{2}',p.parent.name):raise ValueError('Outside approved Git object namespace')
   if p.is_symlink() or p.is_junction():raise ValueError('Redirected target')
   s=p.stat()
   if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns']:raise RuntimeError('Object changed; stop')
  for row in plan['files']:
   target=Path(row['path'])
   try:target.unlink()
   except PermissionError:
    # Git marks loose objects read-only on Windows. Clear that flag only on
    # this preflighted unreachable object, never on a retained object or tree.
    if not target.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:raise
    target.chmod(target.stat().st_mode|stat.S_IWRITE);target.unlink()
   result['deleted_files']+=1;result['bytes_removed']+=row['bytes']
  if metadata()!=plan['git_metadata_before'] or protected()!=set(plan['protected_objects']):raise RuntimeError('Protected Git state changed')
  result['protected_state']='Refs, reflogs and both worktree indexes byte-identical; protected reachable-object set identical'
 finally:
  for lock,handle in reversed(locks):handle.close();lock.unlink()
  (REPORT/'result.json').write_text(json.dumps(result,indent=2))
 print('REMOVED',result['deleted_files'],result['bytes_removed'],'bytes; checking remaining object integrity',flush=True)
 output=git('fsck','--full','--cache','--no-progress')
 result['integrity']='git fsck --full --cache passed';result['status']='passed';result['history_rewritten']=False;result['project_files_deleted']=0;result['count_objects_after']=git('count-objects','-v')
 (REPORT/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':
 import sys
 {'prepare':prepare,'apply':apply}[sys.argv[1]]()
