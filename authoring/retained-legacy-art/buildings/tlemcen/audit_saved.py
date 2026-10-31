import bpy,bmesh,math,json,traceback
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/tlemcen';O=R/'output/buildings_batch/tlemcen';records=[]
try:
 for age in [3,4]:
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Tlemcen_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];imgs=[i for i in bpy.data.images if i.name.startswith('Tlemcen_')];pattern=bpy.data.images.get('Tlemcen_pattern');bad=0;ownerloops=0;neutral=0
   for o in meshes:
    owner=o.data.materials[0].get('ber_owner_mask');uv=o.data.uv_layers.active
    for p in o.data.polygons:
     for li in p.loop_indices:
      u,v=uv.data[li].uv;x=min(255,int(u*256));y=min(255,int(v*256));rgb=pattern.pixels[(y*256+x)*4:(y*256+x)*4+3];bad+=int(abs(rgb[0]-owner)>.01 or rgb[1]>.01 or rgb[2]>.01);ownerloops+=int(owner==1);neutral+=int(owner==0)
   def edge(name,side,axis):
    ob=bpy.data.objects[name];pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];return (min if side==0 else max)(p[axis] for p in pts)
   bpy.context.view_layer.update();validation=json.loads((O/f'age{age}_validation.json').read_text())
   for metric in validation['objects']:
    ob=bpy.data.objects[metric['object']];bm=bmesh.new();bm.from_mesh(ob.data)
    metric['signed_volume']=bm.calc_volume(signed=True);metric['non_manifold_edges']=sum(not e.is_manifold for e in bm.edges);metric['degenerate_faces']=sum(f.calc_area()<1e-10 for f in bm.faces);metric['finite_geometry']=all(math.isfinite(t) for v in ob.data.vertices for t in v.co);metric['positive_transform']=ob.matrix_world.determinant()>0;bm.free()
    assert metric['signed_volume']>0 and metric['non_manifold_edges']==0 and metric['degenerate_faces']==0 and metric['finite_geometry'] and metric['positive_transform'],metric
   for c in validation['contacts']:
    c['signed_gap']=edge(c['child'],0,c['axis'])-edge(c['parent'],1,c['axis']);c['pass']=abs(c['signed_gap']-c['expected'])<1e-5;assert c['pass'],c
   pts=[ob.matrix_world@Vector(v) for ob in meshes for v in ob.bound_box];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)];validation['mesh_bounds']=[lo,hi];assert lo[0]>=-4 and lo[1]>=-4 and hi[0]<=4 and hi[1]<=4 and abs(lo[2])<1e-6
   validation['saved_geometry_rechecked_after_roof_repair']=True;(O/f'age{age}_validation.json').write_text(json.dumps(validation,indent=2))
   joins={f'{side}_gallery_to_hall_roof':edge('gallery_roof_'+side,1,1)-edge('prayer_hall_flat_roof',0,1) for side in ['-2.65','2.65']}
   assert all(abs(v)<1e-5 for v in joins.values()),joins
   front_joins={side:edge('gallery_roof_'+side,0,1)-edge('entry_enclosure',0,1) for side in ['-2.65','2.65']}
   assert all(abs(v)<1e-5 for v in front_joins.values()),front_joins
   courtyard_clear=not bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((0,-1.4,.3)),Vector((0,0,1)),distance=15)[0]
   assert courtyard_clear
   rec={'age':age,'roof_join_overlap':joins,'paint_standoff':{'portal':.001,'minaret':.001},'courtyard_vertical_void':courtyard_clear,'packed_images':{i.name:bool(i.packed_file) for i in imgs},'owner_uv_samples':ownerloops,'neutral_uv_samples':neutral,'incorrect_pattern_samples':bad,'all_stage_properties':all('garrison_building_first_stage' in o for o in meshes),'fbx_bytes':(A/f'Berber_Tlemcen_Age{age}.fbx').stat().st_size,'interior_cutaway_is_preview_only':all(not o.hide_render for o in meshes)}
   assert len(imgs)==5 and all(rec['packed_images'].values()) and rec['all_stage_properties'] and rec['fbx_bytes']>10000 and bad==0 and ownerloops>0 and neutral>0 and rec['interior_cutaway_is_preview_only'],rec
   rec['front_roof_enclosure_signed_gaps']=front_joins;records.append(rec)
 (O/'saved_source_audit.json').write_text(json.dumps(records,indent=2));print('TLEMCEN_SAVED_AUDIT_PASS',flush=True)
 bpy.ops.wm.open_mainfile(filepath=str(A/'UNTouched_Malian_Landmark2a_Reference.blend'))
 with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
  objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];pts=[o.matrix_world@Vector(v) for o in objs for v in o.bound_box];lo=Vector([min(p[k] for p in pts) for k in range(3)]);hi=Vector([max(p[k] for p in pts) for k in range(3)]);target=(lo+hi)/2;size=max(hi-lo)
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=2;sc.render.resolution_x=384;sc.render.resolution_y=384
  bpy.ops.object.camera_add(location=target+Vector((size,-size,size)));cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.6;sc.camera=cam
  bpy.ops.object.light_add(type='AREA',location=target+Vector((-size,-size,size*2)));bpy.context.object.data.energy=2000;bpy.context.object.data.size=size
  sc.world=bpy.data.worlds.new('Donor inspection world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[1].default_value=.7
  sc.render.filepath=str(O/'stock_reference_geometry.png');bpy.ops.render.render(write_still=True)
except Exception:
 (O/'SOURCE_AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()

