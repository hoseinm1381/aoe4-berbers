import bpy,json,traceback
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/funduq';O=R/'output/buildings_batch/funduq';records=[]
try:
 for age in [2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Funduq_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];imgs=[i for i in bpy.data.images if i.name.startswith('Funduq_')];pattern=bpy.data.images.get('Funduq_pattern');bad=0;ownerloops=0;neutral=0
   for o in meshes:
    owner=o.data.materials[0].get('ber_owner_mask');uv=o.data.uv_layers.active
    for p in o.data.polygons:
     for li in p.loop_indices:
      u,v=uv.data[li].uv;x=min(255,int(u*256));y=min(255,int(v*256));rgb=pattern.pixels[(y*256+x)*4:(y*256+x)*4+3];bad+=int(abs(rgb[0]-owner)>.01 or rgb[1]>.01 or rgb[2]>.01);ownerloops+=int(owner==1);neutral+=int(owner==0)
   def edge(name,side,axis):
    ob=bpy.data.objects[name];pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];return (min if side==0 else max)(p[axis] for p in pts)
   joins={'north_to_east_roof':edge('east_roof',0,0)-edge('north_roof',1,0),'west_to_south_roof':edge('south_roof',0,0)-edge('west_roof',1,0)}
   route=[]
   for z in [.46,2.55]:
    hits=[]
    for o in meshes:
     inv=o.matrix_world.inverted()
     if o.ray_cast(inv@Vector((0,-4,z)),inv.to_3x3()@Vector((0,1,0)),distance=4.8)[0]:hits.append(o.name)
    route.append({'centerline_z':z,'from_y':-4,'to_y':.8,'hit_objects':hits,'pass':not hits})
   rec={'age':age,'roof_join_signed_gaps':joins,'gateway_whole_model_rays':route,'gateway_base_clear_width':1.806,'arch_nominal_height':2.82,'shutter_recess_back_x_abs':3.56,'shutter_front_x_abs':3.62,'outer_facade_x_abs':3.68,'shutter_front_recess':.06,'awning_post_to_beam_intentional_overlap':.05,'packed_images':{i.name:bool(i.packed_file) for i in imgs},'owner_uv_samples':ownerloops,'neutral_uv_samples':neutral,'incorrect_pattern_samples':bad,'all_stage_properties':all('garrison_building_first_stage' in o for o in meshes),'fbx_bytes':(A/f'Berber_Funduq_Age{age}.fbx').stat().st_size}
   assert all(abs(v)<1e-5 for v in joins.values()) and all(x['pass'] for x in route),rec
   assert len(imgs)==5 and all(rec['packed_images'].values()) and rec['all_stage_properties'] and rec['fbx_bytes']>10000 and bad==0 and ownerloops>0 and neutral>0,rec
   records.append(rec)
 (O/'saved_source_audit.json').write_text(json.dumps(records,indent=2));print('FUNDUQ_SAVED_AUDIT_PASS',flush=True)
except Exception:
 (O/'SOURCE_AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
