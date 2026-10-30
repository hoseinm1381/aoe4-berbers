"""Release 0.6.0 verified-cache cleanup. Default is inventory only; --apply deletes.

Fixed disposable set: exact verified package/native-package stages, integration
readbacks and attrib intermediate, independently reproducible decoded QA and
Low/High pilot encodes. Normalized WAVs and Medium WEMs are retained. No masters,
receipts, failed diagnostics, editable inputs, prior releases or shared caches.
"""
import argparse,hashlib,os,re,subprocess,zipfile
from pathlib import Path
from common import OUT,ROOT,BASE,BASE_SHA,ARCH,ART,read,write,sha
from package_audio import relative

ACCOUNTING_REPORTS={'cleanup-inventory.json','cleanup-before.json','cleanup-report.json'}
MAIN_REQUIRED={'Berber_future_kingdom.sga','garrison.json','COVERAGE.json','EVIDENCE.json','VOICE_GAPS.md','INSTALL_AND_TEST.txt','REBUILD_060.md','HISTORICAL_REFERENCES.md','voice-script.csv'}
AUDIO_REQUIRED={'native-audio-manifest.json','Install-BerberNativeAudio.ps1','VOICE_GAPS.md','INSTALL_AND_TEST.txt','REBUILD_060.md','HISTORICAL_REFERENCES.md'}


def safe(root,path):
    root=Path(root).resolve();path=Path(os.path.abspath(path))
    if path==root or root not in path.parents:raise ValueError('Cleanup target outside release: '+str(path))
    for p in [path,*path.parents]:
        if p==root:break
        if p.is_symlink() or p.is_junction() or (p.exists() and p.stat().st_file_attributes & 0x400):
            raise ValueError('Cleanup reparse target refused: '+str(p))
    if path.resolve()!=path:raise ValueError('Cleanup target resolves elsewhere')
    return path


def tree(root,target):
    target=safe(root,target)
    if not target.exists():return []
    if target.is_file():return [{'path':target.relative_to(root).as_posix(),'bytes':target.stat().st_size,'sha256':sha(target)}]
    rows=[]
    # Walk without following any directory links, checking each entry first.
    for entry in sorted(target.iterdir()):
        rows.extend(tree(root,entry))
    return rows


def verify_delivery(root):
    root=Path(root).resolve();report=read(root/'release-validation.json');composition=read(root/'composition-report.json')
    if report['status']!='passed' or composition['status']!='passed':raise ValueError('Unverified release')
    for key,required in [('garrison',MAIN_REQUIRED),('native_audio',AUDIO_REQUIRED)]:
        item=report[key];archive=safe(root,Path(item['zip']).resolve())
        if not archive.is_file() or sha(archive)!=item['sha256'] or archive.stat().st_size!=item['bytes']:raise ValueError('Delivery ZIP changed')
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            if len(names)!=len(set(n.lower() for n in names)) or set(names)!=set(item['members']) or not required<=set(names) or z.testzip():
                raise ValueError('Delivery member set/CRC differs')
            for name,expected in item['members'].items():
                relative(name)
                with z.open(name) as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
                if actual!=expected:raise ValueError('Delivery member digest differs: '+name)
    current=safe(root,Path(composition['archive']).resolve())
    if sha(current)!=composition['archive_sha256'] or sha(current)!=report['sga_sha256'] or report['garrison']['members']['Berber_future_kingdom.sga']!=report['sga_sha256']:
        raise ValueError('Current/packaged validated SGA differs')
    return report


def physical_root():
    root=OUT.resolve()
    storage=Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014')
    mapping=read(storage/'path-map.json')
    if not (ROOT/'STORAGE.md').is_file() or not any(Path(r['Source'])==ROOT/'output' and Path(r['Destination']).resolve()==OUT.parent.resolve() and r.get('SHA256Verified') for r in mapping):
        raise ValueError('Documented external output mapping not verified')
    if root!=storage/'output/berber_update_0_6_0' or root.drive.lower()!='f:':raise ValueError('Unexpected physical release root')
    return root


def ensure_idle(root):
    if any((Path(root)/name).exists() for name in ('generation.lock','normalization.lock','encoding.lock')):
        raise ValueError('Generation/normalization/encoding active; cleanup refused')
    check=subprocess.run(['powershell.exe','-NoProfile','-Command',
        "@(Get-Process -Name Wwise,WwiseConsole,vgmstream-cli -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True)
    if check.returncode or check.stdout.strip()!='0':
        raise ValueError('Wwise/decoder active or idle state unavailable; cleanup refused')


def build_plan():
    root=physical_root()
    ensure_idle(root)
    delivery=verify_delivery(root)
    if sha(BASE)!=BASE_SHA or not ARCH.is_file():raise ValueError('Retained archive regeneration inputs unavailable')
    composition=read(root/'composition-report.json')
    # Rebuild code, exact inputs and canonical current SGA must survive.
    required=[ROOT/'research/berber060/release.py',ROOT/'research/berber060/package_audio.py',ROOT/'research/berber060/encoding.py',
        ROOT/'research/berber060/generation.py',ROOT/'research/berber060/Install-BerberNativeAudio.ps1',ART/'recording-plan.json',
        root/'profiles/manifest.json',root/'bindings/payload-manifest.json',root/'baseline-member-sha256.json']
    if any(not p.is_file() for p in required):raise ValueError('Rebuild dependency missing')
    protected=[Path(composition['archive']).resolve(),*(Path(delivery[k]['zip']).resolve() for k in ('garrison','native_audio'))]
    candidates=[];retained=[]
    def add(target,route):
        rows=tree(root,target)
        if rows:
            if any(root/r['path'] in protected for r in rows):raise ValueError('Current deliverable selected for removal')
            candidates.append({'target':str(target),'regenerate':route,'files':rows,'bytes':sum(r['bytes'] for r in rows)})
    for folder,key in [('package','garrison'),('native-package','native_audio')]:
        target=root/folder
        if not target.exists():continue
        rows=tree(root,target)
        actual={str(Path(r['path']).relative_to(folder)).replace('\\','/'):r['sha256'] for r in rows}
        if actual!=delivery[key]['members']:raise ValueError('Staging differs from verified ZIP; retain evidence')
        add(target,'Extract retained '+Path(delivery[key]['zip']).name+' with its checked member hashes')
    add(root/'integration'/('candidate-readback-'+composition['archive_sha256'][:12]),'release.member_hashes: unpack retained current SGA with Garrison archiver')
    from prior_readbacks import validated_prior_readbacks,validated_base_readback
    for prior in validated_prior_readbacks(root,composition['archive_sha256']):
        add(prior['target'],'Rebuild superseded composition from retained BASE + 84 payloads + saved old SCAR; compact proof '+str(prior['proof']))
        for path in prior['protected_rebuild_inputs']:
            if path not in required:required.append(path)
    base_readback=validated_base_readback(root)
    if base_readback:
        add(base_readback['target'],'Unpack retained verified 0.5.1 BASE, restore preserved nonmember helpers from compact proof '+str(base_readback['proof']))
    elif (root/'integration/base-readback').exists():
        retained.append({'path':str(root/'integration/base-readback'),'reason':'No qualified native-member/helper preservation proof; unpack evidence retained'})
    selected_targets={Path(c['target']) for c in candidates}
    for path in (root/'integration').glob('candidate-readback-*'):
        if path not in selected_targets:
            retained.append({'path':str(path),'reason':'No qualified compact prior-composition proof; unverified readback evidence retained'})
    add(root/'integration/attrib-candidate.sga','release.compose: replay retained typed binding payloads and metadata over verified BASE')
    verified_medium={}
    for quality in ('Medium','Low','High'):
        manifest=root/'wem'/quality/'encoding-manifest.json'
        if not manifest.is_file():continue
        encodings=read(manifest);valid=True;quality_wems={}
        for key,row in encodings.items():
            source=Path(row['source']);wem=Path(row['wem']).resolve()
            if not source.is_file() or sha(source)!=row['source_sha256'] or not wem.is_file() or sha(wem)!=row['sha256'] or wem.parent!=manifest.parent/'Windows' or wem.name!=key+'.wem':
                valid=False;break
            quality_wems[key]=wem
        if quality=='Medium':
            if valid:verified_medium=quality_wems
            else:retained.append({'path':str(manifest.parent),'reason':'Medium encoding/source hash differs; decoded evidence must remain'})
        if quality in ('Low','High'):
            if not valid:retained.append({'path':str(manifest.parent),'reason':'Pilot encoding/source hash changed; exact regeneration not established'});continue
            rows=tree(root,manifest.parent)
            admitted={'encoding-manifest.json'}|{'Windows/'+key+'.wem' for key in encodings}
            actual={str(Path(r['path']).relative_to('wem/'+quality)).replace('\\','/') for r in rows}
            if not actual<=admitted:retained.append({'path':str(manifest.parent),'reason':'Unrecognized Wwise output retained for review'});continue
            add(manifest.parent,"encoding.encode(retained source WAV paths, '"+quality+"'); manifest records exact source hashes")
    decoded=root/'decoded-qa'
    if decoded.exists():
        for path in sorted(decoded.iterdir()):
            safe(root,path)
            if path.is_file() and path.suffix=='.wav':
                # Require a retained Medium WEM, because Low/High may be removed.
                medium=verified_medium.get(path.stem)
                if medium and medium.is_file():add(path,'encoding.decoded_check: decode retained hash-validated Medium WEM with retained pinned vgmstream tool')
                else:retained.append({'path':str(path),'reason':'No hash-validated retained Medium WEM proves decode regeneration'})
            else:retained.append({'path':str(path),'reason':'Unrecognized decoded diagnostic retained'})
    retained.extend([{'path':str(root/'wav'),'reason':'Normalized final WAV receipt hashes require exact normalization restore proof; cache retained'},
        {'path':str(root/'wem/Medium'),'reason':'Canonical Medium encoded media retained for deterministic companion rebuild'},
        {'path':str(ART/'masters'),'reason':'Lossless accepted sources and unresolved failed diagnostic masters retained'},
        {'path':str(root/'binding-readback'),'reason':'Audited native source-owner fixtures required by binding composition/tests'}])
    # Full physical release accounting without crossing links.
    allrows=[]
    for path in sorted(root.iterdir()):
        if path.name not in ACCOUNTING_REPORTS:allrows.extend(tree(root,path))
    result={'schema':'berber060-cleanup/v1','mode':'inventory_only','root':str(root),
        'release_validation_sha256':sha(root/'release-validation.json'),'composition_sha256':sha(root/'composition-report.json'),
        'delivery_hashes':{k:delivery[k]['sha256'] for k in ('garrison','native_audio')},
        'accounting_excludes':sorted(ACCOUNTING_REPORTS),'bytes_before':sum(r['bytes'] for r in allrows),'planned_reclaim_bytes':sum(c['bytes'] for c in candidates),
        'candidates':candidates,'retained':retained,'protected_rebuild_files':[{'path':str(p),'sha256':sha(p)} for p in required],
        'current_archive':str(Path(composition['archive']).resolve()),'native_playback':'pending'}
    write(root/'cleanup-inventory.json',result)
    return result


def remove_checked(root,rows):
    # Verify the entire selected file set before the first unlink; never recurse.
    for row in rows:
        path=safe(root,root/row['path'])
        if not path.is_file() or path.stat().st_size!=row['bytes'] or sha(path)!=row['sha256']:raise ValueError('Cleanup inventory changed: '+str(path))
    for row in rows:
        path=safe(root,root/row['path'])
        if sha(path)!=row['sha256']:raise ValueError('Cleanup file changed before deletion')
        path.unlink()


def apply():
    plan=build_plan();root=Path(plan['root']);verify_delivery(root)
    rows=[r for c in plan['candidates'] for r in c['files']]
    write(root/'cleanup-before.json',plan)
    try:
        ensure_idle(root)
        remove_checked(root,rows)
        # Remove only now-empty directories inside the explicit targets.
        for candidate in plan['candidates']:
            target=safe(root,candidate['target'])
            if target.is_dir():
                directories=[]
                for parent,dirs,files in os.walk(target,followlinks=False):
                    safe(root,parent)
                    for name in dirs:safe(root,Path(parent)/name)
                    directories.append(Path(parent))
                for directory in sorted(directories,key=lambda p:len(p.parts),reverse=True):directory.rmdir()
        verify_delivery(root)
        for item in plan['protected_rebuild_files']:
            if sha(item['path'])!=item['sha256']:raise ValueError('Retained rebuild input changed')
        after=[]
        for path in sorted(root.iterdir()):
            if path.name not in ACCOUNTING_REPORTS:after.extend(tree(root,path))
        if plan['bytes_before']-sum(r['bytes'] for r in after)!=sum(r['bytes'] for r in rows):raise ValueError('Release changed during cleanup accounting')
        plan.update(mode='applied',status='passed',bytes_after=sum(r['bytes'] for r in after),
            reclaimed_bytes=sum(r['bytes'] for r in rows),zip_post_cleanup='all member hashes and SGA reverified')
    except Exception as error:
        plan.update(mode='applied',status='incomplete',error=str(error));write(root/'cleanup-report.json',plan);raise
    write(root/'cleanup-report.json',plan)
    return plan

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    result=apply() if args.apply else build_plan()
    print({k:v for k,v in result.items() if k not in ('candidates','retained','protected_rebuild_files')})
