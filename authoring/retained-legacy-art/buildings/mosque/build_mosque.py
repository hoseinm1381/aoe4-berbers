"""Original mosque recipe. Only task-owned outputs; no native cook."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import geometry_helpers as g
from geometry_helpers import bpy,bmesh,math,json,traceback,Vector,ART,OUT,RESEARCH,box,prism,contact,bounds

def cut(wall,cx,y,width=1.5,height=2.0,base=.18,rotate=False):
    o=prism('TEMP_void',g.portal_outline(cx,base,width,height),y-.5,y+.5,'shadow',40)
    if rotate:
        o.rotation_euler.z=math.pi/2
    bpy.context.view_layer.objects.active=wall;mod=wall.modifiers.new('Physical hollow horseshoe','BOOLEAN');mod.operation='DIFFERENCE';mod.object=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(o,do_unlink=True);g.PARTS.pop()

def atlas_uv(o):
    # Per-face planar projection with a strict nonzero island; tile overlap is intentional.
    slot=g.MATS[o['ber_material_role']][1];uv=o.data.uv_layers.active
    for p in o.data.polygons:
        axes=sorted(range(3),key=lambda k:abs(p.normal[k]))[:2]
        coords=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices]
        mins=[min(v[a] for v in coords) for a in axes];spans=[max(v[a] for v in coords)-mins[j] for j,a in enumerate(axes)]
        for li,v in zip(p.loop_indices,coords):
            uv.data[li].uv=((slot%4+.08+.84*(v[axes[0]]-mins[0])/max(spans[0],1e-9))/4,(slot//4+.08+.84*(v[axes[1]]-mins[1])/max(spans[1],1e-9))/2)

def setup():
    ctx=g.reset_scene();g.PARTS.clear();g.CONTACTS.clear();g.MATS.clear();g.setup_maps()
    for name,col in [('normal',(.5,.5,1)),('roughness',(.85,.85,.85)),('metal',(0,0,0))]:
        im=bpy.data.images.new('Mosque_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
    return ctx

def build(age):
    ctx=setup();wall='earth' if age==3 else 'lime';floor=.18;h=2.55+(age-3)*.15;roof=floor+h
    box('foundation',(0,0,.065),(7.8,7.8,.13),'stone',0)
    box('courtyard_floor',(0,0,.155),(7.4,7.4,.05),'lime',0)
    # A shell around a real prayer room, not a solid room-shaped cube.
    back=box('qibla_wall',(0,3.38,floor+h/2),(7.0,.24,h),wall,40);contact(back.name,'courtyard_floor')
    for x in [-3.38,3.38]:
        n='prayer_side_'+str(x);box(n,(x,2.005,floor+h/2),(.24,2.51,h),wall,40);contact(n,'courtyard_floor')
    arcade=box('prayer_hall_horseshoe_arcade',(0,.62,floor+h/2),(7.0,.26,h),wall,40)
    for x in [-2.25,0,2.25]:cut(arcade,x,.62,1.7,2.10)
    contact(arcade.name,'courtyard_floor')
    box('prayer_hall_roof',(0,2.0,roof+.07),(7.0,3.0,.14),'earth',60);contact('prayer_hall_roof','qibla_wall')
    # A second row of hypostyle posts physically supports roof beams.
    for x in [-2.25,0,2.25]:
        n='hypostyle_post_'+str(x);box(n,(x,2.0,floor+(h-.12)/2),(.25,.25,h-.12),'lime',40);contact(n,'courtyard_floor')
    box('hypostyle_crossbeam',(0,2,roof-.06),(6.52,.24,.12),'cedar',60)
    for x in [-2.25,0,2.25]:contact('hypostyle_crossbeam','hypostyle_post_'+str(x))
    contact('prayer_hall_roof','hypostyle_crossbeam')
    for x in [-3.38,3.38]:
        n='outer_gallery_wall_'+str(x);box(n,(x,-1.315,floor+2.1/2),(.24,3.61,2.1),wall,40);contact(n,'courtyard_floor')
        arc=box('side_gallery_arcade_'+str(x),(x*.68,-1.28,floor+2.1/2),(.23,3.7,2.1),wall,40)
        # Cutter coordinates transform around origin: -y maps to world x.
        for yy in [-2.25,-.35]:cut(arc,yy,-x*.68,1.25,1.7,rotate=True)
        contact(arc.name,'courtyard_floor')
        n='gallery_roof_'+str(x);box(n,(x*.84,-1.225,2.33),(1.33,3.65,.10),'earth',60)
        contact(n,arc.name,expected=0)
        contact(n,'outer_gallery_wall_'+str(x))
        contact('prayer_side_'+str(x),arcade.name,axis=1)
        contact(arcade.name,'outer_gallery_wall_'+str(x),axis=1)
        contact('qibla_wall','prayer_side_'+str(x),axis=1)
        box('owner_gallery_frieze_'+str(x),(x*.68,-1.3,2.20),(.27,3.7,.10),'owner_cloth',100)
    gate=box('entrance_wall',(0,-3.25,floor+2.1/2),(7,.26,2.1),wall,40);cut(gate,0,-3.25,1.8,1.85);contact(gate.name,'courtyard_floor')
    box('entrance_cap',(0,-3.25,2.33),(7.12,.4,.10),'lime',60);contact('entrance_cap',gate.name)
    for x in [-1.7,1.7]:box('owner_entrance_stripe',(x,-3.393,1.75),(1.1,.026,.18),'owner_cloth',100)
    box('entry_threshold',(0,-3.80,.135),(2,.15,.01),'stone',0);contact('entry_threshold','foundation')
    # Square minaret sits on a fitted footing beside the entrance.
    box('minaret_footing',(-2.85,-2.63,.29),(1.25,1.25,.22),'stone',20);contact('minaret_footing','courtyard_floor')
    mh=4.0+.32*(age-3)
    box('square_minaret_shaft',(-2.85,-2.63,.40+mh/2),(1.0,1.0,mh),wall,40);contact('square_minaret_shaft','minaret_footing')
    z=.40+mh
    box('minaret_cornice',(-2.85,-2.63,z+.075),(1.16,1.16,.15),'lime',60);contact('minaret_cornice','square_minaret_shaft')
    lan=box('square_minaret_lantern',(-2.85,-2.63,z+.15+.38),(.66,.66,.76),'earth' if age==3 else 'lime',80);contact(lan.name,'minaret_cornice')
    cut(lan,-2.85,-2.63,.28,.50,base=z+.16)
    box('minaret_flat_lantern_cap',(-2.85,-2.63,z+.15+.76+.055),(.80,.80,.11),'lime',80);contact('minaret_flat_lantern_cap',lan.name)
    # Layered parapets seat on roof, timber drains embed into roof edges.
    for x in [-3.40,3.40]:box('hall_side_parapet',(x,2.0,roof+.26),(.20,3.0,.24),wall,80)
    for y in [.6,3.4]:box('hall_end_parapet',(0,y,roof+.26),(6.6,.20,.24),wall,80)
    for x in [-3.48,3.48]:box('timber_roof_drain',(x,2.80,roof+.03),(.42,.10,.10),'cedar',80)
    # Deliberately visible furniture through the actual arcade. Empty relic slots.
    for i,x in enumerate([1.80,2.30,2.80]):
        box('relic_empty_presentation_shelf_'+str(i),(x,3.17,.70),(.42,.32,.16),'cedar',100)
        box('relic_shelf_bracket_'+str(i),(x,3.27,.48),(.10,.15,.44),'cedar',100)
    for i in range(5):box('minbar_step_'+str(i),(-1.50,2.25+i*.16,floor+.10*(i+1)/2),(.70,.16,.10*(i+1)),'cedar',100)
    box('minbar_rear_platform',(-1.50,3.03,.51),(.70,.30,.66),'cedar',100)
    for x in [-1.90,-1.10]:box('minbar_side_board',(x,2.69,.57),(.10,1.0,.78),'cedar',100)
    for x in [-1.90,-1.10]:box('minbar_upgrade_geometric_panel',(x,2.69,1.04),(.11,1.0,.16),'lime',100).hide_render=True
    for o in bpy.context.scene.objects:
        if 'minbar_upgrade' in o.name:o['ber_visual_state']='minbar_upgrade';o.hide_set(True)
    if age==4:
        for x in [-2.4,-1.8,-1.2,1.2,1.8,2.4]:
            o=box('plaster_geometric_diamond',(x,-3.399,1.17),(.17,.03,.17),'lime',100);o.rotation_euler.y=math.pi/4
        for z0 in [2.55,3.15,3.75]:
            for x in [-3.09,-2.61]:
                o=box('minaret_geometric_diamond',(x,-3.139,z0),(.18,.025,.18),'earth',100);o.rotation_euler.y=math.pi/4
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.context.view_layer.update()
    col=bpy.data.collections.new('BER_Mosque_Age'+str(age));bpy.context.scene.collection.children.link(col)
    checks=[]
    for o in objects:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));vol=bm.calc_volume(signed=True)
        if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));vol=-vol
        non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.to_mesh(o.data);bm.free();atlas_uv(o)
        uv=o.data.uv_layers.active;uvdeg=0
        for p in o.data.polygons:
            pts=[uv.data[i].uv for i in p.loop_indices];uvdeg+=abs(sum(pts[i].x*pts[(i+1)%len(pts)].y-pts[(i+1)%len(pts)].x*pts[i].y for i in range(len(pts)))/2)<1e-10
        checks.append({'object':o.name,'non_manifold':non,'degenerate_faces':deg,'uv_zero_area_faces':uvdeg,'outward_volume':vol,'finite':all(math.isfinite(v) for ve in o.data.vertices for v in ve.co),'positive_scale':all(v>0 for v in o.scale),'bounds':bounds(o),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)})
    assert all(c['non_manifold']==0 and c['degenerate_faces']==0 and c['uv_zero_area_faces']==0 and c['outward_volume']>0 and c['finite'] and c['positive_scale'] for c in checks),checks
    assert all(c['pass'] for c in g.CONTACTS),g.CONTACTS
    assert all(c['bounds'][0][0]>=-4 and c['bounds'][1][0]<=4 and c['bounds'][0][1]>=-4 and c['bounds'][1][1]<=4 and c['bounds'][0][2]>=-1e-6 for c in checks)
    # Ray guards prove openings are real through-wall voids, with no false dark panels.
    guards=[]
    for ob,origin,direction,distance in [(gate,(0,-3.8,.7),(0,1,0),.9),(arcade,(0,.2,.7),(0,1,0),.9)]:
        inv=ob.matrix_world.inverted();hit=ob.ray_cast(inv@Vector(origin),inv.to_3x3()@Vector(direction),distance=distance)[0];guards.append({'wall':ob.name,'opening_ray_hit':hit,'pass':not hit})
    for x in [-3.38,3.38]:
        ob=bpy.data.objects['side_gallery_arcade_'+str(x)];origin=Vector((x*.68-.5,-.35,.7));direction=Vector((1,0,0));inv=ob.matrix_world.inverted();hit=ob.ray_cast(inv@origin,inv.to_3x3()@direction,distance=1)[0];guards.append({'wall':ob.name,'opening_ray_hit':hit,'pass':not hit})
    assert all(x['pass'] for x in guards),guards
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':g.CONTACTS,'void_guards':guards,'footprint_m':[8,8],'entrance_clear_width_m':1.548,'arcade_clear_width_m':1.462,'native_anchor_mapping':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'parts':g.PARTS,'assignment':'first visible percentage, cumulative','visual_states':{'default':'all except minbar_upgrade objects','minbar_upgrade':'activate optional minbar_upgrade panels; authored interpretation, mapping pending'},'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Mosque_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    render_setup((12,-16,12),11,(0,0,2.3));bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Mosque_Age{age}.blend'))
    sc=bpy.context.scene;sc.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    sc.render.resolution_x=320;sc.render.resolution_y=320;sc.cycles.samples=4
    for name,loc in [('front',(0,-15,2.6)),('back',(0,15,2.6)),('left',(-15,0,2.6)),('right',(15,0,2.6)),('top',(0,0,15)),('bottom',(0,0,-15))]:
        sc.camera.location=loc;sc.camera.rotation_euler=(Vector((0,0,2.6))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    # Interior proof presentation with only roof hidden temporarily.
    for o in objects:
        if 'roof' in o.name or 'parapet' in o.name:o.hide_render=True
    sc.camera.location=(8,-11,9);sc.camera.rotation_euler=(Vector((0,1,1))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.filepath=str(OUT/f'age{age}_interior.png');bpy.ops.render.render(write_still=True)
    print('MOSQUE_DONE',age,flush=True)

def render_setup(loc,scale,target):
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
    sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
    bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-5,-8,14));bpy.context.object.data.energy=1900;bpy.context.object.data.size=9

def donor():
    ctx=g.reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());groups=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];fs=group.get('triangles',group.get('indices',[]))
        if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched decoded stock positions/topology, no reconstructed material';groups.append({'name':o.name,'bounds':bounds(o),'vertices':len(vs),'faces':len(fs)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Monastery_Age3_Reference.blend'))
    (RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':groups,'geometry_reused':False,'native_footprint_source':'installed core site_ext 8x8; donor bounds are render bounds'},indent=2))
    render_setup((14,-20,14),18,(0,-3,1));bpy.context.scene.render.filepath=str(OUT/'stock_donor_overview.png');bpy.ops.render.render(write_still=True)

try:
    if not (ART/'UNTouched_Abbasid_Monastery_Age3_Reference.blend').exists():donor()
    for age in [3,4]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[3,4],'cook':False,'native_owner_colour':'blocked integration pending'}))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
