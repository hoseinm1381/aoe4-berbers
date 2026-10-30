import bpy,bmesh,json,math,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/siege';O=R/'output/buildings_batch/siege';report=[];success=False
def bb(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]]
try:
    for age in [3,4]:
        bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Siege_Age{age}.blend'))
        with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
            bpy.context.view_layer.update();meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];count=len(meshes);contacts=[]
            assert all(im.packed_file for im in bpy.data.images if im.type=='IMAGE')
            for o in meshes:
                assert len(o.data.uv_layers)>0
                assert all(math.isfinite(v) for ve in o.data.vertices for v in ve.co)
                bm=bmesh.new();bm.from_mesh(o.data);assert bm.calc_volume(signed=True)>0 and all(e.is_manifold for e in bm.edges);bm.free()
                if o.name.startswith('seasoned_lumber'):
                    candidates=[r for r in meshes if r.name.startswith('timber_rack_crossrail')]
                    gap=min(abs(bb(o)[0][2]-bb(r)[1][2]) for r in candidates);assert gap<1e-5;contacts.append({'part':o.name,'interface':'lumber lower face / stock rack rail upper face','gap_m':gap})
            wheel=bpy.data.objects['assembled_wheel_rim'];rail=bpy.data.objects['wheel_display_rail'];wheel_gap=bb(wheel)[0][2]-bb(rail)[1][2]
            assert abs(wheel_gap)<1e-5;contacts.append({'part':'assembled_wheel_rim','interface':'rim bottom / display rail','gap_m':wheel_gap,'tolerance_m':1e-5})
            assert abs(bb(bpy.data.objects['yard_foundation'])[0][2])<1e-6
            manifest=json.loads((A/f'age{age}_construction.json').read_text());assert len(manifest['parts'])==count
            owner=[o.name for o in meshes if o.data.materials[0].get('ber_owner_mask')==1];assert owner
            bpy.ops.wm.read_factory_settings(use_empty=True)
            with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Siege_Age{age}.fbx'))
            imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==count and all(o.data.uv_layers for o in imported)
            report.append({'age':age,'saved_meshes':count,'fbx_meshes':len(imported),'packed_images':True,'stage_manifest_matches':True,'owner_zone_objects':owner,'extra_measured_contacts':contacts,'fbx_uv_present':True,'ground_origin_z':0})
    (O/'saved_source_fbx_audit.json').write_text(json.dumps(report,indent=2));success=True
except Exception:
    (O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:
    bpy.context.preferences.view.use_save_prompt=False
    bpy.ops.wm.quit_blender()
    import os
    os._exit(0 if success else 1)


