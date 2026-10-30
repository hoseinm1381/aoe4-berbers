import subprocess,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'output/buildings_batch/fez';script=ROOT/'research/buildings_batch/fez/audit_saved.py'
env=os.environ.copy();env['BLENDER_USER_CONFIG']=str(out/'private_blender_config')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
with open(out/'audit.log','w',encoding='utf-8') as log:
 p=subprocess.Popen(['E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(script)],cwd='E:/Blender5.2',env=env,stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
 (out/'audit_process.json').write_text(json.dumps({'pid':p.pid,'script':str(script)}));print(p.pid,flush=True);p.wait();print('EXIT',p.returncode)


