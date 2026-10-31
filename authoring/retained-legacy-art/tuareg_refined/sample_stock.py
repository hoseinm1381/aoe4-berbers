import json,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'output/tuareg_refined_trial';WORK.mkdir(exist_ok=True)
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
for index in (143,131,130,119,88,219,117):
    out=WORK/f'clips/clip{index}.json';out.parent.mkdir(exist_ok=True)
    if out.exists():continue
    with (WORK/f'clips/clip{index}.log').open('w',encoding='utf-8') as f:
        p=subprocess.run([str(EXT/'bin/core/garrison-core.exe'),'-m','src.core.animation_clip','--logical-path','art/civilizations/common/humans/archetypes/base_spearshield/base_spearshield.rhka','--clip-index',str(index),'--expected-sha256','6283ae7d072e7a1b0991b482b6a38bed3bb58458dd432d46982c972c7d65621f','--config',str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.local.json'),'--index',str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.sqlite3'),'--output',str(out)],stdout=f,stderr=subprocess.STDOUT,timeout=180)
    assert p.returncode==0,index
    data=json.loads(out.read_text());print(index,data['name'],data['frame_count'],flush=True)
