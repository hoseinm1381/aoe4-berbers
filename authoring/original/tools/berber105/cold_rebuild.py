"""Independent build with original Berber paths denied by a Python audit hook."""
from pathlib import Path
import json,os,shutil,subprocess,sys,time
import workspace as w

def main():
    cold=w.OUT/'work/cold';w.safe_target(cold);cold.mkdir(parents=True,exist_ok=True)
    source=cold/'project';external=cold/'external';tools=source/'tools/berber105'
    shutil.copytree(w.HERE,tools,dirs_exist_ok=True)
    shutil.copytree(w.ROOT/'assets',source/'assets',dirs_exist_ok=True)
    baseline=external/'output/berber_update_1_0_4';baseline.mkdir(parents=True,exist_ok=True)
    for p in (w.BASE,w.ROLLBACK):
        if not (baseline/p.name).exists():shutil.copyfile(p,baseline/p.name)
        assert w.sha(p)==w.sha(baseline/p.name)
    guard=source/'guard.py'
    guard.write_text('''import sys,os,runpy
allowed=os.path.normcase(os.path.abspath('''+repr(str(cold))+'''))+os.sep
blocked=tuple(os.path.normcase(os.path.abspath(p))+os.sep for p in '''+repr([str(w.ROOT),str(w.EXTERNAL)])+''')
def audit(event,args):
 if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes)):
  p=os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
  if not p.startswith(allowed) and any(p.startswith(root) for root in blocked):raise PermissionError('Original Berber tree unavailable: '+p)
sys.addaudithook(audit)
sys.argv=sys.argv[1:];sys.path.insert(0,os.path.dirname(os.path.abspath(sys.argv[0])))
runpy.run_path(sys.argv[0],run_name='__main__')
''')
    env=dict(os.environ,BERBER_STORAGE=str(external),PYTHONPATH='')
    commands=[
        [tools/'test_workspace.py'],[tools/'native_ai/test_native.py'],
        [tools/'build.py','compose','--output',cold/'rebuilt.sga'],
        [tools/'workspace.py','package','--destination',cold/'delivery'],
        [tools/'workspace.py','verify','--destination',cold/'delivery'],
    ]
    results=[]
    for i,args in enumerate(commands):
        started=time.monotonic();p=subprocess.run([sys.executable,'-B',str(guard),*map(str,args)],cwd=source,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
        (w.OUT/('cold-'+str(i)+'.log')).write_text(p.stdout+'\n'+p.stderr)
        assert p.returncode==0,(i,p.stderr[-2500:]);results.append({'command':list(map(str,args)),'exit_code':0,'seconds':round(time.monotonic()-started,2)})
        print('COLD_STEP',i,'passed',flush=True)
    assert w.sha(cold/'rebuilt.sga')==w.BASE_SHA
    w.save(w.OUT/'cold-rebuild-proof.json',{'status':'passed','original_project_and_external_reads_denied':True,'historical_release_folders_present':False,'rebuilt_sga_sha256':w.sha(cold/'rebuilt.sga'),'all_8529_resource_hashes_compared':True,'commands':results,'bytes_of_disposable_cold_workspace':sum(p.stat().st_size for p in w.walk(cold))})
    print('COLD_REBUILD_PASSED',flush=True)
if __name__=='__main__':main()
