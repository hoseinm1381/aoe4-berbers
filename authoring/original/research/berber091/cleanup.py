"""Verified091 release-owned work cleanup, never traversing reparse points."""
from pathlib import Path
import os,sys,shutil
import stat
from release import verify,ROOT,OUT,FINAL,ZIP,BASE,BASE_ZIP
from repair import read,write,sha

PHYSICAL=OUT.resolve()
WORK=PHYSICAL/'work'

def safe_work():
    assert PHYSICAL==Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/berber_update_0_9_1').resolve()
    assert WORK.resolve()==PHYSICAL/'work' and WORK!=PHYSICAL
    if not WORK.exists():return []
    rows=[]
    for p in (PHYSICAL,WORK):
        assert not p.is_symlink() and not p.is_junction()
    pending=[WORK]
    while pending:
        folder=pending.pop()
        # Windows scandir already returns size/attributes. Reuse those cached
        # attributes rather than performing multiple disk lookups per file.
        with os.scandir(folder) as entries:
            for entry in entries:
                p=Path(entry.path); assert p.is_relative_to(WORK)
                metadata=entry.stat(follow_symlinks=False)
                assert not stat.S_ISLNK(metadata.st_mode)
                assert not (metadata.st_file_attributes&0x400)
                assert not p.suffix.lower().startswith('.blend')
                if stat.S_ISDIR(metadata.st_mode):pending.append(p)
                elif stat.S_ISREG(metadata.st_mode):rows.append({'relative':str(p.relative_to(WORK)),'bytes':metadata.st_size})
                else:raise ValueError('Unexpected file type in release work: '+str(p))
    return sorted(rows,key=lambda r:r['relative'])

def inventory():
    verify()
    assert read(OUT/'member-sha256-proof.json')['status']=='passed'
    assert read(OUT/'model-postflight.json')['status']=='passed'
    required={str(p):sha(p) for p in (FINAL,ZIP,BASE,BASE_ZIP)}
    rollback=ROOT/'output/berber_update_0_8_1'
    for p in (rollback/'Berber-0.8.1.zip',rollback/'Berber_future_kingdom.sga'):
        required[str(p)]=sha(p)
    for row in read(OUT/'input-audit.json')['models']:
        p=Path(row['donor']);assert sha(p)==row['donor_sha256']
        required[str(p)]=row['donor_sha256']
    for p in Path(__file__).resolve().parent.iterdir():
        if p.is_file(): required[str(p)]=sha(p)
    rows=safe_work();total=sum(r['bytes'] for r in rows)
    plan={'status':'inventoried','absolute_target':str(WORK),'allowed_root':str(PHYSICAL),
      'bytes_before':total,'file_count':len(rows),'files':rows,'protected_hashes':required,
      'rebuild_dependency_check':'091 donors.json/recipes +090SGA/ZIP +20existing original donor sources; no work-folder dependency',
      'regeneration':'repair.py audit/official/repair/compose; complete decoded readbacks reproduced from retained archives',
      'retained_shared_source_caches':'20 unique original donors retained as preexisting shared/source inputs; no new permanent donor cache'}
    write(OUT/'cleanup-plan.json',plan);return plan

def apply():
    plan=inventory()
    for p,digest in plan['protected_hashes'].items(): assert sha(p)==digest,p
    assert safe_work()==plan['files'],'Work inventory changed'
    # Exactly one checked absolute target; never delete the output junction/root.
    if WORK.exists():shutil.rmtree(WORK)
    assert not WORK.exists()
    for p,digest in plan['protected_hashes'].items(): assert sha(p)==digest,p
    verify()
    result={'status':'passed','bytes_before':plan['bytes_before'],'bytes_after':0,
      'bytes_reclaimed':plan['bytes_before'],'bytes_reclaimed_by_drive':{'E:':0,'F:':plan['bytes_before']},
      'removed_files':plan['file_count'],'removed_absolute_target':str(WORK),
      'post_cleanup_zip_readability_and_all_member_hashes':'passed','protected_inputs_rehashed':len(plan['protected_hashes']),
      'retained_inputs':'091ZIP/SGA;090ZIP/SGA;working081ZIP/SGA;all original Blender/texture/audio inputs;091recipes;20preexisting original donors;compact reports',
      'new_release_disposable_caches_retained':0,
      'preexisting_source_cache_reason':'Exact original donor UV0 bytes are required to reproduce repair;091 needs no decoded-static.json'}
    write(OUT/'cleanup-report.json',result)
    print('091_CLEANUP_PASSED',result['bytes_reclaimed'],'bytes reclaimed; disposable before/after',result['bytes_before'],0)

def finalize_removed():
    """Reconcile completed removal after a known helper-only source revision."""
    initial=read(OUT/'cleanup-initial-inventory.json')
    assert initial['absolute_target']==str(WORK)
    assert not WORK.exists() and safe_work()==[]
    helper=Path(__file__).resolve(); revisions=[]
    for path,digest in initial['protected_hashes'].items():
        actual=sha(path)
        if actual!=digest:
            assert Path(path).resolve()==helper,'Unexpected protected input change: '+path
            revisions.append({'path':path,'before_sha256':digest,'after_sha256':actual,
              'reason':'Cleanup helper changed to cached scandir metadata while the initial run was active; initial removal completed, postflight self-hash correctly rejected that revision. A duplicate inventory aborted on removed cache paths and performed no deletion.'})
    assert len(revisions)==1
    report=verify()
    # Native archive contents are tied to the already-verified exact final SHA.
    assert read(OUT/'model-postflight.json')['archive_sha256']==report['sga_sha256']
    assert read(OUT/'member-sha256-proof.json')['archive_sha256']==report['sga_sha256']
    result={'status':'passed','bytes_before':initial['bytes_before'],'bytes_after':0,
      'bytes_reclaimed':initial['bytes_before'],'bytes_reclaimed_by_drive':{'E:':0,'F:':initial['bytes_before']},
      'removed_files':initial['file_count'],'removed_absolute_target':str(WORK),
      'post_cleanup_zip_readability_and_all_member_hashes':'passed',
      'all_protected_deliverables_rollbacks_and_donor_inputs_rehashed':'passed',
      'protected_inputs_rehashed':len(initial['protected_hashes']),
      'cleanup_helper_revision':revisions,
      'retained_inputs':'091ZIP/SGA;090ZIP/SGA;working081ZIP/SGA;all original Blender/texture/audio inputs;091recipes;20preexisting original donor members;compact reports',
      'new_release_disposable_caches_retained':0,
      'preexisting_source_cache_reason':'Exact original donor UV0 bytes are required to reproduce repair;091 needs no decoded-static.json'}
    write(OUT/'cleanup-report.json',result)
    write(OUT/'cleanup-postflight.json',{'status':'passed','zip_sha256':report['zip_sha256'],
      'sga_sha256':report['sga_sha256'],'work_folder_absent':True,'protected_hashes':{p:sha(p) for p in initial['protected_hashes']}})
    print('091_CLEANUP_FINALIZED',result['bytes_reclaimed'],'bytes reclaimed; disposable before/after',result['bytes_before'],0)

if __name__=='__main__':
    if '--finalize-removed' in sys.argv:finalize_removed()
    elif '--apply' in sys.argv:apply()
    else: print(inventory()['bytes_before'])
