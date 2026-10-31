"""Shield-only correction on a copy of refined.1; retain grip, UVs and all other art."""
import bpy,bmesh,sys,os,json,hashlib,shutil
from datetime import datetime,timezone
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tuareg_lowprofile_shield_trial';ART=ROOT/'art/tuareg_lowprofile_shield'
OUT.mkdir(exist_ok=True);ART.mkdir(exist_ok=True)
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison.asset_authoring import _ActiveUvOnly
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/tuareg_refined/Tuareg_Refined_Ages_I_IV.blend'))
shield=bpy.data.objects['tuareg_agher_refined'];assert len(shield.data.vertices)==762
before=[v.co.copy() for v in shield.data.vertices]
# Recipe ordering: shell 306; edge 416; four-ring grip 32; motifs 8.
# Keep the two central grip rings, refit both end mounts with the shield shell.
grip=set(range(730,746))
for v in shield.data.vertices:
    if v.index in grip:continue
    z=v.co.z
    v.co.z=z*.22 if z>0 else z*1.18
    # The crown is short/narrow while lower body stays broad.
    if z>-.15:v.co.x=.04+(v.co.x-.04)*.78
assert all((shield.data.vertices[i].co-before[i]).length<1e-7 for i in grip)
body=shield.data.vertices[:306];top=max(v.co.z for v in body);bottom=min(v.co.z for v in body)
assert top<.045 and bottom<-1.14
bm=bmesh.new();bm.from_mesh(shield.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(shield.data);bm.free();shield.data.update()
shield['shield_profile']='short crown; elongated lower coverage';shield.name='tuareg_agher_lowprofile'
for o in bpy.context.selected_objects:o.select_set(False)
shield.select_set(True);bpy.context.view_layer.objects.active=shield
saved=shield.matrix_basis.copy();shield.matrix_basis=Matrix.Identity(4)
fbx=ART/'lowprofile_shield.fbx'
with _ActiveUvOnly([shield]):
    assert bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='AUTO',axis_forward='-Z',axis_up='Y',apply_unit_scale=True,use_space_transform=True)=={'FINISHED'}
shield.matrix_basis=saved
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Tuareg_Lowprofile_Shield_Ages_I_IV.blend'))
request=json.loads((ROOT/'art/tuareg_refined/garrison_library/Assets/Custom/tuareg/tuareg_agher_refined/.garrison/requests/20261011T161904Z-63e20c.json').read_text())
oldroot=Path(request['asset_root']);newroot=Path('E:/tsh3/Assets/Custom/tuareg/tuareg_agher_lowprofile')
shutil.copytree(oldroot/'source',newroot/'source',dirs_exist_ok=True);shutil.copy2(fbx,newroot/'source/model.fbx')
request['asset_id']='tuareg_agher_lowprofile'
for m in request['materials']:m['usage']['objects']=['tuareg_agher_lowprofile']
request.update(build_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-low3',asset_root=str(newroot));request['source']['fbx']=str(newroot/'source/model.fbx')
for material in request['materials']:
    for role,path in material['textures'].items():material['textures'][role]=str(newroot/Path(path).relative_to(oldroot))
(OUT/'prepare-request.json').write_text(json.dumps(request,indent=2))
report={'status':'source passed','shield_profile':'short crown; elongated lower body','local_top_m':top,'local_bottom_m':bottom,'below_grip_fraction':-bottom/(top-bottom),'grip_vertices_unchanged':16,'new_resource':'art/scenario/tuareg/tuareg_agher_lowprofile/tuareg_agher_lowprofile','fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'source':str(ART/'Tuareg_Lowprofile_Shield_Ages_I_IV.blend'),'native_fit':'pending user'}
(OUT/'source-check.json').write_text(json.dumps(report,indent=2));print('LOWER_SHIELD_SOURCE_READY',flush=True)
