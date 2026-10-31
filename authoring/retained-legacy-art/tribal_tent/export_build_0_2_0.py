"""Bake approved tent copies, retain construction parts, export via Garrison."""
import bpy, bmesh, sys, json, math, traceback
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/berber_update_0_2_0'
ART=ROOT/'art/tribal_tent/game_export_0_2_0_v3';ART.mkdir(exist_ok=True)
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison')
sys.path.insert(0,str(EXT.parent));sys.path.insert(0,str(ROOT/'art/tuareg_refined'))
import garrison;garrison.register()
from garrison import building_panel,material_adoption
from bake_atlas import bake
SOURCE=ROOT/'art/tribal_tent/iterations/002/Berber_Tribal_Tent_Ages_I_IV_002.blend'
report={'status':'running','approved_source':str(SOURCE),'ages':[]}
def orient_closed_components(mesh):
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    pending=set(bm.faces);flipped=0
    while pending:
        todo=[pending.pop()];component=[]
        while todo:
            face=todo.pop();component.append(face)
            for edge in face.edges:
                for other in edge.link_faces:
                    if other in pending:pending.remove(other);todo.append(other)
        edges={e for face in component for e in face.edges}
        if all(len(e.link_faces)==2 for e in edges):
            volume=sum(face.calc_area()*face.normal.dot(face.calc_center_median())/3 for face in component)
            if volume < -1e-10:
                bmesh.ops.reverse_faces(bm,faces=component);flipped+=1
    bm.to_mesh(mesh);bm.free();mesh.update()
    return flipped
try:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    window=bpy.context.window_manager.windows[0]
    override=bpy.context.temp_override(window=window)
    override.__enter__()
    scene=bpy.context.scene
    scene.garrison.asset_library_root='E:/bt20'
    scene.garrison.game_asset_connection=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json'
    scene.garrison.game_asset_index=r'C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3'
    # Source material roles supply owner-colour islands, retained as a baked mask.
    for material in bpy.data.materials:
        material['tuareg_owner_mask']=float(material.name.endswith('red weave') or material.name.endswith('warm cloth'))
    for age in range(1,5):
        collection=bpy.data.collections[f'BER_Tent002_Age_{age}']
        root=bpy.data.objects[f'BER_Tent002_Age{age}_Origin'];root.location.x=0
        bpy.context.view_layer.update()
        originals=[o for o in collection.all_objects if o.type=='MESH']
        copies=[]
        for original in originals:
            clone=original.copy();clone.data=original.data.copy();scene.collection.objects.link(clone)
            world=original.matrix_world.copy();clone.parent=None;clone.matrix_world=world
            stage=min((0,20,40,60,80,100),key=lambda x:abs(x-float(original.get('ber_source_stage',1))*100))
            if 'peg' in original.name.lower() or 'floor' in original.name.lower() or 'mat' in original.name.lower():stage=0
            group=clone.vertex_groups.new(name=f'STAGE_{stage:03d}');group.add(list(range(len(clone.data.vertices))),1,'REPLACE')
            clone.hide_select=False;clone.hide_viewport=False;clone.hide_set(False);clone.hide_render=False;copies.append(clone)
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action='DESELECT')
        for o in copies:o.select_set(True)
        bpy.context.view_layer.objects.active=copies[0]
        print('JOIN_CONTEXT',age,bpy.context.mode,len(copies),len(bpy.context.selected_objects),copies[0].visible_get(),flush=True)
        if bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
        with bpy.context.temp_override(active_object=copies[0],selected_objects=copies,selected_editable_objects=copies):
            bpy.ops.object.join()
        joined=copies[0]
        joined.name=f'berber_tent_age{age}_atlas'
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        print('NORMAL_COMPONENTS_FIXED',age,orient_closed_components(joined.data),flush=True)
        material,paths=bake(joined,ART/f'age{age}/maps',2048)
        material_adoption.adopt_material(material)
        target=bpy.data.collections.new(f'Berber_Tent_Game_Age{age}');scene.collection.children.link(target)
        parts=[]
        for stage in (0,20,40,60,80,100):
            group=joined.vertex_groups.get(f'STAGE_{stage:03d}')
            if group is None:continue
            indices={v.index for v in joined.data.vertices if any(g.group==group.index and g.weight>.5 for g in v.groups)}
            polygons=[p for p in joined.data.polygons if all(i in indices for i in p.vertices)]
            if not polygons:continue
            lookup={i:j for j,i in enumerate(sorted(indices))}
            mesh=bpy.data.meshes.new(f'age{age}_stage{stage}')
            mesh.from_pydata([joined.data.vertices[i].co for i in sorted(indices)],[],[[lookup[i] for i in p.vertices] for p in polygons]);mesh.update()
            mesh.materials.append(material);uv=mesh.uv_layers.new(name='TuaregAtlas')
            source_uv=joined.data.uv_layers.active
            for new,old in zip(mesh.polygons,polygons):
                new.use_smooth=old.use_smooth
                for nloop,oloop in zip(new.loop_indices,old.loop_indices):uv.data[nloop].uv=source_uv.data[oloop].uv
            orient_closed_components(mesh)
            part=bpy.data.objects.new(f'Berber_Tent_A{age}_S{stage:03d}',mesh);target.objects.link(part)
            part['garrison_building_first_stage']=stage;parts.append(part)
        assert any(o.get('garrison_building_first_stage')==0 for o in parts)
        target['garrison_building_profile']='english-house'
        scene.garrison.author_collection=target
        export=ART/f'age{age}/building'
        try:
            manifest=building_panel.export_building(bpy.context,target,export)
        except Exception:
            (OUT/f'preflight-age{age}.json').write_text(scene.get('garrison_preflight','{}'),encoding='utf-8')
            bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'failed-age{age}.blend'))
            raise
        joined.hide_set(True);joined.hide_render=True
        collection.hide_render=True;collection.hide_viewport=True
        report['ages'].append({'age':age,'source':str(export),'manifest':manifest,'maps':paths,'triangles':sum(len(p.vertices)-2 for p in joined.data.polygons)})
        (OUT/'tent-export.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('TENT_AGE_EXPORTED',age,flush=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Berber_Tribal_Tent_Game_Export_0_2_0.blend'))
    report['status']='passed';report['packed_blend']=str(ART/'Berber_Tribal_Tent_Game_Export_0_2_0.blend')
    (OUT/'tent-export.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('TENT_EXPORT_COMPLETE',flush=True)
except Exception:
    report['status']='failed';report['error']=traceback.format_exc()
    (OUT/'tent-export.json').write_text(json.dumps(report,indent=2),encoding='utf-8');traceback.print_exc()
finally:
    bpy.ops.wm.quit_blender()
