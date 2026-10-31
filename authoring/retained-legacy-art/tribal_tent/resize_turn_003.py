"""Requested uniform size/facing change on a numbered copy; no cook/package."""
import bpy,math,json,hashlib,traceback
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/tribal_tent/iterations/003';OUT=ROOT/'output/tribal_tent/iteration003'
ART.mkdir(exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'art/tribal_tent/iterations/002/Berber_Tribal_Tent_Ages_I_IV_002.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report={'status':'running','scale':2.5,'rotation_degrees':180,'ages':[],'mod_build':False}
try:
    before_hash=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    window=bpy.context.window_manager.windows[0];override=bpy.context.temp_override(window=window);override.__enter__()
    delta=Matrix.Rotation(math.pi,4,'Z')@Matrix.Diagonal((2.5,2.5,2.5,1))
    scene=bpy.context.scene;scene.name='Berber Tribal Tent 003 - larger reversed entrance'
    # Keep an unchanged Age II reference in the scratch presentation only.
    reference=bpy.data.collections.new('Comparison reference - age II');scene.collection.children.link(reference)
    original_root=bpy.data.objects['BER_Tent002_Age2_Origin'];bpy.context.view_layer.update()
    for o in list(bpy.data.collections['BER_Tent002_Age_2'].objects):
        if o.type!='MESH':continue
        clone=o.copy();clone.data=o.data.copy();reference.objects.link(clone)
        clone.parent=None;clone.matrix_world=original_root.matrix_world.inverted()@o.matrix_world
        clone.name='REFERENCE_'+o.name;clone.hide_render=True;clone.hide_viewport=True
    for age in range(1,5):
        col=bpy.data.collections[f'BER_Tent002_Age_{age}'];root=bpy.data.objects[f'BER_Tent002_Age{age}_Origin']
        inv=root.matrix_world.inverted();objects=[o for o in col.objects if o.type=='MESH'];old_points=[];new_points=[]
        for obj in objects:
            relative=inv@obj.matrix_world
            original=[relative@v.co for v in obj.data.vertices]
            old_points.extend(original);obj.data=obj.data.copy();obj.data.transform(delta@relative)
            obj.matrix_basis=Matrix.Identity(4);obj.name=obj.name.replace('BER_Tent002','BER_Tent003')
            new_points.extend(v.co.copy() for v in obj.data.vertices)
            assert all((new-delta@old).length<2e-5 for old,new in zip(original,[v.co for v in obj.data.vertices]))
        old_dimensions=[max(p[i] for p in old_points)-min(p[i] for p in old_points) for i in range(3)]
        new_dimensions=[max(p[i] for p in new_points)-min(p[i] for p in new_points) for i in range(3)]
        assert all(abs(n/o-2.5)<1e-5 for o,n in zip(old_dimensions,new_dimensions))
        root.location=((age-1)*24,0,0);root.name=f'BER_Tent003_Age{age}_Origin';root['draft_envelope_m']=[17,16]
        root['requested_scale']=2.5;root['entrance_rotation_degrees']=180
        col.name=f'BER_Tent003_Age_{age}'
        report['ages'].append({'age':age,'old_dimensions_m':old_dimensions,'new_dimensions_m':new_dimensions,'vertices':len(new_points),'rigid_uniform_transform_verified':True})
    # Comparison references are excluded from the saved authoring source.
    reference_objects=list(reference.objects)
    for obj in reference_objects:scene.collection.objects.link(obj);reference.objects.unlink(obj)
    bpy.data.collections.remove(reference)
    for obj in reference_objects:bpy.data.objects.remove(obj,do_unlink=True)
    for col in bpy.data.collections:
        if col.name.startswith('BER_Tent003'):col.hide_viewport=False;col.hide_render=False
    bpy.context.view_layer.update();bpy.ops.file.pack_all()
    save=ART/'Berber_Tribal_Tent_Ages_I_IV_003.blend';assert not save.exists()
    bpy.ops.wm.save_as_mainfile(filepath=str(save))
    assert sha(SOURCE)==before_hash
    report.update(status='passed',blend=str(save),blend_sha256=sha(save),accepted_002_preserved=True,entrance_before_local=[0,-1,0],entrance_after_local=[0,1,0],native_acceptance='pending next requested build and test')
    (OUT/'source-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('TENT_003_SAVED',flush=True)
except Exception:
    report.update(status='failed',error=traceback.format_exc());(OUT/'source-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');traceback.print_exc()
finally:bpy.ops.wm.quit_blender()
