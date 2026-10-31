"""Refine Tuareg art on stock weighted anatomy, with unique UV/PBR atlases."""
import bpy,bmesh,sys,os,json,math,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/tuareg_refined';WORK=ROOT/'output/tuareg_refined_trial'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent));sys.path.insert(0,str(ART));sys.path.insert(0,str(ROOT/'art/tuareg_overhaul'))
import garrison;garrison.register()
from garrison import game_library,unit_prototype_panel as proto,unit_export,asset_authoring,material_adoption,unit_animation
from mesh_runner import MeshRecipe
from bake_atlas import bake,pin_uv
scene=bpy.context.scene;scene.name='Refined Tuareg Ages I-IV'
scene.garrison.asset_library_root=str(ART/'garrison_library')
scene.garrison.game_asset_connection=str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.local.json')
scene.garrison.game_asset_index=str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.sqlite3')
doc=json.loads(next((ROOT/'output/tuareg_art_guard_trial/prototype').rglob('prototype.json')).read_text())
reference=bpy.data.collections.new('Reference originals - unchanged');scene.collection.children.link(reference)
report={'schema':'tuareg-refined-art/v1','ages':[],'equipment':[],'animation':'inherited stock motion, immediate moving switching not qualified','spearman_skeleton_bones':48}
def keep_reference(root):
    for o in [root,*root.children_recursive]:
        reference.objects.link(o)
        for c in list(o.users_collection):
            if c!=reference:c.objects.unlink(o)
        o.hide_set(True);o.hide_render=True
def authored_material(name,colour,roughness=.82,metal=0,cloth=False,leather=False,owner=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;m['tuareg_owner_mask']=owner
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*colour,1);p.inputs['Roughness'].default_value=roughness;p.inputs['Metallic'].default_value=metal
    if cloth or leather:
        tex=m.node_tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=100 if cloth else 38;tex.inputs['Detail'].default_value=3
        ramp=m.node_tree.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color=(*(c*.72 for c in colour),1);ramp.color_ramp.elements[1].color=(*(min(1,c*1.18) for c in colour),1)
        m.node_tree.links.new(tex.outputs['Fac'],ramp.inputs['Fac']);m.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
        micro=m.node_tree.nodes.new('ShaderNodeTexNoise');micro.inputs['Scale'].default_value=320 if cloth else 190;micro.inputs['Detail'].default_value=2
        bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.17;bump.inputs['Distance'].default_value=.0012
        m.node_tree.links.new(micro.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m
def tint_material(source,name,colour):
    m=source.copy();m.name=name;pin_uv(m)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');socket=p.inputs['Base Color']
    old=socket.links[0].from_socket if socket.is_linked else None
    gray=m.node_tree.nodes.new('ShaderNodeRGBToBW');mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*colour,1)
    if old:m.node_tree.links.new(old,gray.inputs[0])
    m.node_tree.links.new(gray.outputs[0],mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],socket)
    return m
def object_from_recipe(r,collection,mat,rig=None,smooth=True):
    o=r.object(collection,mat,rig);o.data.uv_layers[0].name='UVMap'
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o
def join(objects,active):
    for o in bpy.context.selected_objects:o.select_set(False)
    for o in objects:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=active;bpy.ops.object.join();return active
def classify_skin(mesh,source):
    contract=json.loads(source['garrison_generic_preview_contract_json']);path=contract['connected']['pattern']['projection_path'];im=bpy.data.images.load(path,check_existing=True)
    width,height=im.size;pixels=list(im.pixels);uv=mesh.data.uv_layers.active
    def mask(poly):
        values=[]
        for i in poly.loop_indices:
            u,v=uv.data[i].uv;px=min(width-1,max(0,int(u*width)));py=min(height-1,max(0,int(v*height)));values.append(pixels[(py*width+px)*4+1])
        return sum(values)/len(values)
    return mask

for age in range(1,5):
    print('BUILD_AGE',age,flush=True)
    stock=json.loads(next((ROOT/f'output/tuareg_shield_test/decoded/age{age}').rglob('decoded-static.json')).read_text())
    empty=bpy.data.objects.new(f'Abbasid age{age} original',None);scene.collection.objects.link(empty)
    original_root=game_library._apply_decoded_static(empty,stock,select_result=False,create_controls=False)
    stockrig=next(o for o in original_root.children_recursive if o.type=='ARMATURE');stockrig.data.pose_position='REST'
    original=next(o for o in original_root.children_recursive if o.type=='MESH' and 'lod1' in o.name and any(m.type=='ARMATURE' for m in o.modifiers))
    skin_mask=classify_skin(original,original.data.materials[0]);source=original.data.materials[0]
    categories=[];remove=[]
    for poly in original.data.polygons:
        center=sum((original.data.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)
        skin=skin_mask(poly)>.30
        if center.z>1.6 and not (skin and center.y<-.045 and center.z<1.765):remove.append(poly.index)
        categories.append(0 if skin or center.z<.20 else 2 if age>=3 and center.z>1.12 and abs(center.x)<.245 else 1)
    rig=proto.create_unit(doc,bpy.context);rig.name=f'Refined_Age_{age}_NativeRig';collection=rig.users_collection[0]
    error=max(abs(a-b) for bone in rig.data.bones for ar,br in zip(bone.matrix_local,stockrig.data.bones[bone.name].matrix_local) for a,b in zip(ar,br));assert error<1e-4
    body=original.copy();body.data=original.data.copy();body.animation_data_clear();collection.objects.link(body);body.name=f'Tuareg_Refined_Age_{age}'
    body.parent=rig;body.matrix_parent_inverse=Matrix.Identity(4);body.matrix_basis=Matrix.Identity(4)
    for m in body.modifiers:
        if m.type=='ARMATURE':m.object=rig
    body.hide_set(False);body.hide_render=False
    neutral=source.copy();neutral.name=f'Native skin leather detail age{age}';pin_uv(neutral)
    cloth=tint_material(source,f'Woven native cloth age{age}',(.48,.56,.63) if age==1 else (.24,.43,.72))
    armor=source.copy();armor.name=f'Native armour detail age{age}';pin_uv(armor)
    body.data.materials.clear()
    for m in (neutral,cloth,armor):body.data.materials.append(m)
    for poly,index in zip(body.data.polygons,categories):poly.material_index=index
    bm=bmesh.new();bm.from_mesh(body.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES');bm.to_mesh(body.data);bm.free()
    # Preserve native weights, improving garment silhouette instead of replacing anatomy with tubes.
    for v in body.data.vertices:
        if .52<v.co.z<1.02 and abs(v.co.x)<.31:
            factor=1+.045*math.sin((v.co.z-.52)/.50*math.pi);v.co.x*=factor
    names={g.index:g.name for g in body.vertex_groups};weights=[{names[g.group]:g.weight for g in v.groups} for v in body.data.vertices]
    kd=KDTree(len(body.data.vertices))
    for i,v in enumerate(body.data.vertices):kd.insert(v.co,i)
    kd.balance()
    def front_y(x,z):
        hit,location,normal,index=body.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
        return location.y-.009 if hit else -.19
    def fitted_waist(recipe,zvalues,gap,label):
        points=[];w=[];fs=[];count=32
        for z in zvalues:
            for j in range(count):
                angle=2*math.pi*j/count;direction=Vector((math.cos(angle),math.sin(angle),0))
                hit,location,normal,index=body.ray_cast(Vector((.36*direction.x,.36*direction.y,z)),-direction)
                assert hit,(age,label,z,j)
                point=location+direction*gap;points.append(point);w.append(weight_at(point))
        for j in range(count):fs.append((j,(j+1)%count,count+(j+1)%count,count+j))
        recipe.part(points,fs,w,0,label)
    def weight_at(point):
        merged={}
        for co,i,d in kd.find_n(Vector(point),3):
            for name,w in weights[i].items():merged[name]=merged.get(name,0)+w/max(d,.008)**2
        rows=sorted(merged.items(),key=lambda p:p[1],reverse=True)[:4];s=sum(w for n,w in rows);return {n:w/s for n,w in rows}
    indigo=authored_material('Hand woven indigo '+str(age),(.10,.17,.27) if age>1 else (.25,.28,.30),cloth=True)
    light=authored_material('Wrap folds '+str(age),(.12,.205,.32) if age>1 else (.32,.34,.35),cloth=True)
    leather=authored_material('Dark travel leather '+str(age),(.13,.065,.027),leather=True)
    team=authored_material('Owner cloth stripe '+str(age),(.68,.68,.64),cloth=True,owner=1)
    parts=[];hw={'metarig_head':1}
    # One continuous wrapped cap with diagonal folds, instead of stacked ring primitives.
    r=MeshRecipe('Tailored headwrap age'+str(age));points=[];vw=[];faces=[];n=32
    profile=[(1.765,.119,.126),(1.790,.124,.127),(1.815,.120,.122),(1.841,.114,.115),(1.866,.101,.101),(1.890,.073,.073),(1.905,.020,.020)]
    for k,(z,rx,ry) in enumerate(profile):
        for j in range(n):
            a=2*math.pi*j/n;wave=.0045*math.sin(a*3+k*.9);front=max(0,-math.sin(a));zz=z+max(0,.009-k*.003)*front+.004*math.sin(a*2+k*.7)
            points.append(((rx+wave)*math.cos(a),.004+(ry+wave)*math.sin(a),zz));vw.append(hw)
    for k in range(len(profile)-1):
        for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    faces.append(tuple((len(profile)-1)*n+j for j in range(n)))
    r.part(points,faces,vw,0,'connected diagonal cloth wrap');parts.append(object_from_recipe(r,collection,light,rig))
    # A single connected spiral fold seats on the crown and gives readable wrapped cloth.
    r=MeshRecipe('Continuous spiral wrap fold '+str(age));pts=[];w=[];fs=[]
    for k in range(113):
        angle=5*math.pi*k/112;z=1.782+.080*k/112+.008*math.sin(angle)
        for edge_z in (-.009,.009):
            zz=z+edge_z
            lo,hi=next((a,b) for a,b in zip(profile,profile[1:]) if a[0]<=zz<=b[0]);t=(zz-lo[0])/(hi[0]-lo[0])
            rx=lo[1]*(1-t)+hi[1]*t+.008;ry=lo[2]*(1-t)+hi[2]*t+.008
            pts.append((rx*math.cos(angle),.004+ry*math.sin(angle),zz));w.append(hw)
    for k in range(112):fs.append((2*k,2*k+1,2*k+3,2*k+2))
    r.part(pts,fs,w,0,'seated continuous diagonal wrap');parts.append(object_from_recipe(r,collection,indigo,rig))
    r=MeshRecipe('Face veil age'+str(age));points=[];faces=[];vw=[]
    for k,(z,rx,ry) in enumerate([(1.61,.075,.105),(1.65,.102,.140),(1.69,.116,.180),(1.735,.116,.176)]):
        for j in range(n):
            a=2*math.pi*j/n;front=max(0,-math.sin(a));fold=.003*math.sin(5*a+k*1.5)
            points.append(((rx+fold)*math.cos(a),-.008+(ry+fold)*math.sin(a),z+.009*front*math.sin(2*a)));vw.append(hw)
    for k in range(3):
        for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    r.part(points,faces,vw,0,'draped face veil');parts.append(object_from_recipe(r,collection,indigo,rig))
    r=MeshRecipe('Draped scarf age'+str(age));r.rings([((0,0,1.54),.098,.088,{'metarig_neck1':1}),((0,0,1.62),.087,.087,hw)],0,'wrapped neck bridge',False)
    for x in (-.055,.055):
        pts=[(x+dx,.14+.012*math.sin(k),1.78-k*.065) for k in range(8) for dx in (-.036,.036)]
        r.part(pts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(7)],[hw if p[2]>1.66 else weight_at(p) for p in pts],0,'folded scarf tail')
    parts.append(object_from_recipe(r,collection,indigo,rig))
    # Tailored curved split skirt panels with multiple folds and transferred weights.
    r=MeshRecipe('Layered desert cloth age'+str(age))
    for side in (-1,1):
        for front in (-1,1):
            pts=[];w=[];fs=[];columns=7;rows=7
            for k in range(rows):
                z=1.035-k*.069
                for j in range(columns):
                    t=j/(columns-1);x=side*(.025+(.21+k*.004)*t)
                    y=front*(.163+.025*(1-t)+.009*math.cos(3*t*math.pi+k*.6)+k*.003)
                    p=(x,y,z+.012*math.sin(t*math.pi));pts.append(p);w.append(weight_at(p))
            for k in range(rows-1):
                for j in range(columns-1):a=k*columns+j;fs.append((a,a+1,a+columns+1,a+columns))
            r.part(pts,fs,w,0,'draped split panel')
    parts.append(object_from_recipe(r,collection,indigo,rig))
    r=MeshRecipe('Sashes age'+str(age));fitted_waist(r,(1.035,1.075),.010,'surface fitted leather belt')
    parts.append(object_from_recipe(r,collection,leather,rig))
    r=MeshRecipe('Team stripe age'+str(age));fitted_waist(r,(1.076,1.098),.012,'visible surface fitted owner edge')
    parts.append(object_from_recipe(r,collection,team,rig))
    if age>=2:
        r=MeshRecipe('Leather baldric age'+str(age));pts=[];w=[]
        for k in range(10):
            z=1.46-k*.040;x=-.15+k*.029
            for dx in (-.019,.019):
                p=(x+dx,front_y(x+dx,z),z);pts.append(p);w.append(weight_at(p))
        r.part(pts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(9)],w,0,'curved shoulder strap');parts.append(object_from_recipe(r,collection,leather,rig))
    if age>=3:
        r=MeshRecipe('Armour tabard age'+str(age));pts=[];w=[];fs=[]
        for k in range(7):
            z=1.47-k*.055
            for j in range(5):
                x=(j-2)*.035;y=front_y(x,z)-.004;p=(x,y,z);pts.append(p);w.append(weight_at(p))
        for k in range(6):
            for j in range(4):a=k*5+j;fs.append((a,a+1,a+6,a+5))
        r.part(pts,fs,w,0,'fitted cloth over native armour');parts.append(object_from_recipe(r,collection,indigo,rig))
    keep_reference(original_root);body=join([body,*parts],body)
    # Source material texture detail, unique UVs and original authored wrap surfaces share one atlas.
    mat,paths=bake(body,ART/f'exports/tuareg_age{age}',1024)
    rig.garrison_unit.mesh=body;rig.garrison_unit.build_name=f'tuareg_age{age}'
    folder=ART/f'exports/tuareg_age{age}'
    unit_export.export_unit_model(rig,[body],folder/'model.fbx',unit_export.skeleton_records(rig),three_lods=True,lod_counts=doc['prototype']['lod_counts'])
    action=proto.export_document(rig);action['material_name']=mat.name;action['textures']=list(paths);(folder/'action.json').write_text(json.dumps(action))
    tri=sum(len(p.vertices)-2 for p in body.data.polygons);assert tri<=6000
    report['ages'].append({'age':age,'vertices':len(body.data.vertices),'triangles':tri,'bind_matrix_error':error,'maximum_influences':max(len(v.groups) for v in body.data.vertices),'source_stock_geometry':stock['request']['logical_path'],'atlas_resolution':1024,'new_uv':'unique unwrap, native source UV preserved for baking'})
    rig.parent.location.x=(age-1)*1.9

# Equipment is refined separately; the native hand origins stay fixed.
def equipment(name,objects,active):
    obj=join(objects,active);obj.name=name;mat,paths=bake(obj,ART/f'equipment/{name}',1024)
    props=scene.garrison;props.author_collection=None;props.author_display_name=name;props.author_asset_id=name;props.author_namespace='tuareg';props.author_catalog_folder='Refined Tuareg equipment'
    for o in bpy.context.selected_objects:o.select_set(False)
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    assert bpy.ops.garrison.create_static_container()=={'FINISHED'};material_adoption.adopt_material(mat)
    export=asset_authoring._export_asset(bpy.context,props)
    report['equipment'].append({'name':name,'vertices':len(obj.data.vertices),'export':{k:str(v) for k,v in export.items()}})
    return obj
leather=authored_material('Agher hide',(.23,.115,.045),leather=True);edge=authored_material('Rawhide bindings',(.09,.038,.016),leather=True);paint=authored_material('Mineral ochre markings',(.64,.47,.23),.89)
equip=bpy.data.collections.new('Refined equipment sources');scene.collection.children.link(equip)
r=MeshRecipe('Curved hide shield');pts=[];faces=[];levels=17;cols=9
for back in (False,True):
    for k in range(levels):
        t=k/(levels-1);z=-.53+t*1.15
        half=.30-.060*math.exp(-((t-.50)/.18)**2)-.17*(abs(2*t-1)**5)
        for j in range(cols):
            u=-1+2*j/(cols-1);x=-.12+u*half;y=.065+(.060 if not back else .037)*(1-u*u)
            pts.append((x,y,z))
size=levels*cols
for side in range(2):
    offset=side*size
    for k in range(levels-1):
        for j in range(cols-1):a=offset+k*cols+j;f=(a,a+1,a+cols+1,a+cols);faces.append(f if side==0 else tuple(reversed(f)))
for k in range(levels-1):
    for j in (0,cols-1):a=k*cols+j;faces.append((a,a+cols,a+cols+size,a+size))
for k in (0,levels-1):
    for j in range(cols-1):a=k*cols+j;faces.append((a,a+size,a+1+size,a+1))
r.part(pts,faces,{},0,'bowed leather shell');shell=object_from_recipe(r,equip,leather)
# Fit offset is derived by a separate sampled-pose proof. Use a conservative lower placement initially.
fit=WORK/'shield-fit.json'
offset=Vector(json.loads(fit.read_text())['recommended_offset'] if fit.exists() else (.04,0,-.24))
shell.data.transform(Matrix.Translation(offset));shell['shield_face_offset']=list(offset)
parts=[shell]
r=MeshRecipe('Seated rawhide border')
for j in (0,cols-1):
    path=[Vector(pts[k*cols+j])+offset+Vector((0,.004,0)) for k in range(levels)]
    r.tube(path,[.009]*levels,[{}]*levels,0,'continuous sewn edge',8)
for k in (0,levels-1):
    path=[Vector(pts[k*cols+j])+offset+Vector((0,.004,0)) for j in range(cols)]
    r.tube(path,[.009]*cols,[{}]*cols,0,'seated cap border',8)
# Grip stays at 0. Its mounts seat near the upper quarter of the lowered face.
def back_y(x,z):
    t=(z-offset.z+.53)/1.15;half=.30-.060*math.exp(-((t-.50)/.18)**2)-.17*(abs(2*t-1)**5)
    u=(x-offset.x+.12)/half;assert abs(u)<1
    return offset.y+.065+.037*(1-u*u)
r.tube([(0,back_y(0,-.14),-.14),(0,0,-.085),(0,0,.085),(0,back_y(0,.14),.14)],[.015]*4,[{}]*4,0,'upper hand grip and seated straps',8)
parts.append(object_from_recipe(r,equip,edge))
r=MeshRecipe('Agher original painted motifs')
for z in (-.29,.28):
    p=[Vector((-.12,.128,z+.07))+offset,Vector((-.04,.124,z))+offset,Vector((-.12,.128,z-.07))+offset,Vector((-.20,.124,z))+offset]
    r.part(p,[(0,1,2,3)],{},0,'painted diamond')
parts.append(object_from_recipe(r,equip,paint));shield=equipment('tuareg_agher_refined',parts,shell)
report['shield']={'height_m':1.15,'face_offset':list(offset),'grip_origin':[0,0,0],'pose_fit':'evaluate with check_shield_fit.py; sampled bounds do not establish native clearance'}

wood=authored_material('Desert hardwood spear shaft',(.25,.14,.052),.77,leather=True)
steel=authored_material('Forged spear steel',(.36,.39,.40),.43,.86)
wrap=authored_material('Spear hand leather',(.085,.043,.020),.86,leather=True)
r=MeshRecipe('Long spear shaft');r.tube([(0,0,-.98),(0,0,2.825),(0,0,2.915)],[.015,.015,.012],[{}]*3,0,'75 percent longer shaft, forward extension',12)
shaft=object_from_recipe(r,equip,wood);parts=[shaft]
r=MeshRecipe('Long spear forged steel');r.tube([(0,0,2.815),(0,0,2.985)],[.025,.019],[{}]*2,0,'socket',12)
pts=[(0,0,2.955),(-.047,0,3.105),(0,0,3.355),(.047,0,3.105),(0,-.012,3.115),(0,.012,3.115)]
r.part(pts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],{},0,'unchanged size leaf head')
r.tube([(0,0,-1.02),(0,0,-.97)],[.012,.017],[{}]*2,0,'unchanged butt ferrule',10)
parts.append(object_from_recipe(r,equip,steel,smooth=False))
r=MeshRecipe('Bound spear grip');r.tube([(0,0,-.13),(0,0,.13)],[.020,.020],[{}]*2,0,'native origin hand grip',12)
parts.append(object_from_recipe(r,equip,wrap));spear=equipment('tuareg_long_spear_refined',parts,shaft)
z=[v.co.z for v in spear.data.vertices];assert abs((max(z)-min(z))-4.375)<1e-5
report['spear']={'length_m':max(z)-min(z),'previous_length_m':2.5,'increase_percent':75,'head_width_m':.094,'grip_origin':[0,0,0],'butt_z_m':min(z),'extension':'shaft head side only; grip, thickness, head and butt position preserved'}
shield.location=(0,2,1);spear.location=(2,2,1)
for o in scene.objects:
    if o.type=='ARMATURE':o.hide_set(True);o.hide_render=True
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Tuareg_Refined_Ages_I_IV.blend'))
(WORK/'art-source-checks.json').write_text(json.dumps(report,indent=2));print('REFINED_SOURCE_READY',flush=True)
