"""Remove only verified regenerable0100 work; preserve all release/source inputs."""
from pathlib import Path
import os,stat,shutil,json
from release import verify,ROOT,OUT,FINAL,ZIP,BASE,BASE_ZIP
from pipeline import sha,write

PHYSICAL=OUT.resolve()
WORK=PHYSICAL/'work'
EXPECTED=Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/berber_update_0_10_0')

def inventory():
    assert PHYSICAL==EXPECTED.resolve() and WORK.resolve()==PHYSICAL/'work'
    assert not PHYSICAL.is_symlink() and not PHYSICAL.is_junction()
    rows=[]
    if not WORK.exists():return rows
    assert not WORK.is_symlink() and not WORK.is_junction()
    pending=[WORK]
    while pending:
        folder=pending.pop()
        with os.scandir(folder) as entries:
            for e in entries:
                p=Path(e.path);info=e.stat(follow_symlinks=False)
                assert p.is_relative_to(WORK) and not (info.st_file_attributes&0x400)
                assert not stat.S_ISLNK(info.st_mode) and not p.suffix.lower().startswith('.blend')
                if stat.S_ISDIR(info.st_mode):pending.append(p)
                else:
                    assert stat.S_ISREG(info.st_mode)
                    rows.append({'path':str(p.relative_to(WORK)),'bytes':info.st_size})
    return sorted(rows,key=lambda r:r['path'])

def main():
    report=verify()
    member=json.loads((OUT/'member-sha256-proof.json').read_text())
    assert member['status']=='passed' and member['archive_sha256']==report['sga_sha256']
    protected={str(p):sha(p) for p in (FINAL,ZIP,BASE,BASE_ZIP)}
    for version in ['0_9_0','0_8_1']:
        for p in (ROOT/'output'/('berber_update_'+version)).glob('*'):
            if p.is_file() and p.suffix.lower() in ['.zip','.sga']:protected[str(p)]=sha(p)
    for folder in (ROOT/'research/berber0100',ROOT/'assets/scar/ai'):
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:protected[str(p)]=sha(p)
    for p in [ROOT/'assets/scar/buildings/tribal_tent.scar',ROOT/'assets/scar/winconditions/berber_future_kingdom_GM.scar']:
        protected[str(p)]=sha(p)
    rows=inventory();total=sum(r['bytes'] for r in rows)
    plan={'absolute_target':str(WORK),'bytes_before':total,'files':rows,'protected_hashes':protected,
      'rebuild_dependency_check':'final091SGA/ZIP + frozen AI catalog/source + pipeline/release recipes retained; work contains decoded readbacks/staging only',
      'official_data':'Installed official archives/libraries read-only; no shared cache or Blender work targeted'}
    write(OUT/'cleanup-plan.json',plan)
    assert inventory()==rows
    for p,h in protected.items():assert sha(p)==h,p
    if WORK.exists():shutil.rmtree(WORK)
    assert not WORK.exists() and inventory()==[]
    for p,h in protected.items():assert sha(p)==h,p
    verify()
    write(OUT/'cleanup-report.json',{'status':'passed','absolute_target':str(WORK),
      'bytes_before':total,'bytes_after':0,'bytes_reclaimed':total,'removed_files':len(rows),
      'bytes_reclaimed_by_drive':{'E:':0,'F:':total},'protected_inputs_rehashed':len(protected),
      'zip_crc_members_and_delivery_hashes_after_cleanup':'passed','new_disposable_caches_retained':0,
      'retained':'0100 ZIP/SGA,091/090/081 rollbacks; editable AI/shared SCAR; frozen resolved catalog; tests,recipes,evidence; existing Blender/texture/audio inputs untouched'})
    report['cleanup']='passed';report['cleanup_bytes_reclaimed']=total
    write(OUT/'release-validation.json',report)
    print('CLEANUP_VERIFIED',total,'bytes before;0 after; preserved',len(protected),'inputs')

if __name__=='__main__':main()
