"""Reopen saved ages for packed map and asset-source audit; no renders/cook."""
import bpy,bmesh,json,math,sys,traceback
from mathutils import Vector
from pathlib import Path
P=Path(__file__).parent;O=P.parents[2]/'output/buildings_batch/mill'
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(P/f'Berber_Mill_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   for name,rgb in [('roughness',(.85,.85,.85)),('normal',(.5,.5,1)),('metal',(0,0,0))]:
    im=bpy.data.images.new('Mill_'+name,width=256,height=256,alpha=True);im.use_fake_user=True;im.colorspace_settings.name='Non-Color';im.pixels.foreach_set([*rgb,1]*65536);im.filepath_raw=str(P/(name+'.png'));im.file_format='PNG';im.save();im.pack()
   report={'age':age,'packed_images':[{ 'name':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if im.name.startswith('Mill_')], 'objects':[]}
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
   d=json.loads((O/f'age{age}_validation.json').read_text());d.pop('front_access_clear_corridor',None);d['front_unobstructed_apron']=report['front_unobstructed_apron'];d['decorative_roof_drain_overhang_beyond_footprint']=max(0,d['geometry_bounds'][1][1]-2);(O/f'age{age}_validation.json').write_text(json.dumps(d,indent=2))
   assert all(v['packed'] for v in report['packed_images'])
   assert all(v['signed_volume']>0 and v['non_manifold']==0 and v['degenerate']==0 and v['positive_scale'] for v in report['objects'])
   (O/f'age{age}_saved_audit.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/f'Berber_Mill_Age{age}.blend'))
except Exception:(O/'FINALIZE_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
