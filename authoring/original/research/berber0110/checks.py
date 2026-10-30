"""Run complete domain suite and source checks, separate from native acceptance."""
import io,json,subprocess,sys,unittest
from pathlib import Path
from lupa.lua51 import LuaRuntime
from pipeline import ROOT,OUT,WORK,sha,write

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'research/berber0110/tests'))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (OUT/'tests.log').write_text(stream.getvalue(),encoding='utf8')
    files=sorted((ROOT/'research/berber0110/ai').glob('*.scar'))
    write(OUT/'test-validation.json',{'status':'passed' if result.wasSuccessful() else 'failed',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in files},
        'test_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'research/berber0110/tests').glob('*.py')},
        'interpreter':'Python3.13/lupa Lua5.1; strict mocked boundaries, not native engine',
        'native_runtime':'pending'})
    assert result.wasSuccessful(),stream.getvalue()[-12000:]
    load=LuaRuntime(unpack_returned_tuples=True).eval('function(s) local f,e=loadstring(s);return f~=nil,e end')
    for p in files:
        ok,error=load(p.read_text());assert ok,(str(p),error)
    write(OUT/'lua-syntax-validation.json',{'status':'passed','version':'Lua5.1','files':{str(p):sha(p) for p in files}})
    skill=Path('C:/Users/RS/.codex/skills/aoe4-game-mode-skill')
    checks=[('scar_static',[str(skill/'scripts/validate_scar.py'),*[str(p) for p in files],
        '--project-root',str(ROOT/'research/berber0110'),'--json',str(OUT/'static-validation.json')]),
        ('skill_smoke',[str(skill/'scripts/self_test.py')]),
        ('unchanged_editable_tuning',['C:/Users/RS/.codex/skills/modify-aoe4-tuning-packs/scripts/validate_tuning_pack.py',
         str(ROOT/'Berber_future_kingdom.aoe4mod'),'--json',str(OUT/'tuning-source-validation.json')])]
    rows=[]
    for i,(name,args) in enumerate(checks):
        r=subprocess.run([sys.executable,'-B',*args],capture_output=True,text=True,encoding='utf8',errors='replace')
        (OUT/f'check-{i}.log').write_text(r.stdout+r.stderr,encoding='utf8')
        rows.append({'check':name,'exit_code':r.returncode,'log':f'check-{i}.log'})
        assert r.returncode==0,(name,r.stdout[-2500:]+r.stderr[-2500:])
    write(OUT/'checks-summary.json',{'tests':result.testsRun,'lua51':'passed','checks':rows,'native_runtime':'pending'})
    print('CHECKS_PASSED',result.testsRun,'tests, Lua syntax, SCAR static/skill smoke/tuning')
if __name__=='__main__':main()
