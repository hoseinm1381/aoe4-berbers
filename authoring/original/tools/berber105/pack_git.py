"""Lossless object compression; remove storage copies only after complete coverage.

Uses pack-objects with an explicit inventory including unreachable objects.
No gc, prune, reflog expiry, ref rewrite or worktree/index operation.
"""
from pathlib import Path
import os,re,stat,subprocess,sys
import workspace as w

def main():
    before=w.read(w.OUT/'git-before.json.gz');gitdir=Path(before['gitdir']);objects=gitdir/'objects';packdir=objects/'pack'
    assert gitdir.resolve()==w.ROOT/'.git' and not w.linked(objects) and not (objects/'info/alternates').exists()
    locks=list(gitdir.glob('*.lock'))+list(packdir.glob('*.lock'));assert not locks,locks
    oldpacks={p.name for p in packdir.iterdir() if p.suffix in ('.pack','.idx','.rev','.bitmap')}
    loose=[]
    for directory in objects.iterdir():
        if not directory.is_dir() or not re.fullmatch('[0-9a-f]{2}',directory.name):continue
        assert not w.linked(directory)
        for p in directory.iterdir():
            if re.fullmatch('[0-9a-f]{38}',p.name):loose.append((p,directory.name+p.name))
    current=sorted(w.run('git','cat-file','--batch-all-objects','--batch-check=%(objectname)').splitlines())
    assert current==before['objects'],'Object store changed since inventory'
    w.save(w.OUT/'git-repack-input.json',{'loose_copies':len(loose),'old_pack_files':sorted(oldpacks),'objects':len(current),'bytes_before':sum(p.stat().st_size for p in w.walk(objects))})
    if '--resume' in sys.argv:
        hashes=[line for line in (w.OUT/'git-pack.log').read_text().splitlines() if re.fullmatch('[0-9a-f]{40}',line)]
    else:
        command=['git','-c','core.bigFileThreshold=2g','pack-objects','--no-reuse-delta','--window=2','--depth=50','--threads=1','--window-memory=2g',str(packdir/'pack')]
        p=subprocess.run(command,input='\n'.join(current)+'\n',capture_output=True,text=True)
        (w.OUT/'git-pack.log').write_text(p.stdout+'\n'+p.stderr);assert p.returncode==0
        hashes=p.stdout.splitlines()
    assert hashes and all(re.fullmatch('[0-9a-f]{40}',h) for h in hashes)
    newnames=set();coverage=set()
    for h in hashes:
        prefix='pack-'+h;idx=packdir/(prefix+'.idx')
        assert idx.is_file()
        with idx.open('rb') as source:
            result=subprocess.run(['git','show-index'],stdin=source,capture_output=True,text=True,check=True)
        coverage.update(line.split()[1] for line in result.stdout.splitlines())
        result=subprocess.run(['git','verify-pack',str(idx)],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        newnames.update(p.name for p in packdir.glob(prefix+'.*'))
    assert coverage==set(current),'New pack must contain every object, including unreachable objects'
    w.git_snapshot('packed')
    packed=w.read(w.OUT/'git-packed.json.gz')
    differences=[key for key in set(before['metadata'])|set(packed['metadata']) if before['metadata'].get(key)!=packed['metadata'].get(key)]
    if differences==['index']:
        if 'stage' in before:
            assert before['stage']==packed['stage'],'Staged entries changed; preserve all storage and inspect'
            proof={'staged_entries_equal_initial_snapshot':True}
        else:
            initial=w.read(w.OUT/'tracked-before.json')['status'].splitlines()
            assert not any(line and line[0] not in (' ','?') for line in initial),'Initial staging requires an exact original stage snapshot'
            assert w.run('git','diff','--cached','--raw')=='','Staging changed; preserve all storage and inspect'
            proof={'initial_status_had_no_staged_changes':True,'current_index_equals_HEAD':True}
        w.save(w.OUT/'git-index-cache-refresh.json',{'reason':'Read-only inventory git status refreshed stat/fsmonitor cache; no staged entry changed','before_sha256':before['metadata']['index'],'after_sha256':packed['metadata']['index'],**proof,'current_stage':packed['stage'],'index_not_rewritten_by_repack':True})
        before['metadata']['index']=packed['metadata']['index']
    if 'stage' not in before:before['stage']=packed['stage']
    assert packed['metadata']==before['metadata'] and packed['objects']==current and packed['worktrees']==before['worktrees'] and packed['stage']==before['stage']
    w.save(w.OUT/'git-pack-verification.json',{'status':'passed','all_objects_in_new_pack':len(coverage),'new_pack_files':sorted(newnames),'refs_reflogs_staging_worktrees_unchanged':True,'index_cache_refresh_report':'git-index-cache-refresh.json if present','new_pack_verified_before_removing_duplicate_storage':True})
    # Every deletion is a verified redundant physical representation. Never
    # remove object IDs, expire data, or touch concurrently added loose objects.
    removed=[]
    for path,oid in loose:
        assert path.resolve().is_relative_to(objects.resolve()) and oid in coverage and not w.linked(path)
        if path.exists():
            removed.append({'path':str(path),'bytes':path.stat().st_size})
            if path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:path.chmod(stat.S_IREAD|stat.S_IWRITE)
            path.unlink()
    for name in oldpacks-newnames:
        path=packdir/name
        assert re.fullmatch(r'pack-[0-9a-f]{40}\.(pack|idx|rev|bitmap)',name) and not w.linked(path)
        removed.append({'path':str(path),'bytes':path.stat().st_size})
        if path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:path.chmod(stat.S_IREAD|stat.S_IWRITE)
        path.unlink()
    w.git_snapshot('after')
    after=w.read(w.OUT/'git-after.json.gz');assert before==after
    fsck=subprocess.run(['git','fsck','--full'],capture_output=True,text=True)
    (w.OUT/'git-fsck.log').write_text(fsck.stdout+'\n'+fsck.stderr);assert fsck.returncode==0
    w.save(w.OUT/'git-repack-result.json',{'status':'passed','object_count_preserved':len(current),'refs_reflogs_staged_entries_worktrees_unchanged':True,'index_cache_refresh_report':'git-index-cache-refresh.json if present','fsck_exit':fsck.returncode,'removed_duplicate_storage_bytes':sum(r['bytes'] for r in removed),'bytes_after':sum(p.stat().st_size for p in w.walk(objects)),'removed':removed})
    print('GIT_LOSSLESS_REPACK_COMPLETE',len(current),flush=True)
if __name__=='__main__':main()
