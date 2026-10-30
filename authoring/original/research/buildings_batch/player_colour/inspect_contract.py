import sys, inspect, sqlite3, json
from pathlib import Path
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison')
sys.path.insert(0,str(EXT))
from garrison_shared import building_project
result={}
for m in (building_project,):
    result[m.__name__]={n:str(inspect.signature(v)) for n,v in vars(m).items() if inspect.isfunction(v) and not n.startswith('__')}
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
result['tables']=c.execute("select name,sql from sqlite_master where type='table'").fetchall()
c.close()
Path(__file__).with_name('api.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
