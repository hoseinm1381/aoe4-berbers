"""Installed Garrison SDK and lossless, typed native-table JSON support."""
import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT = Path(os.environ.get('GARRISON_EXTENSION', Path.home() / 'AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'))
sys.path.insert(0, str(EXT))
from garrison_shared import rgd, stock_game, mod_bundle


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def export_table(raw):
    doc = rgd.read(raw)
    def node(n):
        return {'key': n.key, 'hash': n.hash, 'kind': n.kind,
                'value': [node(c) for c in n.value] if isinstance(n.value, list) else n.value}
    return {'schema': 'berbers.native-table/v1', 'version': doc.version, 'platform': doc.platform,
            'chunks': [{'kind': c.kind.hex(), 'id': c.id.hex(), 'version': c.version,
                        'name': c.name.hex(), 'body': base64.b64encode(c.body if c.id not in (b'AEGD', b'KEYS') else b'').decode('ascii')}
                       for c in doc.chunks],
            'keys': doc.keys, 'nodes': [node(n) for n in doc.nodes]}


def import_table(data):
    assert data['schema'] == 'berbers.native-table/v1'
    def node(n):
        value = [node(c) for c in n['value']] if n['kind'] in ('List', 'List2') else n['value']
        if n['key'] is not None:
            assert rgd.dictionary_hash(n['key']) == n['hash'], n['key']
        return rgd.Node(n['hash'], n['kind'], value, n['key'])
    doc = rgd.Rgd(data['version'], data['platform'],
                  [rgd.Chunk(bytes.fromhex(c['kind']), bytes.fromhex(c['id']), c['version'],
                             bytes.fromhex(c['name']), base64.b64decode(c['body'])) for c in data['chunks']],
                  [node(n) for n in data['nodes']], [tuple(k) for k in data['keys']])
    return rgd.write(doc)
