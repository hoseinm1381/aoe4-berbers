import json
from pathlib import Path
d=json.loads(Path('output/buildings_batch/palisade/bounds_debug.json').read_text());a=dict(d['actual']);b=dict(d['expected'])
for n,v in b.items():
 if n not in a:print('MISSING',n);continue
 delta=[a[n][i][j]-v[i][j] for i in range(2) for j in range(3)]
 if max(abs(x) for x in delta)>1e-5:print(n,'expected',v,'actual',a[n],'delta',delta)
