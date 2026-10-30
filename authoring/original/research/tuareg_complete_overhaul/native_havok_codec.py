"""Experimental native Havok adapter using the file's declared type metadata.

No Garrison admission/encoder changes. Native classes are generated from the
current game and the already decoded showcase's metadata in this process only.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "output/tuareg_force_trial"
sys.path.insert(0, str(WORK / "codec_runtime"))
from soulstruct.havok import HKX
from soulstruct.havok.types import hk2018
from soulstruct.havok.tagfile.unpacker import TagFileUnpacker
from soulstruct.utilities.binary import BinaryReader
from soulstruct.havok.tagfile.structs import TagFileItem
from soulstruct.havok.enums import TagDataType
from soulstruct.havok.types import tagfile as tagfile_types

_registered = False
_metadata = []

def register_native_types():
    global _registered
    if _registered: return
    sources = [ROOT / "output/tuareg_shield_test/evidence/source/art/civilizations/common/humans/archetypes/base_spearshield/base_spearshield.rhka",
               ROOT / "output/tuareg_ability_pose_test/showcase-tuning-readback/art/scenario/a4etk_shrek_fitted_v3/a4etk_shrek_fitted_v3.rhka"]
    pending = {}
    for source in sources:
        reader = BinaryReader(source.read_bytes())
        info = TagFileUnpacker()
        try: info.unpack(reader, types_only=True)
        finally: reader.close()
        assert info.hk_version == "20180200"
        for row in info.hk_type_infos[1:]:
            if row.name in row.GENERIC_TYPE_NAMES: continue
            try:
                cls = getattr(hk2018, row.py_name)
                row.check_py_class_match(cls)
            except Exception:
                pending[row.py_name] = row
    for _ in range(8):
        if not pending: break
        progressed = False
        for name, row in list(pending.items()):
            code, _ = row.get_new_type_module_and_import(list(vars(hk2018.core)))
            # Generated relative imports target the SDK module, whereas native
            # types are deliberately registered in memory in this adapter.
            code = re.sub(r"^from \..* import .*\n", "", code, flags=re.MULTILINE)
            namespace = dict(vars(hk2018))
            namespace["__name__"] = __name__
            try: exec(compile(code, str(WORK / "generated-native-types" / (name + ".py")), "exec"), namespace)
            except NameError: continue
            cls = namespace[name]
            row.check_py_class_match(cls)
            setattr(hk2018, name, cls)
            _metadata.append({"native_name": row.name, "python_name": name,
                              "source_declared_size": row.byte_size, "source_declared_alignment": row.alignment})
            del pending[name]; progressed = True
        if not progressed: raise ValueError("Native type dependency unresolved: " + ",".join(pending))
    if pending: raise ValueError("Native type generation incomplete")
    original_item_type = TagFileItem.get_item_hk_data_type
    def native_item_type(item):
        if item.hk_type is hk2018._HavokAnimSet and item.is_ptr and item.length == 1:
            return item.hk_type
        if item.hk_type is not None and item.hk_type.get_tag_data_type() == TagDataType.ConstCharArray:
            return item.hk_type.get_data_type()
        return original_item_type(item)
    TagFileItem.get_item_hk_data_type = native_item_type
    original_string_pack = tagfile_types.pack_string
    class NativeString(str): pass
    def native_string_pack(string_hk_type, item, value, items, queues, is_variant_name=False):
        # The upstream reservation key is the string object's identity. Native
        # bindings reuse the same interned skeleton name in one item.
        return original_string_pack(string_hk_type, item, NativeString(value), items, queues,
                                    is_variant_name=is_variant_name)
    tagfile_types.pack_string = native_string_pack
    _registered = True

def read_native(path):
    register_native_types()
    return HKX.from_path(path)

def type_provenance():
    register_native_types(); return list(_metadata)
