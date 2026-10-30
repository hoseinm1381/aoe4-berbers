import bpy,bmesh,json,math,traceback,os
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/outpost';O=R/'output/buildings_batch/outpost';rows=[];success=False

def bounds(o):
 ps=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in ps) for k in range(3)],[max(v[k] for v in ps) for k in range(3)]]
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Outpost_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   bpy.context.view_layer.update();mesh=[o for o in bpy.context.scene.objects if o.type=='MESH'];states=json.loads((A/f'age{age}_states.json').read_text());manifest=json.loads((A/f'age{age}_construction.json').read_text())
   assert len(mesh)==len(manifest['parts']),(len(mesh),len(manifest['parts']))
   assert all(im.packed_file for im in bpy.data.images if im.type=='IMAGE')
   owners=[o.name for o in mesh if o.data.materials[0].get('ber_owner_mask')==1];assert owners
   for o in mesh:
    assert all(math.isfinite(v) for ve in o.data.vertices for v in ve.co)
    bm=bmesh.new();bm.from_mesh(o.data);assert bm.calc_volume(signed=True)>0 and all(e.is_manifold for e in bm.edges);bm.free()
   sourcechecks=[]
   for name in ['south_thick_wall','fortified_stone_face']:
    for o in mesh:
     if o.name.startswith(name) and o.location.y<0:
      inv=o.matrix_world.inverted();hit=o.ray_cast(inv@Vector((0,-2,.95)),Vector((0,1,0)))[0];assert not hit;sourcechecks.append({'object':o.name,'door_void_clear':True})
   posts=[o for o in mesh if o.name.startswith('lookout_cedar_post')];can=bpy.data.objects['fitted_flat_canopy'];roof=bpy.data.objects['lookout_floor']
   for post in posts:
    assert abs(bounds(post)[0][2]-bounds(roof)[1][2])<1e-5
    assert abs(bounds(can)[0][2]-bounds(post)[1][2])<1e-5
   for prefix in ['springald_stock_runner','cannon_ground_skid','arrow_cover_frame','arrow_shield_panel']:
    for o in mesh:
     if o.name.startswith(prefix):
      gap=bounds(o)[0][2]-bounds(roof)[1][2];assert abs(gap)<1e-5
      sourcechecks.append({'child':o.name,'parent':'lookout_floor','measured_signed_gap':gap,'pass':True})
   for o in [o for o in mesh if o.name.startswith('canopy_long_beam')]:
    gap=bounds(can)[0][2]-bounds(o)[1][2];assert abs(gap)<1e-5
    sourcechecks.append({'child':'fitted_flat_canopy','parent':o.name,'measured_signed_gap':gap,'pass':True})
   front=[o for o in mesh if o.name.startswith('lookout_parapet_front')]
   if age==4:
    barrel=bpy.data.objects['cannon_hollow_barrel'];bb=bounds(barrel);assert bb[0][0]>-.5 and bb[1][0]<.5
    marker=bpy.data.objects['fx_muz_cannon_00'];assert abs(marker.location.y-bb[0][1])<1e-5 and abs(marker.location.z-barrel.data.vertices[0].co.z)<1e-5
    sourcechecks.append({'cannon_forward_embrasure_width':1.0,'barrel_max_width':bb[1][0]-bb[0][0],'clearance_each_side':(.5-(bb[1][0]-bb[0][0])/2),'muzzle_marker_fitted':True})
   exports=[]
   for name,names in states['states'].items():
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Outpost_Age{age}_{name}.fbx'));bpy.context.view_layer.update();imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==len(names),(age,name,len(imported),len(names))
    assert all(o.data.uv_layers for o in imported)
    assert all(bounds(o)[0][2]>=-.0001 for o in imported)
    assert all(bounds(o)[0][0]>=-2.001 and bounds(o)[1][0]<=2.001 and bounds(o)[0][1]>=-2.001 and bounds(o)[1][1]<=2.001 for o in imported)
    exports.append({'state':name,'fbx_mesh_count':len(imported),'uv_present':True,'ground_and_footprint':True})
   rows.append({'age':age,'packed_images':True,'source_mesh_count':len(mesh),'stage_manifest_matches':True,'owner_objects':owners,'measured_interfaces':sourcechecks,'fbx_states':exports})
 (O/'saved_source_fbx_audit.json').write_text(json.dumps(rows,indent=2));success=True
except Exception:
 (O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender();os._exit(0 if success else 1)
