import subprocess,os,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];out=root/'output/buildings_batch/farm';env=os.environ.copy();env['BLENDER_USER_CONFIG']=str(out/'blender_config');si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
script=sys.argv[1] if len(sys.argv)>1 else 'build_farm.py'
with (out/(Path(script).stem+'_stdout.log')).open('w',encoding='utf-8') as log:
 p=subprocess.Popen(['E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(Path(__file__).with_name(script))],cwd='E:/Blender5.2',env=env,startupinfo=si,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,stdout=log,stderr=subprocess.STDOUT)
 (out/'process.json').write_text(json.dumps({'pid':p.pid,'script':'build_farm.py'}));print('PID',p.pid,flush=True);rc=p.wait();print('EXIT',rc)
