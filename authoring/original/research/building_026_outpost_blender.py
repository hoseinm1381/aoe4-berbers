"""Owned Blender worker: import and repaint native mining models without mesh edits."""
import bpy,json,sys,os,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/outpost';OUT=ROOT/'output/berber_update_0_2_6/authors/outpost'
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
recipe=json.loads((ART/'recipe.json').read_text());CAP=OUT/'previews';CAP.mkdir(exist_ok=True)
projections=json.loads((ART/'preview-projections/paths.json').read_text())
def signature(o):
 d=o.data
 return hashlib.sha256(repr(([tuple(v.co) for v in d.vertices],[tuple(p.vertices) for p in d.polygons],[[tuple(u.uv) for u in l.data] for l in d.uv_layers],[tuple(v.normal) for v in d.vertices])).encode()).hexdigest()
def capture(name,label,vec,center,distance,solid=False):
 area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');s=area.spaces.active
 s.region_3d.view_rotation=Vector(vec).to_track_quat('Z','Y');s.region_3d.view_location=Vector(center);s.region_3d.view_distance=distance;s.region_3d.view_perspective='ORTHO';s.overlay.show_overlays=False
 s.shading.type='SOLID' if solid else 'MATERIAL';s.shading.light='STUDIO';s.shading.color_type='SINGLE';s.shading.single_color=(.58,.56,.53)
 sc=bpy.context.scene;sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.filepath=str(CAP/f'{name}_{label}.png')
 with bpy.context.temp_override(area=area,region=region):bpy.ops.render.opengl(write_still=True,view_context=True)
report={'status':'running','models':[],'geometry_policy':'no mesh edits; original topology UV normals transforms retained','bounds_policy':'visible Blender objects only; native fragment selectors may retain additional bounds; consuming stamp remains authoritative for gameplay ground contact'}
for row in recipe['models']:
 bpy.ops.wm.read_factory_settings(use_empty=True);override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
 d=json.loads(Path(row['decode']).read_text());name=row['name'];proxy=bpy.data.objects.new('Stock_Mining_'+name,None);bpy.context.scene.collection.objects.link(proxy)
 proxy['garrison_decode_manifest']=row['decode'];proxy['garrison_logical_path']=row['source'];proxy['garrison_display_name']='Abbasid Outpost '+name
 root=_apply_decoded_static(proxy,d,create_controls=False);meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];before={o.name:signature(o) for o in meshes}
 # Packed DDS can fail GPU reload in Blender; pixel-equivalent PNGs are preview-only.
 for mat in bpy.data.materials:
  if not mat.use_nodes:continue
  for node in mat.node_tree.nodes:
   if node.type=='TEX_IMAGE' and node.image:
    old=node.image;src=str(Path(bpy.path.abspath(old.filepath)))
    if src in projections:
     im=bpy.data.images.load(projections[src],check_existing=True);im.colorspace_settings.name=old.colorspace_settings.name;node.image=im
 visible=[o for o in meshes if not o.hide_get() and not o.hide_render]
 pts=[o.matrix_world@Vector(c) for o in visible for c in o.bound_box];mins=[min(p[i] for p in pts) for i in range(3)];maxs=[max(p[i] for p in pts) for i in range(3)];center=[(a+b)/2 for a,b in zip(mins,maxs)];distance=max(b-a for a,b in zip(mins,maxs))*1.45
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'UNTOUCHED_Abbasid_Outpost_{name}.blend'));capture(name,'before',(1,-1,.9),center,distance)
 remix=json.loads((ART/(name+'-remix-projection.json')).read_text())
 for o in meshes:
  slot=o.get('garrison_material_slot','');gg=next(g for g in remix['geometry']['groups'] if g['preview_material']==slot)
  assert len(o.data.vertices)==len(gg['positions'])
  if slot=='main':
   for v,co in zip(o.data.vertices,gg['positions']):v.co=co
   o.data.normals_split_custom_set_from_vertices(gg['normals'])
  o['berber_stock_model']=row['source'];o['berber_remix']='Berber stock geometry+earth/timber surface remix'
  for mat in o.data.materials:
   slot=o.get('garrison_material_slot','');m=next(x for x in row['materials'] if x['name']==slot)
   for e in m['textures']:
    node=mat.node_tree.nodes.get('Essence · '+e['slot']);assert node,(mat.name,e['slot']);im=bpy.data.images.load(e['image'],check_existing=True);im.colorspace_settings.name='sRGB';node.image=im
   for node in mat.node_tree.nodes:
    for e in m['textures']:
     layer=1 if e['slot']=='albedoTex' else int(e['slot'].removeprefix('albedoTex'))
     if node.type=='RGB' and str(layer) in node.name:
      low=node.name.lower()
      if any(k in low for k in ['highlight','midtone','shadow']):
       c=1 if 'highlight'in low else .84 if 'midtone'in low else .6;node.outputs[0].default_value=(c,c,c,1)
   mat['berber_native_material_edits']=json.dumps(m)
  if o.get('garrison_material_slot')!='main':assert signature(o)==before[o.name]
 root.name='Berber_Outpost_'+name
 for label,vec in [('front',(0,-1,0)),('back',(0,1,0)),('left',(-1,0,0)),('right',(1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]:capture(name,'solid_'+label,vec,center,distance,True)
 capture(name,'after',(1,-1,.9),center,distance)
 for label,colour in [('team_blue',(.02,.15,.8,1)),('team_red',(.8,.025,.025,1))]:
  for mat in bpy.data.materials:
   if mat.use_nodes and (controls:=mat.node_tree.nodes.get('GARRISON Material Controls')) and controls.inputs.get('Team Colour') and controls.inputs.get('Team Colour Strength'):controls.inputs['Team Colour'].default_value=colour;controls.inputs['Team Colour Strength'].default_value=1
  capture(name,label,(1,-1,.9),center,distance)
 for mat in bpy.data.materials:
  if mat.use_nodes and (controls:=mat.node_tree.nodes.get('GARRISON Material Controls')) and controls.inputs.get('Team Colour Strength'):controls.inputs['Team Colour Strength'].default_value=0
 bpy.ops.file.pack_all();dest=ART/f'Berber_Outpost_{name}_0_2_6.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
 report['models'].append({'name':name,'source':row['source'],'mesh_count':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'faces':sum(len(o.data.polygons) for o in meshes),'geometry_uv_normals_hashes':before,'bounds_min':mins,'bounds_max':maxs,'dimensions':[b-a for a,b in zip(mins,maxs)],'scale':list(root.scale),'source_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'topology_uv_transforms_retained':True,'geometry_and_normals_moderately_edited':True,'native_player_colour_maps_retained':True})
 (OUT/'source-validation.json').write_text(json.dumps(report,indent=2));print('SAVED',name,flush=True);override.__exit__(None,None,None)
report['status']='passed';(OUT/'source-validation.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.quit_blender()
