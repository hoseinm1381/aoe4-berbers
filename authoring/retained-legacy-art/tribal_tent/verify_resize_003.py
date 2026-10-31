import bpy,json,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tribal_tent/iteration003'
record=json.loads((OUT/'source-validation.json').read_text())
bpy.ops.wm.open_mainfile(filepath=record['blend'])
delta=Matrix.Rotation(math.pi,4,'Z')@Matrix.Diagonal((2.5,2.5,2.5,1))
saved={}
for age in range(1,5):
    col=bpy.data.collections[f'BER_Tent003_Age_{age}']
    for o in col.objects:
        if o.type=='MESH':saved[o.name.replace('BER_Tent003','BER_Tent002')]=([v.co.copy() for v in o.data.vertices],[(u.uv.x,u.uv.y) for u in o.data.uv_layers.active.data],len(o.data.polygons))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/tribal_tent/iterations/002/Berber_Tribal_Tent_Ages_I_IV_002.blend'))
maximum=0
for name,(coords,uv,faces) in saved.items():
    old=bpy.data.objects[name];assert len(coords)==len(old.data.vertices) and faces==len(old.data.polygons)
    assert uv==[(u.uv.x,u.uv.y) for u in old.data.uv_layers.active.data]
    maximum=max(maximum,max((new-delta@v.co).length for new,v in zip(coords,old.data.vertices)))
assert maximum<2e-5
(OUT/'saved-source-verification.json').write_text(json.dumps({'status':'passed','scale':2.5,'rotation_degrees':180,'max_vertex_transform_error_m':maximum,'UVs_and_topology':'unchanged','ages':4,'native_runtime':'pending next requested build'},indent=2))
print('SAVED_TENT_003_TRANSFORM_VERIFIED',maximum,flush=True)
bpy.ops.wm.quit_blender()
