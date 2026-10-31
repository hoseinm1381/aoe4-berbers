"""Blender geometry regression: trouser vertices must clear closed skirt sides."""
import bpy,ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/tuareg_overhaul/Tuareg_Original_Ages_I_IV.blend'))
rows=[]
for age in range(1,5):
    obj=bpy.data.objects[f'Tuareg_Age_{age}_NewSkin'];parts=ast.literal_eval(obj['tuareg_recipe_parts']);offset=0;trousers=[];panels=[]
    for part in parts:
        points=[v.co.copy() for v in obj.data.vertices[offset:offset+part['vertices']]]
        if part['part'].startswith('loose woven trousers'):trousers.extend(points)
        if part['part']=='split desert hem':panels.append(points)
        offset+=part['vertices']
    assert len(panels)==2 and trousers
    # The outer side face is planar in X/Z. Test actual stored mesh points against it.
    top=max(abs(p[1].x) for p in panels);bottom=max(abs(p[2].x) for p in panels)
    ztop=panels[0][1].z;zbottom=panels[0][2].z
    gaps=[top+(bottom-top)*(ztop-v.z)/(ztop-zbottom)-abs(v.x) for v in trousers if zbottom+.01<v.z<ztop-.01]
    row={'age':age,'minimum_lateral_clearance_m':min(gaps),'vertices_outside_side':sum(g<0 for g in gaps)};rows.append(row)
out=ROOT/'output/tuareg_art_guard_trial/clothing-clearance.json';out.write_text(json.dumps(rows,indent=2))
assert all(r['vertices_outside_side']==0 and r['minimum_lateral_clearance_m']>.003 for r in rows),rows
print('CLOTHING_CLEARANCE_PASS',rows,flush=True)
