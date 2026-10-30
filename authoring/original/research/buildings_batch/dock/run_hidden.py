import subprocess,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];out=ROOT/'output/buildings_batch/dock';script=ROOT/'art/buildings/dock/build_dock.py'
env=os.environ.copy();env['BLENDER_USER_CONFIG']=str(out/'private_blender_config')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
stem='blender_refine' if env.get('DOCK_AGES') else 'blender'
with open(out/(stem+'.log'),'w',encoding='utf-8') as log:
 p=subprocess.Popen(['E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(script)],cwd='E:/Blender5.2',env=env,stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
 (out/(stem+'_process.json')).write_text(json.dumps({'pid':p.pid,'script':str(script),'ages':env.get('DOCK_AGES','1,2,3,4')}));print(p.pid,flush=True);p.wait();print('EXIT',p.returncode)
