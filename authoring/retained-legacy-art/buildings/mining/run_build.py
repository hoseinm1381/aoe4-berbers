import subprocess,os,json,sys
from pathlib import Path
p=Path(__file__).parent;root=p.parents[2];out=root/'output/buildings_batch/mining'
env=os.environ.copy();env['BLENDER_USER_CONFIG']=str(out/'blender_config')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
script=p/(sys.argv[1] if len(sys.argv)>1 else 'build_mining.py')
with (out/(script.stem+'.log')).open('w') as log:
 proc=subprocess.Popen(['E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(script)],cwd='E:/Blender5.2',env=env,startupinfo=si,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,stdout=log,stderr=subprocess.STDOUT)
 (out/(script.stem+'_process.json')).write_text(json.dumps({'pid':proc.pid,'task':'mining','script':str(script)}));code=proc.wait();print('MINING_BLENDER_EXIT',code)
