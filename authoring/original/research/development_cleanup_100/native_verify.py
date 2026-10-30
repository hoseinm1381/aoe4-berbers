"""Read-only native integrity verification of all retained source/checkpoint SGAs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,os,subprocess
from inventory import ROOT,REPORT,sha,save

ARCH=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
rows=json.loads((REPORT/'deletion-plan.json').read_text())['protected_archives']
rows=[r for r in rows if Path(r['path']).suffix.lower()=='.sga']
def check(row):
 p=Path(row['path']);r=subprocess.run([str(ARCH),'list',str(p),'--verify'],capture_output=True,text=True,encoding='utf8',errors='replace')
 result={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'exit_code':r.returncode}
 if r.returncode==0:
  d=json.loads(r.stdout);result['verification']=d['archive']['verification'];result['members']=len(d['members'])
  assert result['verification']['verified']
 else:result['diagnostic']=(r.stderr or r.stdout)[-2000:]
 print('NATIVE',p.parent.name,r.returncode,flush=True);return result
with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(check,rows))
failures=[r for r in results if r['exit_code']]
save(REPORT/'native-sga-verification.json',{'results':results,'failures':failures,'note':'Historical 428-byte Tuareg probe, if rejected, is retained as provenance rather than a release archive.'})
assert all(r['bytes']==428 and 'tuareg' in r['path'].lower() for r in failures),failures
print('NATIVE_VERIFIED',len(results)-len(failures),'historic_probe_exceptions',len(failures))
