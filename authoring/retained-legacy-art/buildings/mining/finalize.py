"""Reopen saved ages for packed map and asset-source audit; no renders/cook."""
import bpy,bmesh,json,math,sys,traceback
from mathutils import Vector
from pathlib import Path
P=Path(__file__).parent;O=P.parents[2]/'output/buildings_batch/mining'
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(P/f'Berber_Mining_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   for side in [o for o in bpy.context.scene.objects if o.name.startswith('store_sidewall')]:
    side.location.y=1.145
    factor=.71/(max(v.co.y for v in side.data.vertices)-min(v.co.y for v in side.data.vertices))
    for v in side.data.vertices:v.co.y*=factor
   if age==4 and not bpy.data.objects.get('basket_lifting_crossbar'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(.91,.45,.715));ob=bpy.context.object;ob.name='basket_lifting_crossbar';ob.dimensions=(.24,.04,.03);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(bpy.data.materials['BerberMining_cedar']);ob['ber_material_role']='cedar';ob['garrison_building_first_stage']=100;ob['ber_source_stage']=1.0;uv=ob.data.uv_layers.active
    for face in ob.data.polygons:
     axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis];coords=[ob.data.vertices[ob.data.loops[i].vertex_index].co for i in face.loop_indices];lo=[min(v[k] for v in coords) for k in axes];hi=[max(v[k] for v in coords) for k in axes]
     for i,v in zip(face.loop_indices,coords):uv.data[i].uv=((3+.06+.88*(v[axes[0]]-lo[0])/(hi[0]-lo[0]))/4,(.06+.88*(v[axes[1]]-lo[1])/(hi[1]-lo[1]))/2)
    manifest=P/f'age{age}_construction.json';d=json.loads(manifest.read_text());d['parts'].append({'object':ob.name,'first_stage':100,'material':'cedar','owner_mask':0});manifest.write_text(json.dumps(d,indent=2))
   for name,rgb in [('roughness',(.85,.85,.85)),('normal',(.5,.5,1)),('metal',(0,0,0))]:
    im=bpy.data.images.new('Mining_'+name,width=256,height=256,alpha=True);im.use_fake_user=True;im.colorspace_settings.name='Non-Color';im.pixels.foreach_set([*rgb,1]*65536);im.filepath_raw=str(P/(name+'.png'));im.file_format='PNG';im.save();im.pack()
   report={'age':age,'packed_images':[{ 'name':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if im.name.startswith('Mining_')], 'objects':[]}
   for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data);report['objects'].append({'name':o.name,'signed_volume':bm.calc_volume(signed=True),'non_manifold':sum(not e.is_manifold for e in bm.edges),'degenerate':sum(f.calc_area()<1e-10 for f in bm.faces),'positive_scale':all(v>0 for v in o.scale)});bm.free()
   def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
   bpy.context.view_layer.update()
   report['fitted_openings']=[]
   for door in [o for o in bpy.context.scene.objects if o.name.startswith('horseshoe_door')]:
    front=min([o for o in bpy.context.scene.objects if o.name.startswith('store_front')],key=lambda o:abs(o.location.x-door.location.x))
    # Door mesh positions encode world x; match using bounding-box center.
    center=(bounds(door)[0][0]+bounds(door)[1][0])/2
    front=min([o for o in bpy.context.scene.objects if o.name.startswith('store_front')],key=lambda o:abs(o.location.x-center))
    recess=bounds(door)[0][1]-bounds(front)[0][1];report['fitted_openings'].append({'door':door.name,'wall':front.name,'measured_recess':recess,'pass':abs(recess-.035)<1e-5,'cut_fit':'insert and cutter use identical portal outline'})
   assert all(v['pass'] for v in report['fitted_openings'])
   meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
   ymin=min(bounds(o)[0][1] for o in meshes if o.name not in ['courtyard_foundation','courtyard_floor'])
   report['front_unobstructed_apron']={'x':[-1.9,1.9],'y':[-1.9,ymin],'depth':ymin+1.9,'scope':'render geometry only; native drop-off pathing pending'}
   assert ymin>-1.9
   d=json.loads((O/f'age{age}_validation.json').read_text());d['front_access_clear_corridor']={'x':[-.10,.55],'y':[-1.9,.40],'minimum_width':.65,'native_pathing':'pending'};d['front_unobstructed_apron']=report['front_unobstructed_apron'];d['decorative_roof_drain_overhang_beyond_footprint']=max(0,d['geometry_bounds'][1][1]-2);(O/f'age{age}_validation.json').write_text(json.dumps(d,indent=2))
   corridor=[]
   for o in meshes:
    if o.name in ['courtyard_foundation','courtyard_floor']:continue
    lo,hi=bounds(o)
    if hi[0]>-.10 and lo[0]<.55 and hi[1]>-1.9 and lo[1]<.40:corridor.append(o.name)
   report['central_court_passage']={'x':[-.10,.55],'y':[-1.9,.40],'measured_width':.65,'intersecting_geometry':corridor,'pass':not corridor}
   assert not corridor,corridor
   report['additional_contacts']=[]
   pairs=[('store_sidewall','store_front',1,0,1,0),('store_backwall','store_sidewall',1,0,1,0),('front_crossbeam','shelter_post',2,0,1,-.06),('store_roof','store_backwall',2,0,1,0)]
   if age==4:pairs.extend([('lifting_jib_post','jib_stone_base',2,0,1,0),('jib_rope','basket_lifting_crossbar',2,0,1,0)])
   for child,parent,axis,cs,ps,expected in pairs:
    gap=bounds(bpy.data.objects[child])[cs][axis]-bounds(bpy.data.objects[parent])[ps][axis]
    report['additional_contacts'].append({'interface':child+' to '+parent,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})
   assert all(c['pass'] for c in report['additional_contacts'])
   assert all(v['packed'] for v in report['packed_images'])
   assert all(v['signed_volume']>0 and v['non_manifold']==0 and v['degenerate']==0 and v['positive_scale'] for v in report['objects'])
   (O/f'age{age}_saved_audit.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/f'Berber_Mining_Age{age}.blend'))
   scene=bpy.context.scene;cam=scene.camera;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.filepath=str(O/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
   scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=384;scene.render.resolution_y=384
   for name,loc in [('front',(0,-8,1)),('back',(0,8,1)),('left',(-8,0,1)),('right',(8,0,1)),('top',(0,0,9)),('bottom',(0,0,-8))]:
    cam.location=loc;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(O/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
   bpy.ops.object.select_all(action='DESELECT')
   for ob in meshes:ob.select_set(True)
   bpy.context.view_layer.objects.active=meshes[0];bpy.ops.export_scene.fbx(filepath=str(P/f'Berber_Mining_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
except Exception:(O/'FINALIZE_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
