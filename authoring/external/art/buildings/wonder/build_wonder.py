"""Original completed Almohad Wonder; deterministic task-owned source recipe."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import geometry_helpers as g
from geometry_helpers import bpy,bmesh,math,json,traceback,Vector,ART,OUT,RESEARCH,box,prism,contact,bounds

GUARDS=[]
def hollow(wall,cx,y,width,height,base=.20,side=False,rayz=None):
    c=prism('TEMP_arch',g.portal_outline(cx,base,width,height),y-1.5,y+1.5,'shadow',40)
    if side:c.rotation_euler.z=math.pi/2
    bpy.context.view_layer.objects.active=wall
    m=wall.modifiers.new('Through masonry opening','BOOLEAN');m.operation='DIFFERENCE';m.object=c
    bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True);g.PARTS.pop()
    z=base+.35 if rayz is None else rayz
    origin=Vector((-y-1.6,cx,z)) if side else Vector((cx,y-1.6,z))
    direction=Vector((1,0,0)) if side else Vector((0,1,0));inv=wall.matrix_world.inverted()
    hit=wall.ray_cast(inv@origin,inv.to_3x3()@direction,distance=3.2)[0]
    GUARDS.append({'object':wall.name,'origin':list(origin),'direction':list(direction),'hit':hit,'pass':not hit,'clear_base_width':round(width*.86,4)})

def atlas(o):
    slot=g.MATS[o['ber_material_role']][1];uv=o.data.uv_layers.active
    for p in o.data.polygons:
        axes=sorted(range(3),key=lambda k:abs(p.normal[k]))[:2]
        cs=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices]
        mins=[min(v[a] for v in cs) for a in axes];spans=[max(v[a] for v in cs)-mins[j] for j,a in enumerate(axes)]
        for li,v in zip(p.loop_indices,cs):uv.data[li].uv=((slot%4+.08+.84*(v[axes[0]]-mins[0])/max(spans[0],1e-9))/4,(slot//4+.08+.84*(v[axes[1]]-mins[1])/max(spans[1],1e-9))/2)

def roof(name,cx,cy,w,d,z):
    box(name,(cx,cy,z+.08),(w,d,.16),'earth',60)
    for xx in [cx-w/2+.10,cx+w/2-.10]:box(name+'_parapet',(xx,cy,z+.26),(.20,d,.20),'lime',80)
    for yy in [cy-d/2+.10,cy+d/2-.10]:box(name+'_parapet',(cx,yy,z+.26),(w-.40,.20,.20),'lime',80)

def setup():
    ctx=g.reset_scene();g.PARTS.clear();g.CONTACTS.clear();g.MATS.clear();GUARDS.clear();g.setup_maps()
    for name,col in [('normal',(.5,.5,1)),('roughness',(.85,.85,.85)),('metal',(0,0,0))]:
        im=bpy.data.images.new('Wonder_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
    return ctx

def build():
    ctx=setup();floor=.20;h=2.65;top=floor+h
    box('foundation',(0,0,.075),(11.6,11.6,.15),'stone',0)
    box('paved_sanctuary',(0,0,.175),(11.3,11.3,.05),'lime',0);contact('paved_sanctuary','foundation')
    # Rear hall is a genuine empty shell, roof carried by two rows of columns.
    box('qibla_wall',(0,5.25,floor+h/2),(10.9,.3,h),'earth',40);contact('qibla_wall','paved_sanctuary')
    for x in [-5.30,5.30]:
        n='hall_outer_wall_'+str(x);box(n,(x,3.0,floor+h/2),(.30,4.2,h),'earth',40);contact(n,'paved_sanctuary')
    arc=box('grand_hypostyle_front_arcade',(0,.75,floor+h/2),(10.9,.30,h),'lime',40)
    for x in [-4.05,-2.025,0,2.025,4.05]:hollow(arc,x,.75,1.6,2.25)
    contact(arc.name,'paved_sanctuary')
    # Discrete bases/capitals and transverse cedar beams; every support is seated.
    for y in [2.25,3.90]:
        for x in [-4.05,-2.025,0,2.025,4.05]:
            tag=f'{x}_{y}';box('column_base_'+tag,(x,y,.29),(.50,.50,.18),'stone',20);contact('column_base_'+tag,'paved_sanctuary')
            box('column_shaft_'+tag,(x,y,.38+2.23/2),(.31,.31,2.23),'lime',40);contact('column_shaft_'+tag,'column_base_'+tag)
            box('column_capital_'+tag,(x,y,2.69),(.45,.45,.16),'lime',40);contact('column_capital_'+tag,'column_shaft_'+tag)
        box('cedar_hall_beam_'+str(y),(0,y,2.81),(10.45,.28,.08),'cedar',60)
        for x in [-4.05,-2.025,0,2.025,4.05]:contact('cedar_hall_beam_'+str(y),'column_capital_'+f'{x}_{y}')
    roof('main_hypostyle_roof',0,3.0,10.9,4.8,top);contact('main_hypostyle_roof','qibla_wall')
    for y in [2.25,3.90]:contact('main_hypostyle_roof','cedar_hall_beam_'+str(y))
    # Raised axial nave emerges above the broad low roofs, without an Ottoman dome.
    for x in [-.64,.64]:box('axial_nave_clerestory',(x,3.0,3.22),(.16,4.20,.42),'lime',60)
    roof('raised_axial_nave_roof',0,3,1.5,4.45,3.43)
    box('rear_mihrab_buttress',(0,5.45,1.0),(1.25,.30,1.6),'earth',40);contact('rear_mihrab_buttress','paved_sanctuary')
    # Flanking galleries have three real through arches and usable shaded space.
    for x in [-5.30,5.30]:
        box('gallery_outer_wall_'+str(x),(x,-1.965,1.35),(.30,5.13,2.30),'earth',40);contact('gallery_outer_wall_'+str(x),'paved_sanctuary')
        a=box('gallery_arcade_'+str(x),(x*.67,-1.965,1.35),(.30,5.13,2.30),'lime',40)
        for y in [-3.65,-2.04,-.43]:hollow(a,y,-x*.67,1.23,1.95,side=True)
        contact(a.name,'paved_sanctuary')
        roof('gallery_roof_'+str(x),x*.835,-1.965,2.049,5.13,2.50)
        contact('gallery_roof_'+str(x),a.name);contact('gallery_roof_'+str(x),'gallery_outer_wall_'+str(x))
        contact(arc.name,'gallery_outer_wall_'+str(x),axis=1)
        contact(arc.name,a.name,axis=1)
        box('owner_gallery_frieze_'+str(x),(x*.67,-1.965,2.42),(.33,5.13,.12),'owner_cloth',100)
    # Twin low facade walls link the monumental tower gateway into the court.
    for x in [-3.28,3.28]:
        w=box('entrance_facade_'+str(x),(x,-4.68,1.35),(4.36,.30,2.30),'earth',40);hollow(w,x,-4.68,1.35,1.95);contact(w.name,'paved_sanctuary')
        box('entrance_cornice_'+str(x),(x,-4.68,2.56),(4.46,.43,.12),'lime',60);contact('entrance_cornice_'+str(x),w.name)
        contact('gallery_outer_wall_'+str(-5.3 if x<0 else 5.3),w.name,axis=1)
    # Central square tower, not a decorated solid box: gateway is cut through shaft.
    box('tower_footing',(0,-4.40,.30),(2.40,2.40,.20),'stone',20);contact('tower_footing','paved_sanctuary')
    tower=box('great_square_tower',(0,-4.40,3.65),(2.2,2.2,6.5),'earth',40);contact(tower.name,'tower_footing')
    hollow(tower,0,-4.40,1.35,2.38,base=.40)
    # Bottom opening cuts footing too, leaving a continuous entry threshold.
    hollow(bpy.data.objects['tower_footing'],0,-4.40,1.35,2.38,base=.20,rayz=.30)
    for z in [3.15,5.85,6.82]:box('tower_stone_coursed_band',(0,-4.40,z),(2.30,2.30,.12),'lime',80)
    # Tiny recessed upper openings are physically cut, four faces share same axis logic.
    hollow(tower,0,-4.4,.45,.90,base=4.78)
    hollow(tower,-4.4,0,.45,.90,base=4.78,side=True)
    box('tower_cornice',(0,-4.40,6.98),(2.55,2.55,.16),'lime',60);contact('tower_cornice',tower.name)
    for xx in [-.94,.94]:box('tower_terrace_parapet',(xx,-4.40,7.22),(.16,2.2,.32),'earth',80)
    for yy in [-5.42,-3.38]:box('tower_terrace_parapet',(0,yy,7.22),(1.72,.16,.32),'earth',80)
    # Hollow lantern frame is independently assembled, open on all four sides.
    for x in [-.44,.44]:
        for y in [-4.84,-3.96]:box('lantern_corner_pier',(x,y,7.48),(.16,.16,.84),'lime',80);contact(bpy.context.object.name,'tower_cornice')
    box('lantern_flat_cap',(0,-4.40,7.965),(1.20,1.20,.13),'lime',80)
    for o in list(bpy.context.scene.objects):
        if o.name.startswith('lantern_corner_pier'):contact('lantern_flat_cap',o.name)
    box('lantern_upper_finial_base',(0,-4.40,8.08),(.48,.48,.10),'stone',100);contact('lantern_upper_finial_base','lantern_flat_cap')
    # Restrained raised lattice craftsmanship deliberately embeds .015 into stone.
    for face in ['front','right']:
        for z in [3.65,4.20]:
            for t in [-.48,0,.48]:
                if face=='front':o=box('tower_sebka_relief',(t,-5.505,z),(.23,.04,.23),'lime',100);o.rotation_euler.y=math.pi/4
                else:o=box('tower_sebka_relief',(1.105,-4.4+t,z),(.04,.23,.23),'lime',100);o.rotation_euler.x=math.pi/4
    # Large readable owner banners: hanging cloth physically touches fitted timber rods.
    for x in [-.78,.78]:
        box('banner_anchored_rod',(x,-5.54,4.62),(.52,.16,.07),'cedar',80)
        box('owner_tower_banner',(x,-5.58,4.05),(.42,.035,1.07),'owner_cloth',100)
    # Raised centre courtyard basin is actual hollow polygonal masonry.
    box('basin_footing',(0,-1.5,.25),(1.5,1.5,.10),'stone',20);contact('basin_footing','paved_sanctuary')
    for x in [-.68,.68]:box('ablution_basin_side',(x,-1.5,.42),(.14,1.5,.24),'stone',100);contact(bpy.context.object.name,'basin_footing')
    for y in [-2.18,-.82]:box('ablution_basin_end',(0,y,.42),(1.22,.14,.24),'stone',100);contact(bpy.context.object.name,'basin_footing')
    box('basin_inset_floor',(0,-1.5,.31),(1.22,1.22,.02),'clay',100);contact('basin_inset_floor','basin_footing')
    for x in [-5.47,5.47]:box('hall_timber_drain',(x,4.35,2.96),(.44,.12,.10),'cedar',80)
    # Final per-object triangulation makes UV area and degeneracy checks unequivocal.
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
    col=bpy.data.collections.new('BER_Wonder_Age4');bpy.context.scene.collection.children.link(col)
    for o in objects:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(o.data);bm.free();o.data.update();atlas(o)
        bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True);non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free()
        uv=o.data.uv_layers.active;areas=[]
        for p in o.data.polygons:
            a,b,c=[uv.data[i].uv for i in p.loop_indices];areas.append(abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2)
        checks.append({'object':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.polygons),'non_manifold_edges':non,'degenerate_faces':deg,'signed_volume':vol,'minimum_uv_triangle_area':min(areas),'positive_transform':o.matrix_world.determinant()>0,'finite_geometry':all(math.isfinite(t) for v in o.data.vertices for t in v.co),'owner_mask':int(g.MATS[o['ber_material_role']][0]['ber_owner_mask'])})
    bpy.context.view_layer.update();bs=[bounds(o) for o in objects];lo=[min(b[0][k] for b in bs) for k in range(3)];hi=[max(b[1][k] for b in bs) for k in range(3)]
    assert all(c['non_manifold_edges']==0 and c['degenerate_faces']==0 and c['signed_volume']>0 and c['minimum_uv_triangle_area']>1e-10 and c['positive_transform'] and c['finite_geometry'] for c in checks),checks
    assert all(c['pass'] for c in g.CONTACTS),g.CONTACTS
    assert all(c['pass'] for c in GUARDS),GUARDS
    assert lo[0]>=-6 and lo[1]>=-6 and hi[0]<=6 and hi[1]<=6 and abs(lo[2])<1e-6,(lo,hi)
    (OUT/'age4_validation.json').write_text(json.dumps({'age':4,'objects':checks,'contacts':g.CONTACTS,'void_guards':GUARDS,'site_footprint':[12,12],'mesh_bounds':[lo,hi],'footprint_pass':True,'ground_z':lo[2],'native_owner_colour':'blocked integration; authored masks only'},indent=2))
    (ART/'age4_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':4,'stages':[0,20,40,60,80,100],'parts':g.PARTS,'assignment':'first visible percentage; cumulative','game_binding_status':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/'Berber_Wonder_Age4.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    render_setup((16,-20,16),18,(0,0,3.4));bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Berber_Wonder_Age4.blend'))
    sc=bpy.context.scene;sc.render.filepath=str(OUT/'age4_preview.png');bpy.ops.render.render(write_still=True)
    sc.render.resolution_x=384;sc.render.resolution_y=384;sc.cycles.samples=8
    for name,loc in [('front',(0,-20,3.4)),('back',(0,20,3.4)),('left',(-20,0,3.4)),('right',(20,0,3.4)),('top',(0,0,22)),('bottom',(0,0,-20))]:
        sc.camera.location=loc;sc.camera.rotation_euler=(Vector((0,0,3.4))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/f'age4_{name}.png');bpy.ops.render.render(write_still=True)
    for o in objects:
        if 'roof' in o.name or 'parapet' in o.name:o.hide_render=True
    sc.camera.location=(14,-16,16);sc.camera.rotation_euler=(Vector((0,0,1))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.filepath=str(OUT/'age4_interior.png');bpy.ops.render.render(write_still=True)
    print('WONDER_DONE',flush=True)

def render_setup(loc,scale,target):
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=768;sc.render.resolution_y=768
    sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
    bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=scale;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-8,-12,20));bpy.context.object.data.energy=3000;bpy.context.object.data.size=10

def donor():
    ctx=g.reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());groups=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];fs=group.get('triangles',group.get('indices',[]))
        if fs and isinstance(fs[0],int):fs=[fs[i:i+3] for i in range(0,len(fs),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched decoded stock positions/topology; no reconstructed material';groups.append({'name':o.name,'bounds':bounds(o),'vertices':len(vs),'faces':len(fs)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Khilji_Mosque_Reference.blend'))
    (RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':groups,'geometry_reused':False,'site_footprint_source':'installed mal.xml site_ext 12x12','donor_render_bounds_are_footprint':False},indent=2))
try:
    if not (ART/'UNTouched_Khilji_Mosque_Reference.blend').exists():donor()
    build();(OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[4],'cook':False,'native_owner_colour':'blocked integration pending'}))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()
