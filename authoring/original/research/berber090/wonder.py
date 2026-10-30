"""090 Koutoubia: original low mosque, vaulted courts and rebuilt 21.9m minaret.
Background Blender only. Existing art, gameplay footprints, and live scenes untouched.
"""
import bpy,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from wonder_runner import Runner,review,export
ART=ROOT/'art/building_remix_0_9_0/wonder';ART.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=1
b=Runner('090_Koutoubia_monumental_mosque',ART)
CHECKS=[];STEPS=[]
# Anatomy ratios: same14.2x14site; hall3.25high; newtower21.9=1.5*14.6.
TX,TY=-5.25,4.55;SHAFT=17.15;TOWER_W=2.8;COURT_TOP=.16
def step(name):STEPS.append({'name':name,'parts':len(b.parts)})
def foundation():
 b.box('090_site_plinth',(0,0,.06),(14.2,14,.12),0,0)
 b.box('090_court_paving',(.35,-3.4,.14),(12.4,6.3,.04),1,0)
 b.box('090_hypostyle_sanctuary',(.9,2.90,1.685),(11.8,6.5,3.13),0,40)
 b.box('090_minaret_square_shaft',(TX,TY,(.12+SHAFT)/2),(TOWER_W,TOWER_W,SHAFT-.12),0,40)
 CHECKS.extend([{'interface':'site to hall','parent_top':.12,'child_bottom':.12,'gap':0}, {'interface':'site to tower','parent_top':.12,'child_bottom':.12,'gap':0}]);step('foundation_and_proportion')
def roof_bays():
 # Six long parallel hipped roof volumes, each modeled connected ridge/eave solid.
 for i in range(6):
  x=-4.07+i*1.97;y=2.90;w=2.06;d=6.72;z=3.37;h=.58;a=w/2;dd=d/2;rr=dd-a
  vs=[(x-a,y-dd,z),(x+a,y-dd,z),(x+a,y+dd,z),(x-a,y+dd,z),(x,y-rr,z+h),(x,y+rr,z+h),(x-a,y-dd,z-.12),(x+a,y-dd,z-.12),(x+a,y+dd,z-.12),(x-a,y+dd,z-.12)]
  b.mesh('090_parallel_prayer_roof_'+str(i),vs,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5),(6,7,1,0),(7,8,2,1),(8,9,3,2),(9,6,0,3),(9,8,7,6)],4,80)
  for side in (-1,1):b.box('090_eave_stone_'+str(i)+str(side),(x,y+side*3.33,3.26),(2.06,.14,.18),1,60)
  # Tile ridge caps give silhouette relief, not detached ornaments.
  b.box('090_roof_ridge_'+str(i),(x,y,3.94),(.12,4.66,.12),4,80)
 CHECKS.append({'interface':'hall top to roof soffit','parent_top':3.25,'child_bottom':3.25,'gap':0});step('parallel_sanctuary_roofs')
def gallery_module(name,u,face,axis='X'):
 # Connected spandrel arch rests on broad square piers; all have single-user mesh.
 r=.73;spring=1.77;top=2.69;dep=.43;n=20;vs=[]
 for d in (-dep/2,dep/2):
  for i in range(n+1):
   xx=-r+2*r*i/n;zz=spring+math.sqrt(max(0,r*r-xx*xx));vs.extend([(xx,d,zz),(xx,d,top)])
 fs=[];N=2*(n+1)
 for i in range(n):a=2*i;fs.extend([(a,a+2,a+3,a+1),(N+a,N+a+1,N+a+3,N+a+2),(a,N+a,N+a+2,a+2),(a+1,a+3,N+a+3,N+a+1)])
 fs.extend([(0,1,N+1,N),(2*n,2*n+N,2*n+N+1,2*n+1)])
 vs=[(u+x,face+y,z) if axis=='X' else (face+y,u+x,z) for x,y,z in vs];b.mesh(name+'_connected_arch',vs,fs,1,60)
 for s in (-1,1):
  c=(u+s*.85,face,.965) if axis=='X' else (face,u+s*.85,.965);sz=(.24,.52,1.61) if axis=='X' else (.52,.24,1.61);b.box(name+'_pier_'+str(s),c,sz,0,20)
  c=(c[0],c[1],1.72);sz=(.34,.60,.10) if axis=='X' else (.60,.34,.10);b.box(name+'_capital_'+str(s),c,sz,1,60)
 c=(u,face,2.79) if axis=='X' else (face,u,2.79);sz=(1.98,.82,.20) if axis=='X' else (.82,1.98,.20);b.box(name+'_canopy',c,sz,0,60)
 c=(c[0],c[1],2.94);sz=(2.0,.88,.10) if axis=='X' else (.88,2.,.10);b.box(name+'_flat_green_gallery_cap',c,sz,4,80)
def court():
 # All three sides have open arcades; broad south entrance opening preserved.
 for side in (-1,1):
  for j,y in enumerate((-5.35,-3.59,-1.83)):gallery_module('090_side_arcade_'+str(side)+'_'+str(j),y,side*6.20,'Y')
 for j,x in enumerate((-4.45,-2.65,2.65,4.45)):gallery_module('090_entrance_arcade_'+str(j),x,-6.10)
 # Raised portal holds elaborated horseshoe doorway opening, no central blocking cube.
 gallery_module('090_main_gateway',0,-6.10)
 for sx in (-1,1):b.box('090_gateway_buttress_'+str(sx),(sx*1.05,-6.10,1.69),(.28,.86,3.06),0,40)
 b.box('090_gateway_frieze',(0,-6.10,3.26),(2.4,.86,.20),1,60)
 for i in range(7):b.box('090_portal_merlon_'+str(i),(-1.08+i*.36,-6.10,3.47),(.22,.64,.22),0,80)
 b.rings('090_ablution_fountain_basin',(.35,-3.3),[(.82,.16),(.82,.45),(.67,.45),(.67,.29),(.05,.29)],12,1,60,True)
 b.rings('090_ablution_water',(.35,-3.3),[(.65,.30),(.65,.32)],12,3,80,True)
 b.rings('090_fountain_center',(.35,-3.3),[(.13,.30),(.13,.65),(.34,.73),(.34,.84),(.22,.84),(.22,.76),(.02,.76)],12,1,80,True)
 CHECKS.extend([{'interface':'arcade pier capital arch','pier_top':1.77,'arch_spring':1.77,'gap':0},{'interface':'arch canopy','arch_top':2.69,'canopy_bottom':2.69,'gap':0},{'interface':'court fountain','paving_top':COURT_TOP,'basin_bottom':COURT_TOP,'gap':0}]);step('open_arcaded_court')
def hall_facades():
 hall=bpy.data.objects['090_hypostyle_sanctuary']
 for i,x in enumerate((-3.20,-.70,1.80,4.30)):
  b.recess(hall,'sanctuary_portal'+str(i),x,-.35,.16,1.35,2.45,'Y',.28)
  b.arch('090_cedar_door_'+str(i),x,-.225,.16,1.28,2.38,.025,'Y',2)
  for s in (-1,1):b.box('090_door_stone_jamb'+str(i)+str(s),(x+s*.79,-.385,1.39),(.16,.16,2.46),1,60)
 for axis,face in [('X',6.8),('Y',6.15)]:
  coords=(.8,2.3,3.8,5.3) if axis=='X' else (-2.7,-.9,.9,2.7,4.5)
  for i,u in enumerate(coords):b.recess(hall,'high_window'+axis+str(i),u,face,1.69,.54,1.01,axis,.24)
 step('recessed_sanctuary_openings')
def minaret():
 shaft=bpy.data.objects['090_minaret_square_shaft']
 for axis,origin,along in [('Y',TY,TX),('X',TX,TY)]:
  for side in (-1,1):
   face=origin+side*1.4
   # Deep broad recesses on allfour faces: carved bands never float over blank walls.
   b.recess(shaft,'main_sebka_'+axis+str(side),along,face,5.1,2.02,6.5,axis,.30)
   b.recess(shaft,'lower_blind_'+axis+str(side),along,face,.85,1.52,3.35,axis,.30)
   for offset in (-.48,.48):b.recess(shaft,'upper_double_'+axis+str(side)+str(offset),along+offset,face,12.45,.70,2.55,axis,.30)
   # Diamond networks are continuous closed thick mesh outlines, seated in recessbed.
   for row in range(6):
    z=5.75+row*.76
    for col in (-1,1):
     u=along+col*.43;outer=[(u,z+.40),(u+.40,z),(u,z-.40),(u-.40,z)];inner=[(u,z+.32),(u+.32,z),(u,z-.32),(u-.32,z)]
     verts=[];dep=.045;plane=face-side*.119
     for d in (plane-dep/2,plane+dep/2):
      for ring in (outer,inner):verts.extend([(p,d,zz) if axis=='Y' else (d,p,zz) for p,zz in ring])
     fs=[]
     for k in range(4):j=(k+1)%4;fs.extend([(k,j,4+j,4+k),(8+k,12+k,12+j,8+j),(k,8+k,8+j,j),(4+k,4+j,12+j,12+k)])
     b.mesh('090_continuous_sebka_'+axis+str(side)+str(row)+str(col),verts,fs,1,80)
 # Major crown/lantern rebuilt to tall tower proportions; seat exact.
 for name,z,ww,h,kind in [('lower_belt',4.65,2.94,.20,1),('middle_belt',11.94,2.94,.23,1),('upper_tile_frieze',15.75,2.87,.55,3),('cornice1',16.71,3.02,.20,1),('cornice2',16.98,3.22,.34,0)]:b.box('090_tower_'+name,(TX,TY,z),(ww,ww,h),kind,80)
 b.box('090_tower_crown',(TX,TY,17.35),(3.18,3.18,.40),0,60)
 for side in (-1,1):
  for k in range(7):
   u=-1.38+k*.46;b.box('090_crown_merlon_Y'+str(side)+str(k),(TX+u,TY+side*1.48,17.75),(.25,.22,.40),0,80)
   if k not in (0,6):b.box('090_crown_merlon_X'+str(side)+str(k),(TX+side*1.48,TY+u,17.75),(.22,.25,.40),0,80)
 lantern=b.box('090_minaret_lantern',(TX,TY,18.57),(1.62,1.62,2.04),0,80)
 for axis,origin,along in [('Y',TY,TX),('X',TX,TY)]:
  for side in (-1,1):b.recess(lantern,'lantern_'+axis+str(side),along,origin+side*.81,17.84,.76,1.30,axis,.24)
 b.box('090_lantern_cornice',(TX,TY,19.66),(1.91,1.91,.14),1,80)
 b.hip('090_lantern_green_cap',TX,TY,2.02,2.02,19.85,.64,4,80)
 b.rings('090_finial_spindle',(TX,TY),[(.04,20.49),(.04,21.90)],8,2,100,True)
 for j,(r,z) in enumerate(((.24,20.79),(.18,21.29),(.11,21.68))):b.rings('090_metal_finial_orb'+str(j),(TX,TY),[(.02,z-r),(.71*r,z-.71*r),(r,z),(.71*r,z+.71*r),(.02,z+r)],12,1,100,True)
 CHECKS.extend([{'interface':'shaft crown','shaft_top':17.15,'crown_bottom':17.15,'gap':0},{'interface':'crown lantern','crown_top':17.55,'lantern_bottom':17.55,'gap':0},{'interface':'finial roof','roof_peak':20.49,'spindle_bottom':20.49,'gap':0},{'interface':'sebka recess seat','recess_depth':.15,'decoration_inner_depth':.1415,'overlap':.0085}]);step('reproportioned_deep_carved_minaret')
def finish():
 # Review repair: widen all tower assemblies coherently around fixed ground anchor.
 prefixes=('090_minaret','090_tower','090_crown','090_lantern','090_finial','090_metal_finial','090_continuous_sebka')
 for ob in b.parts:
  if ob.name.startswith(prefixes):
   for v in ob.data.vertices:
    v.co.x=TX+(v.co.x-TX)*8/7;v.co.y=TY+(v.co.y-TY)*8/7
 # Stepped stone archivolts are solid ring bands seated in the main recess lips.
 for axis,origin,along in [('Y',TY,TX),('X',TX,TY)]:
  for side in (-1,1):
   face=origin+side*1.60
   for band in range(2):
    w=2.35+band*.17;z=4.98-band*.08;h=6.68+band*.17;rad=w/2;spring=z+h-rad
    pts=[(along+rad*math.cos(t),spring+rad*math.sin(t)) for t in [math.pi*i/24 for i in range(25)]]
    pts=[(along-rad,z)]+list(reversed(pts))+[(along+rad,z)]
    for j,(p,q) in enumerate(zip(pts,pts[1:])):
     a=(p[0],face+side*.018,p[1]) if axis=='Y' else (face+side*.018,p[0],p[1]);c=(q[0],face+side*.018,q[1]) if axis=='Y' else (face+side*.018,q[0],q[1]);b.bar('090_stepped_archivolt_'+axis+str(side)+str(band)+str(j),a,c,.065,1,80)
 # Stone sanctuary frieze visibly joins the eaves; its shallow vertical cuts read at gamezoom.
 for i in range(36):
  x=-4.74+i*.322;b.box('090_sanctuary_dentil_'+str(i),(x,-.425,3.10),(.17,.16,.18),1,60)
 b.box('090_sanctuary_lintel_frieze',(.9,-.425,2.97),(11.8,.16,.12),1,60)
 # Explicit copper colour and metalness patch; all finial surfaces address only thispatch.
 im=next(n.image for n in b.mat.node_tree.nodes if n.type=='TEX_IMAGE');pix=list(im.pixels[:]);W,H=im.size
 metal=bpy.data.images.new('090_copper_metalness',width=W,height=H,alpha=True);mp=[0.,0.,0.,1.]*(W*H)
 for y in range(int(H*.90),H):
  for x in range(int(W*.41),int(W*.44)):
   k=4*(y*W+x);pix[k:k+4]=[.47,.23,.075,1];mp[k:k+4]=[.85,.85,.85,1]
 im.pixels.foreach_set(pix);im.filepath_raw=str(ART/'surface_atlas.png');im.file_format='PNG';im.save()
 metal.pixels.foreach_set(mp);metal.filepath_raw=str(ART/'metalness_atlas.png');metal.file_format='PNG';metal.save();metal.colorspace_settings.name='Non-Color'
 tex=b.mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=metal;b.mat.node_tree.links.new(tex.outputs['Color'],b.mat.node_tree.nodes.get('Principled BSDF').inputs['Metallic'])
 for ob in b.parts:
  if ob.name.startswith(('090_finial','090_metal_finial')):
   for uv in ob.data.uv_layers.active.data:uv.uv=(.425,.95)
 b.rings('090_native_owner_flag_pole',(6.60,-5.80),[(.055,.12),(.055,4.70)],8,2,100,True)
 flag={'location':[6.6,-5.77,3.35],'rotation':[0,0,0],'scale':[1,1,1]};(ART/'flag-transform.json').write_text(json.dumps(flag,indent=2))
 topology=b.finalize_meshes()
 from mathutils import Vector
 start=Vector((0,-7.5,1));end=Vector((0,-2,1));hits=[]
 for ob in b.parts:
  inv=ob.matrix_world.inverted();a=inv@start;delta=inv@end-a
  if ob.ray_cast(a,delta.normalized(),distance=delta.length)[0]:hits.append(ob.name)
 assert not hits,('central court gate blocked',hits)
 bounds=review(ART,'koutoubia090_final',b.parts)
 # Renderhelpers are created only after geometry complete and excluded from exportcollection.
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Berber_Koutoubia_Wonder_090.blend'))
 # Background authoring deliberately avoids global addon registration. Integration
 # exports the saved collection with the installed scoped export helper.
 result={'status':'ready_for_scoped_export','collection':b.col.name}
 report={'schema':'berber.wonder-source/v090','status':'source-validated','bounds':bounds,'parts':b.report(),'checks':CHECKS,'steps':STEPS,'site_unchanged':[14.2,14.0],'old_height':14.6,'new_height':21.9,'minaret_height_multiplier':1.5,'flag_transform':flag,'export':result,'topology':topology,'triangles':sum(p['triangles'] for p in topology),'central_entrance_ray_hits':hits,'normal_recalculation':True,'single_user_meshes':all(o.data.users==1 for o in b.parts),'reference':'https://whc.unesco.org/en/list/331/','interpretation':'Game-scale mosque, not a literal reconstruction','native_runtime':'pending'}
 (ART/'source-validation.json').write_text(json.dumps(report,indent=2,default=str));print('WONDER090_READY',len(b.parts),flush=True)
foundation();roof_bays();court();hall_facades();minaret();finish()
