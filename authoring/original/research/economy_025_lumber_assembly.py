import bpy,json,struct,sys,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
R=Path.cwd();O=R/'output/berber_update_0_2_5/authors/lumber';ART=R/'art/economy_remix_0_2_5/lumber';native=json.loads((R/'output/berber_update_0_2_5/integration/com_lumber_camp.native.json').read_text());recipe=json.loads((ART/'recipe.json').read_text())
exec((R/'research/economy_025_lumber_blender.py').read_text().split("report={'status':'running'")[0].split("G=Path")[0])
def capture(label,vec,solid=False):
 a=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');reg=next(r for r in a.regions if r.type=='WINDOW');s=a.spaces.active;objs=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_get()];pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);s.region_3d.view_location=(hi+lo)/2;s.region_3d.view_distance=max(hi-lo)*1.5;s.region_3d.view_rotation=Vector(vec).to_track_quat('Z','Y');s.region_3d.view_perspective='ORTHO';s.overlay.show_overlays=False;s.shading.type='SOLID' if solid else 'MATERIAL';s.shading.light='STUDIO';s.shading.color_type='SINGLE';s.shading.single_color=(.6,.58,.54);sc=bpy.context.scene;sc.render.resolution_x=1024;sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.filepath=str(O/'previews'/('assembly_'+label+'.png'))
 with bpy.context.temp_override(area=a,region=reg):bpy.ops.render.opengl(write_still=True,view_context=True)
 return {'min':list(lo),'max':list(hi),'dimensions':list(hi-lo)}
report={'status':'passed','axis_conversion':'nativeYup to BlenderZup via Rx90 conjugation','states':'healthy crane logs saw; construction pile excluded from healthy display; native state binding retained','assemblies':[]}
for remix in [False,True]:
 bpy.ops.wm.read_factory_settings(use_empty=True);over=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);over.__enter__();B=Matrix.Rotation(math.pi/2,4,'X')
 for row in recipe['models']:
  stem=row['source'].removesuffix('.rgm').replace('/','\\');obj=next(x for x in native if x['type']=='VisualStampBlueprint' and x['fields']['m_blueprint']['text']==stem);raw=struct.unpack('<10f',bytes.fromhex(obj['fields']['m_transform']['raw']));xyzw=raw[:4];pos=raw[4:7];scale=raw[7:10];M=Matrix.Translation(pos)@Quaternion((xyzw[3],*xyzw[:3])).to_matrix().to_4x4()@Matrix.Diagonal((*scale,1))
  file=ART/(f'Berber_{row["name"]}_0_2_5.blend' if remix else f'UNTOUCHED_{row["name"]}.blend')
  with bpy.data.libraries.load(str(file),link=False) as (src,dst):dst.objects=src.objects
  new=[o for o in dst.objects if o];parents=[o for o in new if o.parent is None]
  for o in new:bpy.context.scene.collection.objects.link(o)
  mount=bpy.data.objects.new('NativeStamp_'+row['name'],None);bpy.context.scene.collection.objects.link(mount);mount.matrix_world=B@M@B.inverted();mount['native_transform']=json.dumps(raw)
  for o in parents:o.parent=mount
  if row['name']=='buildpile_wood_lumber':
   for o in new:o.hide_set(True)
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');label='after' if remix else 'before';dims=capture(label,(1,-1,.8));report['assemblies'].append({'state':label,**dims});
 if remix:
  for n,v in [('front',(0,-1,0)),('back',(0,1,0)),('left',(-1,0,0)),('right',(1,0,0)),('top',(0,0,1)),('bottom',(0,0,-1))]:capture('solid_'+n,v,True)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/('Berber_Lumber_Camp_Assembly_0_2_5.blend' if remix else 'UNTOUCHED_Lumber_Camp_Assembly.blend')));over.__exit__(None,None,None)
assert report['assemblies'][0]['dimensions']==report['assemblies'][1]['dimensions'];(O/'assembly-validation.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.quit_blender()
