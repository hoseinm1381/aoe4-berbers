import os,subprocess,json
from pathlib import Path
R=Path.cwd();O=R/'output/buildings_batch/palisade_gate';env=os.environ.copy();env['BLENDER_USER_CONFIG']=str(O/'isolated-config-audit');si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
with (O/'audit.log').open('w') as log:
 p=subprocess.Popen(['E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(R/'art/buildings/palisade_gate/audit_saved.py')],cwd='E:/Blender5.2',env=env,startupinfo=si,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,stdout=log,stderr=subprocess.STDOUT);(O/'audit_pid.json').write_text(json.dumps({'pid':p.pid}));print(p.pid)
