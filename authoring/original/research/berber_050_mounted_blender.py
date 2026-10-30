"""Bootstrap the installed compiled Garrison core for a private mounted review."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

EXT = Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
spec = importlib.util.spec_from_file_location('garrison_shared', EXT / 'garrison_shared.cp313-win_amd64.pyd')
if spec is None or spec.loader is None:
    raise RuntimeError('Installed Garrison compiled core unavailable')
shared = importlib.util.module_from_spec(spec)
sys.modules['garrison_shared'] = shared
spec.loader.exec_module(shared)
sys.modules['garrison.garrison_shared'] = shared
sys.path.insert(0, str(Path(__file__).resolve().parent))

import berber_050_unit_blender
import bpy

bpy.context.preferences.filepaths.save_version = 0
berber_050_unit_blender.main()

# Native names may not encode the real LOD. Show only the imported first LOD.
for root_name in ('Official donor textured','Berber candidate textured'):
    root = bpy.data.objects[root_name]
    for obj in root.children_recursive:
        if obj.type != 'MESH':
            continue
        show = obj.get('garrison_lod_level') == 1
        obj.hide_set(not show)
        obj.hide_render = not show
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
