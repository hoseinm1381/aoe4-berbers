import sys,bpy
from pathlib import Path
sys.executable=r'E:/Blender5.2/5.2/python/bin/python.exe'
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison');sys.path.insert(0,str(EXT));sys.path.insert(0,str(EXT.parent))
import garrison_shared
from garrison_shared import building_project,game_locator
print('SHARED_PASSED',building_project.DEFAULT_PROFILE,game_locator)
sys.modules['garrison.garrison_shared']=garrison_shared
import garrison;garrison.register()
print('REGISTER_PASSED');bpy.ops.wm.quit_blender()

