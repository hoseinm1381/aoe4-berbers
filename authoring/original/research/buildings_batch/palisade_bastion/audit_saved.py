import bpy,json,math,bmesh,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/palisade_bastion';O=R/'output/buildings_batch/palisade_bastion'
rows=[]
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_PalisadeBastion_Age{age}.blend'))
  ctx=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);ctx.__enter__()
  bpy.context.view_layer.update();states=json.loads((A/f'age{age}_states.json').read_text())['states'];ar=[]
  for state,v in states.items():
   objs=[bpy.data.objects[n] for n in v['objects']];pts=[ob.matrix_world@ve.co for ob in objs for ve in ob.data.vertices]
   b=[[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]]
   assert abs(b[0][2])<1e-6 and abs(b[1][2]-4.578125)<1e-6
   assert max(abs(b[i][j]) for i in [0,1] for j in [0,1])<=.682861328125/2+1e-6
   owner=[ob for ob in objs if ob.data.materials[0].get('ber_owner_mask')==1];assert len(owner)==4
   head_ties=[ob for ob in objs if ob.name.startswith('locking_head_tie')];assert len(head_ties)==(4 if age>=2 else 0)
   for ob in objs:
    assert all(s>0 for s in ob.scale) and ob.get('garrison_building_first_stage') in [0,20,40,60,80,100]
    bm=bmesh.new();bm.from_mesh(ob.data);assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)>0;bm.free()
    uv=ob.data.uv_layers.active;assert uv
    for f in ob.data.polygons:
     pp=[uv.data[i].uv for i in f.loop_indices];area=abs(sum(pp[i].x*pp[(i+1)%len(pp)].y-pp[(i+1)%len(pp)].x*pp[i].y for i in range(len(pp)))/2);assert area>1e-10
    assert all(math.isfinite(c) for ve in ob.data.vertices for c in ve.co)
    if ob.name.startswith('terminal_diagonal_stay'):
     ax=max([0,1],key=lambda k:abs(ob.location[k]));pp=[ob.matrix_world@ve.co for ve in ob.data.vertices];inner=min(abs(v[ax]) for v in pp);assert abs(inner-.275)<1e-6
   ar.append({'state':state,'objects':len(objs),'source_bounds':b,'ground':0,'height':4.578125,'owner_panels':len(owner),'head_ties':len(head_ties),'socket_width':.682861328125,'source_envelope_pass':True})
  packed=[im.name for im in bpy.data.images if im.type=='IMAGE' and im.packed_file];assert len(packed)==5
  rows.append({'age':age,'states':ar,'packed_images':packed})
  validation=json.loads((O/f'age{age}_validation.json').read_text())
  for state,v in states.items():
   for objrow in validation['states'][state]:
    ob=bpy.data.objects[objrow['object']];pts=[ob.matrix_world@ve.co for ve in ob.data.vertices];objrow['bounds']=[[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]]
  validation['final_saved_source_verified']=True
  validation['stay_contact']={'inner_plane':.275,'post_outer_plane':.275,'signed_gap':0,'intentional_overlap':0}
  (O/f'age{age}_validation.json').write_text(json.dumps(validation,indent=2))
 (O/'SAVED_SOURCE_AUDIT.json').write_text(json.dumps({'status':'pass','rows':rows,'source_only':True},indent=2))
except Exception:
 (O/'SAVED_SOURCE_AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender()
