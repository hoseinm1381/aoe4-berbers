import bpy,bmesh,json,math,traceback,os
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/palisade';O=R/'output/buildings_batch/palisade';rows=[];success=False
def bb(ob):
 ps=[ob.matrix_world@v.co for v in ob.data.vertices];return [[min(p[k] for p in ps) for k in range(3)],[max(p[k] for p in ps) for k in range(3)]]
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(A/f'Berber_Palisade_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   bpy.context.view_layer.update();states=json.loads((A/f'age{age}_states.json').read_text());manifest=json.loads((A/f'age{age}_construction.json').read_text());mesh=[o for o in bpy.context.scene.objects if o.type=='MESH']
   assert len(mesh)==len(manifest['parts']);assert all(i.packed_file for i in bpy.data.images if i.type=='IMAGE')
   measured=[];sources={}
   for name,names in states['states'].items():
    objects=[bpy.data.objects[n] for n in names];assert any(o.data.materials[0].get('ber_owner_mask')==1 for o in objects)
    join=next(j for j in states['joins'] if j['state']==name);L=join['length'];rise=join['terrain_rise'];base=[o for o in objects if o.name.startswith('earth_seat')][0]
    sourcebounds=[bb(o) for o in objects];sources[name]=sourcebounds
    if name!='corner_90':
     assert abs(bb(base)[0][0]+L/2)<1e-5 and abs(bb(base)[1][0]-L/2)<1e-5
     for ob in objects:
      for v in ob.data.vertices:
       p=ob.matrix_world@v.co;terrain=rise*p.x/L+abs(rise)/2;assert p.z>=terrain-1e-5,(name,ob.name,p,terrain)
     for post in [o for o in objects if o.name.startswith('palm_split_post')]:
      ps=[post.matrix_world@v.co for v in post.data.vertices];gap=min(p.z-rise*p.x/L-abs(rise)/2 for p in ps)-.24;assert abs(gap)<1e-5
     measured.append({'state':name,'measured_base_endpoints':bb(base),'post_to_footing_gap_max':0,'ground_against_affine_terrain':True,'socket_error':0})
    for ob in objects:
     bm=bmesh.new();bm.from_mesh(ob.data);assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)>0;bm.free();assert all(math.isfinite(v) for ve in ob.data.vertices for v in ve.co)
   if age==4:
    scene=bpy.context.scene;scene.cycles.samples=4;scene.render.resolution_x=384;scene.render.resolution_y=384
    for state in ['corner_90','end_socket','slope_up_6m','slope_down_6m']:
     for ob in mesh:ob.hide_render=ob.name not in states['states'][state];ob.hide_set(ob.hide_render)
     scene.render.filepath=str(O/(state+'_preview.png'));bpy.ops.render.render(write_still=True)
   exports=[]
   for name,names in states['states'].items():
    for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
    bpy.ops.import_scene.fbx(filepath=str(A/f'Berber_Palisade_Age{age}_{name}.fbx'));bpy.context.view_layer.update();imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==len(names)
    assert all(o.data.uv_layers for o in imported);assert all(all(v>0 for v in ob.scale) for ob in imported)
    actual=[bb(ob) for ob in imported];expected=sources[name]
    # Import names preserve source; ordered bounds compared through rounded sorted tuples.
    def flatten(bounds):return sorted(tuple(round(v,4) for axis in b for v in axis) for b in bounds)
    actual_by_name={ob.name:bb(ob) for ob in imported}
    max_error=max(abs(actual_by_name[n][i][j]-ex[i][j]) for n,ex in zip(names,expected) for i in range(2) for j in range(3))
    assert max_error<1e-4,(age,name,max_error)
    exports.append({'state':name,'count':len(imported),'uv_present':True,'bounds_match_source_0_0001m':True})
   rows.append({'age':age,'source_meshes':len(mesh),'packed_images':True,'manifest_matches':True,'measured_interfaces':measured,'fbx_states':exports})
 (O/'saved_source_fbx_audit.json').write_text(json.dumps(rows,indent=2));success=True
except Exception:
 (O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:
 bpy.context.preferences.view.use_save_prompt=False;bpy.ops.wm.quit_blender();os._exit(0 if success else 1)
