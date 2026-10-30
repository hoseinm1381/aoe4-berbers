"""Record reproducible tests, Lua syntax and static diagnostics separately."""
import io,json,subprocess,sys,unittest
from pathlib import Path
from lupa.lua51 import LuaRuntime
from pipeline import ROOT,OUT,WORK,sha,write
sys.path.append(str(ROOT/'research/berber0100'))
import test_ai, test_ownership

def main():
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(m) for m in (test_ai,test_ownership)])
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (OUT/'tests.log').write_text(stream.getvalue(),encoding='utf8')
    files=sorted((ROOT/'assets/scar/ai').glob('*.scar'))+[ROOT/'assets/scar/buildings/tribal_tent.scar']
    write(OUT/'test-validation.json',{'status':'passed' if result.wasSuccessful() else 'failed',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in files},
        'interpreter':'Lua5.1 via lupa; mocked engine, not native gameplay',
        'simulation':'eight slots, seven scripted Berbers plus native English; classic/Nomad;180x10s per case',
        'does_not_prove':['native command costs/availability','native pathfinding or combat','native multiplayer sync','native performance']})
    assert result.wasSuccessful(),stream.getvalue()[-6000:]
    lua=LuaRuntime(unpack_returned_tuples=True)
    load=lua.eval('function(s) local f,e=loadstring(s);return f~=nil,e end')
    for p in files:
        ok,error=load(p.read_text());assert ok,(str(p),error)
    write(OUT/'lua-syntax-validation.json',{'status':'passed','files':{str(p.relative_to(ROOT)):sha(p) for p in files},'version':'Lua5.1'})
    skill=Path('C:/Users/RS/.codex/skills/aoe4-game-mode-skill')
    commands=[
      [str(skill/'scripts/validate_scar.py'),*[str(p) for p in files],str(WORK/'baseline/scar/winconditions/berber_future_kingdom_gm.scar'),
       '--project-root',str(ROOT/'assets/scar'),'--json',str(OUT/'static-validation.json')],
      [str(skill/'scripts/self_test.py')],
      ['C:/Users/RS/.codex/skills/modify-aoe4-tuning-packs/scripts/validate_tuning_pack.py',str(ROOT/'Berber_future_kingdom.aoe4mod'),
       '--json',str(OUT/'tuning-source-validation.json')],
    ]
    summaries=[]
    for i,args in enumerate(commands):
        r=subprocess.run([sys.executable,'-B',*args],capture_output=True,text=True,encoding='utf8',errors='replace')
        (OUT/('check-'+str(i)+'.log')).write_text(r.stdout+r.stderr,encoding='utf8')
        summaries.append({'check':['scar_static','skill_smoke','existing_editable_tuning'][i],'exit_code':r.returncode,'log':'check-'+str(i)+'.log'})
        print(summaries[-1])
    write(OUT/'checks-summary.json',{'tests':'passed','lua51_syntax':'passed','checks':summaries,
        'tuning_scope':'no Attribute Editor records changed; shipped tuning preserved by member hashes',
        'native_runtime':'pending'})
    assert summaries[0]['exit_code']==0 and summaries[1]['exit_code']==0
    print(result.testsRun,'tests and Lua5.1 syntax passed')
if __name__=='__main__':main()
