"""Build the original Berber project with isolated Content Editor outputs."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shield_test'
editor=Path(r'E:\Games\steamapps\common\Age of Empires IV\EssenceEditor.exe')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')
run=WORK/'build'/stamp
logs=run/'logs';out=run/'output';intermediate=run/'intermediate'
for folder in (logs,out,intermediate):folder.mkdir(parents=True,exist_ok=False)
args=[str(editor),'-rtm','--safe_settings','--do_not_restore','--quiet_crash_report','--no_source_control',
      '--log_path',str(logs),'--build_mod',str(ROOT/'Berber_future_kingdom.aoe4mod'),'--no_burn_window',
      '--burn_verbose_log_level','--burn_cache_type','Local','--burn_max_threads','1',
      '--burn_log_path',str(logs/'burn.log'),'--build_path',str(out),'--intermediate_path',str(intermediate)]
record={'schema':'tuareg-shield-editor-build/v1','status':'running','command':args,'run_root':str(run)}
(WORK/'build-result.json').write_text(json.dumps(record,indent=2))
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
with (logs/'stdout.log').open('w') as stdout,(logs/'stderr.log').open('w') as stderr:
    result=subprocess.run(args,cwd=editor.parent,stdout=stdout,stderr=stderr,startupinfo=startup,timeout=300)
record.update(exit_code=result.returncode,status='succeeded' if result.returncode==0 else 'failed')
record['archives']=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in out.rglob('*.sga')]
(WORK/'build-result.json').write_text(json.dumps(record,indent=2))
print(json.dumps({k:record[k] for k in ['status','exit_code','archives']},indent=2),flush=True)
assert result.returncode==0 and len(record['archives'])==1
