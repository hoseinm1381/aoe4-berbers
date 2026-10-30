"""Per-atlas native RRMaterial edits preserving all other shader fields and LODs."""
from __future__ import annotations
import struct
import sys
from berber_050_common import EXT
sys.path.insert(0, str(EXT))
from garrison_shared import model_variants as mv
rc = mv.rc


def canonical(path):
    return path.replace('\\', '/').lower()


def texture_pairs(payload):
    count = struct.unpack_from('<I', payload)[0]
    cursor = 4
    pairs = []
    for _ in range(count):
        values = []
        for _ in range(2):
            size = struct.unpack_from('<I', payload, cursor)[0]
            cursor += 4
            value = payload[cursor:cursor + size]
            if len(value) != size:
                raise ValueError('Truncated native material texture string')
            values.append(value.decode('utf8'))
            cursor += size
        pairs.append(tuple(values))
    if cursor != len(payload):
        raise ValueError('Unknown trailing native material texture bytes')
    return pairs


def pack_pairs(pairs):
    data = bytearray(struct.pack('<I', len(pairs)))
    for pair in pairs:
        for value in pair:
            encoded = value.encode('utf8')
            data.extend(struct.pack('<I', len(encoded)))
            data.extend(encoded)
    return bytes(data)


def inventory(data):
    return [(chunk.offset, texture_pairs(chunk.payload)) for chunk in rc.walk(rc.parse(data).roots)
            if chunk.kind == b'DATA' and chunk.tag == b'PbTe']


def remap_albedos(data, mappings):
    mappings = {canonical(k): v for k, v in mappings.items()}
    found = set()
    doc = rc.parse(data)
    changes = {}
    touched_slots = 0
    for chunk in rc.walk(doc.roots):
        if chunk.kind != b'DATA' or chunk.tag != b'PbTe':
            continue
        pairs = texture_pairs(chunk.payload)
        updated = []
        for slot, value in pairs:
            key = canonical(value)
            if slot == 'albedoTexture' and key in mappings:
                found.add(key)
                value = mappings[key]
                touched_slots += 1
            updated.append((slot, value))
        changes[chunk.offset] = pack_pairs(updated)
    if found != set(mappings):
        raise ValueError(f'Per-atlas albedo mappings not found in native material: {sorted(set(mappings)-found)}')
    result = rc.rebuild(doc, lambda chunk: changes.get(chunk.offset))
    before = list(rc.walk(doc.roots))
    after = list(rc.walk(rc.parse(result).roots))
    if len(before) != len(after):
        raise ValueError('Native material chunk topology changed')
    for left, right in zip(before, after):
        if (left.kind, left.tag, left.name, left.version) != (right.kind, right.tag, right.name, right.version):
            raise ValueError('Native material chunk identity changed')
        if not left.children and left.offset not in changes and left.payload != right.payload:
            raise ValueError('Nontexture native material data changed')
        if left.offset in changes:
            expected = [(slot, mappings.get(canonical(value), value) if slot == 'albedoTexture' else value)
                        for slot, value in texture_pairs(left.payload)]
            if texture_pairs(right.payload) != expected:
                raise ValueError('Native texture slots changed outside selected albedo paths')
    return result, {'native_texture_tables': len(changes), 'changed_albedo_slots': touched_slots,
                    'distinct_authored_atlases': len(found), 'all_other_native_bytes_and_slots_preserved': True}
