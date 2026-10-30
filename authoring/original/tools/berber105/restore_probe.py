"""Restore actual canonical inputs in the isolated cold tree, originals denied."""
from pathlib import Path
import json,os,shutil,subprocess,sys
import workspace as w

def main():
    index=w.read(w.HERE/'source-index.json.gz');assert w.sha(index['bundle'])==index['bundle_sha256']
    cold=w.OUT/'work/cold';assert (cold/'project/guard.py').is_file()
    tools=cold/'project/tools/berber105';shutil.copytree(w.HERE,tools,dirs_exist_ok=True)
    target=cold/'external/rebuild_inputs/current/source-blobs.zip';target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():w.safe_target(target).unlink()
    shutil.copyfile(index['bundle'],target);assert w.sha(target)==index['bundle_sha256']
    selected=[];seen=set()
    for r in index['files']:
        kind=r.get('kind','unknown')
        if kind not in seen and 0<r['bytes']<50_000_000:seen.add(kind);selected.append(r)
    sample=tools/'restore-samples.json';w.save(sample,selected)
    probe=tools/'restore_actual.py'
    probe.write_text('''import json,zipfile
from pathlib import Path
import workspace as w
index=w.read(w.HERE/'source-index.json.gz');bundle=w.source_bundle(index)
results=[]
with zipfile.ZipFile(bundle) as z:
 for row in w.read(w.HERE/'restore-samples.json'):
  target=w.EXTERNAL/'restored-probe'/index['bundle_sha256']/row['sha256']
  w.safe_target(target);w.restore_one(z,row['member'],target,row['sha256'])
  assert target.stat().st_size==row['bytes'] and w.sha(target)==row['sha256']
  try:w.restore_one(z,row['member'],target,row['sha256'])
  except FileExistsError:pass
  else:raise AssertionError('Existing edit could be overwritten')
  results.append({'kind':row.get('kind'),'sha256':row['sha256'],'bytes':row['bytes']})
w.save(w.EXTERNAL/'restoration-results.json',results)
''')
    env=dict(os.environ,BERBER_STORAGE=str(cold/'external'),PYTHONPATH='')
    result=subprocess.run([sys.executable,'-B',str(cold/'project/guard.py'),str(probe)],env=env,cwd=cold/'project',capture_output=True,text=True)
    (w.OUT/'restoration-probe.log').write_text(result.stdout+'\n'+result.stderr);assert result.returncode==0,result.stderr
    # Prove that the negative boundary is active, not just a claim in a report.
    deny=tools/'deny_original.py';deny.write_text('open('+repr(str(w.ROOT/'README.md'))+',"rb")\n')
    blocked=subprocess.run([sys.executable,'-B',str(cold/'project/guard.py'),str(deny)],env=env,cwd=cold/'project',capture_output=True,text=True)
    assert blocked.returncode!=0 and 'Original Berber tree unavailable' in blocked.stderr
    w.save(w.OUT/'restoration-proof.json',{'status':'passed','current_bundle_sha256':index['bundle_sha256'],'samples':w.read(cold/'external/restoration-results.json'),'original_tree_access_rejected':True,'existing_files_never_overwritten':True})
    print('CURRENT_INPUT_RESTORE_PASSED',len(selected),flush=True)
if __name__=='__main__':main()
