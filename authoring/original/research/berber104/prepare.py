"""Native AI authoring from installed editor XML; no foreign project writes."""
from pathlib import Path
import collections,copy,hashlib,json,subprocess,sys,xml.etree.ElementTree as E
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
SOURCE=HERE/'source/attrib/instances';GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
ARCH=Path(r'C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com\garrison\bin\sga-archiver.exe')
REFERENCE=Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\ReferenceAttributes.sga')
REFMOD=Path(r'E:\age of empires 4 mods\01_Custom_Civilizations\Community_Civilization_pack\Community_civilization_pack_normal\assets\attrib\instances\ai\ai_economy\complete')
ids=json.loads((HERE/'editor-identities.json').read_text(encoding='utf-8-sig'))
pool=iter(ids['list_item_ids']);allocations=[]
def item():
 value=str(next(pool));allocations.append(value);return value
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def xml(path,root):path.parent.mkdir(parents=True,exist_ok=True);E.indent(root);path.write_bytes(E.tostring(root,encoding='utf-8',xml_declaration=True))
def node(parent,name):return parent.find("*[@name='%s']"%name)
def field(parent,name,value):
 x=node(parent,name);assert x is not None,name;x.set('value',str(value));return x
def reference(parent,name,value):
 x=E.SubElement(parent,'instance_reference',{'name':name,'value':value,'List.ItemID':item()})
 if value in own_paths:x.set('mod',GUID)
 return x
def fresh_ids(root):
 for n in root.iter():
  if 'List.ItemID' in n.attrib:n.set('List.ItemID',item())
  n.attrib.pop('List.ParentItemID',None);n.attrib.pop('List.ListAction',None)
 return root
def read_official(name):return E.parse(HERE/'official/instances'/name).getroot()
def new_instance(donor,pbg,description):
 root=read_official(donor)
 for v in root.findall('variant'):root.remove(v)
 fresh_ids(root);root.set('description',description);root.find('uniqueid').set('value',str(pbg));return root

if (HERE/'mapping.json').exists():
 assert '--refresh' in sys.argv,'Do not overwrite prepared inputs without explicit refresh'
 prior=json.loads((HERE/'mapping.json').read_text())
 for p,h in prior['source_hashes'].items():assert sha(HERE/p)==h,('Unexpected editable drift',p)
index=json.loads(subprocess.check_output([str(ARCH),'inspect',str(REFERENCE)]))
official_paths={x['path'][10:-4].replace('/','\\') for x in index['archive']['members'] if x['path'].startswith('instances/') and x['path'].endswith('.xml')}
own_files={str(p.relative_to(ROOT/'assets/attrib/instances')).replace('/','\\')[:-4]:p for p in (ROOT/'assets/attrib/instances').rglob('*.xml')}
own_paths=set(own_files);all_paths=official_paths|own_paths
def resolve(category,name):
 matches=[p for p in all_paths if p.startswith(category+'\\') and p.rsplit('\\',1)[-1]==name]
 local=[p for p in matches if p in own_paths]
 if len(local)==1:return local[0]
 if len(matches)==1:return matches[0]
 # Existing native economy reference is stronger than a basename guess.
 old=[p for p in matches if p in native_refs]
 assert len(old)==1,(category,name,matches)
 return old[0]

economy=read_official('ai/ai_economy/complete/default_economy.xml')
native_refs={n.get('value') for n in economy.iter('instance_reference')}
lua=LuaRuntime();lua.execute((ROOT/'research/berber103/scar/ai/berber_ai_catalog.scar').read_text())
catalog=lua.globals().BerberAI_Catalog
roster={key:sorted(catalog[key].keys()) for key in ['buildings','squads','upgrades']}
# Include exposed production/research omitted by the former scripted catalog.
for p in own_files.values():
 for ext in E.parse(p).getroot().iter('template_reference'):
  if ext.get('value','').rsplit('\\',1)[-1] not in ('spawner_ext','upgrade_ext'):continue
  for n in ext.iter('instance_reference'):
   value=n.get('value','');category=value.split('\\',1)[0]
   if category=='upgrade':roster['upgrades'].append(value.rsplit('\\',1)[-1])
for key in roster:roster[key]=sorted(set(roster[key]))
custom_squads=sorted(p.rsplit('\\',1)[-1] for p in own_paths if p.startswith('sbps\\races\\malian\\berbers\\'))
grant_only={'upgrade_cul_ancient_relics_ayy','upgrade_cul_medical_centers_ayy','upgrade_econ_agriculture_ayy'}
automatic_buildings={'building_defense_palisade_bastion_mal','building_defense_wall_bastion_mal'}
special_squads={'unit_king_1_mal'}
alliance_names=['grenade_throw_song_cmp','increase_armor_song_cmp','increase_damage_song_cmp']
alliance_paths=[resolve('abilities',n) for n in alliance_names]
upgrade_paths=[resolve('upgrade',n) for n in sorted(grant_only)]
added=[]
official_groups=read_official('ai/ai_economy/complete/default_economy.xml').find("group/list[@name='production_groups']")
def production_binding(category,name):
 # Preserve the native category used for the exact original blueprint name.
 # Custom archive paths often moved under berbers/ or landmarks/.
 original_groups=official_groups
 matches=[node(g,'lua_binding').get('value') for g in original_groups
          for n in node(g,'members')
          if n.get('value','').startswith(category+'\\') and n.get('value','').endswith('\\'+name)]
 if matches:return matches[0]
 if category=='upgrade':
  if 'harvest_rate' in name:return 'ScoringFunctions_PlayerEconGatheringUpgrade'
  return 'ScoringFunctions_PlayerUnitTierUpgrade' if name.startswith('upgrade_unit_knight_4') else 'ScoringFunctions_PlayerUnitCombatUpgrade'
 if name.startswith('unit_handcannon_'):return 'ScoringFunctions_RangedInfantry'
 if name.startswith('unit_naval_combat_warship_'):return 'ScoringFunctions_WarShip'
 if name.startswith('unit_naval_combat_ship_'):return 'ScoringFunctions_NavalMilitary'
 if name.startswith(('unit_ram_','unit_trebuchet_','unit_cannon_')):return 'ScoringFunctions_Siege'
 if name.startswith('unit_siege_tower_'):return 'ScoringFunctions_SiegeTower'
 if name.startswith('unit_scout_'):return 'ScoringFunctions_Scouting'
 role=catalog.squads[name].role
 return 'ScoringFunctions_RangedInfantry' if role in ['archer','masmuda','sanhaja'] else 'ScoringFunctions_Infantry'

for variant in [economy,*economy.findall('variant')]:
 bag=variant.find('group');groups=node(bag,'production_groups')
 def group_with_binding(binding):
  matches=[g for g in groups if node(g,'lua_binding').get('value')==binding]
  if matches:return matches[0]
  donor=next(g for g in official_groups if node(g,'lua_binding').get('value')==binding)
  result=fresh_ids(copy.deepcopy(donor));members=node(result,'members');members.clear();members.set('name','members')
  groups.append(result);return result
 def add_member(group,path):
  members=node(group,'members')
  if not any(n.get('value')==path for n in members):reference(members,'member',path)
 group_refs={n.get('value') for g in groups for n in node(g,'members')}
 for name in roster['squads']:
  if name in special_squads:continue
  # Native ram and siege-tower production scores the entity, not squad.
  category='ebps' if name in ['unit_ram_3_mal','unit_siege_tower_3_mal'] else 'sbps'
  path=resolve(category,name)
  if path in group_refs:continue
  binding=production_binding(category,name)
  add_member(group_with_binding(binding),path);added.append({'variant':variant.get('name','default'),'category':'squad','name':name,'binding':binding})
 for name in roster['upgrades']:
  if name in grant_only:continue
  path=resolve('upgrade',name)
  if path in group_refs:continue
  binding=production_binding('upgrade',name)
  add_member(group_with_binding(binding),path);added.append({'variant':variant.get('name','default'),'category':'upgrade','name':name,'binding':binding})
 # Reconnect relocated buildings to their existing native production category.
 # Tents use the explicit legacy utility below; capital TC and generated wall
 # bastions are not directly constructed production requests.
 for name in roster['buildings']:
  if name in automatic_buildings or name in ['building_hut_ayy','building_town_center_capital_mal']:continue
  path=resolve('ebps',name)
  if path in group_refs:continue
  matches=[g for g in official_groups if any(n.get('value','').endswith('\\'+name) and n.get('value','').startswith('ebps\\') for n in node(g,'members'))]
  if not matches:
   assert name=='building_resource_farm_mal',('Unmapped building',name)
   continue # Official default resource-generator utility owns farms.
  binding=node(matches[0],'lua_binding').get('value')
  add_member(group_with_binding(binding),path);added.append({'variant':variant.get('name','default'),'category':'building','name':name,'binding':binding})
 # The legacy native economy utilities are explicitly enabled by official data.
 assert node(bag,'enable_legacy_scoring').get('value')=='True'
 entities=node(bag,'entities');donor=next(g for g in entities if node(node(g,'utility'),'max_num') is not None)
 tent=fresh_ids(copy.deepcopy(donor));tent.set('comment','Berber Tribal Tents - native construction')
 blueprints=node(tent,'blueprints');blueprints.clear();blueprints.set('name','blueprints')
 reference(blueprints,'entity',resolve('ebps','building_hut_ayy'))
 utility=node(tent,'utility')
 for key,value in [('utility',1000),('utility_function',''),('max_num',4),('max_num_produced',-1),('per_unit_scale',0.5),('per_unit_scale_produced',0),('consider_time_to_acquire','True')]:field(utility,key,value)
 entities.append(tent)
 abilities=node(bag,'abilities');donor=abilities[0]
 for name,path,priority in zip(alliance_names,alliance_paths,[990,1000,990]):
  entry=fresh_ids(copy.deepcopy(donor));entry.set('comment','Berber native alliance '+name)
  blueprints=node(entry,'blueprints');blueprints.clear();blueprints.set('name','blueprints');reference(blueprints,'ability',path)
  utility=node(entry,'utility');field(utility,'utility',priority);field(utility,'utility_function','')
  abilities.append(entry)
xml(SOURCE/'ai/ai_economy/complete/default_economy.xml',economy)

# Native build location mappings. No gameplay placement restrictions are edited.
tent=new_instance('ai/ai_entity/military_production_fre.xml',ids['pbg_ids'][0],'Berber Tribal Tents near town centers')
bag=tent.find('group');app=node(bag,'applicable_blueprints');app.clear();app.set('name','applicable_blueprints');reference(app,'applicable_blueprint',resolve('ebps','building_hut_ayy'))
construction=node(bag,'construction');near=node(construction,'near_to_structures');near.clear();near.set('name','near_to_structures')
for name in ['building_town_center_capital_mal','building_town_center_mal']:reference(near,'structure',resolve('ebps',name))
xml(SOURCE/'ai/ai_entity/berber_tribal_tent.xml',tent)
production=new_instance('ai/ai_entity/military_production_fre.xml',ids['pbg_ids'][1],'Berber production near Tribal Tent or Funduq influence')
bag=production.find('group');app=node(bag,'applicable_blueprints');app.clear();app.set('name','applicable_blueprints')
for name in ['building_unit_infantry_mal','building_unit_ranged_mal','building_unit_cavalry_mal','building_unit_siege_mal','building_econ_market_mal']:
 reference(app,'applicable_blueprint',resolve('ebps',name))
near=node(node(bag,'construction'),'near_to_structures');near.clear();near.set('name','near_to_structures')
for name in ['building_hut_ayy','building_landmark_age1_landmarkb_mal']:reference(near,'structure',resolve('ebps',name))
xml(SOURCE/'ai/ai_entity/berber_production.xml',production)
house=read_official('ai/ai_entity/malian_house.xml')
for v in [house,*house.findall('variant')]:
 near=node(node(v.find('group'),'construction'),'near_to_structures')
 for entry,name in zip(near,['building_town_center_capital_mal','building_town_center_mal','building_landmark_age1_landmarkb_mal']):
  path=resolve('ebps',name);entry.set('value',path)
  if path in own_paths:entry.set('mod',GUID)
xml(SOURCE/'ai/ai_entity/malian_house.xml',house)
mining=read_official('ai/ai_entity/mining_camp.xml')
for v in [mining,*mining.findall('variant')]:reference(node(v.find('group'),'applicable_blueprints'),'applicable_blueprint',resolve('ebps','building_econ_mining_camp_mal'))
xml(SOURCE/'ai/ai_entity/mining_camp.xml',mining)

alliances=new_instance('ai/ai_ability/monastery_create_relic.xml',ids['pbg_ids'][2],'Berber alliances - native economic ability production')
bag=alliances.find('group');abilities=node(bag,'abilities');abilities.clear();abilities.set('name','abilities')
for path in alliance_paths:reference(abilities,'ability',path)
req=node(node(node(bag,'tactic_info_default'),'tactic_info'),'tactic_filter_start_requirements')
# Copy confirmed, existing requirement structure into the native-only tactic filter.
ability=E.parse(own_files[alliance_paths[1]]).getroot()
for path in upgrade_paths:
 donor=next(x for x in ability.iter('template_reference') if x.get('value')=='requirements\\required_player_upgrade' and any(c.get('value')==path for c in x.iter('instance_reference')))
 requirement=fresh_ids(copy.deepcopy(donor));field(requirement,'is_present','False');req.append(requirement)
xml(SOURCE/'ai/ai_ability/berber_alliances.xml',alliances)
combat=new_instance('ai/ai_ability/races/mongol/khan_defensive_arrow.xml',ids['pbg_ids'][3],'Berber defensive combat abilities - native tactics')
bag=combat.find('group');abilities=node(bag,'abilities');abilities.clear();abilities.set('name','abilities')
for name in ['ber_spearman_ranged_damage_reduction','deploy_shields_stationary_cb_ber','shirkuh_speed_activate_ayy','teuton_master_armor_cru']:reference(abilities,'ability',resolve('abilities',name))
tactic=node(node(bag,'tactic_info_default'),'tactic_info')
field(tactic,'tactic_filter_start','');field(tactic,'tactic_max_range_override',-1)
classes=node(tactic,'class');field(classes,'tactic_Combat','True');field(classes,'tactic_OnTask','False');field(classes,'tactic_Moving','False')
field(node(bag,'buff_info'),'buff_allies','False')
xml(SOURCE/'ai/ai_ability/berber_defensive_combat.xml',combat)

gm=ROOT/'research/berber103/scar/winconditions/berber_future_kingdom_GM.scar'
text=gm.read_text();assert text.count('import("ai/berber_ai_controller.scar")')==1
target=HERE/'scar/winconditions'/gm.name;target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(text.replace('import("ai/berber_ai_controller.scar")','-- Berber1.0.4: native AI owns computer players from match start.'),encoding='utf8')
files=sorted(SOURCE.rglob('*.xml'))
report={'version':'1.0.4','native_ai_from_start':True,'custom_squads':custom_squads,'roster':roster,'added':added,
 'new_instances':['ai/ai_entity/berber_tribal_tent.xml','ai/ai_entity/berber_production.xml','ai/ai_ability/berber_alliances.xml','ai/ai_ability/berber_defensive_combat.xml'],
 'grant_only_upgrades':sorted(grant_only),'automatic_buildings':sorted(automatic_buildings),'special_mode_only_squads':sorted(special_squads),
 'reference_project_hashes':{str(p):sha(p) for p in REFMOD.rglob('*') if p.is_file()},
 'official_reference_archive':str(REFERENCE),'official_reference_sha256':sha(REFERENCE),
 'source_hashes':{p.relative_to(HERE).as_posix():sha(p) for p in files},'allocated_list_ids_used':allocations,
 'unrun_native_gates':['native economy','tent placement within influence','alliance ability selection and anti-switch filter','combat ability activation','all ages/save/load/multiplayer']}
write(HERE/'mapping.json',report)
print('PREPARED',len(files),'AI instances;',len(custom_squads),'custom squad variants;',len(allocations),'editor-allocated list IDs')
