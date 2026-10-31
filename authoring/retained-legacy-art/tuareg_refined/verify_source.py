"""Read-only saved-source checks, independent of native cooking/acceptance."""
import bpy,sys,os,json,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/tuareg_refined';WORK=ROOT/'output/tuareg_refined_trial'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison import unit_animation as anim,unit_export
bpy.ops.wm.open_mainfile(filepath=str(ART/'Tuareg_Refined_Ages_I_IV.blend'))
rows=[]
for age in range(1,5):
    rig=bpy.data.objects[f'Refined_Age_{age}_NativeRig'];body=bpy.data.objects[f'Tuareg_Refined_Age_{age}']
    records=unit_export.skeleton_records(rig);assert len(records)==48 and len(rig.data.bones)==48
    assert len(body.data.materials)==1 and body.data.uv_layers.active.name=='TuaregAtlas'
    weights=[sum(g.weight for g in v.groups) for v in body.data.vertices];assert max(abs(w-1) for w in weights)<1e-4
    assert max(len(v.groups) for v in body.data.vertices)<=4
    for role in ['albedo','normal','roughness','metalness','pattern']:
        path=ART/f'exports/tuareg_age{age}/{role}.png';assert path.exists()
        im=bpy.data.images.load(str(path),check_existing=True);assert tuple(im.size)==(1024,1024)
    pattern=bpy.data.images.load(str(ART/f'exports/tuareg_age{age}/pattern.png'),check_existing=True)
    px=list(pattern.pixels);red=px[0::4];assert max(red)>.9 and sum(v>.5 for v in red)/len(red)<.20
    assert max(px[1::4])<.01 and max(px[2::4])<.01
    for index in (143,131,119,88,219,117):
        clip=json.loads((WORK/f'clips/clip{index}.json').read_text());target,action=anim.import_clip_action(rig,clip,root_motion=False)
        for frame in (1,clip['frame_count']//2,clip['frame_count']):
            bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
            assert all(math.isfinite(c) for v in mesh.vertices for c in v.co);ev.to_mesh_clear()
    rows.append({'age':age,'bones':48,'max_influences':max(len(v.groups) for v in body.data.vertices),'max_weight_sum_error':max(abs(w-1) for w in weights),'atlas':1024,'owner_mask_fraction':sum(v>.5 for v in red)/len(red),'motion_samples_checked':18})
spear=bpy.data.objects['tuareg_long_spear_refined'];zs=[v.co.z for v in spear.data.vertices];assert abs(max(zs)-min(zs)-4.375)<1e-5 and abs(min(zs)+1.02)<1e-5
fit=json.loads((WORK/'shield-fit.json').read_text());assert fit['maximum_target_violation_m']<=.005 and fit['additional_offset']==[0,0,0]
report={'status':'passed','ages':rows,'spear_length_m':max(zs)-min(zs),'spear_butt_unchanged':True,'shield_fit_samples':fit['samples'],'native_acceptance':'pending'}
(WORK/'source-validation.json').write_text(json.dumps(report,indent=2));print('SOURCE_VALIDATION_PASS',json.dumps(report),flush=True)
