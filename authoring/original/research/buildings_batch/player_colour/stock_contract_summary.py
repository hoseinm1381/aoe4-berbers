import json,re
from pathlib import Path
d=json.loads(Path(__file__).with_name('stock-material.json').read_text())
out=[]
for m in d['materials']:
 out.append({'name':m['name'],'class':m.get('class'),'blocks':[{'name':b['name'],'params':[p for p in b.get('parameters',[]) if re.search('player|colour|color|team|pattern',p['name'],re.I)],'textures':[{'name':t['name'],'logical_path':t.get('logical_path')} for t in b.get('textures',[]) if re.search('player|colour|color|team|pattern',t['name'],re.I)]} for b in m.get('blocks',[])]})
Path(__file__).with_name('stock-owner-contract.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))
