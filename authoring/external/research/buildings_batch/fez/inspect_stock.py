import sqlite3,json,subprocess
from pathlib import Path
Q=Path('research/buildings_batch/fez'); c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where extension='.rgm' and (logical_path like '%university%abb%' or logical_path like '%landmark%mal%')").fetchall(); c.close(); (Q/'catalog.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[:25],indent=2))
a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
r=Q/'official_parent.rgd';x=Q/'official_parent.xml'
subprocess.run([a,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga','attrib/ebps/races/core/buildings/building_wonder_age3.rgd',str(r)],check=True,capture_output=True)
subprocess.run([a,'decode-rgd',str(r),str(x)],check=True,capture_output=True)
