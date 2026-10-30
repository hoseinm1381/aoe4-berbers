import sqlite3,subprocess,json,hashlib
from pathlib import Path
q=Path(__file__).parent;out=q/'native_layout';out.mkdir(exist_ok=True)
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
cur=c.execute("select logical_path,archive_path,raw_name from resolved_assets where (logical_path like '%layout_stonewall_tower%' or logical_path like '%mal_stonewall_tower/mal_stonewall_tower%') and extension in ('.rgm','.rgo')")
rows=cur.fetchall();c.close();report=[]
a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for logical,archive,raw in rows:
    p=out/Path(logical).name
    if not p.exists():subprocess.run([a,'extract-member',archive,logical,str(p)],check=True,capture_output=True)
    report.append({'logical_path':logical,'archive':archive,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'untouched':True})
(out/'manifest.json').write_text(json.dumps(report,indent=2));print('PRESERVED',len(report),'native model/layout inputs')

