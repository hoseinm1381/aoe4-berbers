import subprocess,os,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];O=R/'output/buildings_batch/marrakech';O.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env['BLENDER_USER_CONFIG']=str(O/'blender_config')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
script=sys.argv[1] if len(sys.argv)>1 else 'build_marrakech.py';tag='audit' if script!='build_marrakech.py' else 'blender'
with (O/(tag+'_stdout.log')).open('w',encoding='utf-8') as out,(O/(tag+'_stderr.log')).open('w',encoding='utf-8') as err:
 p=subprocess.Popen(['E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(R/'art/buildings/marrakech'/script)],cwd='E:/Blender5.2',env=env,startupinfo=si,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS,stdout=out,stderr=err)
 (O/'process.json').write_text(json.dumps({'pid':p.pid,'task':'marrakech','command':'hidden factory-startup offline task-owned GUI process'}));print(p.pid,flush=True);rc=p.wait();print('EXIT',rc)


