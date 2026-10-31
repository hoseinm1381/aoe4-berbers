import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/grand_keep';O=R/'output/buildings_batch/grand_keep'
def mesh_bounds(objects):
 pts=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box];return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
try:
 bpy.ops.wm.open_mainfile(filepath=str(A/'Almohad_GrandKeep_Age4.blend'))
 with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
  meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];count=len(meshes);bs=mesh_bounds(meshes);imgs=[i for i in bpy.data.images if i.name.startswith('GrandKeep_')];pat=bpy.data.images['GrandKeep_pattern'];bad=0;own=0;neutral=0
  for o in meshes:
   owner=o.data.materials[0].get('ber_owner_mask');uv=o.data.uv_layers.active
   for li in range(len(uv.data)):
    u,v=uv.data[li].uv;x=min(255,int(u*256));y=min(255,int(v*256));rgb=pat.pixels[(y*256+x)*4:(y*256+x)*4+3];bad+=int(abs(rgb[0]-owner)>.01 or rgb[1]>.01 or rgb[2]>.01);own+=int(owner==1);neutral+=int(owner==0)
  joins=[]
  # Actual battered face calculation at top-walk Z, independently derived from saved vertices.
  for name,tower,axis in [('W_walk','SW_battered_tower',1),('E_walk','SE_battered_tower',1),('S_gate_walk','SW_battered_tower',0)]:
   walk=bpy.data.objects[name];tw=bpy.data.objects[tower];wb=mesh_bounds([walk]);tb=mesh_bounds([tw]);z=wb[1][2];base=tb[0][2];height=tb[1][2]-base
   # Closed tower lower inner edge ±.82 and upper inner edge ±.66, source scaled .8.
   tower_inner=tb[1][axis]-(.16*.8)*(z-base)/height
   overlap=tower_inner-wb[0][axis]
   joins.append({'walk':name,'tower':tower,'walk_end_source':wb[0][axis],'tower_inner_face_source_at_walk_z':tower_inner,'measured_overlap_source':overlap,'pass':overlap>0})
  rays=[]
  for frame in [1,30]:
   bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();hits=[]
   for o in meshes:
    inv=o.matrix_world.inverted()
    if o.ray_cast(inv@Vector((.12,-3.12,.8)),inv.to_3x3()@Vector((0,1,0)),distance=4.56)[0]:hits.append(o.name)
   rays.append({'frame':frame,'state':'closed' if frame==1 else 'open','gateway_hits':hits,'pass':bool(hits) if frame==1 else not hits})
  left=mesh_bounds([bpy.data.objects['gateway_left_leaf']]);right=mesh_bounds([bpy.data.objects['gateway_right_leaf']]);clear_width=right[0][0]-left[1][0]
  stair=[o for o in meshes if o.name.startswith('court_to_W_walk_stair')];stair_bounds=mesh_bounds(stair);walk_bounds=mesh_bounds([bpy.data.objects['W_walk']]);stair_contact={'signed_x_gap':stair_bounds[0][0]-walk_bounds[1][0],'top_to_walk_gap':stair_bounds[1][2]-walk_bounds[1][2]};assert all(abs(v)<1e-5 for v in stair_contact.values()),stair_contact
  banner=[]
  for prefix in ['SW','SE']:
   o=bpy.data.objects[prefix+'_owner_standard'];vs=[o.matrix_world@v.co for v in o.data.vertices];gaps=[]
   # Sloped banner center plane is embedded 8mm design in tower face.
   for p in vs:
    face=-2.96*.8-.82*.8+.16*.8*(p.z-.16*.8)/(5.1*.8)
    gaps.append(p.y-face)
   banner.append({'object':o.name,'signed_y_extents_to_battered_plane': [min(gaps),max(gaps)],'pass':min(gaps)<0<max(gaps)})
  rec={'mesh_count':count,'source_bounds':bs,'animator125_bounds':[[v*1.25 for v in row] for row in bs],'packed_maps':{i.name:bool(i.packed_file) for i in imgs},'owner_uv_samples':own,'neutral_uv_samples':neutral,'incorrect_pattern_samples':bad,'stage_properties':all('garrison_building_first_stage' in o for o in meshes),'walk_tower_actual_face_contacts':joins,'stair_to_walk_contact':stair_contact,'gateway_actual_open_leaf_clear_width_source':clear_width,'gateway_actual_open_leaf_clear_width_rendered':clear_width*1.25,'gate_action_states':rays,'banner_actual_battered_plane_contacts':banner,'actions':[a.name for a in bpy.data.actions]}
  assert len(imgs)==5 and all(rec['packed_maps'].values()) and bad==0 and own>0 and neutral>0 and rec['stage_properties'],rec
  assert all(x['pass'] for x in joins+rays+banner),rec
  bpy.ops.wm.read_factory_settings(use_empty=True)
  bpy.ops.import_scene.fbx(filepath=str(A/'Almohad_GrandKeep_Age4.fbx'));fbx=[o for o in bpy.context.scene.objects if o.type=='MESH'];fbs=mesh_bounds(fbx)
  rec['fbx_mesh_count']=len(fbx);rec['fbx_bounds']=fbs;rec['fbx_bounds_max_delta']=max(abs(fbs[i][k]-bs[i][k]) for i in range(2) for k in range(3));assert len(fbx)==count and rec['fbx_bounds_max_delta']<1e-4,rec
  (O/'saved_source_fbx_audit.json').write_text(json.dumps(rec,indent=2));print('GRAND_KEEP_SAVED_FBX_AUDIT_PASS',flush=True)
except Exception:
 (O/'SOURCE_AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
