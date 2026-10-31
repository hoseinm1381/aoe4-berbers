from pathlib import Path
import json
p=Path('output/buildings_batch/mining')
for age in range(1,5):
 d=json.loads((p/f'age{age}_validation.json').read_text());lo,hi=d['geometry_bounds'];assert min(lo[:2])>=-2-1e-5 and max(hi[:2])<=2+1e-5 and abs(lo[2])<1e-5;d['footprint_fit']={'ground_z':lo[2],'native_xy':[4,4],'source_bounds':d['geometry_bounds'],'pass':True};(p/f'age{age}_validation.json').write_text(json.dumps(d,indent=2))
 print(age,len(d['objects']),sum(o['triangles'] for o in d['objects']),min(o['minimum_uv_triangle_area'] for o in d['objects']))
