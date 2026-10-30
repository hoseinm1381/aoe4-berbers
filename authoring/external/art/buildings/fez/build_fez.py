"""Task-owned, reproducible Moroccan courtyard blacksmith source; no cook or production edits."""
import bpy,bmesh,math,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/fez'; OUT=ROOT/'output/buildings_batch/fez'; RESEARCH=ROOT/'research/buildings_batch/fez'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.10,.115,.125),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern','roughness','metal','normal'):
        im=bpy.data.images.new('Fez_'+mapname,width=256,height=256,alpha=True);im.use_fake_user=True
        pixels=[]
        for y in range(256):
            for x in range(256):
                slot=(x//64)+4*(y//128); role,c,owner=COLORS[slot]
                variation=.96+.04*math.sin(x*.91)*math.sin(y*.81)
                rgb={'pattern':(owner,0,0),'normal':(.5,.5,1),'metal':(0,0,0),'roughness':((.4,.4,.4) if slot==5 else (.85,.85,.85))}.get(mapname,tuple(v*variation for v in c))
                pixels.extend((*rgb,1))
        im.pixels.foreach_set(pixels);im.filepath_raw=str(ART/(mapname+'.png'));im.file_format='PNG';im.save();im.pack()
        if mapname=='albedo': albedo=im
    for i,(name,c,owner) in enumerate(COLORS):
        m=bpy.data.materials.new('BerberFez_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='FezAtlasUV')
    for face in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis]
        co=[o.data.vertices[o.data.loops[li].vertex_index].co for li in face.loop_indices]
        lo=[min(v[k] for v in co) for k in axes];hi=[max(v[k] for v in co) for k in axes]
        for li,v in zip(face.loop_indices,co):
            uv.data[li].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    PARTS.append({'object':o.name,'first_stage':stage,'material':mat,'owner_mask':MATS[mat][0]['ber_owner_mask']});return o
def box(name,center,size,mat='earth',stage=40):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,stage)
def prism(name,outline,yfront,yback,mat,stage):
    n=len(outline);vs=[(x,y,z) for y in (yfront,yback) for x,z in outline]
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,stage)
def portal_outline(cx,base,width,height):
    r=width*.56;cz=base+height-r
    return [(cx-width*.43,base),(cx+width*.43,base)]+[(cx+r*math.cos(t),cz+r*math.sin(t)) for t in [math.radians(-28+i*236/16) for i in range(17)]]
def cut_portal(wall,cx,y,z,width,height,mat='cedar'):
    outline=portal_outline(cx,z,width,height)
    cutter=prism('TEMP_portal',outline,y-.7,y+.7,'shadow',40)
    bpy.context.view_layer.objects.active=wall;mod=wall.modifiers.new('Real recessed doorway','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
    # closed inserted door, actually seated inside the cut opening
    door=prism('horseshoe_door',outline,y+.035,y+.09,mat,60)
    for x in [cx-width*.32,cx,cx+width*.32]:box('door_joinery',(x,y+.022,z+height*.43),(.035,.035,height*.7),'stone',80)
    CONTACTS.append({'interface':'door recessed into front wall opening','gap':0,'intentional_recess':.035})
    return door
def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
def contact(a,b,axis=2,expected=0):
    bpy.context.view_layer.update(); gap=bounds(bpy.data.objects[a])[0][axis]-bounds(bpy.data.objects[b])[1][axis]
    CONTACTS.append({'child':a,'parent':b,'axis':axis,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})
def tube(name,center,r,h,mat='clay',stage=100):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=h,location=center);return finish(bpy.context.object,name,mat,stage)

def beam(name,a,b,w,mat='cedar',stage=60):
    v=Vector(b)-Vector(a);o=box(name,(Vector(a)+Vector(b))/2,(w,w,v.length),mat,stage);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o

def reuv(o):
    uv=o.data.uv_layers.active;slot=MATS[o['ber_material_role']][1]
    for p in o.data.polygons:
        ax=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=ax];vs=[o.data.vertices[o.data.loops[i].vertex_index].co for i in p.loop_indices];lo=[min(v[k] for v in vs) for k in axes];hi=[max(v[k] for v in vs) for k in axes]
        for i,v in zip(p.loop_indices,vs):uv.data[i].uv=((slot%4+.07+.86*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.07+.86*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/2)

def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]]
def contact(a,b,axis=2,expected=0):
    bpy.context.view_layer.update(); gap=bounds(bpy.data.objects[a])[0][axis]-bounds(bpy.data.objects[b])[1][axis]
    CONTACTS.append({'child':a,'parent':b,'axis':axis,'signed_gap':gap,'expected':expected,'pass':abs(gap-expected)<1e-5})

def open_arch(name,cx,y,width,height,wallheight,depth=.22):
    o=box(name,(cx,y,.16+wallheight/2),(width+.26,depth,wallheight),'lime',40)
    cut=prism('TEMP_opening',portal_outline(cx,.15,width,height),y-depth,y+depth,'shadow',40)
    bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Through horseshoe void','BOOLEAN');m.operation='DIFFERENCE';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cut,do_unlink=True);PARTS.pop()
    # Re-project final cut faces, not the pre-boolean wall UV.
    o.data.materials.clear();PARTS.pop();finish(o,name,'lime',40)
    return o

def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps();floor=.16
    box('scholar_court_foundation',(0,0,.08),(4.4,4.4,.16),'stone',0)
    # Scale-aware source envelope 4.4m, at live 130% animator scale =5.72m inside actual6m footprint.
    for side,x in [('west',-2.04),('east',2.04)]:
        wall=box(side+'_outer_wall',(x,0,1.31),(.20,4.0,2.30),'earth',40);contact(wall.name,'scholar_court_foundation')
        for yy in [-1.22,0,1.22]:
            o=open_arch(side+'_hollow_arcade',0,0,.90,1.75,2.30,.16)
            o.rotation_euler.z=math.pi/2;o.location.x=x/abs(x)*1.18;o.location.y=yy
            bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=False);contact(o.name,'scholar_court_foundation')
        roof=box(side+'_gallery_roof',(x/abs(x)*1.62,0,2.51),(1.04,4.0,.10),'cedar',60);contact(roof.name,wall.name)
        # Student-cell upper shell, divided into three actual chambers opening toward the court.
        cellwall=box(side+'_student_rear_wall',(x,0,2.96),(.20,4.0,.80),'lime',60);contact(cellwall.name,roof.name)
        for yy in [-2.0,-.64,.64,2.0]:
            div=box(side+'_cell_divider',(x/abs(x)*1.62,yy,2.96),(.84,.10,.80),'earth',60);contact(div.name,roof.name)
        for yy in [-1.25,0,1.25]:
            shutter=box(side+'_cell_cedar_shutter',(x/abs(x)*1.21,yy,2.98),(.12,.78,.76),'cedar',80)
            box(side+'_student_sleeping_platform',(x/abs(x)*1.72,yy,2.63),(.40,.70,.14),'straw',80)
            box(side+'_neutral_cell_owner_band',(x/abs(x)*1.137,yy,3.24),(.026,.76,.12),'owner_cloth',100)
        cap=box(side+'_cell_roof',(x/abs(x)*1.62,0,3.41),(1.04,4.10,.10),'earth',80);contact(cap.name,cellwall.name)
        for xx in [x/abs(x)*1.18,x]:
            para=box(side+'_lime_parapet',(xx,0,3.59),(.12,4.10,.26),'lime',80);contact(para.name,cap.name)
        # Fitted cedar lintel spans and shallow geometric plaster diamonds in the arcade spandrels.
        box(side+'_cedar_carved_frieze',(x/abs(x)*1.08,0,2.36),(.10,3.70,.14),'cedar',100)
        for yy in [-1.76,-.61,.61,1.76]:
            for z in [1.95,2.13]:
                o=box(side+'_plaster_geometric_carving',(x/abs(x)*1.08,yy,z),(.035,.10,.10),'stone',100);o.rotation_euler.x=math.pi/4
    # Exterior zellij-like dado and plaster courses prevent blank institutional side walls.
    for side,x in [('west',-2.15),('east',2.15)]:
        box(side+'_exterior_geometric_dado',(x,0,.66),(.026,3.82,.34),'stone',100)
        for yy in [-1.7+i*.34 for i in range(11)]:
            for z in [.61,.74]:
                o=box(side+'_exterior_ceramic_diamond',(x+(-.018 if x<0 else .018),yy,z),(.018,.095,.095),'clay',100);o.rotation_euler.x=math.pi/4
        box(side+'_exterior_carved_plaster_course',(x,0,1.89),(.030,3.82,.18),'lime',100)
        for yy in [-1.7+i*.34 for i in range(11)]:
            o=box(side+'_exterior_plaster_relief',(x+(-.022 if x<0 else .022),yy,1.89),(.025,.075,.075),'stone',100);o.rotation_euler.x=math.pi/4
    rear=box('teaching_hall_rear',(0,2.03,1.56),(2.26,.18,2.80),'lime',40);contact(rear.name,'scholar_court_foundation')
    arch=open_arch('teaching_open_reading_bay',0,1.26,1.70,2.20,2.80,.18);contact(arch.name,'scholar_court_foundation')
    r=box('teaching_hall_roof',(0,1.64,3.01),(2.26,.98,.10),'cedar',60);contact(r.name,rear.name)
    para=box('teaching_hall_parapet',(0,2.08,3.19),(2.26,.12,.26),'lime',80);contact(para.name,r.name)
    entry=open_arch('carved_main_portal',0,-2.03,1.40,2.25,2.70,.20);contact(entry.name,'scholar_court_foundation')
    lintel=box('portal_cedar_carved_lintel',(0,-2.03,2.94),(1.75,.30,.16),'cedar',60);contact(lintel.name,entry.name)
    for xx in [-1.34,1.34]:
        wall=box('front_guest_cell_wall',(xx,-2.03,1.31),(.94,.20,2.30),'earth',40);contact(wall.name,'scholar_court_foundation')
        box('guest_cell_roof',(xx,-1.73,2.51),(.94,.80,.10),'cedar',60)
        box('front_neutral_owner_band',(xx,-2.145,2.17),(.74,.025,.16),'owner_cloth',100)
    # Facade carved star/diamond relief is geometric, no invented writing.
    for xx in [-.60,-.40,-.20,0,.20,.40,.60]:
        o=box('portal_carved_cedar_diamond',(xx,-2.192,2.94),(.085,.025,.085),'straw',100);o.rotation_euler.y=math.pi/4
    # Square central basin is hollow: bottom plus four edge blocks with measurable water seating.
    foot=box('fountain_plinth',(0,0,.22),(.90,.90,.12),'lime',20);contact(foot.name,'scholar_court_foundation')
    bed=box('fountain_basin_bottom',(0,0,.31),(.72,.72,.06),'stone',40);contact(bed.name,foot.name)
    for x,y,sx,sy in [(-.40,0,.08,.88),(.40,0,.08,.88),(0,-.40,.72,.08),(0,.40,.72,.08)]:
        box('fountain_basin_rim',(x,y,.41),(sx,sy,.26),'lime',60)
    water=box('fountain_water',(0,0,.345),(.70,.70,.01),'shadow',100);contact(water.name,bed.name)
    jet=tube('fountain_faceted_spout',(0,0,.50),.055,.30,'stone',100)
    # Ground-level tile inlays and scholarly desk are physically seated.
    for x in [-.78,.78]:
        for y in [-1.50,-1.0,-.5,0,.5,1.0]:
            tile=box('courtyard_geometric_inlay',(x,y,.165),(.15,.15,.01),'clay',100);tile.rotation_euler.z=math.pi/4;contact(tile.name,'scholar_court_foundation')
    desk=box('teaching_desk_pedestal',(0,1.68,.43),(.40,.36,.54),'cedar',80);contact(desk.name,'scholar_court_foundation')
    top=box('teaching_desk_top',(0,1.68,.74),(.74,.50,.08),'cedar',80);contact(top.name,desk.name)
    page=box('scholarly_open_book',(0,1.68,.80),(.38,.31,.04),'straw',100);contact(page.name,top.name)
    # Neutral banner hangs from measured cedar support and faces both front and court.
    box('banner_wall_bracket',(.94,-2.04,2.61),(.08,.08,.68),'cedar',80)
    box('banner_crossbar',(.73,-2.04,2.93),(.48,.08,.06),'cedar',80)
    box('neutral_owner_banner',(.73,-2.065,2.56),(.38,.035,.68),'owner_cloth',100)
    # Every fitted arcade has a measured ray-clear opening at ground and shoulder height.
    voids=[]
    from mathutils.bvhtree import BVHTree
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and ('hollow_arcade' in o.name or 'open_reading_bay' in o.name or 'main_portal' in o.name)]:
        bm=bmesh.new();bm.from_mesh(o.data);tree=BVHTree.FromBMesh(bm)
        lo,hi=bounds(o);axis=0 if 'hollow_arcade' in o.name else 1
        for z in [.5,1.25]:
            world=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,z));world[axis]=lo[axis]-.1
            origin=o.matrix_world.inverted()@world;direct=Vector((1,0,0)) if axis==0 else Vector((0,1,0));direct=o.matrix_world.inverted().to_3x3()@direct
            hit=tree.ray_cast(origin,direct,hi[axis]-lo[axis]+.2)[0];assert hit is None,(o.name,z)
            voids.append({'object':o.name,'height':z,'ray_clear':True})
        bm.free()
    (OUT/'void_checks.json').write_text(json.dumps(voids,indent=2))
    bpy.context.view_layer.update();objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data);vol=bm.calc_volume(signed=True)
        if vol<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);vol=-vol
        non=sum(not e.is_manifold for e in bm.edges);deg=sum(f.calc_area()<1e-10 for f in bm.faces);bm.free()
        uv=o.data.uv_layers.active;uvdeg=0
        for face in o.data.polygons:
            pts=[uv.data[i].uv for i in face.loop_indices];area=abs(sum(pts[i].x*pts[(i+1)%len(pts)].y-pts[(i+1)%len(pts)].x*pts[i].y for i in range(len(pts)))/2);uvdeg+=area<1e-10
        checks.append({'object':o.name,'non_manifold':non,'degenerate_faces':deg,'uv_zero_area_faces':uvdeg,'outward_signed_volume':vol,'finite':all(math.isfinite(v) for vert in o.data.vertices for v in vert.co),'positive_scale':all(v>0 for v in o.scale),'bounds':bounds(o)})
    assert all(c['non_manifold']==0 and c['degenerate_faces']==0 and c['uv_zero_area_faces']==0 and c['outward_signed_volume']>0 and c['finite'] and c['positive_scale'] for c in checks),checks
    assert all(c['pass'] for c in CONTACTS),CONTACTS
    assert all(c['bounds'][0][0]>=-2.3077 and c['bounds'][1][0]<=2.3077 and c['bounds'][0][1]>=-2.3077 and c['bounds'][1][1]<=2.3077 and c['bounds'][0][2]>=-.001 for c in checks)
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[6,6],'animator_scale_percent':130,'scaled_source_envelope_m':[5.72,5.72],'clear_gateway_source_m':1.204,'native_anchor_binding':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'assignment':'first visible percentage, cumulative','parts':PARTS,'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Fez_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(6,-8,12));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=7.0;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
    bpy.ops.object.light_add(type='AREA',location=(0,-5,3));bpy.context.object.data.energy=420;bpy.context.object.data.size=4
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Fez_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=8;scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-12,1.4)),('back',(0,12,1.4)),('left',(-12,0,1.4)),('right',(12,0,1.4)),('top',(0,0,15)),('bottom',(0,0,-12))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=768;scene.render.resolution_y=768;cam.location=(0,-2,7);cam.data.ortho_scale=4.5;cam.rotation_euler=(Vector((0,0,1.1))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/'age4_interior.png');bpy.ops.render.render(write_still=True)
    print('FEZ_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());saved=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched installed Abbasid Age IV university decoded positions/topology';saved.append({'name':o.name,'vertices':len(vs),'faces':len(faces),'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_University_Age4_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':saved,'geometry_reused_in_final':False,'footprint_from':'core.xml site_ext x=8 y=8; render bounds not footprint'},indent=2))
try:
    donor()
    for age in [4]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[4],'cook':False,'native_owner_colour':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()


