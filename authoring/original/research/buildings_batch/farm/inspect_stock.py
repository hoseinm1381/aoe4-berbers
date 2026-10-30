import sqlite3,json,subprocess
from pathlib import Path
O=Path(__file__).parent
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%farm%' and extension in ('.rgd','.rgo')").fetchall();c.close()
(O/'catalog.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
A=Path('C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe')
for logical,archive in rows:
 if logical.endswith('building_resource_farm_mal.rgd') or logical.endswith('building_resource_farm.rgd'):
  rgd=O/(Path(logical).stem+'.rgd');xml=rgd.with_suffix('.xml')
  if not rgd.exists():subprocess.run([str(A),'extract-member',archive,logical,str(rgd)],check=True,capture_output=True)
  subprocess.run([str(A),'decode-rgd',str(rgd),str(xml)],check=True,capture_output=True)
