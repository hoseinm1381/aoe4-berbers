"""Launch task-owned hidden workers, preserving the live user Blender."""
import subprocess,sys,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/berber_update_0_2_0';OUT.mkdir(exist_ok=True)
stage=sys.argv[1];script=Path(sys.argv[2]).resolve()
if stage.startswith('blender'):
    command=[r'E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(script)]
    cwd=r'E:/Blender5.2'
else:
    command=[sys.executable,str(script),*sys.argv[3:]];cwd=ROOT
environment=os.environ.copy();environment['BLENDER_USER_CONFIG']=str(ROOT/'output/tribal_tent/iteration001/isolated-blender-config')
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
with (OUT/(stage+'.stdout.log')).open('w',encoding='utf-8') as a,(OUT/(stage+'.stderr.log')).open('w',encoding='utf-8') as b:
    process=subprocess.Popen(command,stdout=a,stderr=b,stdin=subprocess.DEVNULL,cwd=cwd,env=environment,startupinfo=startup,creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP)
(OUT/(stage+'.process.json')).write_text(json.dumps({'pid':process.pid,'command':command},indent=2),encoding='utf-8')
print(json.dumps({'stage':stage,'pid':process.pid}))
