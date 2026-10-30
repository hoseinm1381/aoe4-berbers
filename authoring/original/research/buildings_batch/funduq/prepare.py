from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[3];A=R/'art/buildings/funduq';Q=Path(__file__).parent
for p in [A/'geometry_helpers.py',Q/'run_build.py']:
 p.write_text(p.read_text().replace('ribat','funduq').replace('Ribat','Funduq'))
s=(R/'art/buildings/ribat/build_ribat.py').read_text().replace('Ribat','Funduq').replace('RIBAT','FUNDUQ').replace('Landmark1a','Landmark1b').replace('landmark 1a','landmark 1b')
s=s.replace('lo[0]>=-3 and lo[1]>=-3 and hi[0]<=3 and hi[1]<=3','lo[0]>=-4 and lo[1]>=-4 and hi[0]<=4 and hi[1]<=4').replace("'site_footprint':[6,6]","'site_footprint':[8,8]").replace('ortho_scale=8.3','ortho_scale=11.3').replace('Vector((0,0,1.5))','Vector((0,0,2.3))')
s=s.replace('location=(8,-10,9)','location=(8,-10,13)').replace("bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Funduq_Age{age}.blend'))", "bpy.ops.object.light_add(type='AREA',location=(0,0,13));bpy.context.object.data.energy=1800;bpy.context.object.data.size=7\n bpy.ops.wm.save_as_mainfile(filepath=str(ART/f'Berber_Funduq_Age{age}.blend'))")
build='''def build(age):
 ctx=g.reset_scene();g.PARTS.clear();g.CONTACTS.clear();g.MATS.clear();GUARDS.clear();g.setup_maps()
 for name,col in [('normal',(.5,.5,1)),('roughness',(.85,.85,.85)),('metal',(0,0,0))]:
  im=bpy.data.images.new('Funduq_'+name,width=256,height=256);im.pixels.foreach_set(list((*col,1))*65536);im.filepath_raw=str(ART/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True
 floor=.16;low=1.80;upper=1.62+(age-2)*.12;deck=floor+low;top=deck+.12+upper;mat='earth' if age==2 else 'lime'
 box('foundation',(0,0,.08),(7.70,7.70,.16),'stone',0)
 # Grand four-wing inn with a real 3.5-square open trading court.
 for side,x in [('west',-3.56),('east',3.56)]:
  wall=box(side+'_outer_wall',(x,0,floor+(top-floor)/2),(.24,6.88,top-floor),mat,40);contact(wall.name,'foundation')
 for side,y in [('south',-3.56),('north',3.56)]:
  wall=box(side+'_outer_wall',(0,y,floor+(top-floor)/2),(7.36,.24,top-floor),mat,40);contact(wall.name,'foundation')
  if side=='south':arch(wall,0,y,2.10,2.82)
 # Continuous inward arcades support the upper galleries; stock room door recesses cut out.
 for side,x in [('west',-1.90),('east',1.90)]:
  arcade=box(side+'_ground_arcade',(x,0,floor+low/2),(.20,5.48,low),mat,40);contact(arcade.name,'foundation')
  for y in [-1.8,-.6,.6,1.8]:arch(arcade,y,-x,.92,1.66,side=True)
  deckob=box(side+'_gallery_floor',((x+(-3.56 if x<0 else 3.56))/2,0,deck+.06),(1.90,7.36,.12),'cedar',60);contact(deckob.name,arcade.name)
  outerroom=box(side+'_merchant_room_front',(x+(-.66 if x<0 else .66),0,deck+.12+upper/2),(.16,6.94,upper),mat,60);contact(outerroom.name,deckob.name)
  for y in [-2.4,-1.2,0,1.2,2.4]:arch(outerroom,y,-(x+(-.66 if x<0 else .66)),.46,1.20,base=deck+.12,side=True)
  for y in [-3,-1.8,-.6,.6,1.8,3]:
   part=box(side+'_room_divider',((x+(-3.56 if x<0 else 3.56))/2+(-.20 if x<0 else .20),y,deck+.12+upper/2),(1.16,.10,upper),mat,60);contact(part.name,deckob.name)
  roof(side+'_roof',(-2.73 if x<0 else 2.73),0,1.90,7.36,top,age);contact(side+'_roof',outerroom.name)
  # Gallery balustrade: seated on the continuous floor, never a floating stripe.
  for y in [-2.4,-1.2,0,1.2,2.4]:
   post=box(side+'_gallery_post',(x,y,deck+.12+.34),(.09,.09,.68),'cedar',80);contact(post.name,deckob.name)
  box(side+'_gallery_rail',(x,0,deck+.12+.68),(.10,5.48,.08),'cedar',80)
 for side,y in [('north',2.78),('south',-2.78)]:
  arcade=box(side+'_ground_arcade',(0,y+(-.80 if y>0 else .80),floor+low/2),(3.64,.20,low),mat,40);contact(arcade.name,'foundation')
  if side=='south':arch(arcade,0,-1.98,2.10,2.82)
  else:
   for x in [-1.2,0,1.2]:arch(arcade,x,1.98,.86,1.66)
  slab=box(side+'_gallery_floor',(0,y,deck+.06),(3.64,1.76,.12),'cedar',60);contact(slab.name,arcade.name)
  front=box(side+'_merchant_rooms',(0,y+.30,deck+.12+upper/2),(3.64,.18,upper),mat,60);contact(front.name,slab.name)
  for x in [-1.2,1.2]:arch(front,x,y+.30,.48,1.2,base=deck+.12)
  if side=='north':arch(front,0,y+.30,.48,1.2,base=deck+.12)
  else:
   arch(front,0,y+.30,2.10,2.82)
   c=box('TEMP_gate_gallery_void',(0,y,deck+.06),(2.18,2.1,.30),'shadow',60)
   bpy.context.view_layer.objects.active=slab;mo=slab.modifiers.new('caravan gateway through upper deck','BOOLEAN');mo.operation='DIFFERENCE';mo.object=c;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(c,do_unlink=True);g.PARTS.pop()
  roof(side+'_roof',0,y,3.56,1.80,top,age);contact(side+'_roof',front.name)
  for x in ([-1.45,-.75,0,.75,1.45] if side=='north' else [-1.45,1.45]):
   post=box(side+'_gallery_post',(x,y+(-.76 if y>0 else .76),deck+.12+.34),(.09,.09,.68),'cedar',80);contact(post.name,slab.name)
  if side=='north':box(side+'_gallery_rail',(0,y-.76,deck+.12+.68),(3.56,.10,.08),'cedar',80)
  else:
   for x in [-1.46,1.46]:box(side+'_gallery_rail',(x,y+.76,deck+.12+.68),(.64,.10,.08),'cedar',80)
 # Actual external shutter recesses punctuate the upper guest-room facade.
 for side,x in [('west',-3.56),('east',3.56)]:
  wall=bpy.data.objects[side+'_outer_wall'];sign=-1 if x<0 else 1
  for y in [-2.4,-1.2,0,1.2,2.4]:
   zz=deck+.12+upper*.56
   c=box('TEMP_shutter_recess',(sign*3.65,y,zz),(.18,.40,.58),'shadow',60)
   bpy.context.view_layer.objects.active=wall;mo=wall.modifiers.new('actual guest room shutter recess','BOOLEAN');mo.operation='DIFFERENCE';mo.object=c;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(c,do_unlink=True);g.PARTS.pop()
   box(side+'_fitted_room_shutter',(sign*3.60,y,zz),(.04,.38,.56),'cedar',80)
   box(side+'_window_sill',(sign*3.67,y,zz-.32),(.20,.48,.06),'stone',80)
 for y in [-3.56,3.56]:
  wall=bpy.data.objects['south_outer_wall' if y<0 else 'north_outer_wall'];sign=-1 if y<0 else 1
  for x in [-2.75,-1.4,1.4,2.75]:
   zz=deck+.12+upper*.56
   c=box('TEMP_shutter_recess',(x,sign*3.65,zz),(.40,.18,.58),'shadow',60)
   bpy.context.view_layer.objects.active=wall;mo=wall.modifiers.new('actual guest room shutter recess','BOOLEAN');mo.operation='DIFFERENCE';mo.object=c;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(c,do_unlink=True);g.PARTS.pop()
   box('fitted_room_shutter',(x,sign*3.60,zz),(.38,.04,.56),'cedar',80)
   box('window_stone_sill',(x,sign*3.67,zz-.32),(.48,.20,.06),'stone',80)
 # Broad loaded-animal entry: actual arch cut through both wall/arcade, clear center route.
 for x in [-1.22,1.22]:
  pier=box('gateway_stone_pier',(x,-3.71,1.58),(.30,.20,2.84),'stone',40);contact(pier.name,'foundation')
  box('gateway_owner_hanging_cloth',(x,-3.825,2.28),(.22,.024,1.04),'owner_cloth',100)
 box('gateway_carved_head',(0,-3.72,3.17),(2.76,.18,.28),'earth' if age==2 else 'lime',80)
 # Permanent cloth awnings cover only the side unloading bays, leave court open to sky.
 for x in [-1.78,1.78]:
  for y in [-1.42,1.42]:
   p=box('awning_post',(x,y,floor+.70),(.08,.08,1.40),'cedar',20);contact(p.name,'foundation')
  box('unloading_owner_awning',(x,0,1.59),(.60,2.92,.055),'owner_cloth',80)
  box('awning_crossbeam',(x,0,1.55),(.09,2.94,.08),'cedar',60)
 # Physical steps against north arcade connect court to upper gallery.
 for i in range(8):
  height=(deck+.12-floor)*(i+1)/8
  step=box('gallery_access_stair',(-1.08,1.28+i*.17,floor+height/2),(.62,.17,height),'stone',60);contact(step.name,'foundation')
 # Merchant logistics: storage stacks, bale loading pads and tether rails seated to ground.
 for x in [-2.85,2.85]:
  for y in [-2.0,-.8,.4,1.6]:
   crate=box('warehouse_crate',(x,y,floor+.27),(.48,.58,.54),'cedar',80);contact(crate.name,'foundation')
   if age>=3:box('stacked_trade_bale',(x,y,floor+.69),(.40,.50,.30),'straw',100);contact(bpy.context.object.name,crate.name)
 for x in [-1.20,1.20]:
  p=box('court_loading_pallet',(x,.70,floor+.05),(.52,.72,.10),'cedar',60);contact(p.name,'foundation')
  bale=box('unloaded_court_bale',(x,.70,floor+.27),(.43,.64,.34),'straw',80);contact(bale.name,p.name)
 for x in [-1.36,1.36]:
  p=box('animal_tether_post',(x,-.70,floor+.38),(.11,.11,.76),'cedar',60);contact(p.name,'foundation')
  box('tether_crossbar',(x,-.40,floor+.65),(.08,.72,.08),'cedar',80)
 if age>=3:
  for x in [-3.56,3.56]:box('lime_gateway_corner_course',(x,-3.58,.46),(.30,.32,.60),'lime',40)
 if age==4:
  for x in [-.90,-.60,-.30,0,.30,.60,.90]:
   o=box('geometric_gateway_inlay',(x,-3.818,3.17),(.105,.025,.105),'clay',100);o.rotation_euler.y=math.pi/4
  for y in [-2,0,2]:
   for x in [-3.7,3.7]:box('roof_timber_drain',(x,y,top+.06),(.30,.10,.09),'cedar',80)
 finalize(age)

'''
s=s[:s.index('def build(age):')]+build+s[s.index('def finalize(age):'):]
(A/'build_funduq.py').write_text(s)
base=Path('C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin')
if not (Q/'mal.rgd').exists():subprocess.run([str(base/'sga-archiver.exe'),'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga','attrib/ebps/races/malian/buildings/building_landmark_age1_landmarkb_mal.rgd',str(Q/'mal.rgd')],check=True,capture_output=True)
if not (Q/'mal.xml').exists():subprocess.run([str(base/'sga-archiver.exe'),'decode-rgd',str(Q/'mal.rgd'),str(Q/'mal.xml')],check=True,capture_output=True)
