import sqlite3,json
from pathlib import Path
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
queries={
 'shaders':"select logical_path,archive_path from resolved_assets where extension in ('.shader','.material') limit 30",
 'houses':"select logical_path,archive_path from resolved_assets where logical_path like '%house%' and extension in ('.rgm','.rgo','.rrm') limit 25"
}
result={k:c.execute(v).fetchall() for k,v in queries.items()};c.close()
Path(__file__).with_name('stock-candidates.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
