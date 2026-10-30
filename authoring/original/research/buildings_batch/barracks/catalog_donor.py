import sqlite3,json,subprocess
from pathlib import Path
O=Path(__file__).parent
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
rows=c.execute("select logical_path,archive_path from resolved_assets where extension='.rgm' and logical_path like '%barracks%' and logical_path like '%abb%'").fetchall();c.close()
(O/'catalog.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[:20],indent=2))
