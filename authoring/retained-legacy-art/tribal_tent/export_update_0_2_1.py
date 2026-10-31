"""Transform qualified construction FBXs; retain atlases, UVs and stage names."""
import bpy,json,math,hashlib,shutil,traceback
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/berber_update_0_2_1';ART=ROOT/'art/tribal_tent/game_export_0_2_1'
ART.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
baseline=json.loads((ROOT/'output/berber_update_0_2_0/tent-export.json').read_text())
report={'status':'running','scale':2.5,'rotation_degrees':180,'ages':[]}
try:
    delta=Matrix.Rotation(math.pi,4,'Z')@Matrix.Diagonal((2.5,2.5,2.5,1))
    for age in baseline['ages']:
        number=age['age'];old=Path(age['source']);folder=ART/f'age{number}/building'
        assert not folder.exists();shutil.copytree(old,folder)
        for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.ops.import_scene.fbx(filepath=str(old/'model.fbx'))
        objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==len(age['manifest']['parts'])
        coords=[];updated=[]
        for o in objects:
            original=[o.matrix_world@v.co for v in o.data.vertices];coords.extend(original)
            uv=[tuple(v.uv) for v in o.data.uv_layers.active.data]
            o.data.transform(delta@o.matrix_world);o.matrix_world=Matrix.Identity(4)
            assert uv==[tuple(v.uv) for v in o.data.uv_layers.active.data]
            assert all((v.co-delta@p).length<3e-5 for v,p in zip(o.data.vertices,original))
            updated.extend(v.co.copy() for v in o.data.vertices)
        widths=lambda pts:[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
        before=widths(coords);after=widths(updated)
        assert all(abs(n/o-2.5)<1e-5 for n,o in zip(after,before))
        assert {o.name for o in objects}=={p['name'] for p in age['manifest']['parts']}
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.export_scene.fbx(filepath=str(folder/'model.fbx'),use_selection=True,object_types={'MESH'},use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',use_custom_props=False)
        assert (folder/'building.json').read_bytes()==(old/'building.json').read_bytes()
        assert all(p.read_bytes()==(old/p.relative_to(folder)).read_bytes() for p in (folder/'materials').rglob('*.png'))
        report['ages'].append({'age':number,'source':str(folder),'before_dimensions_m':before,'after_dimensions_m':after,'parts':len(objects),'UVs_and_atlases':'byte-preserved','fbx_sha256':hashlib.sha256((folder/'model.fbx').read_bytes()).hexdigest()})
        bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Tent_Age{number}_Construction_0_2_1.blend'))
        print('TENT_021_EXPORTED',number,flush=True)
    report['status']='passed'
except Exception:
    report.update(status='failed',error=traceback.format_exc());traceback.print_exc()
finally:
    (OUT/'tent-export.json').write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.quit_blender()
