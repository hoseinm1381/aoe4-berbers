import bpy,json,hashlib,sys,os,math
from pathlib import Path
from mathutils import Vector
G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(G));sys.path.insert(0,str(G.parent));import garrison_shared;sys.modules['garrison.garrison_shared']=garrison_shared;import garrison;garrison.register()
from garrison.decode_projection import _apply_decoded_static
R=Path.cwd();ART=R/'art/economy_remix_0_2_5/lumber';O=R/'output/berber_update_0_2_5/authors/lumber';recipe=json.loads((ART/'recipe.json').read_text());V=O/'previews';V.mkdir(exist_ok=True)
def capture(name,label,vec,solid=False):
 area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');s=area.spaces.active
 objs=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_get()];pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
 s.region_3d.view_location=(lo+hi)/2;s.region_3d.view_distance=max(hi-lo)*1.65;s.region_3d.view_rotation=Vector(vec).to_track_quat('Z','Y');s.region_3d.view_perspective='ORTHO';s.overlay.show_overlays=False;s.shading.type='SOLID' if solid else 'MATERIAL';s.shading.light='STUDIO';s.shading.color_type='SINGLE';s.shading.single_color=(.6,.58,.54)
 bpy.context.scene.render.resolution_x=768;bpy.context.scene.render.resolution_y=768;bpy.context.scene.render.resolution_percentage=100;bpy.context.scene.render.filepath=str(V/f'{name}_{label}.png')
 with bpy.context.temp_override(area=area,region=region):bpy.ops.render.opengl(write_still=True,view_context=True)
def signature(o):
 return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[[tuple(u.uv) for u in l.data] for l in o.data.uv_layers],[tuple(v.normal) for v in o.data.vertices],list(map(list,o.matrix_world)))).encode()).hexdigest()
report={'status':'running','models':[]}
for row in recipe['models']:
 bpy.ops.wm.read_factory_settings(use_empty=True);override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__();name=row['name'];d=json.loads(Path(row['decode']).read_text());proxy=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(proxy);proxy['garrison_decode_manifest']=row['decode'];proxy['garrison_logical_path']=row['source'];proxy['garrison_display_name']=name;root=_apply_decoded_static(proxy,d,create_controls=False)
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];before={o.name:signature(o) for o in meshes};dims={o.name:list(o.dimensions) for o in meshes};bpy.ops.object.select_all(action='DESELECT');bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'UNTOUCHED_{name}.blend'));capture(name,'before',(1,-1,.8))
 for o in meshes:
  edits=next(m for m in row['materials'] if m['name']==o.get('garrison_material_slot',''))
  for mat in o.data.materials:
   for e in edits['textures']:
    node=mat.node_tree.nodes.get('Essence · '+e['slot']);assert node,(mat.name,e['slot']);image=bpy.data.images.load(e['image'],check_existing=True);image.colorspace_settings.name='sRGB';node.image=image
   mat['berber_native_material_edits']=json.dumps(edits)
   for node in mat.node_tree.nodes:
    if node.type=='RGB':
     for e in edits['textures']:
      layer=1 if e['slot']=='albedoTex' else int(e['slot'][9:]);low=node.name.lower()
      if str(layer) in node.name and any(k in low for k in ['highlight','midtone','shadow']):node.outputs[0].default_value=((1,)*3+(1,)) if 'highlight' in low else ((.84,)*3+(1,)) if 'midtone' in low else ((.6,)*3+(1,))
  assert signature(o)==before[o.name]
 for label,vec in [('front',(0,-1,0)),('back',(0,1,0)),('left',(-1,0,0)),('right',(1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]:capture(name,'solid_'+label,vec,True)
 capture(name,'after',(1,-1,.8));bpy.ops.file.pack_all();dest=ART/f'Berber_{name}_0_2_5.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));report['models'].append({'name':name,'mesh_count':len(meshes),'signatures':before,'dimensions':dims,'scale':list(root.scale),'geometry_uv_normals_transforms_retained':True,'blend':str(dest)});(O/'source-validation.json').write_text(json.dumps(report,indent=2));print('LUMBER_BLEND_SAVED',name,flush=True);override.__exit__(None,None,None)
report['status']='passed';(O/'source-validation.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.quit_blender()


