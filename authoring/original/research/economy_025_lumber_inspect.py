import json
from pathlib import Path
for p in Path('output/berber_update_0_2_5/authors/lumber/stock').glob('*/decoded-static.json'):
 d=json.loads(p.read_text());print(d['request']['logical_path'],[(m['name'],[(t['name'],t.get('texture_name')) for b in m['blocks'] for t in b.get('textures',[]) if 'albedo' in t['name'].lower()]) for m in d['material']['materials'] if not m['name'].endswith('_collection')])
