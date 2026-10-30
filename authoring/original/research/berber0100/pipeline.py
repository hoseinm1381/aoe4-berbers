"""Isolated Berber0100 authoring and verified native archive composition."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,shutil,warnings
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/berber_update_0_10_0'
WORK=OUT/'work'
BASE=ROOT/'output/berber_update_0_9_1/Berber_future_kingdom.sga'
BASE_SHA='76bc149faf0a82214806d002a2d91dc6df07461e583a8da74b6a16caeb4b7d14'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
ARCH=EXT/'bin/sga-archiver.exe'
LIB=Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/scar-library'
READER=Path('E:/age of empires 4 mods/07_Subscribed_Mods/Subscribed_Mods/Current/subscribed_mods/.aoe4-sga-v10-runtime')

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
def run(*args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
    if r.returncode:raise RuntimeError(r.stderr[-2500:]+r.stdout[-2500:])
    return r.stdout
def extract(archive,dest,members):
    missing=[n for n in members if not (Path(dest)/n).exists()]
    for start in range(0,len(missing),45):
        args=[ARCH,'extract',archive,dest]
        for n in missing[start:start+45]:args+=['--member',n]
        run(*args)
def prepare():
    assert sha(BASE)==BASE_SHA
    listing=json.loads(run(ARCH,'list',BASE))
    names=[r['path'] for r in listing['members'] if r['path'].endswith('.scar')]
    extract(BASE,WORK/'baseline',names)
    comparisons=[]
    for n in names:
        src=ROOT/'assets'/n
        comparisons.append({'member':n,'packaged_sha256':sha(WORK/'baseline'/n),
          'source_exists':src.exists(),'source_sha256':sha(src) if src.exists() else None,
          'identical':src.exists() and sha(src)==sha(WORK/'baseline'/n)})
    write(OUT/'input-audit.json',{'baseline_sha256':BASE_SHA,'source_comparison':comparisons,
        'scar_library':json.loads((LIB/'scar-library.json').read_text()),'native_runtime':'pending'})
    print('Baseline:',len(names),'SCAR;',sum(x['identical'] for x in comparisons),'source-identical')
    for x in comparisons:
        if not x['identical']:print('DIFF',x['member'])

def stage():
    assert sha(BASE)==BASE_SHA
    dest=WORK/'payload'
    for p in (WORK/'baseline').rglob('*.scar'):
        target=dest/p.relative_to(WORK/'baseline');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    changed={}
    main='scar/winconditions/berber_future_kingdom_gm.scar'
    data=(WORK/'baseline'/main).read_bytes()
    needle=b'import("buildings/malian_house.scar")'
    assert data.count(needle)==1 and b'berber_ai_controller' not in data
    eol=b'\r\n' if b'\r\n' in data else b'\n'
    data=data.replace(needle,needle+eol+b'import("ai/berber_ai_controller.scar")')
    (dest/main).write_bytes(data);changed[main]=dest/main
    tent='scar/buildings/tribal_tent.scar'
    assert sha(WORK/'baseline'/tent)==next(r['packaged_sha256'] for r in json.loads((OUT/'input-audit.json').read_text())['source_comparison'] if r['member']==tent)
    shutil.copyfile(ROOT/'assets'/tent,dest/tent);changed[tent]=dest/tent
    for p in sorted((ROOT/'assets/scar/ai').glob('berber_ai_*.scar')):
        n='scar/ai/'+p.name;target=dest/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);changed[n]=target
    assert len(changed)==9
    write(OUT/'payload-proof.json',{'base_sha256':BASE_SHA,'members':{n:sha(p) for n,p in changed.items()},
        'source_inputs':{str(ROOT/'assets'/n):sha(ROOT/'assets'/n) for n in changed if n!=main},
        'game_mode_recipe':'final091 bytes plus one import after buildings/malian_house.scar; preserve shipped speech/guards',
        'native_acceptance':'pending'})
    print('Staged',len(changed),'members; 2 existing and 7 new SCAR files')

def compose():
    assert sha(BASE)==BASE_SHA
    proof=json.loads((OUT/'payload-proof.json').read_text())
    for n,h in proof['members'].items():assert sha(WORK/'payload'/n)==h
    listing=WORK/'members.txt'
    listing.write_text('\n'.join(n+'='+str((WORK/'payload'/n).resolve()) for n in proof['members'])+'\n',encoding='utf8')
    final=OUT/'Berber_future_kingdom.sga'
    assert not final.exists(),'Preserve existing release archive; inspect before overwriting'
    print('Composing native archive',flush=True)
    run(ARCH,'set-members',BASE,listing,final,'--alias','data')
    print('Native composition written; verifying CRC/SHA1',flush=True)
    verify_archive(WORK/('full-final-'+sha(final)[:12]))

def verify_existing():
    verify_archive(WORK/'full-final')

def archive_hashes(archive,full,names):
    if (READER/'SGA-V10/src').is_dir():
        sys.path[:0]=[str(READER/'site-packages'),str(READER/'SGA-V10/src')]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            from relic.sga.v10 import EssenceFSHandler
            from relic.sga.core.definitions import Version
        with Path(archive).open('rb') as stream:
            header=stream.read(12);stream.seek(0)
            assert header[:8]==b'_ARCHIVE'
            EssenceFSHandler.version=Version(int.from_bytes(header[8:10],'little'),int.from_bytes(header[10:12],'little'))
            fs=EssenceFSHandler.read(stream);raw_names=list(fs.walk.files())
            result={n.lstrip('/').replace('\\','/'):hashlib.sha256(fs.readbytes(n)).hexdigest() for n in raw_names}
        assert len(result)==len(raw_names) and set(result)==set(names)
        print('All decoded SHA256 hashes read directly from native archive',flush=True)
        return result,'Direct read-only compatible V10/V11 archive reader; no extracted asset cache'
    print('Reader unavailable; using native exact-member extraction fallback',flush=True)
    if not full.exists():run(ARCH,'extract',archive,full,'--filter','/')
    extract(archive,full,[n for n in names if not (full/n).exists()])
    def one(n):return n,sha(full/n)
    with ThreadPoolExecutor(max_workers=8) as pool:return dict(pool.map(one,names)),'Native full decoded readback'

def verify_archive(full):
    final=OUT/'Berber_future_kingdom.sga'
    proof=json.loads((OUT/'payload-proof.json').read_text())
    after=json.loads(run(ARCH,'list',final,'--verify'))
    assert after['archive']['verification']['verified']
    write(OUT/'archive-inventory.json',after)
    previous=json.loads((ROOT/'output/berber_update_0_9_1/member-sha256-proof.json').read_text())
    assert previous['status']=='passed' and previous['archive_sha256']==BASE_SHA
    old=previous['after'];names=[r['path'] for r in after['members']]
    assert set(old)<=set(names)
    assert set(names)-set(old)=={n for n in proof['members'] if n not in old}
    new,method=archive_hashes(final,full,names)
    changed=[n for n,h in old.items() if new[n]!=h]
    assert set(changed)=={'scar/winconditions/berber_future_kingdom_gm.scar','scar/buildings/tribal_tent.scar'}
    for n,h in proof['members'].items():assert new[n]==h
    protected=[n for n in old if n.startswith(('art/','audio/','attrib/')) or 'speech' in n or 'voice' in n]
    assert all(old[n]==new[n] for n in protected)
    write(OUT/'member-sha256-proof.json',{'status':'passed','baseline_sha256':BASE_SHA,'archive_sha256':sha(final),
        'baseline_members':len(old),'final_members':len(new),'changed_existing':changed,
        'new_members':sorted(set(new)-set(old)),'removed_members':[],
        'unchanged_member_count':len(old)-len(changed),'all_art_audio_attrib_and22uv_members_identical':True,
        'baseline_hash_evidence':'Retained full decoded091 member hashes, tied to freshly verified exact baseline SGA SHA256',
        'final_hash_method':method,
        'protected_member_count':len(protected),'native_archive_verification':after['archive']['verification'],
        'before':old,'after':new})
    print('COMPOSED',len(changed),'changed;',len(new)-len(old),'new;',len(old)-len(changed),'unchanged; SHA',sha(final))

def revise_unpublished():
    final=OUT/'Berber_future_kingdom.sga'
    assert not (OUT/'Berber-0.10.0.zip').exists(),'Never move a published delivery'
    proof=json.loads((OUT/'member-sha256-proof.json').read_text())
    assert proof['status']=='passed' and sha(final)==proof['archive_sha256']
    assert final.resolve().parent==OUT.resolve() and WORK.resolve().parent==OUT.resolve()
    prefix='previous-'+sha(final)[:12]
    destination=WORK/(prefix+'.sga');assert not destination.exists()
    final.rename(destination)
    shutil.copyfile(OUT/'member-sha256-proof.json',WORK/(prefix+'-proof.json'))
    print('Preserved unpublished composition for regression revision')

if __name__=='__main__':
    globals()[sys.argv[1]]()
