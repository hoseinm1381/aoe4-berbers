"""Build four editable Saharan Tuareg skins and equipment using Garrison's public exporters.

Stock joint hierarchy and exposed hands/feet are construction references. All clothing,
headwear, shield and spear surfaces are new recipe geometry. No animation export claims.
"""
import bpy, importlib, json, math, os, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/tuareg_overhaul';WORK=ROOT/'output/tuareg_art_guard_trial'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT.parent));sys.path.insert(0,str(ART))
import garrison;garrison.register()
from garrison import unit_prototype_panel as prototype, unit_export, game_library, asset_authoring, material_adoption
from mesh_runner import MeshRecipe
scene=bpy.context.scene;scene.name='Tuareg original art Ages I-IV'
scene.garrison.asset_library_root=str(ART/'garrison_library')
scene.garrison.game_asset_connection=str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.local.json')
scene.garrison.game_asset_index=str(Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/game-assets.sqlite3')
doc=json.loads(next((WORK/'prototype').rglob('prototype.json')).read_text())
sources=ART/'exports';sources.mkdir(parents=True,exist_ok=True)
textures=ART/'textures';textures.mkdir(exist_ok=True)
report={'schema':'tuareg-original-art/v1','ages':[],'contacts':[],'stock_skeleton':'unchanged English Spearman Age II, 48 bones; native Tuareg motion retained','animation_status':'no custom motion exported'}

def atlas(age=2):
    import numpy as np
    # Original tile atlas. Indigo is an artistic Tuareg reference, not a medieval dating claim.
    colours=[(.07,.12,.27),(.76,.66,.47),(.26,.11,.055),(.40,.245,.14),(.012,.012,.018),(.55,.58,.61),(.64,.47,.21),(.64,.66,.70),(.28,.31,.34),(.42,.22,.09),(.82,.75,.60),(.22,.31,.45),(.62,.43,.24),(.12,.055,.025),(.80,.80,.72),(.10,.14,.19)]
    if age==1:colours[0]=(.26,.28,.31)
    if age==4:colours[0]=(.045,.08,.19);colours[6]=(.76,.59,.32)
    size=512; yy,xx=np.mgrid[:size,:size];tile=(xx//128)+(yy//128)*4
    base=np.asarray(colours)[tile]
    grain=.965+.035*np.sin(xx*1.93+yy*2.7)+.012*np.sin(xx*.41-yy*.67)
    albedo=np.clip(base*grain[:,:,None],0,1)
    # Fine woven lines and interlocking mail rings, distinct materials in one atlas.
    weave=1-.07*((xx%6==0)|(yy%7==0));albedo*=np.where(np.isin(tile,[0,1,7,10,11,15]),weave,1)[:,:,None]
    cx=(xx%12)-6;cy=(yy%10)-5;ring=((cx/5)**2+(cy/4)**2)
    albedo*=np.where((tile==8)&(ring>.65)&(ring<1.3),.55,1)[:,:,None]
    maps={'albedo':albedo,'roughness':np.repeat(np.where(np.isin(tile,[5,6,8]),.52,.86)[:,:,None],3,2),
          'metalness':np.repeat(np.where(np.isin(tile,[5,8]),.83,np.where(tile==6,.5,0))[:,:,None],3,2),
          'pattern':np.stack([np.where(tile==7,1.,0),np.zeros((size,size)),np.zeros((size,size))],2)}
    paths={}
    for role,data in maps.items():
        im=bpy.data.images.new(f'Tuareg age{age} {role}',width=size,height=size,alpha=True)
        if role!='albedo':im.colorspace_settings.name='Non-Color'
        rgba=np.concatenate([data,np.ones((size,size,1))],2).astype('float32');im.pixels.foreach_set(rgba.ravel())
        im.filepath_raw=str(textures/f'age{age}_{role}.png');im.file_format='PNG';im.save();paths[role]=im.filepath_raw
    mat=bpy.data.materials.new(f'Tuareg age{age} atlas');mat.use_nodes=True
    p=mat.node_tree.nodes.get('Principled BSDF')
    for role,input_name in [('albedo','Base Color'),('roughness','Roughness'),('metalness','Metallic')]:
        n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images[f'Tuareg age{age} {role}'];mat.node_tree.links.new(n.outputs['Color'],p.inputs[input_name])
    return mat,paths

def load_reference():
    path=next((ROOT/'output/tuareg_shield_test/decoded/age1').rglob('decoded-static.json'))
    ref=bpy.data.collections.new('REFERENCE ORIGINALS - preserved');scene.collection.children.link(ref)
    proxy=bpy.data.objects.new('REFERENCE Abbasid Age I',None);scene.collection.objects.link(proxy)
    root=game_library._apply_decoded_static(proxy,json.loads(path.read_text()),select_result=False,create_controls=False)
    rig=next(o for o in root.children_recursive if o.type=='ARMATURE');rig.data.pose_position='REST'
    mesh=next(o for o in root.children_recursive if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers) and 'lod1' in o.name)
    for o in [root,*root.children_recursive]:
        ref.objects.link(o)
        for c in list(o.users_collection):
            if c!=ref:c.objects.unlink(o)
        o.hide_set(True);o.hide_render=True
    return rig,mesh

ref_rig,ref_mesh=load_reference()
def retain_exposed(recipe):
    names={g.index:g.name for g in ref_mesh.vertex_groups}
    rows=[{names[g.group]:g.weight for g in v.groups} for v in ref_mesh.data.vertices]
    selected=set()
    for v,w in zip(ref_mesh.data.vertices,rows):
        hand=sum(value for name,value in w.items() if any(s in name for s in ('palm','index','middle','thumb')))
        if v.co.z<.19 or hand>.65:selected.add(v.index)
    faces=[p for p in ref_mesh.data.polygons if set(p.vertices)<=selected]
    used=sorted({i for p in faces for i in p.vertices});lookup={old:i for i,old in enumerate(used)}
    # Boots and skin use new atlas, preserving source weights and stock grip geometry.
    for tile,subset in [(2,[p for p in faces if sum(ref_mesh.data.vertices[i].co.z for i in p.vertices)/len(p.vertices)<.19]),(3,[p for p in faces if sum(ref_mesh.data.vertices[i].co.z for i in p.vertices)/len(p.vertices)>=.19])]:
        ids=sorted({i for p in subset for i in p.vertices});m={old:i for i,old in enumerate(ids)}
        recipe.part([ref_mesh.data.vertices[i].co for i in ids],[tuple(m[i] for i in p.vertices) for p in subset],[rows[i] for i in ids],tile,'reference hands' if tile==3 else 'reference feet')

def torso_weights(z,x=0):
    if z<1.0:return {'metarig_pelvis':1.}
    if z<1.23:
        t=(z-1.0)/.23;return {'metarig_pelvis':1-t,'metarig_ribcage':t}
    return {'metarig_ribcage':1.}
def build_body(rig,age,mat):
    r=MeshRecipe(f'Tuareg_Age_{age}_NewSkin');retain_exposed(r)
    for side in ('l','r'):
        h=rig.data.bones[f'metarig_{side}leg1'].head_local;k=rig.data.bones[f'metarig_{side}leg2'].head_local;a=rig.data.bones[f'metarig_{side}legankle'].head_local
        r.tube([a,a.lerp(k,.25),k,k.lerp(h,.6),h],[.075,.080,.091,.110,.105],
            [{f'metarig_{side}legankle':.65,f'metarig_{side}leg2':.35},{f'metarig_{side}leg2':1},{f'metarig_{side}leg2':.5,f'metarig_{side}leg1':.5},{f'metarig_{side}leg1':1},{f'metarig_{side}leg1':1}],1,'loose woven trousers '+side)
        sh=rig.data.bones[f'metarig_{side}armupper1'].head_local;el=rig.data.bones[f'metarig_{side}armlower1'].head_local;wr=rig.data.bones[f'metarig_{side}armpalm'].head_local
        r.tube([sh,sh.lerp(el,.45),el,el.lerp(wr,.6),wr], [.096,.09,.078,.072,.055],
            [{f'metarig_{side}armupper1':1},{f'metarig_{side}armupper1':.3,f'metarig_{side}armupper2':.7},{f'metarig_{side}armupper2':.5,f'metarig_{side}armlower1':.5},{f'metarig_{side}armlower1':.3,f'metarig_{side}armlower2':.7},{f'metarig_{side}armlower2':1}],0 if age<3 else 8,'cloth sleeve '+side)
    torso_profile=[(1.01,.17,.115),(1.12,.155,.125),(1.30,.205,.145),(1.46,.20,.12),(1.52,.205,.115),(1.55,.085,.075)]
    r.rings([((0,0,z),rx,ry,torso_weights(z)) for z,rx,ry in torso_profile],0 if age<3 else 8,'tailored desert tunic')
    # Two split skirt panels: independent leg influence, never a rigid tube across both knees.
    for s in (-1,1):
        points=[(s*.02,-.150,1.05),(s*.225,-.150,1.05),(s*.235,-.19,.66),(s*.025,-.20,.70),
                (s*.02,.13,1.05),(s*.225,.13,1.05),(s*.235,.16,.66),(s*.025,.18,.70)]
        leg='metarig_'+('l' if s>0 else 'r')+'leg1'
        r.part(points,[(0,1,2,3),(4,7,6,5),(1,5,6,2),(0,3,7,4),(0,4,5,1),(3,2,6,7)],
               [{'metarig_pelvis':1},{'metarig_pelvis':1},{leg:.85,'metarig_pelvis':.15},{leg:.85,'metarig_pelvis':.15}]*2,0,'split desert hem')
    r.rings([((0,0,z),.176,.132,torso_weights(z)) for z in (1.015,1.07)],2,'waist leather sash')
    r.rings([((0,0,z),.173,.131,torso_weights(z)) for z in (1.072,1.102)],7,'owner colour waist band')
    if age>=2:
        # Leather diagonal carrier seats on chest surface; upper section follows ribcage.
        points=[];weights=[]
        for z,x in [(1.47,-.14),(1.40,-.11),(1.30,-.04),(1.20,.035),(1.08,.12)]:
            lo,hi=next((a,b) for a,b in zip(torso_profile,torso_profile[1:]) if a[0]<=z<=b[0]);t=(z-lo[0])/(hi[0]-lo[0])
            rx=lo[1]*(1-t)+hi[1]*t;ry=lo[2]*(1-t)+hi[2]*t
            for edge in (-.021,.021):
                px=x+edge;points.append((px,-ry*math.sqrt(max(.01,1-(px/rx)**2))-.014,z));weights.append(torso_weights(z))
        r.part(points,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(4)],weights,2,'seated diagonal equipment strap')
    # Wrapped crown and face veil, anchored to native head, with exposed eye slit.
    hw={'metarig_head':1.}
    r.rings([((0,.008,z),rx,ry,hw) for z,rx,ry in [(1.64,.087,.09),(1.72,.109,.112),(1.82,.108,.108),(1.875,.08,.075),(1.90,.025,.025)]],0,'wrapped head silhouette')
    for j in range(5+age):
        z=1.74+j*.021
        if z>1.884:break
        rx=.112 if z<1.83 else .105-(z-1.83)*.5
        r.rings([((0,.004,z),rx,.113,hw),((0,.004,z+.014),rx+.002,.114,hw)],0 if j%2==0 else 11,'headwrap fold '+str(j),cap=False)
    # The brow band and eyes sit ahead of the veil; dark eye apertures remain visibly narrow.
    r.part([(-.080,-.115,1.753),(.080,-.115,1.753),(.082,-.111,1.782),(-.082,-.111,1.782)],[(0,1,2,3)],hw,3,'exposed eye slit')
    for x in (-.042,.042):
        r.part([(x-.022,-.118,1.760),(x+.022,-.118,1.760),(x+.02,-.117,1.773),(x-.02,-.117,1.773)],[(0,1,2,3)],hw,4,'narrow eye')
    r.rings([((0,-.015,z),rx,ry,hw) for z,rx,ry in [(1.63,.077,.096),(1.69,.108,.123),(1.744,.111,.120)]],0,'face covering and veil')
    r.rings([((0,0,1.55),.087,.081,{'metarig_neck1':1}),((0,0,1.65),.084,.085,hw)],0,'wrapped collar')
    # Scarf tail connects to crown back, bends into upper back instead of floating.
    r.part([(-.075,.11,1.82),(.075,.11,1.82),(.093,.151,1.51),(.067,.148,1.31),(-.055,.148,1.29),(-.091,.151,1.51)],[(0,1,2,5),(5,2,3,4)],
           [hw,hw,{'metarig_head':.3,'metarig_ribcage':.7},{'metarig_ribcage':1},{'metarig_ribcage':1},{'metarig_head':.3,'metarig_ribcage':.7}],11,'cloth scarf tail')
    if age>=3:
        r.part([(-.075,-.16,1.45),(.075,-.16,1.45),(.09,-.15,1.13),(-.09,-.15,1.13)],[(0,1,2,3)],{'metarig_ribcage':1},0,'indigo tabard over mail')
    if age==4:
        for x in (-.077,.077):r.part([(x-.009,-.164,1.44),(x+.009,-.164,1.44),(x+.009,-.155,1.15),(x-.009,-.155,1.15)],[(0,1,2,3)],{'metarig_ribcage':1},6,'refined tabard edging')
    collection=rig.users_collection[0];o=r.object(collection,mat,rig)
    return o,r

for age in range(1,5):
    rig=prototype.create_unit(doc,bpy.context);rig.name=f'Tuareg_Age_{age}_NativeRig'
    # Named weight reuse requires the source and prototype bind matrices to agree.
    assert set(ref_rig.data.bones.keys())==set(rig.data.bones.keys())
    rest_error=max(abs(a-b) for bone in rig.data.bones for ar,br in zip(bone.matrix_local,ref_rig.data.bones[bone.name].matrix_local) for a,b in zip(ar,br))
    assert rest_error<1e-4,rest_error
    mat,paths=atlas(age);body,recipe=build_body(rig,age,mat)
    rig.garrison_unit.mesh=body;rig.garrison_unit.build_name=f'tuareg_age{age}'
    folder=sources/f'tuareg_age{age}';folder.mkdir(exist_ok=True)
    unit_export.export_unit_model(rig,[body],folder/'model.fbx',unit_export.skeleton_records(rig),three_lods=True,lod_counts=doc['prototype']['lod_counts'])
    action=prototype.export_document(rig);action['material_name']=mat.name;action['textures']=list(paths)
    import shutil
    for role,path in paths.items():shutil.copy2(path,folder/(role+'.png'))
    (folder/'action.json').write_text(json.dumps(action))
    report['ages'].append({'age':age,'vertices':len(body.data.vertices),'faces':len(body.data.polygons),'bones':len(rig.data.bones),'stock_bind_error':rest_error,'parts':recipe.steps,'new_geometry_vertices':len(body.data.vertices)-sum(p['vertices'] for p in recipe.steps if p['part'].startswith('reference')),'maximum_influences':max(len(v.groups) for v in body.data.vertices)})
    rig.parent.location.x=(age-1)*1.9

def equipment(name,recipe):
    mat,paths=atlas(2);collection=bpy.data.collections.new(name);scene.collection.children.link(collection)
    obj=recipe.object(collection,mat)
    props=scene.garrison
    props.author_collection=None;props.author_display_name=name;props.author_asset_id=name;props.author_namespace='tuareg';props.author_catalog_folder='Tuareg original equipment'
    for o in bpy.context.selected_objects:o.select_set(False)
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    assert bpy.ops.garrison.create_static_container()=={'FINISHED'}
    material_adoption.adopt_material(mat)
    exported=asset_authoring._export_asset(bpy.context,props)
    report.setdefault('equipment',[]).append({'name':name,'vertices':len(obj.data.vertices),'faces':len(obj.data.polygons),'export':{k:str(v) for k,v in exported.items()},'parts':recipe.steps})
    return obj

# Shield uses the Donso local grip origin and axes. A continuous waisted hide shell
# is bowed in depth; rawhide rim shares the perimeter topology rather than floating.
r=MeshRecipe('tuareg_agher_shield')
outline=[(-.12,-.53),(.09,-.47),(.18,-.25),(.14,0),(.20,.30),(.10,.56),(-.12,.62),(-.35,.55),(-.45,.30),(-.40,0),(-.44,-.25),(-.34,-.47)]
pts=[(x,y,z) for y in (.095,.055) for x,z in outline]
n=len(outline);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
r.part(pts,faces,{},9,'waisted hide shell')
for k in range(n):
    x,z=outline[k];x2,z2=outline[(k+1)%n];r.tube([(x,.096,z),(x2,.096,z2)],[.012,.012],[{},{}],2,'seated rawhide edge '+str(k),sides=6)
# Reinforcement runs down the shell and touches it. Handle grip centre is exact model origin.
r.tube([(-.12,.104,-.43),(-.12,.104,.51)],[.022,.022],[{},{}],13,'central hide reinforcement',8)
r.tube([(0,.055,-.12),(0,0,-.095),(0,0,.095),(0,.055,.12)],[.017]*4,[{}]*4,2,'rear hand grip through origin',8)
for z in (-.30,.27):
    # Painted motifs are original, seated 1mm ahead of the hide surface.
    r.part([(-.12,.097,z+.08),(-.04,.097,z),(-.12,.097,z-.08),(-.20,.097,z)],[(0,1,2,3)],{},10,'painted ochre diamond')
shield=equipment('tuareg_agher_shield',r);report['contacts'].append({'interface':'shield grip midpoint / native model origin','distance_m':0,'shield_height_m':1.15,'method':'recipe vertices at y0 symmetric z +-.095'})

# Long narrow leaf blade and socket meet a continuous shaft; stock spear axis is +Z
# in decoded Blender coordinates, grip at the native origin. Confirmed separately in reference report.
r=MeshRecipe('tuareg_leaf_spear')
r.tube([(0,0,-.98),(0,0,.95),(0,0,1.04)],[.015,.015,.012],[{}]*3,12,'tapered hardwood shaft',10)
r.tube([(0,0,-.13),(0,0,.13)],[.020,.020],[{}]*2,2,'leather hand grip',10)
r.tube([(0,0,.94),(0,0,1.11)],[.025,.019],[{}]*2,5,'steel socket seated on shaft',10)
points=[(0,0,1.08),(-.047,0,1.23),(0,0,1.48),(.047,0,1.23),(0,-.012,1.24),(0,.012,1.24)]
r.part(points,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],{},5,'forged leaf spearhead with central ridge')
r.tube([(0,0,-1.02),(0,0,-.97)],[.012,.017],[{}]*2,5,'iron butt ferrule',10)
spear=equipment('tuareg_leaf_spear',r);report['contacts'].append({'interface':'shaft / socket','overlap_m':.10,'spear_length_m':2.5,'grip_offset_m':0})
shield.location=(0,2,1);spear.location=(2,2,1)
for o in scene.objects:
    if o.type=='ARMATURE':o.hide_render=True;o.hide_set(True)
for o in bpy.context.selected_objects:o.select_set(False)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Tuareg_Original_Ages_I_IV.blend'))
(WORK/'art-source-checks.json').write_text(json.dumps(report,indent=2))
print('TUAREG_NEW_ART_READY',json.dumps({'ages':len(report['ages']),'equipment':len(report['equipment'])}),flush=True)
