import bpy,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/wall_tower';OUT=ROOT/'output/buildings_batch/wall_tower'
try:
    for age in [2,3,4]:
        bpy.ops.wm.open_mainfile(filepath=str(ART/f'Berber_WallTower_Age{age}.blend'))
        with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
            scene=bpy.context.scene;meshes=[o for o in scene.objects if o.type=='MESH']
            report=[]
            for o in meshes:
                areas=[]
                uv=o.data.uv_layers.active
                for p in o.data.polygons:
                    coords=[uv.data[i].uv for i in p.loop_indices]
                    area=abs(sum(coords[i].x*coords[(i+1)%len(coords)].y-coords[(i+1)%len(coords)].x*coords[i].y for i in range(len(coords))))*.5
                    areas.append(area)
                assert min(areas)>1e-10,(o.name,min(areas))
                report.append({'object':o.name,'minimum_face_uv_area':min(areas),'uv_total_area':sum(areas)})
            def bounds(name):
                o=bpy.data.objects[name];points=[o.matrix_world@Vector(v)for v in o.bound_box]
                return [[min(p[k]for p in points)for k in range(3)],[max(p[k]for p in points)for k in range(3)]]
            deck=bounds('through_walk_deck');rear=bounds('rear_walk_parapet');front=bounds('front_upper_chamber');roof=bounds('roof_platform')
            width=rear[0][1]-front[1][1]
            assert abs(width-3)<1e-5 and abs(deck[1][2]-7)<1e-5
            stair=bounds('rear_access_step_19');east=bounds('rear_walk_parapet_east')
            entry_width=east[0][0]-rear[1][0]
            assert abs(entry_width-1.7)<1e-5 and abs(stair[1][2]-deck[1][2])<1e-5
            # Read mesh bounds rather than author constants: no solid intersects the clear walk prism.
            intruders=[]
            for o in meshes:
                b=bounds(o.name)
                if b[0][0]<3.2-1e-5 and b[1][0]>-3.2+1e-5 and b[0][1]<1.5-1e-5 and b[1][1]>-1.5+1e-5 and b[0][2]<9.6 and b[1][2]>7+1e-5:intruders.append(o.name)
            assert not intruders,intruders
            mounts=[]
            for name in ['springald_mount_base','cannon_carriage']:
                if name in bpy.data.objects:
                    gap=bounds(name)[0][2]-roof[1][2]
                    assert abs(gap)<1e-5,(name,gap)
                    mounts.append({'name':name,'signed_gap':gap})
            owner=[o.name for o in meshes if o.data.materials[0].get('ber_owner_mask')==1]
            assert owner and all(i.packed_file for i in bpy.data.images if i.name!='Render Result')
            allpts=[o.matrix_world@Vector(v)for o in meshes for v in o.bound_box]
            envelope=[[min(p[k]for p in allpts)for k in range(3)],[max(p[k]for p in allpts)for k in range(3)]]
            assert envelope[0][2]>=-1e-5
            (OUT/f'age{age}_saved_audit.json').write_text(json.dumps({'age':age,'uv':report,'walk_clear_width':width,'walk_deck_z':deck[1][2],'stair_entry_width':entry_width,'stair_top_to_deck_gap':stair[1][2]-deck[1][2],'walk_prism_intruders':intruders,'mounts':mounts,'owner_zones':owner,'images_packed':True,'render_envelope':envelope,'note':'Source geometry only; envelope not gameplay footprint'},indent=2))
            print('SAVED_AUDIT_PASS',age,flush=True)
except Exception:
    (OUT/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
