"""Encode private native stamps without reconstructing opaque terrain splines.

New ReflectStringHash identities come exclusively from a fresh native key cook.
All original object layout, arrays and runtime machinery are retained verbatim.
"""
import hashlib,struct
from economy_025_native_stamp import NativeTree,clone_id
from garrison_shared import relic_chunky as rc

def rebind(tree,mapping,key_table):
 doc=tree.document;memory=bytearray(tree.chunks[b'RFCI'].payload);objects=bytearray(tree.chunks[b'ROBJ'].payload)
 identities={oid:clone_id(tree,oid) for oid in tree.objects};strings=dict(tree.strings);changes=[]
 for i in range(len(tree.objects)):
  oid,tid,offset,owner,checksum=struct.unpack_from('<QQQQI',objects,8+i*36)
  struct.pack_into('<QQQQI',objects,8+i*36,identities[oid],tid,offset,identities[owner] if owner else 0,checksum)
 for oid,o in tree.objects.items():
  for name,f in o['fields'].items():
   at=o['offset']+int(f.get('Offset'))-tree.memory.payload_offset
   if name=='m_objectID':
    value=struct.unpack_from('<Q',memory,at)[0];assert value==oid;struct.pack_into('<Q',memory,at,identities[value])
   if name=='m_blueprint' and f.get('FieldTypeName') in ['Reflect::ReflectStringHash','util::ReflectString<StdTraits>']:
    old=tree.field(o,f)['text'];new=mapping.get(old.replace('\\','/'))
    if new is None:continue
    new=new.replace('/','\\');probe=key_table[new];assert probe['text']==new
    if f.get('FieldTypeName')=='Reflect::ReflectStringHash':
     key=probe['hash']
     if key in strings:assert strings[key]==new
     strings[key]=new;struct.pack_into('<Q',memory,at,key)
    else:
     displacement,count=struct.unpack_from('<qQ',memory,at);value=new.encode('utf8');assert len(value)<=count,(old,new,count)
     start=at+displacement;assert bytes(memory[start:start+count]).decode('utf8')==old
     memory[start:start+count]=value+b'\0'*(count-len(value));struct.pack_into('<Q',memory,at+8,len(value));key=None
    changes.append({'object':oid,'old':old,'new':new,'fresh_native_key':key,'fresh_native_string_type':probe['kind']})
 assert len(changes)==len(mapping)
 payload=bytearray(struct.pack('<Q',len(strings)))
 for key,value in strings.items():
  encoded=value.encode('utf8');payload.extend(struct.pack('<QI',key,len(encoded)));payload.extend(encoded)
 # RSHI follows RFCI in this native schema, so extending it cannot relocate
 # original data/object addresses or any native pointer/array storage.
 assert tree.chunks[b'RSHI'].payload_offset>tree.memory.payload_offset
 creation=bytearray(tree.chunks[b'RNEW'].payload);count=struct.unpack_from('<Q',creation)[0];assert len(creation)==8+29*count
 for i in range(count):
  oid,tid,offset,checksum,flags=struct.unpack_from('<QQQIB',creation,8+29*i);o=tree.objects[oid]
  assert tid==o['type_id'] and offset==o['offset'] and checksum==int(tree.types[tid].get('Checksum'))
  struct.pack_into('<Q',creation,8+29*i,identities[oid])
 for c in doc.roots:
  if c.tag in [b'RFUP',b'RERF']:assert not any(struct.pack('<Q',i) in c.payload for i in tree.objects),(c.tag,'unexpected external object identity')
 edits={tree.chunks[b'ROBJ'].offset:bytes(objects),tree.chunks[b'RNEW'].offset:bytes(creation),tree.chunks[b'RFCI'].offset:bytes(memory),tree.chunks[b'RSHI'].offset:bytes(payload)}
 result=rc.rebuild(doc,lambda c:edits.get(c.offset))
 return result,{'source_sha256':hashlib.sha256(tree.path.read_bytes()).hexdigest(),'encoded_sha256':hashlib.sha256(result).hexdigest(),'route':'Native reflected graph preserved; private IDs and fresh native-cooked string identities rebound','changes':changes}
