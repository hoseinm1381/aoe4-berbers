import bpy,sys,sqlite3,json,traceback
from pathlib import Path
R=Path(r'E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai');O=R/'research/buildings_batch/tc'
E=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison');sys.path.insert(0,str(E.parent))
import garrison;garrison.register()
from garrison.addon_common import _core_bridge
try:
 c=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
 rows=c.execute("select logical_path,archive_path from resolved_assets where extension='.rgm' and (logical_path like '%town%center%' or logical_path like '%towncentre%')").fetchall();c.close()
 (O/'donor_candidates.json').write_text(json.dumps(rows,indent=2))
 print('CANDIDATES',rows[:30],flush=True)
 chosen=next((r for r in rows if 'abb' in r[0] and 'age01' in r[0] and 'control' in r[0]),rows[0]);p=bpy.context.scene.garrison;p.asset_library_root='E:/bt20';p.game_asset_connection='C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json';p.game_asset_index='C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3'
 result=_core_bridge(p,180).decode_game_asset_static(chosen[0],p.game_asset_connection,p.game_asset_index,O/'stock')
 (O/'decode_result.txt').write_text(str(result));print('DECODE',str(result)[:1000],flush=True)
except: (O/'DECODE_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

