from pathlib import Path
import re,json,hashlib
O=Path(__file__).parent
d={}
for name in ['layout_docks.rgo','layout_docks.rgm']:
 b=(O/name).read_bytes();strings=[s.decode('ascii') for s in re.findall(rb'[\x20-\x7e]{4,}',b)]
 d[name]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'header_hex':b[:32].hex(),'observed_ascii_strings':strings,'transform_decode':'not qualified; string evidence only, preserve bytes'}
(O/'layout_bytes_evidence.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2)[:6000])
g=json.loads(next((O/'piers_stock').rglob('decoded-static.json')).read_text())['geometry']['groups']
summary=[]
for x in g:
 p=x['positions'];summary.append({'group':x['name'],'vertices':len(p),'bounds':[[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]})
(O/'pier_donor_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
