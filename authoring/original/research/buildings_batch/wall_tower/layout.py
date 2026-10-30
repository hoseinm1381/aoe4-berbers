import sqlite3,json,subprocess
from pathlib import Path
q=Path('research/buildings_batch/wall_tower');c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True);r=c.execute("select logical_path from resolved_assets where logical_path like '%layout_stonewall_tower%' or logical_path like '%mal_stonewall_tower%' ").fetchall();c.close();print(r)
base='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/core/garrison-core.exe'
p='art/civilizations/common/layouts/archetypes/layout_stonewall_tower/layout_stonewall_tower.rgm'
subprocess.run([base,'convert','decode-static','--logical-path',p,'--config','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json','--index','C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3','--output-root',str(q/'stock')],check=True,capture_output=True)
