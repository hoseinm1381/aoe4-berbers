from pathlib import Path
import struct,json
P=Path(__file__).parent
b=(P/'layout_docks.rgm').read_bytes()
# The file is Relic Chunky v4. Inventory candidate chunk identifiers without interpreting transforms.
ids=[]
for i in range(len(b)-8):
 if b[i:i+4] in [b'DATA',b'FOLD'] and all(65<=x<=90 for x in b[i+4:i+8]):
  ids.append({'offset':i,'id':b[i:i+8].decode(),'next_uint32':list(struct.unpack_from('<4I',b,i+8)) if i+24<=len(b) else []})
(P/'layout_chunk_inventory.json').write_text(json.dumps(ids,indent=2));print(json.dumps(ids,indent=2)[:5000])
