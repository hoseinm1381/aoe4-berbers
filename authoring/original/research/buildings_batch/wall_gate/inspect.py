import sqlite3,json,subprocess
from pathlib import Path
Q=Path(__file__).parent
base=Path('C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin')
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path from resolved_assets where logical_path like '%abbasids%gate%.rgm'").fetchall();c.close();print(rows)
for k,p in [('mal','attrib/ebps/races/malian/buildings/building_defense_wall_mal/building_defense_wall_gate_mal.rgd'),('core','attrib/ebps/races/core/buildings/building_defense_wall_gate.rgd')]:
 r=Q/(k+'.rgd');x=r.with_suffix('.xml')
 if not r.exists():subprocess.run([str(base/'sga-archiver.exe'),'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',p,str(r)],check=True,capture_output=True)
 if not x.exists():subprocess.run([str(base/'sga-archiver.exe'),'decode-rgd',str(r),str(x)],check=True,capture_output=True)
for p in ['art/civilizations/malian/structures/stonewall/mal_stonewall_smallgate_mp/mal_stonewall_smallgate_mp.rgm']:
 subprocess.run([str(base/'core/garrison-core.exe'),'convert','decode-static','--logical-path',p,'--config','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json','--index','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3','--output-root',str(Q/'stock')],check=True,capture_output=True)
 print('DECODED',p)
