import json
from pathlib import Path
p=next(Path(__file__).parent.glob('stock-house/*/decoded-static.json'))
d=json.loads(p.read_text()); print(d.keys())
for k,v in d.items():
 if 'material' in k:
  Path(__file__).with_name('stock-material.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
  print(k,str(v)[:18000])
