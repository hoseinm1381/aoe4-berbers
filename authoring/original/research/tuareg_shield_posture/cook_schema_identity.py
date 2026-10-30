"""Ask Garrison's current serializer to issue the private schema identity."""
import json
import os
from pathlib import Path
import sys
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import mod_project
ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_shield_posture_test"
project = WORK / "schema-library/Mods/tuareg_posture_schema"
result = mod_project.cook_mod_project(project, Path(r"E:\Games\steamapps\common\Age of Empires IV\EssenceEditor.exe"), timeout_seconds=300)
(WORK / "schema-cook.json").write_text(json.dumps(result, indent=2, default=str))
print(json.dumps(result, default=str), flush=True)
