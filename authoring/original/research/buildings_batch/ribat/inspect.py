import sqlite3,json,subprocess
from pathlib import Path
Q=Path(__file__).parent
base=Path('C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin')
a=str(base/'sga-archiver.exe')
for key,path in [('core','attrib/ebps/races/core/buildings/building_wonder_age1.rgd'),('mal','attrib/ebps/races/malian/buildings/building_landmark_age1_landmarka_mal.rgd')]:
 r=Q/(key+'.rgd');x=r.with_suffix('.xml')
 if not r.exists():subprocess.run([a,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',path,str(r)],check=True,capture_output=True)
 if not x.exists():subprocess.run([a,'decode-rgd',str(r),str(x)],check=True,capture_output=True)
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where extension='.rgm' and (logical_path like '%landmark%' and (logical_path like '%mal%' or logical_path like '%abb%'))").fetchall();c.close()
(Q/'catalog.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))

