"""Task-owned, reproducible Moroccan courtyard market source; no cook or production edits."""
import bpy,bmesh,math,json,traceback,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'art/buildings/siege'; OUT=ROOT/'output/buildings_batch/siege'; RESEARCH=ROOT/'research/buildings_batch/siege'
COLORS=[('earth',(.49,.285,.15),0),('lime',(.76,.66,.48),0),('stone',(.37,.31,.23),0),('cedar',(.22,.095,.037),0),('owner_cloth',(.77,.73,.63),1),('shadow',(.065,.04,.022),0),('clay',(.52,.18,.085),0),('straw',(.52,.40,.22),0),('iron',(.12,.13,.14),0),('unused_a',(.2,.2,.2),0),('unused_b',(.2,.2,.2),0),('unused_c',(.2,.2,.2),0)]
MATS={}; PARTS=[]; CONTACTS=[]
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    override=bpy.context.temp_override(window=bpy.context.window_manager.windows[0]);override.__enter__()
    return override
def setup_maps():
    # Shared atlas: material islands are distinct; pattern and albedo use exactly the same UVs.
    for mapname in ('albedo','pattern','roughness','normal','metal'):
        im=bpy.data.images.new('Siege_'+mapname,width=256,height=384,alpha=True);im.use_fake_user=True
        pixels=[]
        for y in range(384):
            for x in range(256):
                slot=(x//64)+4*(y//128); role,c,owner=COLORS[slot]
                variation=.96+.04*math.sin(x*.91)*math.sin(y*.81)
                rgb={'pattern':(owner,0,0),'roughness':((.45,.45,.45) if slot==8 else (.85,.85,.85)),'normal':(.5,.5,1),'metal':((.8,.8,.8) if slot==8 else (0,0,0))}.get(mapname,tuple(v*variation for v in c))
                pixels.extend((*rgb,1))
        im.pixels.foreach_set(pixels);im.filepath_raw=str(ART/(mapname+'.png'));im.file_format='PNG';im.save();im.pack()
        if mapname=='albedo': albedo=im
    for i,(name,c,owner) in enumerate(COLORS):
        m=bpy.data.materials.new('BerberSiege_'+name);m.use_nodes=True;m['ber_owner_mask']=owner;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.85
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);MATS[name]=(m,i)
def finish(o,name,mat,stage):
    o.name=name;o['garrison_building_first_stage']=stage;o['ber_source_stage']=stage/100;o['ber_material_role']=mat
    o.data.materials.append(MATS[mat][0]);slot=MATS[mat][1];uv=o.data.uv_layers.active or o.data.uv_layers.new(name='SiegeAtlasUV')
    for face in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3) if k!=axis]
        co=[o.data.vertices[o.data.loops[li].vertex_index].co for li in face.loop_indices]
        lo=[min(v[k] for v in co) for k in axes];hi=[max(v[k] for v in co) for k in axes]
        for li,v in zip(face.loop_indices,co):
            uv.data[li].uv=((slot%4+.08+.84*(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8))/4,(slot//4+.08+.84*(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8))/3)
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
def ring(name,center,outer,inner,depth,mat='cedar',stage=100,vertical=True):
    # A continuous annular closed mesh with an actual through bore.
    cx,cy,cz=center;n=16;vs=[]
    for side in [-depth/2,depth/2]:
        for r in [outer,inner]:
            for i in range(n):
                a=i*math.tau/n
                vs.append((cx+r*math.cos(a),cy+side,cz+r*math.sin(a)) if vertical else (cx+r*math.cos(a),cy+r*math.sin(a),cz+side))
    fs=[]
    for i in range(n):
        j=(i+1)%n
        fs.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);return finish(o,name,mat,stage)

def build(age):
    global PARTS,CONTACTS
    ctx=reset_scene();PARTS=[];CONTACTS=[];MATS.clear();setup_maps()
    wall='earth' if age==3 else 'lime';floor=.16;h=2.4 if age==3 else 2.65
    box('yard_foundation',(0,0,.08),(6,6,.16),'earth',0)
    # Rear working hall is open across the front; solid walls enclose tools behind.
    box('rear_engineering_wall',(0,2.55,floor+h/2),(5.1,.28,h),wall,40);contact('rear_engineering_wall','yard_foundation')
    for side,x in [('west',-2.42),('east',2.42)]:
        box(side+'_hall_wall',(x,1.13,floor+h/2),(.26,2.58,h),wall,40);contact(side+'_hall_wall','yard_foundation')
        box(side+'_portal_pier',(x,-.18,floor+h/2),(.30,.30,h),'cedar',20);contact(side+'_portal_pier','yard_foundation')
    box('wide_open_portal_header',(0,-.18,floor+h+.09),(5.14,.3,.18),'cedar',60);contact('wide_open_portal_header','west_portal_pier')
    # One closed gabled roof prism, bearing on side wall top planes.
    roof=prism('pitched_engineering_shelter',[(-2.67,floor+h),(2.67,floor+h),(2.67,floor+h+.13),(0,floor+h+.82),(-2.67,floor+h+.13)],-.43,2.83,'straw' if age==3 else 'clay',60)
    contact('pitched_engineering_shelter','west_hall_wall')
    for y in [-.28,.58,1.44,2.30]:
        box('roof_tie_beam',(0,y,floor+h-.05),(4.7,.10,.10),'cedar',60)
    box('portal_owner_neutral_stripe',(0,-.345,floor+h-.18),(2.4,.025,.40),'owner_cloth',100)
    # Left timber stock yard: racks and lumber seated on load rails.
    for x in [-2.50,-1.35]:
        box('timber_rack_leg',(x,-1.55,.66),(.13,1.42,1),'cedar',20);contact(bpy.context.object.name,'yard_foundation')
    for z in [.66,1.18]:
        box('timber_rack_crossrail',(-1.925,-1.55,z),(1.28,.14,.12),'cedar',60)
        for j in range(4):
            box('seasoned_lumber',(-2.38+j*.29,-1.55,z+.11),(.22,2.25,.10),'straw',100)
    # A distinct wheel-maker station within the rear shelter.
    box('wheel_workbench',(-1.73,1.22,.90),(1.4,.9,.14),'cedar',80)
    for x in [-2.30,-1.16]:
        box('wheel_bench_leg',(x,1.22,.495),(.13,.70,.67),'cedar',60);contact(bpy.context.object.name,'yard_foundation')
    contact('wheel_workbench','wheel_bench_leg')
    box('wheel_display_rail',(-1.73,.69,.97),(1.4,.10,.14),'cedar',80)
    wheelz=1.04+.56
    ring('assembled_wheel_rim',(-1.73,.69,wheelz),.56,.43,.10)
    # Hub and eight connected radial spokes share a horizontal axle.
    hub=tube('wheel_hub',(-1.73,.69,wheelz),.115,.18,'cedar');hub.rotation_euler.x=math.pi/2
    for i in range(8):
        a=i*math.tau/8;o=box('wheel_radial_spoke',(-1.73+.26*math.cos(a),.69,wheelz+.26*math.sin(a)),(.54,.075,.065),'cedar',100);o.rotation_euler.y=-a
    # Rope making bench and coiled rope with actual bores, outside the central lane.
    box('rope_bench',(1.74,-1.48,.83),(1.15,1.30,.14),'cedar',80)
    for y in [-1.98,-.98]:
        box('rope_bench_trestle',(1.74,y,.46),(.96,.12,.60),'cedar',60);contact(bpy.context.object.name,'yard_foundation')
    contact('rope_bench','rope_bench_trestle')
    for r in [.30,.24,.18]:ring('rope_coil',(1.74,-1.48,.935),r,r-.04,.07,'straw',100,False)
    for y in [-1.95,-1.0]:
        box('rope_spin_post',(2.16,y,1.13),(.08,.08,.46),'cedar',80);contact(bpy.context.object.name,'rope_bench')
    box('rope_stretch_line',(2.16,-1.475,1.32),(.026,1.03,.026),'straw',100)
    # Forge in the rear east bay: hearth, anvil and useful chimney silhouette.
    box('forge_hearth',(1.73,1.40,.49),(1.1,1.08,.66),'stone',40);contact('forge_hearth','yard_foundation')
    box('forge_firebed',(1.73,1.14,.84),(.74,.54,.04),'shadow',80);contact('forge_firebed','forge_hearth')
    for x in [1.28,2.18]:
        box('forge_hood_support',(x,1.64,1.015),(.16,.58,.39),wall,60);contact(bpy.context.object.name,'forge_hearth')
    box('forge_hood',(1.73,1.64,1.60),(1.12,.62,.82),wall,60)
    contact('forge_hood','forge_hood_support',expected=-.02)
    box('forge_chimney',(1.73,1.69,2.40),(.44,.45,1.60 if age==3 else 2.1),wall,80)
    box('anvil_stump',(1.73,.33,.45),(.43,.43,.58),'cedar',60);contact('anvil_stump','yard_foundation')
    box('anvil_waist',(1.73,.33,.87),(.22,.22,.26),'iron',80);contact('anvil_waist','anvil_stump')
    box('anvil_head',(1.73,.33,1.07),(.69,.26,.14),'iron',100);contact('anvil_head','anvil_waist')
    # Imperial has masonry wall caps, joined portal ornament and loft stock shelf.
    if age==4:
        box('rear_wall_lime_cap',(0,2.55,floor+h+.045),(5.15,.35,.09),'lime',80);contact('rear_wall_lime_cap','rear_engineering_wall')
        for x in [-2.36,2.36]:box('portal_pier_stone_shoe',(x,-.18,.35),(.40,.38,.38),'stone',20)
        for x in [-1.15,-.75,-.35,.35,.75,1.15]:
            o=box('portal_geometric_inlay',(x,-.357,floor+h+.06),(.12,.025,.12),'lime',100);o.rotation_euler.y=math.pi/4
        box('rear_tool_shelf',(0,2.35,1.5),(1.5,.38,.12),'cedar',80)
        for x in [-.65,.65]:box('shelf_bracket',(x,2.42,1.32),(.08,.30,.25),'cedar',80)
        for x in [-.5,0,.5]:box('iron_stock',(x,2.34,1.63),(.36,.22,.14),'iron',100)
        box('rope_owner_neutral_strip',(1.74,-2.145,.83),(.75,.025,.12),'owner_cloth',100)
    # Exact source interfaces, not native anchors or walk-surface assertions.
    for name,loc in [('siege_exit',(0,-3,0)),('hall_working_lane',(0,1,floor)),('rally_direction',(0,-4,0))]:
        o=bpy.data.objects.new('AUTHOR_'+name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;o['native_binding']='pending'
    contact('assembled_wheel_rim','wheel_display_rail')
    bpy.context.view_layer.update()
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('seasoned_lumber')]:
        rails=[r for r in bpy.context.scene.objects if r.name.startswith('timber_rack_crossrail')]
        gap=min(abs(bounds(o)[0][2]-bounds(r)[1][2]) for r in rails)
        CONTACTS.append({'child':o.name,'interface':'lumber lower face/rack rail upper face','signed_gap':gap,'expected':0,'pass':gap<1e-5})
    # Source-only unobstructed corridor test over ground and below 2m elevation.
    for o in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name!='yard_foundation']:
        lo,hi=bounds(o)
        crosses=hi[0]>-1+1e-5 and lo[0]<1-1e-5 and hi[1]>-3 and lo[1]<2.1 and lo[2]<2.0
        assert not crosses,(o.name,lo,hi)

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
    assert all(c['bounds'][0][0]>=-3.001 and c['bounds'][1][0]<=3.001 and c['bounds'][0][1]>=-3.001 and c['bounds'][1][1]<=3.001 and c['bounds'][0][2]>=-.001 for c in checks)
    (OUT/f'age{age}_validation.json').write_text(json.dumps({'age':age,'objects':checks,'contacts':CONTACTS,'footprint_m':[6,6],'clear_gateway_m':4.54,'central_transit_corridor_m':2.0,'native_anchor_binding':'pending'},indent=2))
    (ART/f'age{age}_construction.json').write_text(json.dumps({'schema':'berber-building-source-stage/v1','age':age,'stages':[0,20,40,60,80,100],'assignment':'first visible percentage, cumulative','parts':PARTS,'game_binding':'pending'},indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(ART/f'Berber_Siege_Age{age}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,path_mode='COPY',embed_textures=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=768;scene.render.resolution_y=768
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.55,.62,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.camera_add(location=(10,-13,11));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=9.5;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-4,-6,12));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
    bpy.ops.object.light_add(type='AREA',location=(0,-5,3));bpy.context.object.data.energy=420;bpy.context.object.data.size=4
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Siege_Age{age}.blend'));scene.render.filepath=str(OUT/f'age{age}_preview.png');bpy.ops.render.render(write_still=True)
    scene.cycles.samples=8;scene.render.resolution_x=256;scene.render.resolution_y=256
    for name,loc in [('front',(0,-12,1.4)),('back',(0,12,1.4)),('left',(-12,0,1.4)),('right',(12,0,1.4)),('top',(0,0,15)),('bottom',(0,0,-12))]:
        cam.location=loc;cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'age{age}_{name}.png');bpy.ops.render.render(write_still=True)
    print('SIEGE_DONE',age,flush=True)
def donor():
    ctx=reset_scene();d=json.loads(next((RESEARCH/'stock').glob('*/decoded-static.json')).read_text());saved=[]
    for group in d['geometry']['groups']:
        vs=group['positions'];faces=group.get('triangles',group.get('indices',[]))
        if faces and isinstance(faces[0],int):faces=[faces[i:i+3] for i in range(0,len(faces),3)]
        me=bpy.data.meshes.new(group['name']);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new(group['name'],me);bpy.context.scene.collection.objects.link(o);o['reference_only']='Untouched installed Abbasid Age III siege decoded positions/topology';saved.append({'name':o.name,'vertices':len(vs),'faces':len(faces),'bounds':bounds(o)})
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/'UNTouched_Abbasid_Siege_Age3_Reference.blend'));(RESEARCH/'donor_summary.json').write_text(json.dumps({'groups':saved,'geometry_reused_in_final':False,'footprint_from':'core.xml site_ext x=6 y=6; render bounds not footprint'},indent=2))
try:
    donor()
    for age in [int(n) for n in os.environ.get('BER_SIEGE_AGES','3,4').split(',')]:build(age)
    (OUT/'BUILD_COMPLETE.json').write_text(json.dumps({'ages':[3,4],'cook':False,'native_owner_colour':'pending'},indent=2))
except Exception:
    (OUT/'BUILD_ERROR.txt').write_text(traceback.format_exc());raise
finally:bpy.ops.wm.quit_blender()


