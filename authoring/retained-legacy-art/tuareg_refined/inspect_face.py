import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/tuareg_refined/Tuareg_Refined_Ages_I_IV.blend'))
mesh=next(o for o in bpy.data.collections['Reference originals - unchanged'].objects if o.type=='MESH' and 'abb_infantry_light_age02' in o.name and 'lod1' in o.name)
ids={g.index:g.name for g in mesh.vertex_groups};points=[]
for v in mesh.data.vertices:
    if any('head' in ids[g.group] and g.weight>.5 for g in v.groups) and v.co.y<-.10:
        points.append({'id':v.index,'xyz':list(v.co)})
(ROOT/'output/tuareg_refined_trial/face-reference-points.json').write_text(json.dumps(points,indent=2))
print(json.dumps(sorted(points,key=lambda p:p['xyz'][2])),flush=True)
