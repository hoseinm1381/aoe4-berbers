import sys,subprocess,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_3_0';OUT.mkdir(exist_ok=True)
stage=sys.argv[1];script=Path(sys.argv[2]).resolve()
command=([r'E:/Blender5.2/blender.exe','--factory-startup','--offline-mode','-noaudio','--python',str(script)] if stage.startswith('blender') else [sys.executable,str(script),*sys.argv[3:]])
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
environment=os.environ.copy();environment['BLENDER_USER_CONFIG']=str(ROOT/'output/tribal_tent/iteration001/isolated-blender-config')
with (OUT/(stage+'.stdout.log')).open('w') as a,(OUT/(stage+'.stderr.log')).open('w') as b:
    process=subprocess.Popen(command,stdout=a,stderr=b,stdin=subprocess.DEVNULL,env=environment,cwd='E:/Blender5.2' if stage.startswith('blender') else ROOT,startupinfo=startup,creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP)
(OUT/(stage+'.process.json')).write_text(json.dumps({'pid':process.pid,'command':command},indent=2));print(stage,process.pid)
