import sys,bpy
from pathlib import Path
sys.path.insert(0,r'E:\age of empires 4 mods\AI_Assisted_modding\Berber_future_kingdom_ai\art\buildings\wall_bastion')
try:
 exec(compile(Path(r'E:\age of empires 4 mods\AI_Assisted_modding\Berber_future_kingdom_ai\art\buildings\wall_bastion\build_bastion.py').read_text().split('try:\n donor()')[0],r'E:\age of empires 4 mods\AI_Assisted_modding\Berber_future_kingdom_ai\art\buildings\wall_bastion\build_bastion.py', 'exec'))
 build(4)
finally:bpy.ops.wm.quit_blender()
