import bpy,json,math,bmesh,traceback,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/farm';O=R/'output/buildings_batch/farm'
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Farm_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   def bounds(ob):
    p=[ob.matrix_world@Vector(v) for v in ob.bound_box];return [[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]
   bpy.context.view_layer.update();allmesh=[o for o in bpy.context.scene.objects if o.type=='MESH'];crops=[o for o in allmesh if o.name.startswith('cereal_connected')];base=[o for o in allmesh if o not in crops]
   if age>=3:bpy.data.objects['crossing_plank'].location.z=.16
   bpy.context.view_layer.update()
   contacts=[]
   for o in allmesh:
    if o.name.startswith(('raised_bed','shade_post','low_side','south_edge')):contacts.append({'child':o.name,'parent':'flat_earth_plot','signed_z_gap':bounds(o)[0][2]-.05,'expected':0})
   contacts.append({'child':'woven_tool_shade','parent':'shade_crossbeam','signed_z_gap':bounds(bpy.data.objects['woven_tool_shade'])[0][2]-bounds(bpy.data.objects['shade_crossbeam'])[1][2],'expected':0})
   if age>=3:contacts.append({'child':'crossing_plank','parent':'branch_channel_bank','signed_z_gap':bounds(bpy.data.objects['crossing_plank'])[0][2]-bounds(bpy.data.objects['branch_channel_bank'])[1][2],'expected':0})
   for o in allmesh:
    if o.name.startswith('branch_water'):contacts.append({'child':o.name,'parent':'header_channel_water','signed_y_gap':bounds(o)[1][1]-bounds(bpy.data.objects['header_channel_water'])[0][1],'expected':0})
   for c in contacts:c['pass']=abs(c.get('signed_z_gap',c.get('signed_y_gap',999))-c['expected'])<1e-5
   assert all(c['pass'] for c in contacts),contacts
   state={'gatherable':crops};man={};state_checks=[]
   for label,factor,mat in [('untouched',.22,'Farm_green'),('depleted',.10,'Farm_crop')]:
    if mat not in bpy.data.materials:
     mm=crops[0].data.materials[0].copy();mm.name=mat;mm['ber_owner_mask']=0
    col=bpy.data.collections.new('SOURCE_RESOURCE_STATE_'+label);bpy.context.scene.collection.children.link(col);obs=[]
    for source in crops:
     ob=source.copy();ob.data=source.data.copy();ob.name=label+'_'+source.name;col.objects.link(ob)
     for v in ob.data.vertices:v.co.z=.11+(v.co.z-.11)*factor
     if label=='untouched' and age!=2:
      for uv in ob.data.uv_layers.active.data:uv.uv.x+=.25
     if label=='depleted' and age==2:
      for uv in ob.data.uv_layers.active.data:uv.uv.x-=.25
     ob.data.materials.clear();ob.data.materials.append(bpy.data.materials[mat]);ob['resource_state']=label;ob.hide_render=True;ob.hide_set(True);obs.append(ob)
     bm=bmesh.new();bm.from_mesh(ob.data);ck={'state':label,'object':ob.name,'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'outward_volume':bm.calc_volume(signed=True),'degenerate_faces':sum(f.calc_area()<1e-10 for f in bm.faces)};bm.free();assert ck['non_manifold_edges']==0 and ck['outward_volume']>0 and ck['degenerate_faces']==0;state_checks.append(ck)
    state[label]=obs
   for label,obs in state.items():
    for ob in obs:ob['resource_state']=label
    bpy.ops.object.select_all(action='DESELECT')
    for ob in base+obs:ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.export_scene.fbx(filepath=str(A/f'Berber_Farm_Age{age}_{label}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    if label=='gatherable':shutil.copyfile(A/f'Berber_Farm_Age{age}_{label}.fbx',A/f'Berber_Farm_Age{age}.fbx')
    if label!='gatherable':
     for ob in obs:ob.hide_set(True)
    man[label]={'objects':[o.name for o in obs],'fbx':f'Berber_Farm_Age{age}_{label}.fbx','integration':'source static state alternative only; native growing/gathered selectors pending'}
   (A/f'age{age}_resource_states.json').write_text(json.dumps(man,indent=2))
   d=json.loads((O/f'age{age}_validation.json').read_text());d['measured_contacts']=contacts;d['resource_state_geometry_checks']=state_checks;d['packed_images']=all(im.packed_file for im in bpy.data.images if im.name.startswith('Farm_'));d['resource_states_source']=['untouched','gatherable','depleted'];assert d['packed_images'];(O/f'age{age}_validation.json').write_text(json.dumps(d,indent=2))
   bpy.ops.wm.save_as_mainfile(filepath=str(A/f'Berber_Farm_Age{age}.blend'))
except Exception:
 (O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
