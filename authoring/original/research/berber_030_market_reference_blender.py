"""Open decoded stock donor copies in an isolated Blender reference scene."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
spec = importlib.util.spec_from_file_location("garrison_shared", str(EXT / "garrison_shared.cp313-win_amd64.pyd"))
shared = importlib.util.module_from_spec(spec)
sys.modules["garrison_shared"] = shared
spec.loader.exec_module(shared)
sys.path.insert(0, str(EXT.parent))
import garrison

sys.modules["garrison.garrison_shared"] = shared
from garrison.decode_projection import _apply_decoded_static


def add_donor(manifest, label, x_offset):
    data = json.loads(manifest.read_text(encoding="utf-8"))
    proxy = bpy.data.objects.new(label + " source", None)
    bpy.context.scene.collection.objects.link(proxy)
    proxy["garrison_decode_manifest"] = str(manifest)
    proxy["garrison_logical_path"] = data["request"]["logical_path"]
    proxy["garrison_display_name"] = label
    root = _apply_decoded_static(proxy, data, create_controls=False)
    root.name = label
    root.location.x = x_offset
    print(label, "meshes", len([o for o in root.children_recursive if o.type == "MESH"]))


bpy.ops.wm.read_factory_settings(use_empty=True)
cache = ROOT / "output/shared_stock_cache/buildings_030"
add_donor(cache / "1ab6b9d2f7f10490f630/decoded-static.json", "Abbasid Market Age II", 0)
add_donor(cache / "4550424ff074a6ab50fd/decoded-static.json", "Byzantine Mercenary Barracks Age II", 15)
bpy.ops.file.pack_all()
target = ROOT / "art/building_remix_0_3_0/reference/market_stock_donors.blend"
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists():
    raise FileExistsError(target)
bpy.ops.wm.save_as_mainfile(filepath=str(target))
print("REFERENCE_SAVED", target)
