"""Isolated native Town Center source, comparison views and geometry validation."""
import bpy,os,sys,json,hashlib,struct,math,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/building_remix_0_2_6/barracks';OUT=ROOT/'output/berber_update_0_2_6/authors/barracks';CAP=OUT/'previews';CAP.mkdir(exist_ok=True)
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';sys.path.insert(0,str(EXT))
spec=importlib.util.spec_from_file_location('garrison_shared',str(EXT/'garrison_shared.cp313-win_amd64.pyd'));shared=importlib.util.module_from_spec(spec);sys.modules['garrison_shared']=shared;spec.loader.exec_module(shared);sys.path.insert(0,str(EXT.parent));import garrison;sys.modules['garrison.garrison_shared']=shared;garrison.register()
from garrison.decode_projection import _apply_decoded_static
recipe=json.loads((ART/'recipe.json').read_text());assemblies=json.loads((OUT/'native-assemblies.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def transform(raw):
 qx,qy,qz,qs,x,y,z,sx,sy,sz=struct.unpack('<10f',bytes.fromhex(raw));basis=Matrix(((-1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
 return basis @ Matrix.Translation(Vector((x,y,z))) @ Quaternion((qs,qx,qy,qz)).to_matrix().to_4x4() @ Matrix.Diagonal((sx,sy,sz,1)) @ basis.inverted()
def import_age(age):
 bpy.ops.wm.read_factory_settings(use_empty=True);items=[]
 override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
 donors=json.loads((ART/'donors.json').read_text());by_source={m['source'][:-4]:m for m in donors};edits={m['source'][:-4]:m for m in recipe['models']}
 assembly=next(a for a in assemblies if a['age']==age)
 for ci,component in enumerate(assembly['components']):
  source=component['model'];model=edits.get(source,dict(by_source[source],materials=[]));d=json.loads(Path(model['decode']).read_text())
  proxy=bpy.data.objects.new(f"{model['name']}_{ci}",None);bpy.context.scene.collection.objects.link(proxy);proxy['garrison_decode_manifest']=model['decode'];proxy['garrison_logical_path']=model['source'];proxy['garrison_display_name']=model['name'];root=_apply_decoded_static(proxy,d,create_controls=False)
  root.matrix_world=transform(component['fields']['m_transform']['raw'])
  meshes=[o for o in root.children_recursive if o.type=='MESH'];assert len(meshes)==len(d['geometry']['groups']),(model['name'],len(meshes),len(d['geometry']['groups']))
  if source in edits:items.append((model,d,root,meshes))
 bpy.context.view_layer.update();return items

def inspect():
 data={};points=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  m=o.data;points.extend(o.matrix_world@Vector(co) for co in o.bound_box)
  data[o.name]={'positions':[tuple(v.co) for v in m.vertices],'polygons':[tuple(p.vertices) for p in m.polygons],'uv':{u.name:[tuple(x.uv) for x in u.data] for u in m.uv_layers},'matrix':[list(r) for r in o.matrix_world],'normals':[tuple(v.normal) for v in m.vertices]}
 return data,{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def setup(bounds):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=True;s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100
 s.world=bpy.data.worlds.new('Preview World');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.45,.45,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.render.image_settings.file_format='PNG'
 for name,loc,power,size in [('Key',(-8,-10,18),1800,12),('Fill',(10,4,12),1100,10)]:
  light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;o=bpy.data.objects.new(name,light);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
 cam=bpy.data.cameras.new('Evidence Camera');obj=bpy.data.objects.new('Evidence Camera',cam);s.collection.objects.link(obj);s.camera=obj;cam.type='ORTHO'
 extent=max(bounds['max'][i]-bounds['min'][i] for i in range(3));cam.ortho_scale=extent*1.5
 return Vector(tuple((a+b)*.5 for a,b in zip(bounds['min'],bounds['max'])))
def capture(age,label,center,direction=(1,-1,.85),solid=False):
 s=bpy.context.scene;o=s.camera;o.location=center+Vector(direction).normalized()*35;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(CAP/f'age{age}_{label}.png')
 temporary=[]
 if solid:
  clay=bpy.data.materials.get('Evidence Clay') or bpy.data.materials.new('Evidence Clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.42,.41,.39,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
  for ob in bpy.context.scene.objects:
   if ob.type=='MESH':temporary.append((ob,list(ob.data.materials)));ob.data.materials.clear();ob.data.materials.append(clay)
 bpy.ops.render.render(write_still=True)
 for ob,mats in temporary:
  ob.data.materials.clear()
  for mat in mats:ob.data.materials.append(mat)
def main():
 rows=[]
 for age in range(1,5):
  items=import_age(age);before,bounds=inspect();bpy.ops.file.pack_all();stock=ART/f'UNTOUCHED_Abbasid_Barracks_Age{age}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(stock));center=setup(bounds);capture(age,'before',center)
  for model,d,root,meshes in items:
   remix=json.loads(Path(model['remix_decode']).read_text())
   # Match each imported mesh by its decoded native material/vertex count.
   used=set()
   for ob in meshes:
    slot=ob.get('garrison_material_slot');candidates=[(i,g) for i,g in enumerate(d['geometry']['groups']) if i not in used and len(g['positions'])==len(ob.data.vertices) and tuple(g['positions'][0])==tuple(ob.data.vertices[0].co)]
    assert len(candidates)==1,(model['name'],ob.name,len(candidates));gi,g=candidates[0];used.add(gi);new=remix['geometry']['groups'][gi]
    assert [tuple(v.co) for v in ob.data.vertices]==[tuple(p) for p in g['positions']]
    for v,co in zip(ob.data.vertices,new['positions']):v.co=co
    ob.data.normals_split_custom_set_from_vertices(new['normals'])
    matrecipe=next(m for m in model['materials'] if m['name']==slot)
    for mat in ob.data.materials:
     for tex in matrecipe['textures']:
      node=mat.node_tree.nodes.get('Essence · '+tex['slot']);assert node;im=bpy.data.images.load(tex['image'],check_existing=True);im.colorspace_settings.name='sRGB';node.image=im
     for node in mat.node_tree.nodes:
      if node.type!='RGB':continue
      for key,val in matrecipe['parameters'].items():
       layer=''.join(c for c in key if c.isdigit());tone=key.split('Color')[0]
       if tone.lower() in node.name.lower() and layer in node.name:node.outputs[0].default_value=val
    ob['berber_native_source']=model['source'];ob['native_span_remix']=True
  bpy.context.view_layer.update();after,newbounds=inspect();changed=0
  assert set(before)==set(after)
  for name,old in before.items():
   new=after[name];assert old['polygons']==new['polygons'] and old['uv']==new['uv'] and old['matrix']==new['matrix']
   for a,b in zip(old['positions'],new['positions']):
    assert a[:2]==b[:2]
    if a[2]<=2.15:assert a==b
    if a!=b:changed+=1
  assert bounds['min'][:2]==newbounds['min'][:2] and bounds['max'][:2]==newbounds['max'][:2]
  assert abs(bounds['min'][2]-newbounds['min'][2])<.001
  capture(age,'after',center)
  for label,vec in [('front',(0,-1,0)),('back',(0,1,0)),('left',(-1,0,0)),('right',(1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]:capture(age,'solid_'+label,center,vec,True)
  for label,colour in [('team_blue',(.015,.12,.8,1)),('team_red',(.8,.025,.025,1))]:
   for mat in bpy.data.materials:
    if mat.use_nodes and (control:=mat.node_tree.nodes.get('GARRISON Material Controls')) and control.inputs.get('Team Colour'):control.inputs['Team Colour'].default_value=colour;control.inputs['Team Colour Strength'].default_value=1
   capture(age,label,center)
  for mat in bpy.data.materials:
   if mat.use_nodes and (control:=mat.node_tree.nodes.get('GARRISON Material Controls')) and control.inputs.get('Team Colour Strength'):control.inputs['Team Colour Strength'].default_value=0
  bpy.ops.file.pack_all();path=ART/f'Berber_Barracks_Age{age}_0_2_6.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
  rows.append({'age':age,'untouched_blend':str(stock),'untouched_sha256':sha(stock),'remix_blend':str(path),'remix_sha256':sha(path),'stock_bounds':bounds,'remix_bounds':newbounds,'changed_vertices':changed,'topology_uv_native_transforms_preserved':True,'all_xy_lower_2_15m_positions_preserved':True,'base_ground_contact_preserved':True,'scope':'Complete native combined barracks + flags, shields, training dummies and sagebush instances at stock transforms. No combined/control/tower duplicate.'})
  (OUT/'source-validation.json').write_text(json.dumps({'status':'running','ages':rows},indent=2)+'\n');print('DOCK_AGE_SAVED',age,flush=True)
 (OUT/'source-validation.json').write_text(json.dumps({'status':'passed','ages':rows},indent=2)+'\n');print('DOCK_SOURCE_COMPLETE',flush=True)
if __name__=='__main__':main()

bpy.ops.wm.quit_blender()

