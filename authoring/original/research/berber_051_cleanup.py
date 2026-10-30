"""Verified release-owned cleanup for the 0.5.1 texture patch."""
from pathlib import Path
import argparse
import hashlib
from zipfile import ZipFile
from berber_050_common import ROOT, OUT as OLD, read, write, sha, GUID
from berber_050_cleanup import inventory, no_reparse, mapped, is_reparse, verify_bundle, CACHE, safe_relative
from berber_051_skin import OUT, ART, BASE, BASE_SHA
from berber_051_release import verify_zip


def delivery():
    out=mapped(OUT);r=read(out/'release-validation.json')
    if r['status']!='passed' or sha(BASE)!=BASE_SHA or sha(r['zip'])!=r['zip_sha256'] or sha(r['sga'])!=r['sga_sha256']:
        raise ValueError('Verified delivery/baseline required before cleanup')
    if Path(r['zip']).resolve().parent!=out or Path(r['sga']).resolve()!=out/'package/Berber_future_kingdom.sga':
        raise ValueError('Unexpected delivery target')
    verify_zip(r['zip'],r['sga_sha256'])
    with ZipFile(r['zip']) as z:
        for name in z.namelist():
            p=out/'package'/safe_relative(name);no_reparse(p,out)
            if sha(p)!=hashlib.sha256(z.read(name)).hexdigest():raise ValueError('ZIP/package member differs')
    old=read(OLD/'release-validation.json')
    if sha(old['zip'])!=old['zip_sha256'] or old['sga_sha256']!=BASE_SHA:
        raise ValueError('0.5.0 rollback changed')
    return {'zip_sha256':r['zip_sha256'],'sga_sha256':r['sga_sha256'],
            'baseline_050_sha256':BASE_SHA,'rollback_050_zip_sha256':old['zip_sha256']}


def owned_projects():
    roots=[]
    for filename in ['pilot-project.json',*[p.name for p in OUT.glob('cook-project*.json')]]:
        p=OUT/filename
        if not p.exists():continue
        row=read(p);root=Path(row['owned_root'])
        if not root.exists():continue
        if root.absolute()!=root.resolve() or root.parent!=Path('F:/aoe_4_temp') or not root.name.startswith(('berber051_pilot_','berber051_cook_')):
            raise ValueError('Unexpected native temporary root')
        if is_reparse(root):raise ValueError('Native temporary root is a reparse point')
        owner=root/'.berber-051-owner.json';no_reparse(owner,root);d=read(owner)
        if d['guid']!=GUID or Path(d['workspace']).resolve()!=ROOT.resolve():raise ValueError('Temporary root ownership differs')
        if 'owner_sha256' in row and sha(owner)!=row['owner_sha256']:raise ValueError('Native cook owner sentinel changed')
        roots.append(root)
    return roots


def cleanup():
    initial=delivery();out=mapped(OUT);art=mapped(ART);external=owned_projects()
    roots={'out':out,'art':art,**{f'native_{i}':p for i,p in enumerate(external)}}
    # Only the decoded JSONs borrowed from the already verified old bundle.
    bundle=verify_bundle();cache=mapped(CACHE)
    borrowed=[]
    for row in bundle['files']:
        p=cache/safe_relative(row['relative'])
        if p.exists():
            no_reparse(p,cache)
            if sha(p)!=row['sha256']:raise ValueError('Borrowed cache changed; retain it for diagnosis')
            borrowed.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'scope':'borrowed_cache','reason':'restored for skin inspection; exact old rebuild bundle retained'})
    before_scopes={};targets=[];skipped=[]
    for name,root in roots.items():
        files,links=inventory(root);skipped+=links
        before_scopes[name]={'root':str(root),'bytes':sum(p.stat().st_size for p in files)}
        for p in files:
            rel=p.relative_to(root);reason=None
            if name.startswith('native_'):reason='verified disposable native texture carrier/pilot project'
            elif name=='out':
                if rel.parts[0] in ('payloads','candidate-readback','cook-readback'):reason='verified regenerable payload/readback copy'
                elif str(rel) in ('candidate.sga','pilot-texture.rrtex'):reason='duplicate candidate or feasibility texture; current packaged archive retained'
                elif rel.parts[0]=='baseline-inputs' and p.name not in ('eng_skin_tinting_lut.rrtex','eng_skin_tinting_lut.dds'):
                    reason='extractable baseline/reference probe; exact native fair-palette source retained'
            elif name=='art' and '__pycache__' in rel.parts:reason='regenerable Python bytecode'
            if reason:
                no_reparse(p,root);targets.append({'path':str(p),'scope':name,'bytes':p.stat().st_size,'sha256':sha(p),'reason':reason})
    before_scopes['borrowed_cache']={'root':str(cache),'bytes':sum(r['bytes'] for r in borrowed),'scope':'only the 90 borrowed decoded JSONs'}
    targets+=borrowed
    rebuild=OUT/'rebuild';rebuild.mkdir(exist_ok=True)
    configs={str(p):{'sha256':sha(p),'config':read(p)} for root in external for p in inventory(root)[0] if p.name=='mod-project.json'}
    write(rebuild/'native-project-configurations.json',configs)
    report={'status':'preflight_verified','delivery':initial,'scopes':before_scopes,
        'before_bytes':sum(v['bytes'] for v in before_scopes.values()),'targets':targets,'skipped_reparse_points':skipped,
        'retained':['candidate ZIP/current package SGA and 0.5.0 rollback','editable original Blends and all source PNGs untouched',
                    'five authored albedos, masks, recipes and compact skin review evidence','native fair-palette source and matching DDS preview projection',
                    'scripts, native configuration records, compact cook/CRC/hash reports'],
        'shared_cache_reason':'Native donor inputs remain required by original 0.5.0 art recipes. Borrowed JSONs return to the verified old restore bundle; no new duplicate stock cache.'}
    write(OUT/'cleanup-preflight.json',report);removed=[]
    try:
        for row in targets:
            p=Path(row['path']);scope=cache if row['scope']=='borrowed_cache' else roots[row['scope']]
            no_reparse(p,scope)
            if sha(p)!=row['sha256']:raise ValueError('Disposable target changed after preflight')
            p.unlink();removed.append(row)
        for root in external:
            stack=[root];directories=[]
            while stack:
                d=stack.pop();directories.append(d)
                for p in d.iterdir():
                    if is_reparse(p):raise ValueError('Reparse point appeared during owned directory pruning')
                    if p.is_dir():no_reparse(p,root);stack.append(p)
            for p in reversed(directories):p.rmdir()
    except Exception as error:
        report.update(status='cleanup_incomplete',error=str(error),removed_targets=removed,
                      removed_bytes=sum(r['bytes'] for r in removed))
        write(OUT/'cleanup-report.json',report)
        raise
    if delivery()!=initial:raise ValueError('Protected hashes changed after cleanup')
    verify_bundle()
    report.update(status='cleanup_complete' if not skipped else 'cleanup_incomplete_reparse_points_retained',
                  removed_targets=removed,removed_bytes=sum(r['bytes'] for r in removed),
                  borrowed_decoded_manifests_recleaned=len(borrowed))
    for attempt in range(8):
        report['after_scopes']={name:{'root':str(root),'bytes':sum(p.stat().st_size for p in inventory(root)[0])} for name,root in roots.items()}
        report['after_scopes']['borrowed_cache']={'root':str(cache),'bytes':sum(Path(r['path']).stat().st_size for r in borrowed if Path(r['path']).exists())}
        report['after_bytes']=sum(v['bytes'] for v in report['after_scopes'].values())
        report['net_bytes_reclaimed']=report['before_bytes']-report['after_bytes']
        write(OUT/'cleanup-report.json',report)
        observed=sum(p.stat().st_size for root in roots.values() for p in inventory(root)[0])
        if observed==report['after_bytes']:break
    else:raise ValueError('Cleanup report byte counts did not converge')
    print('051_CLEANUP',report['status'],report['before_bytes'],report['after_bytes'],report['net_bytes_reclaimed'],flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('run','verify'));a=parser.parse_args()
    print(delivery()) if a.mode=='verify' else cleanup()
