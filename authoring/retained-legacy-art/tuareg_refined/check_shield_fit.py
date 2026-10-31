"""Measure native idle/walk/guard shield bounds and fit a fixed grip-relative surface offset."""
import bpy,sys,os,json,math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/tuareg_refined';WORK=ROOT/'output/tuareg_refined_trial'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison import unit_animation as anim
bpy.ops.wm.open_mainfile(filepath=str(ART/'Tuareg_Refined_Ages_I_IV.blend'))
rig=bpy.data.objects['Refined_Age_1_NativeRig'];shield=bpy.data.objects['tuareg_agher_refined']
initial=json.loads((WORK/'art-source-checks.json').read_text())['shield']['face_offset'];points=[v.co.copy() for v in list(shield.data.vertices)[:306]]
C=Matrix(anim.BONE_AXES).inverted()@Matrix(anim.COOKED_TO_BLENDER).inverted();rows=[]
for index in (143,131,130,119,88):
    clip=json.loads((WORK/f'clips/clip{index}.json').read_text());target,action=anim.import_clip_action(rig,clip,root_motion=False)
    for frame in sorted(set([1,clip['frame_count'],*range(1,clip['frame_count']+1,max(1,clip['frame_count']//12))])):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();M=rig.matrix_world@rig.pose.bones['metarig_larmpalmsocket'].matrix@C
        heights=[(M@p).z for p in points];head=(rig.matrix_world@rig.pose.bones['metarig_head'].matrix).translation.z
        rows.append({'clip':clip['name'],'frame':frame,'top':max(heights),'bottom':min(heights),'head_pivot':head,'row':list(M[2])[:3],
                     'limit':head+(.005 if index in (131,130,119) else -.04)})
def penalty(delta):
    violations=[]
    for r in rows:
        move=sum(a*b for a,b in zip(r['row'],delta));violations.extend([max(0,r['top']+move-r['limit']),max(0,.035-r['bottom']-move)])
    return max(violations),sum(v*v for v in violations)
best=((0,0,0),penalty((0,0,0)))
if best[1][0]>.005:
    for ix in range(-25,26):
        for iz in range(-30,21):
            delta=(ix*.01,0,iz*.01);p=penalty(delta)
            if (p[0],p[1],sum(d*d for d in delta))<(best[1][0],best[1][1],sum(d*d for d in best[0])):best=(delta,p)
offset=[a+b for a,b in zip(initial,best[0])]
for r in rows:
    move=sum(a*b for a,b in zip(r['row'],best[0]));r['fitted_top']=r['top']+move;r['fitted_bottom']=r['bottom']+move
result={'schema':'tuareg-shield-fit/v1','current_offset':initial,'recommended_offset':offset,'additional_offset':list(best[0]),'maximum_target_violation_m':best[1][0],
        'samples':len(rows),'observations':rows,'grip':'native origin unchanged; face and supports refitted','height_m':1.15,'native_runtime':'pending'}
(WORK/'shield-fit.json').write_text(json.dumps(result,indent=2));print('SHIELD_FIT',json.dumps({k:v for k,v in result.items() if k!='observations'}),flush=True)
