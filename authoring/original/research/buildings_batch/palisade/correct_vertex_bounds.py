from pathlib import Path
q=Path('research/buildings_batch/palisade')
for f in ['audit_saved.py','audit_age1.py']:
 p=q/f;s=p.read_text().replace('ob.matrix_world@Vector(v) for v in ob.bound_box','ob.matrix_world@v.co for v in ob.data.vertices');p.write_text(s)
