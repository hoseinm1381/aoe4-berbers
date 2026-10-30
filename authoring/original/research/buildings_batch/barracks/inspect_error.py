import ast
from pathlib import Path
s=Path('output/buildings_batch/barracks/BUILD_ERROR.txt').read_text();r=ast.literal_eval(s.split('AssertionError: ',1)[1]);print([x for x in r if x.get('non_manifold',0) or x.get('degenerate_faces',0) or x.get('uv_zero_area_faces',0)])
