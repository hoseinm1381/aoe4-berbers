"""Use public tagfile metadata to inspect AoE-specific Havok type layouts."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_force_trial"
sys.path.insert(0, str(WORK / "codec_runtime"))
from soulstruct.havok.tagfile.unpacker import TagFileUnpacker
from soulstruct.utilities.binary import BinaryReader
from soulstruct.havok.types import hk2018
source = ROOT / "output/tuareg_shield_test/evidence/source/art/civilizations/common/humans/archetypes/base_spearshield/base_spearshield.rhka"
unpacker = TagFileUnpacker()
reader = BinaryReader(source.read_bytes())
try:
    unpacker.unpack(reader, types_only=True)
finally:
    reader.close()
rows = []
definitions = WORK / "generated-native-types"; definitions.mkdir(exist_ok=True)
for info in unpacker.hk_type_infos[1:]:
    if info.name in info.GENERIC_TYPE_NAMES: continue
    try:
        cls = getattr(hk2018, info.py_name)
        info.check_py_class_match(cls)
        status = "matches"
    except Exception as error:
        status = type(error).__name__ + ": " + str(error)
        module, _ = info.get_new_type_module_and_import(list(vars(hk2018.core)))
        (definitions / (info.py_name + ".py")).write_text(module)
    rows.append({"native_name": info.name, "python_name": info.py_name, "status": status})
(WORK / "native-havok-types.json").write_text(json.dumps(rows, indent=2))
print(json.dumps({"version": unpacker.hk_version, "types": len(rows),
                  "differences": [x for x in rows if x["status"] != "matches"]}, indent=2))
