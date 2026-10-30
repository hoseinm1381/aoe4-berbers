"""Installed Garrison SDK and lossless editable native tables (Python 3.13)."""
import base64,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXT=Path(os.environ.get('GARRISON_EXTENSION',Path.home()/'AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'))
sys.path.insert(0,str(EXT))
from garrison_shared import rgd,stock_game,mod_bundle
def read_json(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write_json(p,doc):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def import_table(data):
    if data['schema'] not in ('garrison.native-table/v1','berbers.native-table/v1'):raise ValueError('Unsupported table schema')
    def node(n):
        value=[node(c) for c in n['value']] if n['kind'] in ('List','List2') else n['value']
        if n['key'] is not None and rgd.dictionary_hash(n['key'])!=n['hash']:raise ValueError('Native key/hash mismatch: '+n['key'])
        return rgd.Node(n['hash'],n['kind'],value,n['key'])
    d=rgd.Rgd(data['version'],data['platform'],[rgd.Chunk(bytes.fromhex(c['kind']),bytes.fromhex(c['id']),c['version'],bytes.fromhex(c['name']),base64.b64decode(c['body'])) for c in data['chunks']], [node(n) for n in data['nodes']], [tuple(k) for k in data['keys']])
    return rgd.write(d)
def export_table(raw):
    d=rgd.read(raw)
    def node(n):return {'key':n.key,'hash':n.hash,'kind':n.kind,'value':[node(c) for c in n.value] if isinstance(n.value,list) else n.value}
    return {'schema':'garrison.native-table/v1','version':d.version,'platform':d.platform,
      'chunks':[{'kind':c.kind.hex(),'id':c.id.hex(),'version':c.version,'name':c.name.hex(),'body':base64.b64encode(c.body if c.id not in (b'AEGD',b'KEYS') else b'').decode('ascii')} for c in d.chunks],
      'keys':d.keys,'nodes':[node(n) for n in d.nodes]}
def child(parent,key):
    values=parent.nodes if hasattr(parent,'nodes') else parent.value
    return next(n for n in values if n.key==key or (n.key is None and n.hash==rgd.dictionary_hash(key)))
def at(parent,path):
    for part in path.split('/'):parent=child(parent,part)
    return parent
def refs(nodes,path=''):
    for n in nodes:
        if isinstance(n.value,list):
            fields={c.key:c for c in n.value}
            if '$PBGNAME' in fields:
                yield path+'/'+str(n.key),fields.get('$PBGMAP').value.replace('\\','/') if fields.get('$PBGMAP') else '',fields['$PBGNAME'].value,n
            yield from refs(n.value,path+'/'+str(n.key))

