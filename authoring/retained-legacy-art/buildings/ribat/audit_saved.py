import bpy,json,traceback
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/ribat';O=R/'output/buildings_batch/ribat';records=[]
try:
 for age in [2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Ribat_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];imgs=[i for i in bpy.data.images if i.name.startswith('Ribat_')];pattern=bpy.data.images.get('Ribat_pattern');bad=0;ownerloops=0;neutral=0
   for o in meshes:
    owner=o.data.materials[0].get('ber_owner_mask');uv=o.data.uv_layers.active
    for p in o.data.polygons:
     for li in p.loop_indices:
      u,v=uv.data[li].uv;x=min(255,int(u*256));y=min(255,int(v*256));rgb=pattern.pixels[(y*256+x)*4:(y*256+x)*4+3];bad+=int(abs(rgb[0]-owner)>.01 or rgb[1]>.01 or rgb[2]>.01);ownerloops+=int(owner==1);neutral+=int(owner==0)
   def edge(name,side,axis):
    ob=bpy.data.objects[name];pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];return (min if side==0 else max)(p[axis] for p in pts)
   joins={'council_to_right_cell_roof_x':edge('cells_flat_roof_2.6',0,0)-edge('council_roof',1,0),'left_cell_to_council_roof_x':edge('council_roof',0,0)-edge('cells_flat_roof_-2.6',1,0)}
   assert all(abs(v)<1e-5 for v in joins.values()),joins
   rec={'age':age,'roof_join_signed_gaps':joins,'tower_stripe_surface_standoff':.001,'standoff_note':'intentional source paint face separation to avoid coplanar flicker','packed_images':{i.name:bool(i.packed_file) for i in imgs},'owner_uv_samples':ownerloops,'neutral_uv_samples':neutral,'incorrect_pattern_samples':bad,'all_stage_properties':all('garrison_building_first_stage' in o for o in meshes),'fbx_bytes':(A/f'Berber_Ribat_Age{age}.fbx').stat().st_size}
   assert len(imgs)==5 and all(rec['packed_images'].values()) and rec['all_stage_properties'] and rec['fbx_bytes']>10000 and bad==0 and ownerloops>0 and neutral>0,rec
   records.append(rec)
 (O/'saved_source_audit.json').write_text(json.dumps(records,indent=2));print('RIBAT_SAVED_AUDIT_PASS',flush=True)
except Exception:
 (O/'SOURCE_AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
