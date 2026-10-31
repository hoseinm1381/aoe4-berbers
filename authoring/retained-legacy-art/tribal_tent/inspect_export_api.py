import bpy, sys, inspect, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison')
sys.path.insert(0,str(EXT))
from garrison_shared import asset_authoring, building_project
result={}
for module in (asset_authoring,building_project):
    result[module.__name__]={n:str(inspect.signature(v)) for n,v in vars(module).items() if inspect.isfunction(v) and not n.startswith('_')}
out=ROOT/'output/berber_update_0_2_0'
out.mkdir(exist_ok=True)
(out/'export-api.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('API_INSPECTION_DONE',flush=True)
bpy.ops.wm.quit_blender()
