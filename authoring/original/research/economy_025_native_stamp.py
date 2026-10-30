"""Read-only reflected native tree inspection; no native resource mutation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

EXT = Path(os.environ["APPDATA"]) / "Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison"
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "art/economy_remix_0_2_5"

class NativeTree:
    def __init__(self, path):
        self.path = Path(path)
        self.document = relic_chunky.load(self.path)
        self.chunks = {x.tag: x for x in self.document.roots}
        self.types = {int(x.get("Id")): x for x in ET.parse(WORK / "reflect.db").getroot()}
        self.objects = {}
        objects = self.chunks[b"ROBJ"].payload
        count = struct.unpack_from("<Q", objects)[0]
        assert len(objects) == 8 + 36 * count
        self.memory = self.chunks[b"RFCI"]
        self.strings = {}
        strings = self.chunks[b"RSHI"].payload
        count_strings = struct.unpack_from("<Q", strings)[0]
        cursor = 8
        for _ in range(count_strings):
            key, length = struct.unpack_from("<QI", strings, cursor)
            cursor += 12
            self.strings[key] = strings[cursor:cursor+length].decode("utf-8")
            cursor += length
        assert cursor == len(strings)
        for index in range(count):
            oid, tid, offset, owner, checksum = struct.unpack_from("<QQQQI", objects, 8 + 36 * index)
            kind = self.types.get(tid)
            if kind is None:
                raise ValueError(f"Unresolved reflected type {tid} at {offset}")
            assert checksum == int(kind.get("Checksum")), kind.attrib
            relative = offset - self.memory.payload_offset
            assert relative >= 0 and relative + int(kind.get("Size")) <= len(self.memory.payload)
            fields = {x.get("Name"): x for x in kind.findall("Fields/ReflectField")}
            id_field = fields.get("m_objectID")
            # Reference wrappers have an m_objectID containing the referenced
            # target, rather than the wrapper's serialization identity.
            if id_field is not None and id_field.get("DeclaringType", "").startswith("util::ReflectObject<"):
                assert self.u64(offset + int(id_field.get("Offset"))) == oid, (
                    index, kind.get("Name"), offset, oid,
                    self.u64(offset + int(id_field.get("Offset"))))
            self.objects[oid] = {"id": oid, "type_id": tid, "type": kind.get("Name"),
                                 "offset": offset, "owner": owner, "fields": fields}
        self.by_offset = {x["offset"]: x for x in self.objects.values()}

    def bytes(self, address, size):
        relative = address - self.memory.payload_offset
        assert 0 <= relative and relative + size <= len(self.memory.payload), (address, size)
        return self.memory.payload[relative:relative+size]

    def u64(self, address):
        return struct.unpack("<Q", self.bytes(address, 8))[0]

    def field(self, obj, field):
        address = obj["offset"] + int(field.get("Offset"))
        kind = field.get("FieldTypeName")
        if kind == "Reflect::ReflectStringHash":
            key = self.u64(address)
            return {"hash": key, "text": self.strings.get(key)}
        if kind.startswith("FamilyManagerEnum<"):
            key = self.u64(address)
            return {"hash": key, "text": self.strings.get(key), "enum_type": kind}
        if kind == "util::ReflectString<StdTraits>":
            displacement, count = struct.unpack("<qQ", self.bytes(address, 16))
            text = self.bytes(address + displacement, count).decode("utf-8") if count else ""
            return {"text": text}
        if kind in ("uint64_t", "int64_t"):
            return self.u64(address)
        if kind == "bool":
            return bool(self.bytes(address, 1)[0])
        if kind == "float":
            return struct.unpack("<f", self.bytes(address, 4))[0]
        if kind.startswith("util::ReflectObjectRef<"):
            reference_type = self.types[int(field.get("FieldTypeId"))]
            identity = reference_type.find('Fields/ReflectField[@Name="m_objectID"]')
            assert identity is not None, kind
            return {"object_ref": self.u64(address + int(identity.get("Offset")))}
        if kind.startswith("util::ReflectArray<"):
            displacement, count, capacity = struct.unpack("<qII", self.bytes(address, 16))
            return {"data_address": address + displacement if displacement else 0,
                    "count": count, "capacity": capacity, "element_type": kind}
        if int(field.get("BaseSize")) == 8:
            displacement = struct.unpack("<q", self.bytes(address, 8))[0]
            target = self.by_offset.get(address + displacement) if displacement else None
            return {"relative_pointer": displacement,
                    "target_id": target["id"] if target else None,
                    "target_type": target["type"] if target else None,
                    "raw_u64": self.u64(address)}
        return {"type": kind, "raw": self.bytes(address, int(field.get("BaseSize"))).hex()}

    def describe(self, obj):
        return {k: v for k, v in obj.items() if k != "fields"} | {
            "fields": {name: self.field(obj, field) for name, field in obj["fields"].items()}}

    def selected(self):
        hits = []
        for obj in self.objects.values():
            name_field = obj["fields"].get("m_name")
            if name_field is not None and name_field.get("FieldTypeName") == "Reflect::ReflectStringHash":
                name = self.field(obj, name_field)["text"] or ""
                if "spearman_defensive" in name or "spearman_shield_wall" in name:
                    hits.append(obj)
        selected = {x["id"] for x in hits}
        for _ in range(12):
            added = {x["id"] for x in self.objects.values() if x["owner"] in selected}
            if added <= selected:
                break
            selected |= added
        return hits, [self.describe(self.objects[x]) for x in selected]

def clone_id(tree, oid):
    return int.from_bytes(hashlib.sha256(('berber_economy_025:'+hashlib.sha256(tree.path.read_bytes()).hexdigest()+':'+str(oid)).encode()).digest()[:8],'little')

def decompile(tree, mapping, private_ids=True):
    """Emit stock stamp RDO; every field is schema-derived, never a new layout."""
    warehouse = ET.Element('DataWarehouse')
    emitted = set()
    scalar = {'float': ('Float','<f'), 'bool': ('Bool','<?'),
              'uint64_t': ('UInt64','<Q'), 'int64_t': ('Int64','<q'),
              'uint32_t': ('UInt32','<I'), 'uint8_t': ('UInt8','<B')}
    identity=lambda oid:clone_id(tree,oid) if private_ids else oid
    def nested(prop, obj):
        ET.SubElement(prop,'DataValue',Name=obj['type']).text=str(identity(obj['id']))
        emit(prop,obj)
    def emit(parent,obj):
        assert obj['id'] not in emitted
        emitted.add(obj['id'])
        attrs={'Name':'','Type':obj['type'],'Id':str(identity(obj['id']))}
        if obj['owner']: attrs['OwnerId']=str(identity(obj['owner']))
        node=ET.SubElement(parent,'DataObject',attrs)
        typ=tree.types[obj['type_id']]
        bases=''.join(tree.types[int(b.get('Id'))].get('Name')+'#'+b.get('Offset')+'|' for b in typ.findall('BaseTypes/BaseType'))
        if bases: ET.SubElement(node,'DataProperty',Name='#BaseTypes',Type='String',Value=bases)
        for name,field in obj['fields'].items():
            address=obj['offset']+int(field.get('Offset'));kind=field.get('FieldTypeName')
            if kind in scalar:
                label,fmt=scalar[kind];v=struct.unpack(fmt,tree.bytes(address,struct.calcsize(fmt)))[0]
                if name=='m_objectID':v=identity(v)
                ET.SubElement(node,'DataProperty',Name=name,Type=label,Value=str(v).lower() if isinstance(v,bool) else str(v))
            elif kind=='util::ReflectString<StdTraits>' or kind=='Reflect::ReflectStringHash':
                v=tree.field(obj,field)['text'];assert v is not None
                if name=='m_blueprint':v=mapping.get(v.replace('\\','/'),v).replace('/','\\')
                ET.SubElement(node,'DataProperty',Name=name,Type='String',Value=v)
            elif kind.startswith('util::ReflectArray<'):
                prop=ET.SubElement(node,'DataProperty',Name=name,Type='Object');v=tree.field(obj,field)
                assert kind=='util::ReflectArray<IStampBlueprint *,StdTraits>'
                for i in range(v['count']):
                    slot=v['data_address']+i*8;relative=struct.unpack('<q',tree.bytes(slot,8))[0]
                    targets=[o for o in tree.objects.values() if o['offset']==slot+relative and o['type'].endswith('StampBlueprint')]
                    assert len(targets)==1;nested(prop,targets[0])
            else:
                prop=ET.SubElement(node,'DataProperty',Name=name,Type='Object')
                targets=[o for o in tree.objects.values() if o['offset']==address and o['type']==kind and o['owner']==obj['id']]
                if targets:
                    assert len(targets)==1;nested(prop,targets[0])
                else:
                    # Inline native enums lack object records. Raw serialization preserves
                    # Terrain/Surface alignment instead of silently taking defaults.
                    typ2=tree.types[int(field.get('FieldTypeId'))]
                    assert int(typ2.get('Size'))==int(field.get('BaseSize'))
                    assert all(int(f.get('BaseSize'))==0 for f in typ2.findall('Fields/ReflectField')),kind
                    oid=int.from_bytes(hashlib.sha256(f"{identity(obj['id'])}:{name}".encode()).digest()[:8],'little')
                    raw=tree.bytes(address,int(typ2.get('Size')))
                    assert len(raw) in (1,2,4,8),(kind,len(raw))
                    enum_value=int.from_bytes(raw,'little')
                    enum_mask=(1<<(8*len(raw)))-1
                    names=[f.get('Name') for f in typ2.findall('Fields/ReflectField') if int(f.get('EnumValue'))&enum_mask==enum_value]
                    assert len(names)==1,(kind,raw)
                    prop.set('Type','String');prop.set('Value',names[0])
    roots=[o for o in tree.objects.values() if not o['owner']]
    assert len(roots)==1 and roots[0]['type']=='StampBlueprint'
    emit(warehouse,roots[0]);assert emitted==set(tree.objects)
    ET.indent(warehouse,space='  ')
    return ET.tostring(warehouse,encoding='utf-8')

