import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/barracks';O=R/'output/buildings_batch/barracks';report=[]
def bb(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]]
try:
 for age in [1,2,3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Barracks_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   bpy.context.view_layer.update();objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];contacts=[]
   for o in objs:
    if o.name.startswith('shed_post'):
     assert abs(bb(o)[0][2]-.17)<1e-5
     beam=next(b for b in objs if b.name.startswith('shed_crossbeam') and abs(b.location.y-o.location.y)<.01)
     gap=bb(beam)[0][2]-bb(o)[1][2];assert abs(gap+.10)<1e-5;contacts.append({'part':o.name,'contact':'shed beam over post','measured_overlap':-gap})
   boundary=bb(bpy.data.objects['court_side_wall']);armoury=bb(bpy.data.objects['west_armoury']);join_gap=armoury[0][1]-boundary[1][1];assert abs(join_gap)<1e-5
   gateway=bpy.data.objects['gateway_arch'];cap=bpy.data.objects['entry_cap'];assert abs(bb(cap)[0][2]-bb(gateway)[1][2])<1e-5
   clear=[o for o in objs if bb(o)[0][0]<.69999 and bb(o)[1][0]>-.69999 and bb(o)[0][1]<-1.0 and bb(o)[1][1]>-3 and bb(o)[0][2]<1.7 and bb(o)[1][2]>.2]
   assert not clear,[o.name for o in clear]
   assert all(im.packed_file for im in bpy.data.images if im.type=='IMAGE')
   saved_count=len(objs);stage_count=len(json.loads((A/f'age{age}_construction.json').read_text())['parts']);assert stage_count==saved_count
   assert all(m.get('ber_owner_mask') in [0,1] for m in bpy.data.materials if m.name.startswith('BerberBarracks'))
   bpy.ops.wm.read_factory_settings(use_empty=True)
   with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Barracks_Age{age}.fbx'))
   imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==saved_count;assert all(o.data.uv_layers for o in imported)
   report.append({'age':age,'saved_meshes':saved_count,'fbx_meshes':len(imported),'packed_images':True,'manifest_matches_meshes':True,'measured_shed_contacts':contacts,'entry_cap_contact':True,'unblocked_entry_lane':True,'west_boundary_armoury_join_gap':join_gap})
 (O/'saved_source_fbx_audit.json').write_text(json.dumps(report,indent=2))
except Exception:(O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):bpy.ops.wm.quit_blender()

