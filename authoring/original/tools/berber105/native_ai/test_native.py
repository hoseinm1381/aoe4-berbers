from pathlib import Path
import json,unittest,xml.etree.ElementTree as E
HERE=Path(__file__).resolve().parent
class NativeTests(unittest.TestCase):
 def setUp(self):
  self.report=json.loads((HERE/'mapping.json').read_text())
  self.source=HERE/'source/attrib/instances'
 def test_scripted_controller_is_not_imported(self):
  gm=(HERE/'scar/winconditions/berber_future_kingdom_GM.scar').read_text()
  self.assertNotIn('import("ai/berber_ai_controller.scar")',gm)
  self.assertNotIn('AI_Enable(',gm)
  self.assertNotIn('AI_SetDifficulty(',gm)
 def test_all_custom_combat_variants_have_native_groups(self):
  r=E.parse(self.source/'ai/ai_economy/complete/default_economy.xml').getroot()
  for variant in [r,*r.findall('variant')]:
   bag=variant.find('group')
   groups=bag.find("list[@name='production_groups']")
   refs={x.get('value').rsplit('\\',1)[-1] for x in groups.iter('instance_reference')}
   for n in self.report['custom_squads']:self.assertIn(n,refs)
 def test_tribal_tent_has_bounded_native_construction_utility(self):
  r=E.parse(self.source/'ai/ai_economy/complete/default_economy.xml').getroot()
  for v in [r,*r.findall('variant')]:
   candidates=[n for n in v.findall("group/list[@name='entities']/group") if any(x.get('value','').endswith('building_hut_ayy') for x in n.iter('instance_reference'))]
   self.assertEqual(len(candidates),1)
   self.assertEqual(candidates[0].find("template_reference/int[@name='max_num']").get('value'),'4')
 def test_alliance_abilities_registered_for_native_production(self):
  r=E.parse(self.source/'ai/ai_ability/berber_alliances.xml').getroot()
  self.assertEqual(r.find("group/enum[@name='ability_type']").get('value'),'player_production')
  self.assertEqual(len(r.findall("group/list[@name='abilities']/instance_reference")),3)
  req=r.find("group/template_reference/group/list[@name='tactic_filter_start_requirements']")
  self.assertEqual(len(req),3)
  self.assertTrue(all(n.find("bool[@name='is_present']").get('value')=='False' for n in req))
 def test_identity_allocation_and_local_references(self):
  ids=json.loads((HERE/'editor-identities.json').read_text(encoding='utf-8-sig'))
  expected=set(map(str,ids['pbg_ids']));pool=set(map(str,ids['list_item_ids']))
  for rel in self.report['new_instances']:
   r=E.parse(self.source/rel).getroot();self.assertIn(r.find('uniqueid').get('value'),expected)
   for n in r.iter():
    if n.get('List.ItemID'):self.assertIn(n.get('List.ItemID'),pool)
 def test_reference_mod_is_untouched(self):
  import hashlib
  for path,h in self.report['reference_project_hashes'].items():self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),h)
 def test_no_human_gameplay_records_in_patch(self):
  self.assertTrue(all(str(p.relative_to(self.source)).startswith('ai') for p in self.source.rglob('*.xml')))
 def test_original_native_entries_preserved(self):
  r=E.parse(self.source/'ai/ai_economy/complete/default_economy.xml').getroot()
  old=E.parse(HERE/'official/instances/ai/ai_economy/complete/default_economy.xml').getroot()
  # Existing list members retain values/IDs; additions cannot rewrite another civ.
  def entries(root):
   return {(i,n.get('List.ItemID'),n.get('name')):n.get('value') for i,v in enumerate([root,*root.findall('variant')]) for n in v.iter('instance_reference') if n.get('List.ItemID')}
  before=entries(old);after=entries(r)
  for key,value in before.items():self.assertEqual(after[key],value)

 def test_role_specific_production(self):
  expected={
   'unit_villager_1_mal':'Gatherer','unit_trade_cart_mal':'Trader',
   'unit_scout_1_mal':'Scouting','unit_scout_2_mal':'Scouting',
   'unit_handcannon_4_mal':'RangedInfantry',
   'unit_naval_combat_ship_2_abb':'NavalMilitary',
   'unit_naval_combat_warship_4_abb':'WarShip',
   'unit_ram_3_mal':'Siege','unit_siege_tower_3_mal':'SiegeTower',
   'unit_trebuchet_4_tr_mal':'Siege',
   'upgrade_econ_resource_stone_harvest_rate_2':'PlayerEconGatheringUpgrade',
  }
  r=E.parse(self.source/'ai/ai_economy/complete/default_economy.xml').getroot()
  for variant in [r,*r.findall('variant')]:
   groups=variant.find("group/list[@name='production_groups']")
   for name,binding in expected.items():
    refs=[(g.find("string[@name='lua_binding']").get('value'),n.get('value')) for g in groups for n in g.iter('instance_reference') if n.get('value').endswith('\\'+name)]
    self.assertTrue(refs,(name,'unmapped'))
    if name.startswith('upgrade_econ_resource_stone_'):
     self.assertTrue({b for b,p in refs}<={'ScoringFunctions_PlayerEconGatheringUpgrade','ScoringFunctions_PlayerEconUpgrade'},name)
    else:self.assertEqual({b for b,p in refs},{'ScoringFunctions_'+binding},name)
    if name in ('unit_ram_3_mal','unit_siege_tower_3_mal'):
     self.assertTrue(all(p.startswith('ebps\\') for b,p in refs),name)

 def test_relocated_landmarks_have_native_production(self):
  r=E.parse(self.source/'ai/ai_economy/complete/default_economy.xml').getroot()
  for variant in [r,*r.findall('variant')]:
   refs={n.get('value') for n in variant.find("group/list[@name='production_groups']").iter('instance_reference')}
   for p in (HERE.parents[2]/'assets/attrib/instances/ebps').rglob('*.xml'):
    if p.stem.startswith('building_landmark_') or p.stem=='building_wonder_age4_great_mosque_control_mal':
     self.assertTrue(str(p.relative_to(HERE.parents[2]/'assets/attrib/instances')).replace('/','\\')[:-4] in refs,p.stem)

 def test_all_exposed_training_and_research_in_every_variant(self):
  import zipfile
  exposed=set()
  with zipfile.ZipFile(HERE/'cook-reference-inputs.zip') as z:
   for name in z.namelist():
    if not name.startswith('assets/attrib/instances/') or not name.endswith('.xml'):continue
    for ext in E.fromstring(z.read(name)).iter('template_reference'):
     if ext.get('value','').rsplit('\\',1)[-1] in ('spawner_ext','upgrade_ext'):
      exposed.update(n.get('value').rsplit('\\',1)[-1] for n in ext.iter('instance_reference') if n.get('value','').startswith(('sbps\\','upgrade\\')))
  r=E.parse(self.source/'ai/ai_economy/complete/default_economy.xml').getroot()
  for v in [r,*r.findall('variant')]:
   refs={n.get('value').rsplit('\\',1)[-1] for n in v.find('group').iter('instance_reference')}
   self.assertFalse(exposed-refs,(v.get('name','default'),sorted(exposed-refs)))

if __name__=='__main__':unittest.main(verbosity=2)
