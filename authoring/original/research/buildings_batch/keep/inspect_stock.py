import sqlite3,json,subprocess
from pathlib import Path
O=Path('research/buildings_batch/keep');c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select * from resolved_assets where logical_path like '%keep%' and extension='.rgm'").fetchall();cols=[d[1] for d in c.execute('pragma table_info(resolved_assets)')];c.close()
(O/'catalog.json').write_text(json.dumps([dict(zip(cols,r)) for r in rows],indent=2));print(json.dumps([dict(zip(cols,r)) for r in rows][:8],indent=2))
a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for key,path in [('core','attrib/ebps/races/core/buildings/building_defense_keep.rgd'),('mal','attrib/ebps/races/malian/buildings/building_defense_keep_mal.rgd')]:
 r=O/(key+'.rgd');x=r.with_suffix('.xml')
 if not r.exists():subprocess.run([a,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',path,str(r)],check=True,capture_output=True)
 if not x.exists():subprocess.run([a,'decode-rgd',str(r),str(x)],check=True,capture_output=True)

