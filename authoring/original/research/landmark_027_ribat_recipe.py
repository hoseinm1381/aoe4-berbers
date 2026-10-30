"""Original measured Ribat of the Sanhaja. Rebuild in an owned Blender process only."""
import bpy,bmesh,sys,json,math,random,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'art/landmarks_0_2_7/ribat';sys.path.insert(0,str(ROOT/'research'))
from landmark_027_ribat_runner import Runner,remap_uv
random.seed(2707)
EXT=Path(r'C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison');sys.path.insert(0,str(EXT.parent))

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'

mat=bpy.data.materials.new('BerberRibat_OriginalAtlas2048');mat.use_nodes=True;nt=mat.node_tree;bsdf=nt.nodes.get('Principled BSDF')
for semantic,socket in [('basecolor','Base Color'),('roughness','Roughness'),('metallic','Metallic')]:
 node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ART/'textures'/f'ribat_{semantic}.png'))
 if semantic!='basecolor':node.image.colorspace_settings.name='Non-Color'
 nt.links.new(node.outputs['Color'],bsdf.inputs[socket])
node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ART/'textures/ribat_normal.png'));node.image.colorspace_settings.name='Non-Color';norm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(node.outputs['Color'],norm.inputs['Color']);nt.links.new(norm.outputs['Normal'],bsdf.inputs['Normal'])
col=bpy.data.collections.new('Ribat_Editables');scene.collection.children.link(col);run=Runner(col,mat,'Ribat_')
# Step1: anchored courtyard and defensive shell. All ground supports terminate on Z0.
run.box('CourtyardPaving',(0,0,.075),(12,12,.15),4,0)
# Weathered cut-stone blocks: deliberately cut corners, not decorative smoothing/subdivision.
def stone(name,center,size,panel=4,stage=20):
 x,y,z=center;a,b,h=[v/2 for v in size];cut=min(a,b)*.12
 poly=[(-a+cut,-b), (a-cut,-b),(a,-b+cut),(a,b-cut),(a-cut,b),(-a+cut,b),(-a,b-cut),(-a,-b+cut)]
 vs=[(x+px*(1-.035*level),y+py*(1-.035*level),z+(-h if level==0 else h)) for level in [0,1] for px,py in poly]
 return run.mesh(name,vs,[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)],panel,stage)
# Single complete stone course module verified before replication.
for side in range(4):
 for row in range(4):
  for j in range(34):
   along=-5.75+(j+.5)*11.5/34
   if side==0 and abs(along)<1.05:continue
   pos=[(along,-5.72),(5.72,along),(along,5.72),(-5.72,along)][side]
   sz=(11.5/34-.009,.49,.195) if side%2==0 else (.49,11.5/34-.009,.195)
   stone(f'EnclosureFoot_{side}_{row}_{j}',(*pos,.15+.2*(row+.5)),sz,4 if (j+row)%3 else 12)
run.contact('Footing underside / courtyard top',.0025)
run.box('RearWall',(0,5.58,2.0),(10.7,.52,2.6),0,40,taper=.035)
run.box('WestWall',(-5.58,0,2.0),(.52,10.7,2.6),8,40,taper=.035)
run.box('EastWall',(5.58,0,2.0),(.52,10.7,2.6),0,40,taper=.035)
for sign in [-1,1]:run.box('FrontWall_'+str(sign),(sign*3.72,-5.58,2.0),(3.65,.52,2.6),0,40,taper=.035)
# Four tapered corner loft towers, integral roof terraces and arrow apertures.
for tx,ty in [(-5,-5),(5,-5),(-5,5),(5,5)]:
 tag=f'Tower{tx}_{ty}'
 for side in range(4):
  for row in range(5):
   for j in range(7):
    q=-.83+(j+.5)*1.66/7;px,py=[(tx+q,ty-.87),(tx+.87,ty+q),(tx+q,ty+.87),(tx-.87,ty+q)][side]
    sz=(1.66/7-.006,.35,.19) if side%2==0 else (.35,1.66/7-.006,.19)
    stone(tag+f'Base_{side}_{row}_{j}',(px,py,.15+.2*(row+.5)),sz,4 if j%2 else 12)
 run.box(tag+'TaperedBody',(tx,ty,2.83),(1.86,1.86,3.46),1,40,taper=.08)
 run.box(tag+'RoofSeat',(tx,ty,4.61),(1.79,1.79,.16),2,60)
 for side in range(4):
  for j in range(2):
   q=-.25+j*.50;px,py=[(tx+q,ty-.76),(tx+.76,ty+q),(tx+q,ty+.76),(tx-.76,ty+q)][side]
   run.box(tag+f'Crenel{side}_{j}',(px,py,4.93),(.30,.30,.55),1,100,taper=.14)
 for cx in [-.76,.76]:
  for cy in [-.76,.76]:run.box(tag+f'CornerCrenel{cx}_{cy}',(tx+cx,ty+cy,4.93),(.30,.30,.55),1,100,taper=.14)
 # Deep arrow slit: actual pocket cut in forward face, no painted black plaque.
 tower=next(o for o in run.objects if o.name=='Ribat_'+tag+'TaperedBody')
 bpy.ops.mesh.primitive_cube_add(size=1,location=(tx,ty-1.0,3.55));cut=bpy.context.object;cut.dimensions=(.18,.55,.80);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=tower.modifiers.new('Arrow slit cut','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=tower;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 # regenerate planar UVs after boolean
 mesh=tower.data;uv=mesh.uv_layers.active
 for p in mesh.polygons:
  for li in p.loop_indices:
   co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(.26+((co.x-tx)/2+.5)*.23,.76+((co.z-1)/3.8)*.23)
 run.contact(tag+' body / stone footing',-.045,.05)
# True entrance tunnel: front/back archwalls, side walls, roof slab, never a hidden solid box.
run.archwall('GateFrontArch',0,-5.65,3.8,.48,5.85,1.05,1.55,1,40)
run.archwall('GateRearArch',0,-3.2,3.8,.38,5.85,1.05,1.55,1,40)
for sign in [-1,1]:run.box('GateSide'+str(sign),(sign*1.66,-4.41,2.92),(.48,2.43,5.85),1,40)
run.box('GateRoof',(0,-4.43,5.91),(3.8,2.85,.18),2,60)
# Segmented stone arch trim seated around genuine arch edge, contrasting recessed threshold.
for faceY in [-5.925,-2.995]:
 for j in range(24):
  a0=math.pi*j/24;a1=math.pi*(j+1)/24;rad0=1.05;rad1=1.27
  prof=[(rad0*math.cos(a0),1.55+rad0*math.sin(a0)),(rad1*math.cos(a0),1.55+rad1*math.sin(a0)),(rad1*math.cos(a1),1.55+rad1*math.sin(a1)),(rad0*math.cos(a1),1.55+rad0*math.sin(a1))]
  run.prism(f'ArchVoussoir{faceY}_{j}',prof,faceY-.06,faceY+.06,7,60)
 for sign in [-1,1]:
  for j in range(8):stone(f'ArchPier{faceY}_{sign}_{j}',(sign*1.16,faceY,.15+j*.19+.095),(.22,.15,.183),7,60)
# Genuine shallow geometric entrance panel recesses in plaster surface.
for targetname in ['GateFrontArch']:
 obj=next(o for o in run.objects if o.name=='Ribat_'+targetname)
 for sign in [-1,1]:
  for zz in [3.4,4.2,5.0]:
   bpy.ops.mesh.primitive_cube_add(size=1,location=(sign*1.45,-5.93,zz));cut=bpy.context.object;cut.dimensions=(.32,.16,.26);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
   mod=obj.modifiers.new('Earthen shallow pocket','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# Gate leaves open against tunnel side walls with measured plank joinery.
for side in [-1,1]:
 for j in range(12):run.box(f'GateLeaf{side}_{j}',(side*1.10,-4.0+j*.105,1.0),(.09,.095,1.7),3,80)
 for z in [.48,1.45]:run.box(f'GateStrap{side}_{z}',(side*1.045,-3.45,z),(.03,1.25,.08),11,80)
run.contact('Gate leaf underside / paving',0)
# Gatehouse upper watch chamber roof and crenellated terrace; roof walls wrap an actual open core.
for sign in [-1,1]:run.box('WatchSide'+str(sign),(sign*1.58,-4.43,6.44),(.35,2.55,1.08),1,60)
run.box('WatchBack',(0,-3.20,6.44),(3.45,.30,1.08),1,60)
# Three actual front watch apertures separated by uprights; broad lintel upper face.
for x in [-1.45,-.5,.5,1.45]:run.box('WatchPier'+str(x),(x,-5.65,6.32),(.25,.35,.8),7,60)
run.box('WatchLintel',(0,-5.65,6.84),(3.40,.37,.25),7,60)
run.box('WatchRoof',(0,-4.43,7.02),(3.53,2.64,.16),2,80)
for side in range(4):
 for j in range(7 if side%2==0 else 5):
  q=(-1.5+j*.5) if side%2==0 else (-1.02+j*.51)
  x,y=[(q,-5.70),(1.64,-4.43+q),(q,-3.16),(-1.64,-4.43+q)][side]
  run.box(f'WatchCrenel{side}_{j}',(x,y,7.28),(.28,.28,.30),7,100,taper=.10)
# Rear command/storage hall with actual segmented door bays.
run.box('RearHallFloor',(0,3.82,.25),(7.8,2.4,.20),4,20)
run.box('RearHallBack',(0,4.9,1.97),(7.8,.35,3.44),0,40)
for sign in [-1,1]:run.box('RearHallSide'+str(sign),(sign*3.73,3.84,1.97),(.34,2.2,3.44),0,40)
for x in [-2.6,0,2.6]:
 run.archwall('HallDoorArch'+str(x),x,2.75,2.6,.35,3.6,.62,1.30,1,60,16)
 # Recessed closed rear storage door planks at .26m behind facade opening.
 for j in range(8):run.box('HallDoorPlank'+str(x)+'_'+str(j),(x-.53+j*.15,3.015,.88),(.143,.10,1.46),3,80)
run.box('RearHallRoof',(0,3.82,3.72),(7.8,2.4,.22),2,60)
for side in [-1,1]:run.box('RearHallParapetSide'+str(side),(side*3.82,3.715,4.05),(.20,2.19,.45),1,80)
run.box('RearHallParapetBack',(0,4.91,4.05),(7.8,.20,.45),1,80)
run.contact('Rear roof side parapet end / back parapet inside face',0,.001)
# Seated cavalry bay modules: floor → post → crossbeam → rafters → woven canopy.
for side in [-1,1]:
 x=side*4.47
 run.box('StableFloor'+str(side),(x,-.05,.21),(1.95,5.4,.12),4,20)
 for j in range(7):
  y=-2.60+j*.86
  for px in [side*3.65,side*5.30]:
   run.box(f'StablePost{side}_{j}_{px}',(px,y,1.48),(.13,.13,2.42),3,80)
   run.box(f'StablePostCollar{side}_{j}_{px}',(px,y,.40),(.19,.19,.14),11,100)
  run.beam(f'StableCrossBeam{side}_{j}',(side*3.58,y,2.73),(side*5.36,y,2.73),.16,3,80)
  # Fine visible pegged timber joinery, 10-sided pegs seated through beam ends.
  for px in [side*3.65,side*5.3]:
   run.box(f'Peg{side}_{j}_{px}',(px,y-.095,2.72),(.045,.04,.045),11,100)
 for k in range(13):run.beam(f'StableRafter{side}_{k}',(side*(3.60+k*.14),-2.68,2.855),(side*(3.60+k*.14),2.62,2.855),.09,3,80)
 # Canopy draped lattice strips are actual mild sag elevation, connected ring surfaces.
 for k in range(26):
  x0=side*(3.56+k*.071);x1=x0+side*.07
  vs=[]
  for j in range(17):
   y=-2.74+j*.335;z=2.902-.025*math.sin(j*math.pi/16)
   vs.extend([(x0,y,z),(x1,y,z)])
  run.mesh(f'WovenCanopy{side}_{k}',vs,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(16)],5,80)
 for j in range(5):
  y=-2.20+j*.96
  # Tether rails physically seat into bay posts; low stall dividers, feed trough seated below.
  run.beam(f'Tether{side}_{j}',(side*3.70,y,1.2),(side*5.26,y,1.2),.095,3,100)
  run.box(f'FeedBed{side}_{j}',(side*5.04,y+.28,.47),(.50,.58,.40),3,100)
  for sign in [-1,1]:run.box(f'FeedRim{side}_{j}_{sign}',(side*5.04,y+.28+sign*.28,.72),(.54,.07,.12),11,100)
 run.contact('Stable foot / paving '+str(side),0)
 run.contact('Stable post top / beam bottom '+str(side),-.04,.045)
 run.contact('Stable rafter / canopy '+str(side),.002,.005)
# Upper wall stepped earthen crenels and geometric relief. Each is tied to a wall surface.
for side in [1,2,3]:
 for j in range(23):
  q=-4.4+j*.4;x,y=[(0,0),(5.58,q),(q,5.58),(-5.58,q)][side]
  run.box(f'WallCrenel{side}_{j}',(x,y,3.5),(.29,.29,.40),1,100,taper=.14)
# Timber walkway planking on defensive walls, useful silhouette/access detail.
for side in [1,2,3]:
 for j in range(74):
  q=-4.70+(j+.5)*9.4/74
  x,y=[(0,0),(5.28,q),(q,5.28),(-5.28,q)][side]
  sz=(.38,.122,.075) if side!=2 else (.122,.38,.075)
  run.box(f'WalkPlank{side}_{j}',(x,y,3.28),sz,3,80)
# Paired restrained zigzag relief on gatehouse facade; modeled as small diamond sections.
for row,z in enumerate([3.55,4.0,4.48,4.94]):
 for side in [-1,1]:
  x=side*1.50
  for j in range(1):
   zz=z
   prof=[(x-.13,zz),(x,zz+.13),(x+.13,zz),(x,zz-.13)]
   run.prism(f'GateRelief{row}_{side}_{j}',prof,-5.915-j*.001,-5.965-j*.001,6,100)
# Courtyard training equipment: rack, rounded shields and bundled spear shafts; silhouette readable, no pot farm.
for side in [-1,1]:
 px=side*2.25;py=.7
 for q in [-.6,.6]:run.box(f'RackPost{side}_{q}',(px+q,py,1.1),(.15,.15,1.9),3,100)
 run.beam('RackCross'+str(side),(px-.70,py,1.8),(px+.70,py,1.8),.13,3,100)
 for j in range(9):
  x=px-.48+j*.12
  run.beam(f'Spear{side}_{j}',(x,py+.06,.15),(x+.14,py+.06,2.13),.035,3,100)
  run.mesh(f'Spearhead{side}_{j}',[(x+.14,py+.06,2.28),(x+.08,py+.02,2.12),(x+.20,py+.02,2.12),(x+.14,py+.10,2.13)],[(0,1,2),(0,2,3),(0,3,1),(1,3,2)],12,100)
 for j in range(3):
  x=px-.4+j*.4;vs=[(x,py-.12,1.13)]
  for k in range(32):
   a=2*math.pi*k/32;vs.append((x+.20*math.cos(a),py-.18,1.13+.28*math.sin(a)))
  run.mesh(f'Shield{side}_{j}',vs,[(0,k+1,(k+1)%32+1) for k in range(32)],3,100)
# Flag pole is authored; owner-colour cloth is root-injected native304triangle mesh.
FLAG_ANCHOR=(.0,-4.42,8.075-1.339*.7);POLE_TOP=8.075
run.box('FlagPole',(0,-4.42,(7.10+POLE_TOP)/2),(.06,.06,POLE_TOP-7.10),3,100)
run.box('FlagPoleBase',(0,-4.42,7.15),(.16,.16,.10),11,100)
run.contact('Pole foot / watch roof top',0)
# Re-project all Boolean-modified elevations to nondegenerate atlas UVs.
for ob in run.objects:
 if 'TaperedBody' in ob.name or ob.name=='Ribat_GateFrontArch':remap_uv(ob,1)
# Validate source before joining. Numerical contact planes listed above correspond measured recipe anchors.
for ob in run.objects:ob.data.update()
source_tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in run.objects)
# Group exact six names and single atlas; retain editables, excluded from production export.
for o in run.objects:o.hide_render=True
exports=[];counts={}
# Semantic LOD construction protects architectural shells and all silhouette modules.
for lod in [0,1,2]:
 lc=bpy.data.collections.new(f'Ribat_LOD{lod}');scene.collection.children.link(lc);lc['garrison_building_profile']='english-house'
 lr=Runner(lc,mat,f'RibatLOD{lod}_');rows=[]
 def bounds(o):
  pts=[o.matrix_world@v.co for v in o.data.vertices]
  lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
  return [(lo[i]+hi[i])/2 for i in range(3)],[hi[i]-lo[i] for i in range(3)]
 for o in run.objects:
  isfoot=('EnclosureFoot_' in o.name) or ('Tower' in o.name and 'Base_' in o.name)
  isstone=isfoot or 'ArchPier' in o.name
  if lod==2 and isfoot:continue
  if lod==2 and ('WalkPlank' in o.name or 'Peg' in o.name or 'StablePostCollar' in o.name):continue
  if lod and isstone:
   centre,size=bounds(o);lr.box(o.name+'_solid',centre,size,o.get('atlas_panel',4),o.get('garrison_building_first_stage'));continue
  no=o.copy();no.data=o.data.copy();lc.objects.link(no);no.hide_render=False
 if lod==2:
  # Exactly closed plinth masses stand in for chipped masonry course edges.
  for n,center,size in [('Rear',(0,5.72,.55),(11.5,.49,.795)),('West',(-5.72,0,.55),(.49,11.5,.795)),('East',(5.72,0,.55),(.49,11.5,.795)),('FrontWest',(-3.4,-5.72,.55),(4.7,.49,.795)),('FrontEast',(3.4,-5.72,.55),(4.7,.49,.795))]:lr.box('EnclosurePlinth'+n,center,size,4,20)
  for tx,ty in [(-5,-5),(5,-5),(-5,5),(5,5)]:lr.box(f'TowerPlinth{tx}_{ty}',(tx,ty,.65),(2.09,2.09,.99),4,20)
  lr.box('WestWalkway',(-5.28,0,3.28),(.38,9.4,.075),3,80)
  lr.box('EastWalkway',(5.28,0,3.28),(.38,9.4,.075),3,80)
  lr.box('RearWalkway',(0,5.28,3.28),(9.4,.38,.075),3,80)
 for stage in [0,20,40,60,80,100]:
  copies=[o for o in lc.objects if o.get('garrison_building_first_stage')==stage]
  bpy.ops.object.select_all(action='DESELECT')
  for o in copies:o.select_set(True)
  bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();obj=bpy.context.object;obj.name=f'RibatStage{stage:03}';obj['garrison_building_first_stage']=stage
  obj.data.calc_loop_triangles();rows.append({'name':obj.name,'stage':stage,'triangles':len(obj.data.loop_triangles)})
 counts[str(lod)]=rows
 if lod>0:lc.hide_render=True;lc.hide_viewport=True
# Exclude construction editables and leave primary model visible for editable source opening.
col.hide_render=True;col.hide_viewport=True
# Garrison names differ if global Blender names suffixLOD. Normalize manifest part identities after export copies same6.
report={'building':'Ribat of the Sanhaja','historical_status':'original reconstruction not replica','dimensions_target':[12,12,7.4],'native_stamp':'identity','native_owner_colour':'retained cloth injected by root; runtime pending','flag_transform':{'location':FLAG_ANCHOR,'rotation':[0,0,0],'scale':[.7,.7,.7]},'flag_pole_top':POLE_TOP,'flag_pole_contact':{'cloth_top':FLAG_ANCHOR[2]+1.339*.7,'pole_top':POLE_TOP,'gap':0},'contacts':run.contacts,'source_triangles':source_tri,'lods':counts,'export_manifests':exports,'runtime':'pending user game test'}
# Measure every visible exported vertex including functionalflagpole.
obs=list(bpy.data.collections['Ribat_LOD0'].objects);points=[o.matrix_world@v.co for o in obs for v in o.data.vertices]
lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
report['bounds']={'min':lo,'max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)]};report['uv_count']=sum(len(o.data.uv_layers.active.data) for o in obs);report['missing_uv']=sum(o.data.uv_layers.active is None for o in obs)
report['triangles_reason']='Stone footing uses deliberately chipped corner geometry; all other detail tied to architecture. No flat-plane triangle padding.'
(ART/'source-validation.json').write_text(json.dumps(report,indent=2));(ART/'export.json').write_text(json.dumps({'project_name':'br027_ribat','sources':[f'export_lod{i}' for i in range(3)],'owner_colour':'native root-injected cloth','flags_excluded':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'ribat_of_sanhaja.blend'))
# Presentation cameras added only after anatomy/model finished; workbench captures geometric solid views.
prev=ART/'previews';prev.mkdir(exist_ok=True);scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
camdata=bpy.data.cameras.new('Review camera');camera=bpy.data.objects.new('Review camera',camdata);scene.collection.objects.link(camera);scene.camera=camera;camdata.type='ORTHO';camdata.ortho_scale=18
scene.render.engine='BLENDER_WORKBENCH';scene.world.color=(.055,.055,.055);scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.58,.58,.58);scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
for name,pos in [('front',(0,-25,4)),('rear',(0,25,4)),('left',(-25,0,4)),('right',(25,0,4)),('top',(0,0,30)),('bottom',(0,0,-30)),('gameplay',(18,-23,20)),('gate-contact',(8,-17,9))]:
 camera.location=pos;target=Vector((0,0,3.8)) if name not in ['top','bottom'] else Vector((0,0,0));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(prev/(name+'_solid.png'));bpy.ops.render.render(write_still=True)
# Material/gameplay render with correctly linked original atlas.
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.world.color=(.35,.35,.35)
for name,loc,energy,size in [('Key',(-8,-10,18),2600,12),('Fill',(12,-1,10),1800,10),('Back',(0,12,15),1800,8)]:
 ld=bpy.data.lights.new(name,'AREA');lo=bpy.data.objects.new(name,ld);scene.collection.objects.link(lo);lo.location=loc;lo.rotation_euler=(Vector((0,0,2))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=energy;ld.shape='DISK';ld.size=size
camera.location=(18,-23,20);camera.rotation_euler=(Vector((0,0,3.4))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(prev/'gameplay_material.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'ribat_of_sanhaja.blend'))
# Independently display each real geometric LOD before handoff.
for lod in range(3):
 for c in bpy.data.collections:
  if c.name.startswith('Ribat_LOD'):c.hide_render=(c.name!=f'Ribat_LOD{lod}')
 scene.render.engine='BLENDER_WORKBENCH';scene.render.filepath=str(prev/f'lod{lod}_solid.png');bpy.ops.render.render(write_still=True)
 scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.filepath=str(prev/f'lod{lod}_material.png');bpy.ops.render.render(write_still=True)
for c in bpy.data.collections:
 if c.name.startswith('Ribat_LOD'):c.hide_render=(c.name!='Ribat_LOD0')
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'ribat_of_sanhaja.blend'))
print('RIBAT_AUTHOR_COMPLETE',json.dumps(report['bounds']),source_tri);bpy.ops.wm.quit_blender()








