"""Release-owned paths. Never derive the editable root from a resolved junction."""
from pathlib import Path
import hashlib, json, os, subprocess, time

ROOT = Path(__file__).absolute().parents[2]
OUT = ROOT / 'output/berber_update_0_6_0'
ART = ROOT / 'art/voices_0_6_0'
BASE = ROOT / 'output/berber_update_0_5_1/package/Berber_future_kingdom.sga'
BASE_SHA = 'acbcd6501a1e8ebea2c7dae8701641625c96c078e3a4d33e9c2968111732717b'
GUID = '1d3145e8-f1b2-427f-8bb0-067851fcf0f1'
EXT = Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE = EXT / 'bin/core/garrison-core.exe'
ARCH = EXT / 'bin/sga-archiver.exe'
GAME = Path('E:/Games/steamapps/common/Age of Empires IV')
WWISE = Path('C:/Audiokinetic/Wwise_2023.1.3.8471/Authoring/x64/Release/bin/WwiseConsole.exe')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def write(p,value):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Windows readers/AV can briefly deny replacing a closed destination. Keep
    # atomic replacement: never truncate or unlink the previous valid document.
    for attempt in range(8):
        try:
            tmp.replace(p)
            break
        except PermissionError:
            if attempt==7:raise
            time.sleep(min(.05*2**attempt,1.6))

def run(*args,timeout=600):
    r=subprocess.run([str(a) for a in args],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=timeout)
    if r.returncode: raise RuntimeError(f'Tool failed {r.returncode}: {args[0]}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}')
    return r.stdout
