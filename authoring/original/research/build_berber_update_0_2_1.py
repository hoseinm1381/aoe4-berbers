"""Versioned tent-only update of the verified complete 0.2.0 Berber archive."""
import os,sys,json,hashlib,shutil,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_1';OUT.mkdir(exist_ok=True)
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe';PROJECT=Path('E:/bt21/Mods/berber_tent_art_020')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def run(label,args):
    with (OUT/(label+'.log')).open('w',encoding='utf-8') as log:
        p=subprocess.run([str(x) for x in args],stdout=log,stderr=subprocess.STDOUT,timeout=900)
    assert p.returncode==0,(label,p.returncode)
    return (OUT/(label+'.log')).read_text(encoding='utf-8')
def launch():
    stage=sys.argv[2]
    command=([r'E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(ROOT/'art/tribal_tent/export_update_0_2_1.py')] if stage=='export' else [sys.executable,str(Path(__file__).resolve()),stage])
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
    environment=os.environ.copy();environment['BLENDER_USER_CONFIG']=str(ROOT/'output/tribal_tent/iteration001/isolated-blender-config')
    with (OUT/(stage+'.stdout.log')).open('w') as a,(OUT/(stage+'.stderr.log')).open('w') as b:
        proc=subprocess.Popen(command,stdout=a,stderr=b,stdin=subprocess.DEVNULL,startupinfo=startup,env=environment,cwd='E:/Blender5.2' if stage=='export' else ROOT,creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP)
    write(OUT/(stage+'.process.json'),{'pid':proc.pid,'command':command});print(stage,proc.pid)
def cook():
    export=read(OUT/'tent-export.json');assert export['status']=='passed'
    assert not PROJECT.exists();shutil.copytree('E:/bt20/Mods/berber_tent_art_020',PROJECT,ignore=shutil.ignore_patterns('dist','.garrison.lock','cache'))
    for age in export['ages']:
        run(f'age{age["age"]}-add',[CORE,'mod-project','building','--project',PROJECT,'--source',age['source'],'--name',f'berber_tent_age{age["age"]}','--profile','english-house','--integration','script'])
    run('release-settings',[CORE,'mod-project','settings','--project',PROJECT,'--version','0.2.1','--live-reload','off','--summary','Tribal Tents 2.5x larger with reversed entrance'])
    run('tent-cook',[CORE,'mod-project','cook','--project',PROJECT,'--editor',Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--timeout','600'])
    result=read(PROJECT/'mod-project.json')['cooks'][-1];assert not result['live_reload'] and sha(result['archive'])==result['sha256']
    write(OUT/'cook.json',{'status':'passed','cook':result});print('TENT_021_COOK_PASSED',flush=True)
def package():
    old=read(ROOT/'output/berber_update_0_2_0/delivery.json');base=Path(old['archive']);assert sha(base)==old['archive_sha256']
    assert sha(ROOT/'archives/Berber_future_kingdom.sga')==sha(base)
    cooked=read(OUT/'cook.json');assert cooked['status']=='passed'
    donor=Path(cooked['cook']['archive']);assert sha(donor)==cooked['cook']['sha256']
    inv=lambda label,path:json.loads(run(label,[ARCH,'list',path,'--verify']))
    before=inv('baseline-inventory',base);art=inv('donor-inventory',donor)
    prefixes=('art/scenario/garrison/berber_tent_art_020/buildings/','art/stamps/garrison/berber_tent_art_020/')
    members=[r['path'] for r in art['members'] if r['path'].startswith(prefixes)]
    assert {r['path'] for r in before['members'] if r['path'].startswith(prefixes)}==set(members)
    assert sum(p.endswith('.rrgeom') for p in members)==4
    directory=OUT/'package';directory.mkdir(exist_ok=True);final=directory/'Berber_future_kingdom.sga'
    if not final.exists():run('graft-tent-update',[ARCH,'graft',base,donor,final,*members])
    after=inv('final-inventory',final);assert after['archive']['verification']['verified']
    assert after['archive']['name'].replace('-','')=='1d3145e8f1b2427f8bb0067851fcf0f1'
    a={r['path']:r for r in before['members']};b={r['path']:r for r in after['members']};assert set(a)==set(b)
    original=OUT/'baseline-readback';fresh=OUT/'final-readback'
    if not original.exists():run('unpack-old',[ARCH,'unpack',base,'--output',original])
    if not fresh.exists():run('unpack-new',[ARCH,'unpack',final,'--output',fresh])
    donor_readback=OUT/'donor-readback'
    if not donor_readback.exists():run('unpack-donor',[ARCH,'unpack',donor,'--output',donor_readback])
    changed=[p for p in a if sha(original/p)!=sha(fresh/p)]
    assert set(changed)<=set(members)
    assert all(f'art/scenario/garrison/berber_tent_art_020/buildings/berber_tent_age{i}/model.rrgeom' in changed for i in range(1,5))
    baseline_path=OUT/'source-baseline.json'
    baseline=read(baseline_path) if baseline_path.exists() else {p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
    if not baseline_path.exists():write(baseline_path,baseline)
    rollback=OUT/'rollback';rollback.mkdir(exist_ok=True)
    if not (rollback/'Berber_future_kingdom-0.2.0.sga').exists():shutil.copy2(base,rollback/'Berber_future_kingdom-0.2.0.sga')
    for p in members:
        current=ROOT/'assets'/p;assert current.exists()
        backup=rollback/'assets'/p;backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():
            assert sha(current)==baseline['assets/'+p];shutil.copy2(current,backup)
        assert sha(backup)==baseline['assets/'+p]
        assert sha(donor_readback/p)==sha(fresh/p)
        shutil.copy2(fresh/p,current)
    assert all(sha(ROOT/p)==h for p,h in baseline.items() if p.removeprefix('assets/') not in members)
    test='''BERBER UPDATE 0.2.1
Close AoE4. Import berber_future_kingdom-0.2.1.zip into Garrison, confirm version 0.2.1, enable it and launch through Play.
Tuning Pack: The Berber Dynasties. Game Mode: Berber Civilization. Civilization: Malians. Start a fresh match.

All four tent variants are uniformly 2.5 times their previous dimensions and rotated 180 degrees; the entrance now faces the opposite side. Tuareg bodies, shield, long spear, voices, Q controller, gameplay and all tuning/SCAR records are byte-preserved from 0.2.0.
Test Ages I-IV: placement/construction, existing tent age-up and a newly built tent; confirm size and entrance direction. Check ground contact, workers walking nearby, nearby-building overlap and selection. Check Tent Influence and free-villager production. Confirm Tuaregs still appear and behave as in 0.2.0. Existing moving-Q delay remains unchanged.
Report screenshots, the tested age and warnings.log if anything is wrong. Native acceptance is pending your test.
Rollback: close AoE4 and reimport the preserved 0.2.0 ZIP. Source/media rollback files are retained in output/berber_update_0_2_1/rollback.
'''
    (directory/'INSTALL_AND_TEST.txt').write_text(test,encoding='utf-8')
    manifest=read(ROOT/'output/berber_update_0_2_0/package/garrison.json')
    manifest['members'][0]['sha256']=sha(final);manifest['details'].update(version='0.2.1',summary='Tribal Tents 2.5x larger with reversed entrance',changelog='Uniform 2.5x enlargement and 180-degree rotation for all four tent ages; retain complete Berber and Tuareg content.',description='Updates the original Berber civilization with larger reversed-facing tents. All other 0.2.0 resources and gameplay are preserved. Native test pending.')
    write(directory/'garrison.json',manifest)
    evidence={'status':'cook and archive readback passed','version':'0.2.1','scale':2.5,'rotation_degrees':180,'tent_ages':4,'archive_sha256':sha(final),'changed_members':changed,'unchanged_members':len(a)-len(changed),'all_tuning_SCAR_and_Tuareg_resources':'byte-preserved from 0.2.0','native_acceptance':'pending user','archive':str(final)}
    write(directory/'EVIDENCE.json',evidence)
    for name in ('tent-export.json','cook.json','tent-cook.log'):shutil.copy2(OUT/name,directory/name)
    zpath=OUT/'berber_future_kingdom-0.2.1.zip'
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in directory.iterdir():z.write(p,p.name)
    with zipfile.ZipFile(zpath) as z:assert z.testzip() is None and hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
    evidence.update(zip=str(zpath),zip_sha256=sha(zpath));write(OUT/'delivery.json',evidence)
    shutil.copy2(final,ROOT/'archives/Berber_future_kingdom.sga')
    shutil.copytree(PROJECT,ROOT/'art/tribal_tent/garrison_library_0_2_1/Mods/berber_tent_art_020',ignore=shutil.ignore_patterns('dist','.garrison.lock'),dirs_exist_ok=True)
    print('BERBER_0_2_1_READY',str(zpath),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
