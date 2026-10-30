import json
from pathlib import Path
O=Path('output/buildings_batch/palisade');rows=[]
for age in range(1,5):
 d=json.loads((O/f'age{age}_validation.json').read_text())
 for name,cs in d['states'].items():
  if name=='corner_90':continue
  j=next(j for j in d['joins'] if j['state']==name);L=j['length']
  base=next(c for c in cs if c['object'].startswith('earth_seat'));ties=[c for c in cs if c['object'].startswith('continuous_rear_tie')]
  for c in [base]+ties:
   b=c['bounds'];gap=(b[0][0]+L)-b[1][0];assert abs(gap)<1e-5
   rows.append({'age':age,'state':name,'component':c['object'],'adjacent_same_length_translation_m':L,'measured_interface_gap_m':gap,'pass':True})
(O/'numeric_join_audit.json').write_text(json.dumps(rows,indent=2));print('join_components',len(rows),'PASS')
