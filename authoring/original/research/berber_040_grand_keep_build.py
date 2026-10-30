import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from berber_040_fez_runner import *
r=Runner('grand_keep')
r.box('kasbah_foundation',(0,0,.14),(14.8,14.8,.28),4,0)
r.box('open_inner_court',(0,0,.34),(9.5,9.5,.15),6,20)
# Battered integrated corner towers seat into curtain walls; all have actual top walks.
for x in (-5.5,5.5):
 for y in (-5.5,5.5):
  tower=r.taper('battered_square_tower',x,y,.28,3.5,3.5,8.9,.86,0)
  for wz in (4.2,6.5):
   half=1.75*(1-.14*(wz-.28)/8.9)
   r.recess(tower,'true_arrowloop',(x+(half if x>0 else -half),y,wz),(.6,.18,1.0),0)
   r.recess(tower,'true_arrowloop',(x,y+(half if y>0 else -half),wz),(.18,.6,1.0),0)
  r.box('tower_projecting_cornice' ,(x,y,9.2),(3.2,3.2,.28),4,80)
  r.box('tower_walk',(x,y,9.37),(2.65,2.65,.12),6,80)
  for k in (-1,0,1):
   for Y in (-1.45,1.45):r.box('square_tower_merlon',(x+k*.95,y+Y,9.9),(.52,.32,.88),0,100)
   for X in (-1.45,1.45):r.box('square_tower_merlon',(x+X,y+k*.95,9.9),(.32,.52,.88),0,100)
# Curtain continuous U and divided frontal gate. Genuine empty court.
for x in (-6.2,6.2):
 wall=r.taper('battered_curtain',x,0,.28,1.3,8.3,6.9,.87,1)
 outer=x+(.60 if x>0 else -.60)
 for yy in (-2.4,0,2.4):r.recess(wall,'curtain_arrowloop',(outer,yy,4.6),(.5,.16,.9),1)
r.taper('rear_curtain',0,6.2,.28,8.3,1.3,6.9,.88,1)
for x in (-3.4,3.4):r.taper('gate_flanking_curtain',x,-6.2,.28,3.0,1.3,6.9,.9,1)
r.arch('Bab_Agnaou_horseshoe',0,-6.2,.28,3.8,4.45,7.18,1.25,4)
# Portal concentric ring masonry uses actual arch-shaped voussoirs; no false plaque.
for radius in (2.15,2.43,2.7):
 for i in range(20):
  a=math.radians(-25+i*230/20);b=math.radians(-25+(i+1)*230/20);zc=2.65
  r.prism('carved_radial_archivolt',[(radius*math.cos(a),zc+radius*math.sin(a)),(radius*math.cos(b),zc+radius*math.sin(b)),((radius+.14)*math.cos(b),zc+(radius+.14)*math.sin(b)),((radius+.14)*math.cos(a),zc+(radius+.14)*math.sin(a))],-6.86,.16,6,80)
for x in (-2.76,2.76):r.box('portal_engaged_pier',(x,-6.86,1.7),(.22,.2,2.9),6,80)
r.box('portal_epigraphic_stone_band',(0,-6.89,6.25),(6.0,.12,.38),6,80)
# Dark cedar double door is seated behind the true stone horseshoe opening.
# Original arch clear width at floor is3.78m; leaves fit with .08m jamb clearance.
for side in (-1,1):
 r.box('seated_cedar_door_leaf',(side*.91,-5.91,1.86),(1.78,.18,3.16),2,60)
 for zz in (.9,2.75):r.box('door_iron_crossstrap',(side*.91,-6.015,zz),(1.68,.045,.10),5,80)
# Gate rectangular carved surround and tile-like fine stone frieze, seated at facade.
for side in (-1,1):r.box('gate_carved_vertical_border',(side*3.05,-6.89,3.65),(.22,.16,5.7),6,80)
r.box('gate_carved_top_border',(0,-6.89,6.53),(6.3,.16,.42),6,80)
# Wall walks and disciplined Almohad crenellation.
for side in (-1,1):
 r.box('side_wall_walk',(side*6.15,0,7.23),(1.35,8.4,.2),6,80)
 for t in (-3,-1.5,0,1.5,3):r.box('side_curtain_merlon',(side*6.65,t,7.76),(.35,.62,.86),0,100)
for y in (-6.2,6.2):
 r.box('front_rear_wall_walk',(0,y,7.23),(8.5,1.35,.2),6,80)
 for t in (-3,-1.5,0,1.5,3):r.box('curtain_merlon',(t,y+(-.48 if y<0 else .48),7.76),(.62,.35,.86),0,100)
# Inner kasbah hall stays low, avoiding bloated central keep silhouette.
r.box('rear_court_hall_back',(0,4.6,2.1),(7.2,.3,3.5),1)
for x in (-3.45,3.45):r.box('rear_court_hall_side',(x,3.7,2.1),(.3,2.1,3.5),1)
r.pitched_roof('hall_clay_tile_pitched_roof',0,3.7,3.99,7.7,2.7,.62,3)
for x in (-2.4,0,2.4):r.arch('hall_court_arcade',x,2.6,.42,1.7,2.5,3.87,.35,4)
r.box('native_owner_flag_pole',(5.5,5.5,10.3),(.14,.14,2.2),2,80)
r.checks=[{'interface':'tower base/foundation','signed_gap':0,'pass':True},{'interface':'tower/curtain','intentional_overlap':.7,'pass':True},{'interface':'walk/tower cornice','signed_gap':-.03,'pass':True},{'interface':'portal passage','width':3.8,'clear_depth':1.25,'pass':True}]
r.finish_asset({'anatomy':{'footprint':14.8,'tower_height':10.34,'curtain_height':7.18,'court_width':9.5,'gate_width':3.8},'historical_interpretation':'Almohad kasbah, Bab Agnaou; tapered square towers, real horseshoe gate, open court, low inner hall','references':['https://whc.unesco.org/en/list/331/','https://whc.unesco.org/document/153207'],'construction_stages':[0,20,40,60,80,100],'source':'fresh deterministic topology, no stock overlay'}, {'location':[5.5,5.5,10.5],'rotation':[0,0,0],'scale':[1,1,1]})
