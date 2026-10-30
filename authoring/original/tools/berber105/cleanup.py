"""Verified source retirement and release-owned scratch cleanup."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip,json,os,stat,sys,zipfile
import workspace as w

def scratch_cleanup():
    work=w.safe_target(w.OUT/'work');rows=[]
    if not work.exists():return {'before':0,'after':0,'reclaimed':0}
    # Preflight the ENTIRE tree for reparse points before deleting its first file.
    for folder,dirs,files in os.walk(work,followlinks=False):
        for name in dirs+files:
            p=Path(folder)/name
            if w.linked(p):raise ValueError('Linked scratch target '+str(p))
        for name in files:
            p=Path(folder)/name;rows.append({'path':str(p),'bytes':p.stat().st_size})
    w.save(w.OUT/'scratch-inventory.json.gz',rows)
    for r in rows:w.safe_target(r['path']).unlink()
    for folder,dirs,files in os.walk(work,topdown=False,followlinks=False):
        p=Path(folder);w.safe_target(p).rmdir()
    return {'before':sum(r['bytes'] for r in rows),'after':0,'reclaimed':sum(r['bytes'] for r in rows)}

def retire():
    assert not (w.OUT/'retirement-complete.json').exists(),'Retirement already completed'
    assert w.sha(w.BASE)==w.BASE_SHA and w.sha(w.ROLLBACK)==w.ROLLBACK_SHA
    delivery=w.verify_zip(w.OUT/'Berber-1.0.5.zip');rollback=w.verify_zip(w.ROLLBACK)
    for proof in ('cold-rebuild-proof.json','development-probes.json','blender-edit-probes.json','input-bundle-verification.json','native-cook-proof.json','resource-coverage.json','restoration-proof.json','retired-package-input-proof.json'):
        assert w.read(w.OUT/proof)['status']=='passed',proof
    rows=w.read(w.OUT/'inventory.json.gz');plan=w.read(w.OUT/'cleanup-candidates.json.gz')
    index=w.read(w.HERE/'source-index.json.gz');assert w.sha(index['bundle'])==index['bundle_sha256']==plan['source_bundle_sha256']
    bundle_proof=w.read(w.OUT/'input-bundle-verification.json')
    assert bundle_proof['bundle_sha256']==index['bundle_sha256'] and bundle_proof['all_blobs_decoded_and_sha256_checked']
    indexed={(r['path'],r['sha256'],r['bytes']) for r in index['files']}
    assert all((r['path'],r['sha256'],r['bytes']) in indexed for r in plan['bundled'])
    candidates=plan['retire']+plan['bundled'];assert len(candidates)==len({r['path'] for r in candidates})
    tracked=set(w.read(w.OUT/'tracked-before.json')['tracked'])
    for r in candidates:
        if r['scope']=='project':assert r['relative'] not in tracked,('tracked source protected',r['path'])
    # Inventory already hashed every candidate, and bundling rehashed selected
    # inputs. Require unchanged size/mtime and physical ownership at retirement;
    # the current bundle's exact archive SHA ties its full decoded verification.
    # There is no need to repeatedly reread 17GB of retired release history.
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda r:w.verify_cleanup_candidate(r,hash_bytes=False),candidates))
    w.save(w.OUT/'cleanup-preflight.json',{'status':'passed','files':len(candidates),'candidate_bytes':sum(r['bytes'] for r in candidates),'delivery':delivery,'rollback':rollback,'observed_storage_before_retirement':w.totals()})
    with (w.OUT/'deletion-journal.jsonl').open('x',encoding='utf8') as journal:
        for i,r in enumerate(candidates):
            p=w.safe_target(r['path']);s=p.stat()
            assert s.st_size==r['bytes'] and s.st_mtime_ns==r['mtime_ns'],('changed just before removal',str(p))
            if s.st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:p.chmod(stat.S_IREAD|stat.S_IWRITE)
            p.unlink();journal.write(json.dumps(r)+'\n')
            if i%500==0:journal.flush();print('RETIRED',i,len(candidates),flush=True)
    removed={r['path'] for r in candidates};failures=[]
    owned_changes={str(w.ROOT/n) for n in ('STORAGE.md','PORTING.md','REBUILD_NEXT.md','README.md','research/source_bundle.py')}
    # These paths are the only intentionally edited existing source locations.
    protected=[r for r in rows if r['path'] not in removed and not Path(r['path']).is_relative_to(w.HERE) and r['path'] not in owned_changes]
    def check(r):
        p=Path(r['path']);return None if p.is_file() and w.sha(p)==r['sha256'] else r['path']
    with ThreadPoolExecutor(max_workers=3) as pool:failures=[r for r in pool.map(check,protected) if r]
    w.save(w.OUT/'protected-verification.json',{'status':'passed' if not failures else 'failed','rehashed_files':len(protected),'failures':failures,'explicit_owned_change_paths':sorted(owned_changes),'owned_tools':str(w.HERE)})
    assert not failures,failures[:20]
    assert w.verify_zip(w.OUT/'Berber-1.0.5.zip')==delivery and w.verify_zip(w.ROLLBACK)==rollback
    assert w.sha(w.BASE)==w.BASE_SHA
    w.save(w.OUT/'retirement-complete.json',{'status':'passed','removed_files':len(candidates),'removed_bytes_by_drive':{d:sum(r['bytes'] for r in candidates if Path(r['path']).drive==d) for d in ('E:','F:')},'protected_files_rehashed':len(protected)})
    print('SOURCE_RETIREMENT_VERIFIED',len(candidates),flush=True)

def finish():
    assert w.read(w.OUT/'retirement-complete.json')['status']=='passed'
    assert w.read(w.OUT/'exfat-inputs-complete.json')['status']=='passed'
    assert w.read(w.OUT/'restoration-proof.json')['current_bundle_sha256']==w.read(w.HERE/'source-index.json.gz')['bundle_sha256']
    validation=w.read(w.OUT/'input-validation.json')
    assert validation['status']=='passed' and validation['bundle_sha256']==w.read(w.HERE/'source-index.json.gz')['bundle_sha256']
    before=w.verify_zip(w.OUT/'Berber-1.0.5.zip');scratch=scratch_cleanup()
    assert w.verify_zip(w.OUT/'Berber-1.0.5.zip')==before
    assert w.sha(w.BASE)==w.BASE_SHA and w.sha(w.ROLLBACK)==w.ROLLBACK_SHA
    # Only remove empty parents of verified retired files, never traverse links.
    plan=w.read(w.OUT/'cleanup-candidates.json.gz')
    parents=set()
    for row in plan['retire']+plan['bundled']+w.read(w.OUT/'exfat-input-plan.json.gz'):
        p=Path(row['path']).parent
        for ancestor in (p,*p.parents):
            if ancestor in (w.ROOT,w.EXTERNAL):break
            if ancestor.is_relative_to(w.ROOT) or ancestor.is_relative_to(w.EXTERNAL):parents.add(ancestor)
    empty=0
    for p in sorted(parents,key=lambda p:-len(p.parts)):
        if p.exists():
            w.safe_target(p)
            try:p.rmdir();empty+=1
            except OSError:pass
    w.save(w.OUT/'cleanup-report.json',{'status':'passed','source_retirement':w.read(w.OUT/'retirement-complete.json'),'exfat_consolidation':w.read(w.OUT/'exfat-inputs-complete.json'),'empty_verified_directories_removed':empty,'scratch':scratch,'delivery_rechecked_after_cleanup':before,'baseline_sha256':w.BASE_SHA,'rollback_sha256':w.ROLLBACK_SHA,'storage_after':w.totals()})
    print('CLEANUP_COMPLETE',scratch['reclaimed'],'scratch bytes',flush=True)
if __name__=='__main__':
    if sys.argv[1]=='retire':retire()
    elif sys.argv[1]=='finish':finish()
    else:raise ValueError('retire or finish required')
