import sqlite3,json,subprocess
from pathlib import Path
O=Path(__file__).parent;c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%building_town_center%' and extension='.rgd'").fetchall();c.close();(O/'stock_blueprint_catalog.json').write_text(json.dumps(rows,indent=2));print(rows[:5])
A=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe')
for logical,archive in rows:
 if '/core/' in logical or logical.endswith('building_town_center_mal.rgd') or logical.endswith('building_town_center_capital_mal.rgd'):
  stem=Path(logical).stem;rgd=O/(stem+'.rgd');xml=O/(stem+'.xml')
  subprocess.run([str(A),'extract-member',archive,logical,str(rgd)],check=True,capture_output=True)
  subprocess.run([str(A),'decode-rgd',str(rgd),str(xml)],check=True,capture_output=True)
