"""Cook all source buildings, then compose owned visual-only test bindings."""
import json,os,sys,subprocess,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_3_0';LIB=Path('E:/b30');PROJECT=LIB/'Mods/berber_buildings_030'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe';GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(label,args,timeout=1800):
    env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
    with (OUT/(label+'.log')).open('w',encoding='utf-8') as f:
        result=subprocess.run([str(a) for a in args],stdout=f,stderr=subprocess.STDOUT,timeout=timeout,env=env)
    assert result.returncode==0,(label,result.returncode)
    return (OUT/(label+'.log')).read_text(encoding='utf-8')
def cook():
    export=read(OUT/'export-report.json');assert export['status']=='passed' and len(export['assets'])==92
    if not PROJECT.exists():
        run('create-art-project',[CORE,'mod-project','create','--library',LIB,'--name','Berber Buildings 030'])
        run('art-settings',[CORE,'mod-project','settings','--project',PROJECT,'--mod-id',GUID,'--version','0.3.0','--live-reload','off','--summary','All Berber building model source variants'])
    record=read(PROJECT/'mod-project.json');existing={r['name'] for r in record.get('buildings',[])}
    rebuild=set(read(OUT/'texture-normalization.json')['rebuild_names']) if (OUT/'texture-normalization.json').exists() else set()
    for i,asset in enumerate(export['assets']):
        if asset['name'] not in existing or asset['name'] in rebuild:
            run('add-'+asset['name'],[CORE,'mod-project','building','--project',PROJECT,'--source',asset['export'],'--name',asset['name'],'--profile','english-house','--integration','script'])
        write(OUT/'cook-progress.json',{'stage':'added','completed':i+1,'total':92,'name':asset['name']})
        print('ADDED',i+1,asset['name'],flush=True)
    run('art-cook',[CORE,'mod-project','cook','--project',PROJECT,'--editor',Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--timeout','1500'],timeout=1800)
    result=read(PROJECT/'mod-project.json')['cooks'][-1];assert not result['live_reload'] and sha(result['archive'])==result['sha256']
    write(OUT/'art-build.json',{'status':'passed','project':str(PROJECT),'cook':result});print('ALL_92_MODELS_COOKED',flush=True)
def extract():
    old=read(ROOT/'output/berber_update_0_2_1/delivery.json');base=Path(old['archive']);assert sha(base)==old['archive_sha256']
    donor=Path(read(OUT/'art-build.json')['cook']['archive'])
    for label,archive in [('baseline',base),('donor',donor)]:
        destination=OUT/(label+'-readback')
        if not destination.exists():run(label+'-unpack',[ARCH,'unpack',archive,'--output',destination])
    official=Path(r'E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
    if not (OUT/'official-inventory.json').exists():write(OUT/'official-inventory.json',json.loads(run('official-inventory',[ARCH,'list',official,'--verify'])))
    (OUT/'official').mkdir(exist_ok=True)
    print('READBACK_INPUTS_READY',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
