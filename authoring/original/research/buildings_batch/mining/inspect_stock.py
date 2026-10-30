import sqlite3,json,subprocess
from pathlib import Path
p=Path('research/buildings_batch/mining')
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%mining_camp%' and extension in ('.rgo','.rgd')").fetchall();c.close();(p/'catalog.json').write_text(json.dumps(rows,indent=2));print(json.dumps([r for r in rows if 'malian' in r[0]],indent=2))
a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for logical,archive in rows:
 if logical.endswith('building_econ_mining_camp_mal.rgd') or logical.endswith('building_econ_mining_camp.rgd'):
  rgd=p/Path(logical).name;subprocess.run([a,'extract-member',archive,logical,str(rgd)],check=True,capture_output=True);subprocess.run([a,'decode-rgd',str(rgd),str(rgd.with_suffix('.xml'))],check=True,capture_output=True)
