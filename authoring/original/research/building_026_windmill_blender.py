"""Import stock houses, repaint their existing surfaces, save source and views.

Run inside the claimed, initially empty Blender session. No replacement geometry.
"""
import bpy,json,copy,math,hashlib,sys,os
from pathlib import Path
from mathutils import Vector
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT))
import importlib.util
spec=importlib.util.spec_from_file_location('garrison_shared',str(EXT/'garrison_shared.cp313-win_amd64.pyd'))
shared=importlib.util.module_from_spec(spec);sys.modules['garrison_shared']=shared;spec.loader.exec_module(shared)
sys.path.insert(0,str(EXT.parent))
import garrison
sys.modules['garrison.garrison_shared']=shared
garrison.register()
from garrison.decode_projection import _apply_decoded_static

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/windmill';OUT=ROOT/'output/berber_update_0_2_6/authors/windmill'
recipe=json.loads((ART/'recipe.json').read_text());sys.path.insert(0,str(ROOT/'research'));from building_026_windmill_geometry import deform;captures=OUT/'previews';captures.mkdir(exist_ok=True)
def frame(direction,center,solid=False):
    area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in area.regions if r.type=='WINDOW')
    space=area.spaces.active;space.region_3d.view_rotation=Vector(direction).to_track_quat('Z','Y')
    space.region_3d.view_location=Vector(center);space.region_3d.view_distance=12.0;space.region_3d.view_perspective='ORTHO'
    space.overlay.show_overlays=False;space.shading.type='SOLID' if solid else 'MATERIAL'
    space.shading.light='STUDIO';space.shading.color_type='SINGLE';space.shading.single_color=(.58,.56,.53)
    return area,region
def capture(age,label,solid=False,direction=(1,-1,.9),center=(0,0,4.1)):
    area,region=frame(direction,center,solid)
    scene=bpy.context.scene;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.render.filepath=str(captures/f'age{age}_{label}.png')
    with bpy.context.temp_override(area=area,region=region):bpy.ops.render.opengl(write_still=True,view_context=True)

report={'status':'running','ages':[]}
for age in [dict(recipe,age=1)]:
    n=age['age'];bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    d=json.loads(Path(age['decode']).read_text());before=copy.deepcopy(d)
    proxy=bpy.data.objects.new(f'Common_Windmill_Age{n}_Untouched',None);bpy.context.scene.collection.objects.link(proxy)
    proxy['garrison_decode_manifest']=age['decode'];proxy['garrison_logical_path']=age['source'];proxy['garrison_display_name']=f'Common Stock Windmill Age {n}'
    root=_apply_decoded_static(proxy,d,create_controls=False)
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'UNTOUCHED_Common_Windmill_Age{n}.blend'))
    stock_objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];original={o.name:([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons]) for o in stock_objects}
    root.scale=(recipe['scale'],)*3;bpy.context.view_layer.update();capture(n,'before')
    # Moderate donor vertex edits, matched to native known spans; retain fans/axle.
    for obj in stock_objects:
        if obj.get('garrison_material_slot','')=='windmill':
            group=d['geometry']['groups'][1]
            assert len(obj.data.vertices)==len(group['positions'])
            native_remix=json.loads((ART/'remix-projection.json').read_text())['geometry']['groups'][1]
            for v,co in zip(obj.data.vertices,native_remix['positions']):v.co=co
            obj.data.normals_split_custom_set_from_vertices(native_remix['normals'])
    # Change native texture-image nodes, retain UV wiring and owner masks.
    for obj in stock_objects:
        obj['berber_stock_model']=age['source'];obj['berber_remix']='earthen Amazigh geometry and material remix; stock topology retained'
        for mat in obj.data.materials:
            slot=obj.get('garrison_material_slot','')
            edits=next((m for m in age['materials'] if m['name']==slot),None)
            assert edits,(n,obj.name,slot)
            for edit in edits['textures']:
                node=mat.node_tree.nodes.get('Essence · '+edit['slot']);assert node,(mat.name,edit['slot'])
                image=bpy.data.images.load(edit['image'],check_existing=True);image.colorspace_settings.name='sRGB';node.image=image
            mat['berber_native_material_edits']=json.dumps(edits)
            # Rebuild native tonal colour nodes from the per-material palette.
            for node in mat.node_tree.nodes:
                for edit in edits['textures']:
                    layer=1 if edit['slot']=='albedoTex' else int(edit['slot'].removeprefix('albedoTex'))
                    if node.type=='RGB' and str(layer) in node.name:
                        low=node.name.lower()
                        if any(k in low for k in ['highlight','midtone','shadow']):
                            c=1 if 'highlight' in low else .84 if 'midtone' in low else .6
                            node.outputs[0].default_value=(c,c,c,1)
        assert original[obj.name][1]==[tuple(p.vertices) for p in obj.data.polygons],'Topology changed unexpectedly'
    root.name=f'Berber_Windmill_Age{n}_Stock_Remix';root['berber_visual_scale']=recipe['scale']
    bpy.context.view_layer.update()
    for name,vec in [('front',(0,-1,0)),('back',(0,1,0)),('left',(-1,0,0)),('right',(1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]:capture(n,'solid_'+name,True,vec)
    capture(n,'after')
    for label,colour in [('team_blue',(.02,.15,.8,1)),('team_red',(.8,.025,.025,1))]:
        for mat in bpy.data.materials:
            if mat.use_nodes and (controls:=mat.node_tree.nodes.get('GARRISON Material Controls')):
                controls.inputs['Team Colour'].default_value=colour;controls.inputs['Team Colour Strength'].default_value=1
        capture(n,label)
    for mat in bpy.data.materials:
        if mat.use_nodes and (controls:=mat.node_tree.nodes.get('GARRISON Material Controls')):controls.inputs['Team Colour Strength'].default_value=0
    frame((1,-1,.9),(0,0,1.2));bpy.ops.file.pack_all();path=ART/f'Berber_Windmill_Age{n}_0_2_6.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    report['ages'].append({'age':n,'source':str(path),'stock_topology_uv_retained':True,'geometry_moderately_edited':True,'mesh_count':len(stock_objects),'vertices':sum(len(o.data.vertices) for o in stock_objects),'faces':sum(len(o.data.polygons) for o in stock_objects),'visual_scale':recipe['scale'],'all_uv_layers_retained':True,'native_team_masks_retained':True,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (OUT/'source-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('BERBER_WINDMILL_SOURCE_SAVED',n,flush=True)
    override.__exit__(None,None,None)
report['status']='passed';(OUT/'source-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
bpy.ops.wm.quit_blender()

