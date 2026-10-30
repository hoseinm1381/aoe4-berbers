import sqlite3
c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
print(c.execute("select logical_path,archive_path from resolved_assets where logical_path like '%stamps%' and logical_path like '%lumber%'").fetchall())
print(c.execute("select logical_path from resolved_assets where extension='.rgm' and (logical_path like '%wood_camp%' or logical_path like '%lumber%' or logical_path like '%sawmill%' or logical_path like '%shelter%')").fetchall())
