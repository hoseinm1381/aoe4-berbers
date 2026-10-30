import json,sqlite3,subprocess,os
from pathlib import Path
R=Path.cwd(); O=R/'output/berber_update_0_2_5/authors/lumber';O.mkdir(parents=True,exist_ok=True)
G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'; A=G/'bin/sga-archiver.exe'
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%econ_wood%' or logical_path like '%lumbercamp%' or logical_path like '%lumber_camp%' ").fetchall(); c.close()
(O/'catalog.json').write_text(json.dumps(rows,indent=2))
for p,a in rows:
 if p.endswith('.rgd') and ('tier1_econ_wood_control_eng' in p or p.endswith('/building_econ_wood.rgd')):
  dest=O/Path(p).name;subprocess.run([str(A),'extract-member',a,p,str(dest)],check=True,capture_output=True);subprocess.run([str(A),'decode-rgd',str(dest),str(dest.with_suffix('.xml'))],check=True,capture_output=True)
print([(p,a) for p,a in rows if p.endswith('.rgd')])
