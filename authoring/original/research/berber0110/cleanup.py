"""Delete only explicitly inventoried 0110 generated work after verified delivery."""
from pathlib import Path
import os,stat,shutil,json
from release import verify,ROOT,OUT,FINAL,ZIP,BASE,BASE_ZIP
from pipeline import sha,write

PHYSICAL=OUT.resolve()
EXPECTED=Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/berber_update_0_11_0')
AUTHOR=(ROOT/'research/berber0110').resolve()
TARGETS=[PHYSICAL/'work',AUTHOR/'reports/catalog-scratch',AUTHOR/'reports/catalog-market']
for p in [AUTHOR/'__pycache__',AUTHOR/'tests/__pycache__']:
    if p.exists():TARGETS.append(p)

def inventory():
    assert PHYSICAL==EXPECTED.resolve() and not PHYSICAL.is_symlink() and not PHYSICAL.is_junction()
    rows=[]
    for target in TARGETS:
        assert target.resolve()==target and target not in [PHYSICAL,AUTHOR,ROOT.resolve()]
        assert target.parent in [PHYSICAL,AUTHOR,AUTHOR/'reports',AUTHOR/'tests']
        if not target.exists():continue
        assert not target.is_symlink() and not target.is_junction()
        pending=[target]
        while pending:
            folder=pending.pop()
            with os.scandir(folder) as entries:
                for e in entries:
                    p=Path(e.path);info=e.stat(follow_symlinks=False)
                    assert p.is_relative_to(target) and not (info.st_file_attributes&0x400)
                    assert not stat.S_ISLNK(info.st_mode) and not p.suffix.lower().startswith('.blend')
                    if stat.S_ISDIR(info.st_mode):pending.append(p)
                    else:
                        assert stat.S_ISREG(info.st_mode)
                        rows.append({'path':str(p),'bytes':info.st_size,'target':str(target)})
    return sorted(rows,key=lambda r:r['path'])

def main():
    report=verify()
    member=json.loads((OUT/'member-sha256-proof.json').read_text())
    assert member['status']=='passed' and member['archive_sha256']==report['sga_sha256']
    protected={str(p):sha(p) for p in [FINAL,ZIP,BASE,BASE_ZIP]}
    for version in ['0_10_0','0_9_1','0_9_0','0_8_1']:
        for p in (ROOT/'output'/('berber_update_'+version)).glob('*'):
            if p.is_file() and p.suffix.lower() in ['.zip','.sga']:protected[str(p)]=sha(p)
    for folder in [AUTHOR,ROOT/'assets/scar/ai']:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not any(p.resolve().is_relative_to(t) for t in TARGETS):
                protected[str(p)]=sha(p)
    for p in [ROOT/'docs/superpowers/specs/2026-10-18-berber-ai-build-order-design.md',ROOT/'docs/superpowers/plans/2026-10-18-berber-0110.md',ROOT/'assets/scar/buildings/tribal_tent.scar']:
        protected[str(p)]=sha(p)
    rows=inventory();total=sum(r['bytes'] for r in rows)
    plan={'targets':list(map(str,TARGETS)),'bytes_before':total,'files':rows,'protected_hashes':protected,
        'rebuild_dependency_check':'Retained final0101 SGA/ZIP, frozen corrected AI catalog, source/recipe/tests, compact exact source hashes/mappings and extraction research scripts. Native donor is installed official Attrib.sga. Ordinary rebuild needs no decoded cache.',
        'scope':'Only0110 payload/baseline-SCAR staging and explicitly generated official-data extraction scratch. All Blender/game/shared caches untouched.'}
    write(OUT/'cleanup-plan.json',plan)
    assert inventory()==rows
    for p,h in protected.items():assert sha(p)==h,p
    for target in TARGETS:
        if target.exists():shutil.rmtree(target)
    assert inventory()==[]
    for p,h in protected.items():assert sha(p)==h,p
    verify()
    drives={}
    for row in rows:
        drive=Path(row['path']).drive;drives[drive]=drives.get(drive,0)+row['bytes']
    write(OUT/'cleanup-report.json',{'status':'passed','targets':list(map(str,TARGETS)),
        'bytes_before':total,'bytes_after':0,'bytes_reclaimed':total,'removed_files':len(rows),
        'bytes_reclaimed_by_drive':drives,'protected_inputs_rehashed':len(protected),
        'zip_crc_members_and_delivery_hashes_after_cleanup':'passed','new_disposable_caches_retained':0,
        'retained':'0110 finalZIP/SGA;0101/0100/091/090/081 rollbacks;rooteditable+isolatedauthoredSCAR;frozenverifiedcatalog;baseline-source;tests,runtime,recipes,compactreports;alloriginalBlender/texture/audioinputs untouched'})
    report['cleanup']='passed';report['cleanup_bytes_reclaimed']=total
    write(OUT/'release-validation.json',report)
    print('CLEANUP_VERIFIED',total,'bytes before;0 after; protected',len(protected),'inputs',drives)
if __name__=='__main__':main()
