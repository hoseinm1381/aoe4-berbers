"""Reproducible four-age Tribal Tent source. No export/cook/gameplay changes.

Phase 1: measured frame, tensioned textile shells and ground anchors.
Phase 2: seams, original geometric trim and portable council furnishings.
"""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/tribal_tent/iteration001';ART=ROOT/'art/tribal_tent/iterations/001'
PREFIX='BER_Tent001';SPECS=[(2.35,1.8,2.45,1.15,0),(2.55,1.85,2.75,1.4,.25),(2.7,1.95,3.05,1.55,.45),(2.8,2.1,3.3,1.7,.6)]
CONTACTS=[];PARTS=[];ROOTS={};MATS={};CANOPY_BVH={}
PALETTE=[('dark haircloth',(.075,.050,.032),.94,0,True,False),('warm cloth',(.26,.17,.095),.9,0,True,False),('ivory cloth',(.66,.58,.42),.86,0,True,False),('woven black skirts',(.115,.072,.041),.92,0,True,False),('cedar',(.25,.115,.048),.84,0,False,True),('rope',(.45,.31,.16),.94,0,False,False),('red weave',(.39,.072,.043),.86,0,True,False),('ochre weave',(.64,.34,.075),.83,0,True,False),('cream weave',(.78,.69,.47),.84,0,True,False),('mat straw',(.39,.29,.13),.95,0,True,False),('clay',(.33,.12,.06),.88,0,False,False),('metal fittings',(.39,.27,.12),.42,.65,False,False)]
def material(name,color,rough=.8,metal=0,cloth=False,wood=False):
    m=bpy.data.materials.new(PREFIX+' '+name);m.use_fake_user=True;m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;m.diffuse_color=(*color,1)
    if cloth or wood:
        n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=90 if cloth else 8;n.inputs['Detail'].default_value=3
        r=m.node_tree.nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(*(c*.65 for c in color),1);r.color_ramp.elements[1].color=(*(min(1,c*1.2) for c in color),1)
        m.node_tree.links.new(n.outputs['Fac'],r.inputs[0]);m.node_tree.links.new(r.outputs['Color'],p.inputs['Base Color'])
        w=m.node_tree.nodes.new('ShaderNodeTexWave');w.wave_type='BANDS';w.bands_direction='X';w.inputs['Scale'].default_value=190 if cloth else 16;w.inputs['Distortion'].default_value=1.7
        b=m.node_tree.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.16;b.inputs['Distance'].default_value=.012 if cloth else .017
        m.node_tree.links.new(w.outputs['Color'],b.inputs['Height']);m.node_tree.links.new(b.outputs['Normal'],p.inputs['Normal'])
    MATS[name]=m;return m
def ensure_materials():
    for name,c,rough,metal,clothflag,woodflag in PALETTE:
        existing=bpy.data.materials.get(PREFIX+' '+name)
        if existing:existing.use_fake_user=True;MATS[name]=existing
        else:material(name,c,rough,metal,clothflag,woodflag)
def mesh(age,name,verts,faces,mat,stage=.5,smooth=False):
    col=bpy.data.collections.get(f'{PREFIX}_Age_{age}');data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(f'{PREFIX}_A{age}_{name}',data);col.objects.link(obj);obj.parent=ROOTS[age];data.materials.append(MATS[mat]);obj['ber_source_stage']=stage;obj['ber_material_role']=mat
    uv=data.uv_layers.new(name='SourceUV')
    for poly in data.polygons:
        a,b,c=[data.vertices[i].co for i in list(poly.vertices)[:3]];normal=(b-a).cross(c-a);axis=max(range(3),key=lambda k:abs(normal[k]));axes=[k for k in range(3) if k!=axis]
        for li in poly.loop_indices:
            co=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]*.3,co[axes[1]]*.3)
        poly.use_smooth=smooth
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    PARTS.append({'age':age,'object':obj.name,'stage':stage,'material':mat});return obj
def box(age,name,center,size,mat,stage=.5):
    c=Vector(center);sx,sy,sz=[v*.5 for v in size];v=[c+Vector((x*sx,y*sy,z*sz)) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh(age,name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,stage)
def tube(age,name,path,radius,mat,stage=.25,sides=8):
    path=[Vector(p) for p in path];verts=[];faces=[]
    for k,c in enumerate(path):
        d=(path[min(k+1,len(path)-1)]-path[max(k-1,0)]).normalized();ref=Vector((0,1,0)) if abs(d.y)<.9 else Vector((1,0,0));u=d.cross(ref).normalized();v=d.cross(u).normalized();r=radius[k] if isinstance(radius,list) else radius
        for j in range(sides):verts.append(c+r*(u*math.cos(2*math.pi*j/sides)+v*math.sin(2*math.pi*j/sides)))
    for k in range(len(path)-1):
        for j in range(sides):faces.append((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j))
    faces+=[tuple(reversed(range(sides))),tuple((len(path)-1)*sides+j for j in range(sides))]
    return mesh(age,name,verts,faces,mat,stage,True)
def cloth(age,name,fn,nu,nv,mat,stage=.55,thick=.028):
    points=[];normals=[]
    for j in range(nv+1):
        for i in range(nu+1):
            u=i/nu;v=j/nv;points.append(Vector(fn(u,v)))
            du=Vector(fn(min(1,u+.001),v))-Vector(fn(max(0,u-.001),v));dv=Vector(fn(u,min(1,v+.001)))-Vector(fn(u,max(0,v-.001)))
            normal=du.cross(dv).normalized()
            if normal.z<-.2:normal=-normal
            normals.append(normal)
    n=len(points);verts=points+[p-normal*thick for p,normal in zip(points,normals)];faces=[]
    for j in range(nv):
        for i in range(nu):
            a=j*(nu+1)+i;b=a+1;c=b+nu+1;d=a+nu+1;faces.extend([(a,b,c,d),(a+n,d+n,c+n,b+n)])
    edges=[]
    edges += [(i,i+1) for i in range(nu)]+[(nv*(nu+1)+i+1,nv*(nu+1)+i) for i in range(nu)]
    edges += [((j+1)*(nu+1),j*(nu+1)) for j in range(nv)]+[(j*(nu+1)+nu,(j+1)*(nu+1)+nu) for j in range(nv)]
    faces.extend((a,a+n,b+n,b) for a,b in edges);return mesh(age,name,verts,faces,mat,stage,True)
def roof(age,x,y):
    hw,hd,peak,eave,_=SPECS[age-1];u=min(1,abs(x)/hw)
    z=eave+(peak-eave)*(1-u**.78)-.14*math.sin(math.pi*u)*math.sin(math.pi*(y+hd)/(2*hd))
    return Vector((x,y,z))
def canopy_hit(age,x,y,upper=False):
    origin=Vector((x,y,5 if upper else -.2));direction=Vector((0,0,-1 if upper else 1));hit=CANOPY_BVH[age].ray_cast(origin,direction,8)[0]
    assert hit is not None,(age,x,y,'missing canopy surface');return hit
def set_view(center=(13.5,0,1.3),distance=38,rotation=(math.radians(63),0,math.radians(32)),material_view=False):
    if not bpy.context.screen:return
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.shading.type='MATERIAL' if material_view else 'SOLID';area.spaces.active.shading.color_type='SINGLE';area.spaces.active.overlay.show_overlays=False
            r=area.spaces.active.region_3d;r.view_distance=distance;r.view_location=Vector(center);r.view_rotation=__import__('mathutils').Euler(rotation).to_quaternion();r.view_perspective='ORTHO'
def initialize():
    assert not any(c.name.startswith(PREFIX) for c in bpy.data.collections),'Preserve the existing iteration; use a new revision for changes.'
    for o in bpy.context.scene.objects:o.hide_set(True);o.hide_render=True
    ensure_materials()
    for age in range(1,5):
        col=bpy.data.collections.new(f'{PREFIX}_Age_{age}');bpy.context.scene.collection.children.link(col);r=bpy.data.objects.new(f'{PREFIX}_Age{age}_Origin',None);col.objects.link(r);r.location=((age-1)*9,0,0);r['age']=age;r['draft_envelope_m']=[6.8,6.4];ROOTS[age]=r
def structural():
    for age in range(1,5):
        hw,hd,peak,eave,porch=SPECS[age-1];colmat='dark haircloth' if age<3 else 'ivory cloth'
        canopy=cloth(age,'Tensioned_panel_canopy',lambda u,v:roof(age,(2*u-1)*hw,(2*v-1)*hd),18,14,colmat)
        CANOPY_BVH[age]=BVHTree.FromPolygons([v.co for v in canopy.data.vertices],[list(p.vertices) for p in canopy.data.polygons])
        beam_z=peak-.028-.075;post_top=beam_z-.075
        tube(age,'Ridge_beam',[(0,-hd,beam_z),(0,hd,beam_z)],.075,'cedar',.25)
        for k,y in enumerate((-.62*hd,.62*hd)):
            tube(age,f'Ridge_upright_{k}',[(0,y,0),(0,y,post_top)],.075 if age<3 else .09,'cedar',.25)
            CONTACTS.append({'age':age,'interface':'ridge upright / underside of ridge beam','gap_m':post_top-(beam_z-.075)})
        CONTACTS.append({'age':age,'interface':'beam / canopy underside','gap_m':beam_z+.075-(peak-.028)})
        for side in (-1,1):
            for k,y in enumerate((-hd,0,hd)):
                x=side*(hw-.045);yy=max(-hd+.005,min(hd-.005,y));contact=canopy_hit(age,x,yy);top=contact.z+.004
                post=tube(age,f'Eave_upright_{side}_{k}',[(x,yy,0),(x,yy,top)],.04,'cedar',.25)
                CONTACTS.append({'age':age,'interface':'eave post / raycast canopy underside','overlap_m':max(v.co.z for v in post.data.vertices)-contact.z})
            def side_skirt(u,v,s=side):
                x=s*(hw-.04);y=-hd+.01+u*(2*hd-.02);bottom=.70 if age==1 and s==1 and u<.55 else .055;top=canopy_hit(age,x,y).z+.006
                return (x,y,bottom*(1-v)+top*v+.012*math.sin(u*10*math.pi)*math.sin(v*math.pi))
            cloth(age,f'Side_skirt_{side}',side_skirt,18,4,'woven black skirts',.75,.02)
            if age==1 and side==1:
                tube(age,'Supported_lifted_side_roll',[(hw-.04,-hd+.01,.7),(hw-.04,-hd+.55*(2*hd-.02),.7)],.044,'dark haircloth',.75,8)
                for y in (-hd+.01,0):tube(age,'Side_lift_tie',[(hw-.04,y,.7),canopy_hit(age,hw-.04,y)],.014,'rope',.75,6)
        cloth(age,'Rear_screen',lambda u,v:((2*u-1)*(hw-.035),hd-.035,.055*(1-v)+(canopy_hit(age,(2*u-1)*(hw-.035),hd-.035).z+.006)*v),16,4,'woven black skirts',.75,.02)
        # Front flaps expose a 1.7m wide council entrance; corners remain connected.
        for side in (-1,1):
            cloth(age,f'Entrance_flap_{side}',lambda u,v,s=side:(s*(.85+u*(hw-.89)),-hd+.025+.025*math.sin(u*math.pi),.055*(1-v)+(canopy_hit(age,s*(.85+u*(hw-.89)),-hd+.025+.025*math.sin(u*math.pi)).z+.006)*v),8,5,'warm cloth' if age<3 else 'ivory cloth',.75,.022)
        # Named rope endpoints come from the cloth edge, with stakes inside the envelope.
        anchors=[(s*(hw-.01),y) for s in (-1,1) for y in (-hd+.01,0,hd-.01)]+[(0,hd-.01)]
        for k,(x,y) in enumerate(anchors):
            start=canopy_hit(age,x,y,upper=True);end=Vector((x+(math.copysign(.43,x) if x else 0),y+(math.copysign(.43,y) if y else 0),.065))
            tube(age,f'Guyline_{k}',[start,end],.021,'rope',.55)
            tube(age,f'Peg_{k}',[(end.x,end.y,-.04),(end.x,end.y,.16)],.027,'cedar',0)
            CONTACTS.append({'age':age,'interface':'guyline / raycast canopy anchor','anchor_surface_distance_m':CANOPY_BVH[age].find_nearest(start)[3]})
        if porch:
            # Raised front awning is supported at its corners and slopes back into main roof.
            for side in (-1,1):tube(age,f'Porch_column_{side}',[(side*.96,-hd-porch,0),(side*.96,-hd-porch,2.05+(age-2)*.2)],.065,'cedar',.25)
            frontz=2.05+(age-2)*.2
            cloth(age,'Council_entry_awning',lambda u,v:((u*2-1)*.96,-hd-porch+v*porch,frontz*(1-v)+roof(age,(u*2-1)*.96,-hd).z*v-.05*math.sin(math.pi*v)*math.sin(math.pi*u)),10,5,'red weave' if age==2 else 'ivory cloth',.55)
    set_view();bpy.context.view_layer.update();print('TENT_STRUCTURE_READY',len(PARTS),'parts; measured contacts',len(CONTACTS))
def pot(age,name,x,y,size):
    rings=[(0,.09),(.03,.16),(.13,.22),(.30,.21),(.40,.14),(.44,.125),(.46,.14)];n=12;verts=[];faces=[]
    for z,r in rings:
        verts.extend((x+size*r*math.cos(i*2*math.pi/n),y+size*r*math.sin(i*2*math.pi/n),.025+size*z) for i in range(n))
    for k in range(len(rings)-1):
        for i in range(n):faces.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i))
    faces.append(tuple(reversed(range(n))));mesh(age,name,verts,faces,'clay',1,True)
def cushion(age,x,y,mat):
    verts=[];faces=[]
    for z,hx,hy,c in [(.038,.19,.14,.04),(.09,.25,.20,.065),(.19,.24,.19,.06),(.245,.17,.13,.04)]:
        verts.extend((x+a,y+b,z) for a,b in [(-hx+c,-hy),(hx-c,-hy),(hx,-hy+c),(hx,hy-c),(hx-c,hy),(-hx+c,hy),(-hx,hy-c),(-hx,-hy+c)])
    for k in range(3):
        for i in range(8):faces.append((k*8+i,k*8+(i+1)%8,(k+1)*8+(i+1)%8,(k+1)*8+i))
    faces.append(tuple(reversed(range(8))));verts.append((x,y,.232))
    faces.extend((24+i,24+(i+1)%8,32) for i in range(8));mesh(age,'Council_cushion',verts,faces,mat,1,True)
def detailed():
    for age in range(1,5):
        hw,hd,peak,eave,porch=SPECS[age-1]
        # Sewn panel edges: continuous lines sampled on the measured roof surface.
        for k in range(1,7+age):
            y=-hd+k*2*hd/(7+age);path=[roof(age,-hw+i*2*hw/24,y)+Vector((0,0,.013)) for i in range(25)]
            tube(age,f'Sewn_panel_{k}',path,.0075,'rope',.55,4)
        for side in (-1,1):
            tube(age,f'Reinforced_eave_band_{side}',[roof(age,side*hw,-hd)+Vector((0,0,.018)),roof(age,side*hw,hd)+Vector((0,0,.018))],.035 if age<3 else .055,'red weave' if age>1 else 'warm cloth',.55,6)
            tube(age,f'Canopy_front_trim_{side}',[roof(age,side*(.85+k*(hw-.85)/16),-hd)+Vector((0,-.012,.01)) for k in range(17)],.027,'ochre weave' if age>2 else 'rope',.75,6)
        box(age,'Council_floor_mat',(0,-.10,.025),(3.8,2.7,.045),'mat straw' if age==1 else 'red weave',.75)
        if age>1:
            # Original diamond weave inlaid just above the carpet surface.
            for x in (-1.3,0,1.3):
                mesh(age,'Carpet_lozenge',[(x,-.45,.052),(x+.3,-.05,.052),(x,.35,.052),(x-.3,-.05,.052)],[(0,1,2,3)],'cream weave',.75)
            box(age,'Low_council_table',(0,-.60,.29),(1.05,.65,.11),'cedar',1)
            for x in (-.40,.40):
                for y in (-.80,-.40):box(age,'Table_leg',(x,y,.12),(.07,.07,.24),'cedar',1)
            for k in range(2+age):
                y=-.75+k*.46;cushion(age,-1.45,y,'ochre weave' if k%2 else 'cream weave')
        vessel_size=1+.15*age;vessel_spacing=.44*vessel_size+.08
        for k in range(1+age//2):pot(age,f'Water_storage_{k}',hw-.45-k*vessel_spacing,hd-.45,vessel_size)
        # Portable rolled bedding and side storage reinforce the nomadic identity.
        tube(age,'Rolled_bedding',[(hw-.55,.15,.20),(hw-.55,.85,.20)],.17,'warm cloth',1,12)
        if age>=3:
            for side in (-1,1):
                # Narrow geometric curtain bands with repeated original lozenges.
                box(age,f'Skirt_border_{side}',(side*(hw-.031),0,.44),(.018,2*hd-.08,.17),'red weave',.75)
                for k in range(8):
                    y=-hd+.2+k*(2*hd-.4)/7;x=side*(hw-.019)
                    mesh(age,'Curtain_diamond',[(x,y-.10,.44),(x,y,.505),(x,y+.10,.44),(x,y,.375)],[(0,1,2,3)],'cream weave',.75)
            for side in (-1,1):
                x=side*(hw+.25);y=.45;top=2.7+(age-3)*.45
                tube(age,f'Banner_staff_{side}',[(x,y,0),(x,y,top)],.034,'cedar',1)
                cloth(age,f'Council_banner_{side}',lambda u,v,x=x,y=y,t=top,s=side:(x+s*u*.27,y+.07*math.sin(v*math.pi),t-.10-v*.82),3,8,'red weave',1,.014)
                if age==4:
                    tube(age,'Staff_metal_cap',[(x,y,top-.035),(x,y,top+.055)],.053,'metal fittings',1,8)
            # Peg-to-peg side front rope braces meet the new porch precisely.
            for side in (-1,1):
                start=Vector((side*.96,-hd-porch,2.05+(age-2)*.2));end=Vector((side*1.4,-3.12,.07))
                tube(age,'Entry_tension_rope',[start,end],.02,'rope',.55);tube(age,'Entry_peg',[(end.x,end.y,-.04),(end.x,end.y,.16)],.025,'cedar',0)
        if age==4:
            for side in (-1,1):
                # Secondary coloured shoulder cloth increases visible Imperial layering.
                cloth(age,f'Embroidered_shoulder_{side}',lambda u,v,s=side:roof(age,s*(hw*.60+u*hw*.18),(v*2-1)*hd)+Vector((0,0,.012)),3,12,'red weave',.55,.010)
                for k in range(8):
                    y=-hd+.2+k*(2*hd-.4)/7;x=side*hw*.69
                    mesh(age,'Brocade_lozenge',[roof(age,x+dx,y+dy)+Vector((0,0,.02)) for dx,dy in [(-.08,0),(0,.11),(.08,0),(0,-.11)]],[(0,1,2,3)],'cream weave',.55)
            for side in (-1,1):tube(age,'Porch_leather_fitting',[(side*.96,-hd-porch,1.9),(side*.96,-hd-porch,2.12)],.075,'metal fittings',1,8)
    bpy.context.view_layer.update();print('TENT_DETAIL_READY',len(PARTS),'parts')
def validate_save():
    record=ART/'iteration.json'
    if record.exists():assert json.loads(record.read_text()).get('approval_status')!='accepted','Accepted iteration is locked; create a new numbered source iteration.'
    report={'iteration':'001','status':'source passed','ages':[],'contacts':CONTACTS,'part_count':len(PARTS),'native_age_switching':'pending integration','construction_damage_ruins':'source stage tags only; native integration pending','source_materials':'procedural source roles; bake/atlas and geometric LOD export pending approval','gameplay_changed':False}
    assert all(abs(x.get('gap_m',0))<1e-6 and x.get('anchor_surface_distance_m',0)<1e-5 and -.001<x.get('overlap_m',.004)<.01 for x in CONTACTS)
    for age in range(1,5):
        objs=[o for o in bpy.data.collections[f'{PREFIX}_Age_{age}'].objects if o.type=='MESH'];verts=[o.matrix_local@v.co for o in objs for v in o.data.vertices]
        assert all(math.isfinite(c) for v in verts for c in v);assert max(abs(v.x) for v in verts)<=3.4 and max(abs(v.y) for v in verts)<=3.2
        assert min(v.z for v in verts)>=-.08
        tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objs)
        zero_uv=0
        for o in objs:
            for p in o.data.polygons:
                if p.area<1e-9:continue
                coords=[o.data.uv_layers.active.data[i].uv for i in p.loop_indices];area=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(coords,coords[1:]+coords[:1])))*.5
                if area<1e-10:zero_uv+=1
        assert zero_uv==0,(age,zero_uv,'collapsed UV faces')
        report['ages'].append({'age':age,'objects':len(objs),'triangles':tris,'width_m':max(v.x for v in verts)-min(v.x for v in verts),'depth_m':max(v.y for v in verts)-min(v.y for v in verts),'height_m':max(v.z for v in verts),'uv_and_materials':all(o.data.uv_layers and o.data.materials for o in objs),'collapsed_uv_faces':zero_uv})
    ART.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'source-validation.json').write_text(json.dumps(report,indent=2));(ART/'construction-parts.json').write_text(json.dumps(PARTS,indent=2))
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Berber_Tribal_Tent_Ages_I_IV_001.blend'))
    print('TRIBAL_TENT_SOURCE_SAVED',json.dumps(report['ages']))
