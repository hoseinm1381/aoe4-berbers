"""Read-only geometry checks on the saved iteration after visual review repairs."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tribal_tent/iteration001'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/tribal_tent/iterations/001/Berber_Tribal_Tent_Ages_I_IV_001.blend'))
def tree(obj):return BVHTree.FromPolygons([v.co for v in obj.data.vertices],[list(p.vertices) for p in obj.data.polygons])
report={'status':'passed','native_acceptance':'not tested','ages':[]}
for age in range(1,5):
    objects=[o for o in bpy.data.collections[f'BER_Tent001_Age_{age}'].objects if o.type=='MESH'];canopy=next(o for o in objects if o.name.endswith('Tensioned_panel_canopy'));bvh=tree(canopy);overlap=[];anchors=[]
    for o in objects:
        if 'Eave_upright' in o.name:
            xs=[v.co.x for v in o.data.vertices];ys=[v.co.y for v in o.data.vertices];x=(max(xs)+min(xs))/2;y=(max(ys)+min(ys))/2
            hit=bvh.ray_cast(Vector((x,y,-.2)),Vector((0,0,1)),8)[0];assert hit is not None
            value=max(v.co.z for v in o.data.vertices)-hit.z;assert .002<value<.006,(age,value);overlap.append(value)
        if 'Guyline_' in o.name:
            point=sum((v.co for v in list(o.data.vertices)[:8]),Vector())/8;d=bvh.find_nearest(point)[3];assert d<1e-5;anchors.append(d)
    jars=[o for o in objects if 'Water_storage_' in o.name];gaps=[]
    for i,a in enumerate(jars):
        for b in jars[i+1:]:
            def disc(o):
                xs=[v.co.x for v in o.data.vertices];ys=[v.co.y for v in o.data.vertices];return Vector(((max(xs)+min(xs))/2,(max(ys)+min(ys))/2,0)),(max(xs)-min(xs))/2
            ca,ra=disc(a);cb,rb=disc(b);gap=(ca-cb).length-ra-rb;assert gap>.07,(age,gap);gaps.append(gap)
    report['ages'].append({'age':age,'actual_eave_roof_overlap_m':overlap,'actual_rope_anchor_distance_m':anchors,'minimum_vessel_gap_m':min(gaps) if gaps else None})
objects=list(bpy.data.collections['BER_Tent001_Age_4'].objects);shoulders={s:tree(next(o for o in objects if o.name.endswith(f'Embroidered_shoulder_{s}'))) for s in (-1,1)};clearances=[]
for o in objects:
    if 'Brocade_lozenge' in o.name:
        for v in o.data.vertices:
            s=1 if v.co.x>0 else -1;hit=shoulders[s].ray_cast(Vector((v.co.x,v.co.y,5)),Vector((0,0,-1)),8)[0];assert hit is not None;delta=v.co.z-hit.z;assert delta>.004,(o.name,delta);clearances.append(delta)
report['roof_motif_min_clearance_m']=min(clearances)
(OUT/'saved-source-verification.json').write_text(json.dumps(report,indent=2));print('SAVED_SOURCE_GEOMETRY_VERIFIED',flush=True)
bpy.ops.wm.quit_blender()
