import sqlite3,json
from pathlib import Path
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
r=c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%building_unit_naval%' or logical_path like '%tier2_unit_naval_control_mal%' or logical_path like '%layout_dock%' or logical_path like '%layout_naval%'").fetchall();c.close()
Path(__file__).with_name('anchor_paths.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
