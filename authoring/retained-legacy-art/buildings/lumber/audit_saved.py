"""Reopen final sources, audit packed textures, preserve optional resource attachment states."""
import bpy,bmesh,json,math,traceback
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;O=P.parents[2]/'output/buildings_batch/lumber'
try:
 for age in range(1,5):
  bpy.ops.wm.open_mainfile(filepath=str(P/f'Berber_Lumber_Age{age}.blend'))
  with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
   report={'age':age,'packed_images':[{'name':im.name,'packed':bool(im.packed_file)} for im in bpy.data.images if im.name.startswith('Lumber_')],'objects':[]}
   for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True);nm=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free()
    report['objects'].append({'name':o.name,'signed_volume':vol,'non_manifold':nm,'degenerate':deg,'positive_scale':all(v>0 for v in o.scale),'first_stage':o['garrison_building_first_stage']})
   assert all(v['packed'] for v in report['packed_images'])
   assert len(report['packed_images'])==5
   assert all(v['signed_volume']>0 and v['non_manifold']==0 and v['degenerate']==0 and v['positive_scale'] for v in report['objects'])
   bpy.context.view_layer.update()
   def bb(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
   d=json.loads((O/f'age{age}_validation.json').read_text())
   left=max(bb(o)[1][0] for o in bpy.context.scene.objects if o.name.startswith('sawpit_cross_bearer'))
   right=min(bb(o)[0][0] for o in bpy.context.scene.objects if o.name.startswith(('stack_dunnage','stack_retaining_post','sorted_timber')))
   d['pit_sorting_corridor']={'x':[left,right],'minimum_width':right-left,'scope':'measured visual passage only; native drop-off/pathing pending'}
   assert right-left>.5
   for post in [o for o in bpy.context.scene.objects if o.name.startswith('shelter_post')]:
    pad=min([o for o in bpy.context.scene.objects if o.name.startswith('post_stone_pad')],key=lambda o:(o.location-post.location).xy.length)
    gap=bb(post)[0][2]-bb(pad)[1][2];d['contacts'].append({'interface':post.name+' to '+pad.name,'signed_gap':gap,'expected':0,'pass':abs(gap)<1e-5});assert abs(gap)<1e-5
   bottom=min(bb(o)[0][2] for o in bpy.context.scene.objects if o.name.startswith('sorted_timber'))
   top=bb(bpy.data.objects['stack_dunnage'])[1][2];assert abs(bottom-top)<1e-5
   d['contacts'].append({'interface':'lowest timber row to dunnage','signed_gap':bottom-top,'expected':0,'pass':True})
   (O/f'age{age}_validation.json').write_text(json.dumps(d,indent=2))
   # Stock parent has a distinct resource attachment tier. Keep authored stock props modular.
   stock=bpy.data.collections.new('BER_Lumber_ResourceStock_Optional');bpy.context.scene.collection.children.link(stock)
   static=bpy.data.collections.new('BER_Lumber_Structure');bpy.context.scene.collection.children.link(static)
   resource=[];base=[]
   for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    is_resource=o.name.startswith('sorted_timber') or (o.name.startswith('sawn_endgrain.') and int(o.name.split('.')[-1])>=2)
    for c in list(o.users_collection):c.objects.unlink(o)
    (stock if is_resource else static).objects.link(o)
    o['ber_attachment_state']='resource_stocked' if is_resource else 'structure'
    (resource if is_resource else base).append(o.name)
   (P/f'age{age}_modular_states.json').write_text(json.dumps({'age':age,'stock_official_tier_attachments':['tier1_econ_wood_control_eng','resource'],'source_states':{'empty':base,'stocked':base+resource},'optional_collection':stock.name,'resource_objects':resource,'integration':'authored visibility sets; preserve official attachment selector and stock action semantics during integration; native binding pending'},indent=2))
   # Empty yard export is available without deleting source stock geometry.
   bpy.ops.object.select_all(action='DESELECT')
   for name in base:bpy.data.objects[name].select_set(True)
   bpy.context.view_layer.objects.active=bpy.data.objects[base[0]]
   bpy.ops.export_scene.fbx(filepath=str(P/f'Berber_Lumber_Age{age}_ResourceEmpty.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
   report['resource_state_objects']=len(resource)
   (O/f'age{age}_saved_audit.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/f'Berber_Lumber_Age{age}.blend'))
except Exception:(O/'AUDIT_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
