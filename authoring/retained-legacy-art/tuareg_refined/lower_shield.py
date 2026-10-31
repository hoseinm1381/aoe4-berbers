"""Shield-only correction on a copy of refined.1; retain grip, UVs and all other art."""
import bpy,bmesh,sys,os,json,hashlib,shutil
from datetime import datetime,timezone
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tuareg_lower_shield_trial';ART=ROOT/'art/tuareg_lower_shield'
OUT.mkdir(exist_ok=True);ART.mkdir(exist_ok=True)
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent));import garrison;garrison.register()
from garrison.asset_authoring import _ActiveUvOnly
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/tuareg_refined/Tuareg_Refined_Ages_I_IV.blend'))
shield=bpy.data.objects['tuareg_agher_refined'];assert len(shield.data.vertices)==762
before=[v.co.copy() for v in shield.data.vertices]
# Recipe ordering: shell 306; edge 416; four-ring grip 32; motifs 8.
# Keep the two central grip rings, refit both end mounts with the shield shell.
grip=set(range(730,746));delta=Vector((0,0,-.35))
for v in shield.data.vertices:
    if v.index not in grip:v.co+=delta
assert all((shield.data.vertices[i].co-before[i]).length<1e-7 for i in grip)
assert all(((shield.data.vertices[i].co-before[i])-delta).length<2e-7 for i in range(762) if i not in grip)
bm=bmesh.new();bm.from_mesh(shield.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(shield.data);bm.free();shield.data.update()
shield['shield_face_offset']=[.04,0,-.80];shield['lower_shield_delta_m']=-.35
for o in bpy.context.selected_objects:o.select_set(False)
shield.select_set(True);bpy.context.view_layer.objects.active=shield
saved=shield.matrix_basis.copy();shield.matrix_basis=Matrix.Identity(4)
fbx=ART/'lowered_shield.fbx'
with _ActiveUvOnly([shield]):
    assert bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='AUTO',axis_forward='-Z',axis_up='Y',apply_unit_scale=True,use_space_transform=True)=={'FINISHED'}
shield.matrix_basis=saved
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Tuareg_Lower_Shield_Ages_I_IV.blend'))
request=json.loads((ROOT/'art/tuareg_refined/garrison_library/Assets/Custom/tuareg/tuareg_agher_refined/.garrison/requests/20261011T161904Z-63e20c.json').read_text())
oldroot=Path(request['asset_root']);newroot=Path('E:/tsh2/Assets/Custom/tuareg/tuareg_agher_refined')
shutil.copytree(oldroot/'source',newroot/'source',dirs_exist_ok=True);shutil.copy2(fbx,newroot/'source/model.fbx')
request.update(build_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-lower2',asset_root=str(newroot));request['source']['fbx']=str(newroot/'source/model.fbx')
for material in request['materials']:
    for role,path in material['textures'].items():material['textures'][role]=str(newroot/Path(path).relative_to(oldroot))
(OUT/'prepare-request.json').write_text(json.dumps(request,indent=2))
report={'status':'source passed','shield_local_lowering_m':.35,'shell_height_m':1.15,'grip_vertices_unchanged':16,'vertices_shifted':746,'face_offset':[.04,0,-.80],'fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'source':str(ART/'Tuareg_Lower_Shield_Ages_I_IV.blend'),'native_fit':'pending user'}
(OUT/'source-check.json').write_text(json.dumps(report,indent=2));print('LOWER_SHIELD_SOURCE_READY',flush=True)
