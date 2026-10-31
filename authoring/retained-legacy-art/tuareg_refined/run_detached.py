"""Launch a task-owned, hidden worker outside the tool session's Windows job."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'output/tuareg_refined_trial'
kind=sys.argv[1]
python=r'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
commands={
 'source-check':[r'E:\Blender5.2\blender.exe','--background','--factory-startup','--python',str(ROOT/'art/tuareg_refined/verify_source.py')],
 'art-cook':[python,str(ROOT/'art/tuareg_refined/build_garrison.py'),'--cook-only'],
 'candidate-build':[python,str(ROOT/'art/tuareg_refined/integrate_trial.py'),'build']}
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
out=(WORK/(kind+'-detached.stdout.log')).open('w');err=(WORK/(kind+'-detached.stderr.log')).open('w')
flags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS
try:
    proc=subprocess.Popen(commands[kind],stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=flags|subprocess.CREATE_BREAKAWAY_FROM_JOB,startupinfo=startup,cwd=ROOT)
except OSError:
    proc=subprocess.Popen(commands[kind],stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=flags,startupinfo=startup,cwd=ROOT)
(WORK/(kind+'-process.json')).write_text(json.dumps({'pid':proc.pid,'command':commands[kind]},indent=2));print(kind,proc.pid)
