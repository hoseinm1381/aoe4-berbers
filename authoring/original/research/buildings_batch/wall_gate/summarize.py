import json
from pathlib import Path
Q=Path(__file__).parent
for p in (Q/'stock').glob('*/decoded-static.json'):
 d=json.loads(p.read_text());print(p, list(d),list(d.get('model',{})))
 if 'smallgate' not in str(d.get('source',d)):continue
 (Q/'donor_keys.json').write_text(json.dumps({k:v for k,v in d.items() if k not in ['geometry','materials']},indent=2))
 print('geometry',[(g['name'],len(g['positions'])) for g in d['geometry']['groups']])
