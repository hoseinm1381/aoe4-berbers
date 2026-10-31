"""Cook the corrected shield and graft only its resources into refined.1."""
import os,sys,json,subprocess,hashlib,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tuareg_lower_shield_trial';EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe';PROJECT=Path('E:/tsh2/project');VERSION='0.1.6-tuareg-lower-shield.1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(label,args):
    p=subprocess.run([str(a) for a in args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=900)
    (OUT/(label+'.log')).write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');assert p.returncode==0,(label,p.returncode,p.stderr[-500:]);print(label,'PASS',flush=True);return p.stdout
def inv(p):return json.loads(run('inventory-'+Path(p).stem,[ARCH,'list',p,'--verify']))
if sys.argv[1]=='cook':
    if not PROJECT.exists():shutil.copytree(Path('E:/trf1'),PROJECT,ignore=shutil.ignore_patterns('dist','cache','.garrison.lock'))
    else:assert sha(PROJECT/'mod-project.json')==sha(Path('E:/trf1/mod-project.json')),'Existing candidate has changed; preserve it and choose a new path.'
    request=OUT/'prepare-request.json';run('shield-prepare',[CORE,'static','prepare','--request',request,'--report',OUT/'prepare-report.json'])
    run('shield-add',[CORE,'mod-project','add','--project',PROJECT,'--manifest','E:/tsh2/Assets/Custom/tuareg/tuareg_agher_refined/workspace.json','--label','Lowered Tuareg shield'])
    editor=json.loads(request.read_text())['cook_editor'];run('shield-cook',[CORE,'mod-project','cook','--project',PROJECT,'--editor',editor,'--timeout','600'])
    (OUT/'cook-pass.json').write_text(json.dumps({'status':'passed','project':str(PROJECT)},indent=2))
elif sys.argv[1]=='package':
    assert json.loads((OUT/'cook-pass.json').read_text())['status']=='passed'
    baseinfo=json.loads((ROOT/'output/tuareg_refined_trial/delivery.json').read_text());base=Path(baseinfo['archive']);assert sha(base)==baseinfo['archive_sha256']
    cook=json.loads((PROJECT/'mod-project.json').read_text())['cooks'][-1];donor=Path(cook['archive']);assert not cook['live_reload'] and sha(donor)==cook['sha256']
    old=inv(base);di=inv(donor);prefix='art/scenario/tuareg/tuareg_agher_refined/'
    members=[r['path'] for r in di['members'] if r['path'].lower().startswith(prefix)];assert any(p.endswith('.rrgeom') for p in members)
    package=OUT/'package';package.mkdir();final=package/'Berber_future_kingdom.sga';run('graft',[ARCH,'graft',base,donor,final,*members]);new=inv(final)
    a={r['path']:r for r in old['members']};b={r['path']:r for r in new['members']};assert a.keys()==b.keys()
    assert new['archive']['name'].replace('-','').lower()=='1d3145e8f1b2427f8bb0067851fcf0f1'
    changed=[]
    for path in b:
        dst=OUT/'readback'/path;src=OUT/'baseline-readback'/path;dst.parent.mkdir(parents=True,exist_ok=True);src.parent.mkdir(parents=True,exist_ok=True)
        run('extract',[ARCH,'extract-member',final,path,dst]);run('extract-baseline',[ARCH,'extract-member',base,path,src])
        if sha(dst)!=sha(src):changed.append(path)
    assert changed and all(p in members for p in changed);assert any(p.endswith('.rrgeom') for p in changed)
    for path in members:assert sha(OUT/'readback'/path)==sha(ROOT/'output/tuareg_refined_trial/readback'/path) or path in changed
    report={'status':'passed','version':VERSION,'archive':str(final),'archive_sha256':sha(final),'members':len(b),'changed_members':changed,'unchanged_members':len(b)-len(changed),'lowering_m':.35,'gameplay_and_Q_controller':'byte-preserved','native_fit':'pending user'}
    (package/'EVIDENCE.json').write_text(json.dumps(report,indent=2));shutil.copy2(OUT/'source-check.json',package/'source-check.json');shutil.copy2(OUT/'shield-cook.log',package/'shield-cook.log')
    (package/'TEST.txt').write_text('Close AoE4. Import '+VERSION+' ZIP into Garrison; enable it and launch through Play.\nTuning: The Berber Dynasties. Game Mode: Berber Civilization. Civilization: Malians.\nShield body is 35 cm lower; central hand grip stays fixed. Check Ages I-IV idle, Q guard, walk/run, attack and brace for height, hand contact and ground/body clipping.\nQ controller and delay, models, longer spear and gameplay are unchanged.\nRollback: close AoE4 and reimport 0.1.5-tuareg-refined.1 ZIP.\n')
    sys.path.insert(0,str(EXT));from garrison_shared import mod_bundle
    mod_bundle.write_manifest(package,bundle_key='berber_future_kingdom',members=[{'mod_key':'berber_future_kingdom','role':'tuning','path':final.name,'sha256':sha(final)}],details={'id':'berber_future_kingdom','name':'The Berber Dynasties','version':VERSION,'summary':'Tuareg shield lowered another 35 cm','author':'hossein81 and marcokistan','updated':'2026-10-11','min_garrison':'0.1.3','content_types':['game-mode','tuning-pack'],'description':'Shield-only fitting trial. Preserve refined bodies, long spear, Q controller and gameplay.','changelog':'Lower shield shell 35 cm with fixed central grip and extended mounts.'})
    zpath=OUT/f'berber_future_kingdom-{VERSION}.zip'
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(zpath) as z:assert z.testzip() is None and hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
    report.update(zip=str(zpath),zip_sha256=sha(zpath));(OUT/'delivery.json').write_text(json.dumps(report,indent=2));print('LOWER_SHIELD_READY',str(zpath),flush=True)
