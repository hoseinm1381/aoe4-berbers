"""Cook original Tuareg art through installed, supported Garrison operations."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'output/tuareg_art_guard_trial';ART=ROOT/'art/tuareg_overhaul'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe';PROJECT=ART/'garrison_library/Mods/tuareg_art_v2'
report={'status':'running','steps':[]}
def run(label,args):
    log=WORK/(label+'.log')
    with log.open('w',encoding='utf-8') as f:
        result=subprocess.run([str(CORE),*[str(x) for x in args]],stdout=f,stderr=subprocess.STDOUT,timeout=900)
    row={'step':label,'exit_code':result.returncode,'log':str(log)};report['steps'].append(row)
    (WORK/'garrison-art-build.json').write_text(json.dumps(report,indent=2))
    if result.returncode:raise RuntimeError(row)
    print(label,'passed',flush=True)
for age in ([] if '--cook-only' in sys.argv else range(1,5)):
    source=ART/f'exports/tuareg_age{age}'
    run(f'age{age}-validate',['mod-project','unit-validate','--source',source/'action.json'])
    run(f'age{age}-add',['mod-project','unit-add','--project',PROJECT,'--source',source,'--name',f'tuareg_age{age}'])
for item in ([] if '--cook-only' in sys.argv else json.loads((WORK/'art-source-checks.json').read_text())['equipment']):
    export=item['export'];name=item['name']
    run(name+'-prepare',['static','prepare','--request',export['request'],'--report',export['report']])
    run(name+'-add',['mod-project','add','--project',PROJECT,'--manifest',export['manifest'],'--label',name])
model_editor=json.loads(Path(json.loads((WORK/'art-source-checks.json').read_text())['equipment'][0]['export']['request']).read_text())['cook_editor']
run('art-cook',['mod-project','cook','--project',PROJECT,'--editor',model_editor,'--timeout','600'])
report['status']='succeeded';(WORK/'garrison-art-build.json').write_text(json.dumps(report,indent=2));print('TUAREG_ART_COOKED',flush=True)
