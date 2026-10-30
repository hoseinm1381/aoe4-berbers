"""UI-independent invocation of installed Garrison building-source contracts.

The installed UI imports unavailable compiled setup modules. Only the actual
material snapshot functions are loaded from its source; the mesh preflight,
parts contract, FBX convention, UV flip and materials are otherwise unchanged.
No add-on files or user preferences are modified.
"""
import bpy, sys, os, ast, json, hashlib, shutil
from pathlib import Path
from collections import Counter
from typing import Any
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[2]
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT));sys.path.insert(0,str(EXT.parent))
import garrison_shared
from garrison_shared import building_project as bp
sys.modules['garrison.garrison_shared']=garrison_shared
from garrison import material_adoption as ma
from garrison.image_snapshot import save_png_snapshot
from garrison.model_preflight_ui import require_valid


def export(blend, collection_name, output):
    output=Path(output)
    if output.exists():raise FileExistsError('Preserving previous export: '+str(output))
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    col=bpy.data.collections[collection_name];meshes=[o for o in col.all_objects if o.type=='MESH']
    for ob in meshes:
        used={p.material_index for p in ob.data.polygons}
        mats={ob.data.materials[i] for i in used if i<len(ob.data.materials) and ob.data.materials[i]}
        if len(mats)!=1:raise ValueError('Each mesh must have one active atlas '+ob.name)
        mat=mats.pop();ob.data.materials.clear();ob.data.materials.append(mat)
        for p in ob.data.polygons:p.material_index=0
    materials={o.data.materials[0] for o in meshes}
    if len(materials)!=1:raise ValueError('One shared building atlas required')
    for m in materials:ma.adopt_material(m)
    proof=require_valid(meshes,bpy.context)
    rows=bp.parts([{'name':o.name,'first_stage':o.get(bp.STAGE_PROPERTY)} for o in meshes],'english-house')
    needed={'_author_material_usage','_semantic_color','_save_semantic_snapshot','_export_adopted_materials'}
    source=EXT/'asset_authoring.py';tree=ast.parse(source.read_text(encoding='utf8'))
    funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in needed]
    assert len(funcs)==4
    namespace=dict(globals());namespace.update({name:getattr(ma,name) for name in
        ('stored_contract','analyze_principled_material','MaterialAdoptionError','ENCODER_PRESET','SUPPORTED_SEMANTICS')})
    exec(compile(ast.Module(body=funcs,type_ignores=[]),str(source),'exec'),namespace)
    output.mkdir(parents=True)
    records=namespace['_export_adopted_materials'](meshes,output)
    stages={r['name']:r['first_stage'] for r in rows}
    copies=[];graph=bpy.context.evaluated_depsgraph_get()
    for index,ob in enumerate(sorted(meshes,key=lambda o:o.name)):
        me=bpy.data.meshes.new_from_object(ob.evaluated_get(graph),depsgraph=graph)
        clone=bpy.data.objects.new(f'090_export_pending_{index:04}',me);bpy.context.scene.collection.objects.link(clone)
        me.transform(ob.matrix_world);clone.matrix_world=Matrix.Identity(4)
        active=me.uv_layers.active
        for layer in list(me.uv_layers):
            if layer!=active:me.uv_layers.remove(layer)
        for loop in active.data:loop.uv.y=1-loop.uv.y
        copies.append((clone,stages[ob.name]))
    # All parts with the same stage have exactly the same native visibility.
    # Combine evaluated export copies only, leaving the editable source intact.
    source_triangles=sum(len(p.vertices)-2 for clone,_ in copies for p in clone.data.polygons)
    grouped=[];stage_groups=[]
    for stage in sorted(set(s for _,s in copies)):
        members=[ob for ob,s in copies if s==stage]
        for ob in bpy.context.selected_objects:ob.select_set(False)
        for ob in members:ob.select_set(True)
        bpy.context.view_layer.objects.active=members[0]
        if len(members)>1:bpy.ops.object.join()
        clone=bpy.context.view_layer.objects.active
        clone.name=f'garrison_part_{len(grouped):04}'
        grouped.append((clone,stage));stage_groups.append({'stage':stage,'source_parts':len(members)})
    copies=grouped
    assert sum(len(p.vertices)-2 for ob,_ in copies for p in ob.data.polygons)==source_triangles
    for ob in bpy.context.selected_objects:ob.select_set(False)
    for clone,_ in copies:clone.select_set(True)
    bpy.context.view_layer.objects.active=copies[0][0]
    result=bpy.ops.export_scene.fbx(filepath=str(output/'model.fbx'),use_selection=True,object_types={'MESH'},
        use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',use_custom_props=False)
    assert 'FINISHED' in result
    manifest={'schema':bp.SCHEMA,'profile':'english-house','parts':[{'name':o.name,'first_stage':s} for o,s in copies],
              'material_name':records[0]['source_name'],
              'textures':{k:Path(v).relative_to(output).as_posix() for k,v in records[0]['textures'].items()}}
    (output/'building.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    (output.parent/'export-validation.json').write_text(json.dumps({'status':'passed','preflight':proof,
       'parts':len(copies),'editable_parts':len(meshes),'stage_groups':stage_groups,
       'export_triangles':source_triangles,'stage_group_triangle_preservation':True,
       'stages':sorted(set(stages.values())),
       'source':str(blend),'source_sha256':hashlib.sha256(Path(blend).read_bytes()).hexdigest(),
       'export_contract':'installed building-source/v1, exact Garrison material snapshot functions and FBX conventions',
       'installed_material_helper_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf8')
    print('090_EXPORT_PASSED',len(copies),output,flush=True)


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    export(Path(args[0]),args[1],Path(args[2]))
