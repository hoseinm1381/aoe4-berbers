"""Small selective official donor regeneration. Python3.13 + installed Garrison."""
import json,os,subprocess
from pathlib import Path
from berber_040_integrate_cache import read_cached_json
CACHE=Path('F:/aoe_4_temp/berber_040_university_donors')
SOURCE='art/civilizations/abbasids/structures/university/abb_university_control_age04/abb_university_control_age04.rgm'
def ensure():
 for directory in CACHE.iterdir():
  if not directory.is_dir():continue
  p=directory/'decoded-static.json'
  if not p.exists() and not (directory/'rebuild-cache.json').exists():continue
  d=read_cached_json(p)
  if d['request']['logical_path']==SOURCE and Path(d['geometry']['source']['path']).is_file():return p
 ext=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
 subprocess.run([str(ext/'bin/core/garrison-core.exe'),'convert','decode-static','--logical-path',SOURCE,'--config','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json','--index','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3','--output-root',str(CACHE)],check=True)
 return next(p for p in CACHE.glob('*/decoded-static.json') if json.loads(p.read_text())['request']['logical_path']==SOURCE)
if __name__=='__main__':print(ensure())
