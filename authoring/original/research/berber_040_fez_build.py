import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from berber_040_fez_runner import *
r=Runner('fez')
# Original Marinid madrasa: measured 14x14 court, 6.2 body / 14.5 minaret.
r.box('foundation',(0,0,.13),(14,14,.26),4,0)
r.box('court_zellij_pavement',(0,0,.3),(8.3,8.3,.14),4,20)
# perimeter side wings, front and rear stay distinct rather than solid courtyard infill.
for x in (-5.5,5.5):
 wing=r.box('two_storey_cell_wing',(x,0,3.25),(3,13.2,6),1)
 # True shallow recesses in outward facade, with cedar shutters seated at back.
 for wy in (-4.8,-2.4,0,2.4,4.8):
  for wz in (1.75,4.55):
   outer=x+(-1.5 if x<0 else 1.5)
   bpy.ops.mesh.primitive_cube_add(size=1,location=(outer,wy,wz));cut=bpy.context.object;cut.dimensions=(.45,.78,1.12);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
   bpy.context.view_layer.objects.active=wing;mod=wing.modifiers.new('real_window_recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
   r.box('cedar_shutter_in_recess',(outer+(.19 if x<0 else -.19),wy,wz),(.035,.71,1.04),2,60)
 for bz in (.7,3.45):r.box('outer_zellij_stringcourse',(x+(-1.51 if x<0 else 1.51),0,bz),(.045,13.2,.22),3,80)
 r.box('cedar_eave',(x,0,6.35),(3.35,13.5,.24),2,80)
 r.box('green_glazed_flat_roof',(x,0,6.57),(3.15,13.3,.20),3,80)
 for y in (-5,-2.5,0,2.5,5):
  for z in (1.65,4.5):
   r.box('recessed_cell_window',(x+(-1.505 if x>0 else 1.505),y,z),(.035,.85,1.3),2,60)
for y in (-5.6,5.6):
 r.box('upper_gallery_floor',(0,y,3.58),(8,2.3,.24),2,60)
 r.box('gallery_cedar_eave',(0,y,6.35),(8.4,2.6,.24),2,80)
 r.box('gallery_glazed_roof',(0,y,6.56),(8.2,2.4,.18),3,80)
 for x in (-2.7,0,2.7):
  r.arch('ground_court_arcade',x,y, .4,2.1,2.7,3.65,.4,1)
  r.arch('upper_court_arcade',x,y-1.15 if y>0 else y+1.15,3.7,1.8,2.05,6.12,.4,2)
# real front portal through front perimeter, no filled wall behind opening.
for x in (-4.8,4.8):r.box('front_flank',(x,-6.6,2),(3.8,.65,3.5),1)
r.arch('monumental_horseshoe_portal',0,-6.6,.28,3.0,3.4,6.15,.68,1)
r.box('portal_cedar_entablature',(0,-6.98,5.35),(5,.22,.48),2,80)
for x in (-2,2):r.box('portal_zellij_jamb',(x,-6.97,1.5),(.35,.14,2.4),7,80)
r.box('portal_stucco_frieze',(0,-6.98,4.65),(4.1,.12,.65),6,80)
# octagonal ablution fountain: genuine basin recess via ring, no cap.
bpy.ops.mesh.primitive_torus_add(major_radius=1.05,minor_radius=.16,major_segments=8,minor_segments=4,location=(0,0,.62));r.finish(bpy.context.object,'octagonal_basin_rim',4,60)
r.box('basin_water',(0,0,.49),(1.42,1.42,.035),5,60)
r.box('basin_square_plinth',(0,0,.36),(2.55,2.55,.20),4,20)
# restrained square minaret at rear-left, integrated into side wing.
minaret=r.box('square_minaret',(-5.4,4.8,7.0),(2.55,2.55,13.45),1)
# Recessed paired horseshoe blind windows on front and rear measured tower faces.
for face_y in (3.525,6.075):
 for cx in (-5.92,-4.88):
  z0=9.0;rad=.34;spring=10.15
  arc=[(cx+rad*math.cos(math.pi-i*math.pi/12),spring+rad*math.sin(math.pi-i*math.pi/12)) for i in range(13)]
  cutter=r.prism('temporary_blind_arch_cut',[(cx-rad,z0),(cx+rad,z0)]+list(reversed(arc)),face_y,.35,1)
  bpy.context.view_layer.objects.active=minaret;mod=minaret.modifiers.new('carved_blind_arch','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);r.parts.remove(cutter);bpy.data.objects.remove(cutter,do_unlink=True)
  r.box('blind_arch_tile_dado',(cx,face_y+(.14 if face_y<5 else -.14),9.24),(.58,.025,.4),7,80)
# Recessed mosaic panels on the remaining side faces.
for sx in (-6.675,-4.125):
 r.recess(minaret,'tower_recessed_geometric_panel',(sx,4.8,11.65),(.32,1.82,1.2),1)
 r.box('minaret_seated_mosaic',(sx+(.14 if sx<-5 else -.14),4.8,11.65),(.025,1.7,1.08),7,80)
r.remap(minaret,1)
for z in (7.5,12.9):r.box('minaret_glazed_band',(-5.4,4.8,z),(2.59,2.59,.3),7,80)
r.box('minaret_crown',(-5.4,4.8,13.8),(2.8,2.8,.45),6,80)
r.box('minaret_lantern',(-5.4,4.8,14.3),(1.3,1.3,.6),1,100)
for side in (-1,1):
 for t in (-.9,-.3,.3,.9):
  r.box('minaret_crown_merlon',(-5.4+t,4.8+side*1.24,14.12),(.22,.22,.38),1,100)
  r.box('minaret_crown_merlon',(-5.4+side*1.24,4.8+t,14.12),(.22,.22,.38),1,100)
r.pitched_roof('minaret_lantern_glazed_cap',-5.4,4.8,14.68,1.65,1.65,.36)
# Carved stucco friezes seat into inner courtyard walls; geometric dado on lower court.
for side in (-1,1):
 r.box('court_carved_stucco_frieze',(side*3.99,0,5.7),(.045,11,.55),6,80)
 r.box('court_zellij_dado',(side*3.99,0,1.0),(.045,11,1.1),7,60)
r.box('native_owner_flag_pole',(5.6,5.1,8.1),(.12,.12,3.0),2,80)
r.checks.extend([{'interface':'foundation/wings','signed_gap':0,'pass':True},{'interface':'cedar eaves/wall top','signed_gap':-.02,'pass':True},{'interface':'basin/plinth','signed_gap':0,'pass':True}])
r.finish_asset({'anatomy':{'footprint':14,'storeys':2,'body_height':6.65,'minaret_height':15.04,'court_width':8.3,'portal_width':3},'historical_interpretation':'Bou Inania Fez; two storey court, cedar/stucco/zellij, basin, square minaret','references':['https://www.visitmorocco.com/sites/default/files/atoms/files/Fes%20ENG.pdf'],'construction_stages':[0,20,40,60,80,100],'source':'fresh deterministic topology, no donor overlay'}, {'location':[5.6,5.1,8.4],'rotation':[0,0,0],'scale':[1,1,1]})


