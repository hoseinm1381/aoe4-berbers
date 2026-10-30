import sqlite3,json,subprocess
from pathlib import Path
O=Path(__file__).parent
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%lumber%' and extension in ('.rgo','.rrgeom','.rgm')").fetchall();c.close()
(O/'catalog.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[:35],indent=2))
A=Path('C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe')
rgd=O/'official_wood_mal.rgd';xml=rgd.with_suffix('.xml')
if not rgd.exists():subprocess.run([str(A),'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga','attrib/ebps/races/malian/buildings/building_econ_wood_mal.rgd',str(rgd)],check=True,capture_output=True)
if not xml.exists():subprocess.run([str(A),'decode-rgd',str(rgd),str(xml)],check=True,capture_output=True)


