"""Regression against the actual user-tested 0.1.1 native Codex, not a mock."""
import sys,unittest,gzip,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from runtime import read_json,import_table,rgd,at,child,refs
from codex import build,validate_native_layout
class Update012(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cfg=read_json(ROOT/'project.json');cls.review=read_json(ROOT/'source/codex-review.json')
  cls.tables={p.relative_to(ROOT/'source/tables').as_posix()[:-5]:rgd.read(import_table(read_json(p))) for p in (ROOT/'source/tables').rglob('*.rgd.json')}
  cls.new,cls.report=build(cls.tables,cls.cfg);cls.old=rgd.read((ROOT/'tests/fixtures/codex-before-012.rgd').read_bytes())
 def test_actual_old_empty_or_donor_overview_replaced(self):
  old=at(self.old,'default/codex_bag');new=at(self.new,'default/codex_bag');owner=self.cfg['owner'].replace('-','')+':'
  if self.cfg['race']!='berbers':self.assertEqual(len(child(old,'unique_units').value),0);self.assertEqual(len(child(old,'unique_techs').value),0)
  else:self.assertTrue(any(not n.startswith(owner) for _,f,n,_ in refs(child(old,'unique_techs').value)))
  for field,key in (('unique_units','unique_units'),('unique_techs','unique_techs')):
   self.assertEqual([child(n,'$PBGNAME').value for n in child(new,field).value],[owner+n for n in self.review[key]])
 def test_blacksmith_three_real_research_ages_and_no_overlap(self):
  validate_native_layout(self.new);self.assertFalse(self.report['missing_stock_evidence'])
  group=next(g for g in self.report['groups'] if 'tech_unit_infantry' in g['producer']);ages={n:a for f,n,a in group['items']}
  for base in ('upgrade_melee_damage','upgrade_melee_armor','upgrade_ranged_damage','upgrade_ranged_armor'):
   for suffix,age in (('i',2),('ii',3),('iii',4)):self.assertEqual(ages[base+'_'+suffix],age)
  for group in self.report['groups']:
   if len(group['positions'])>1:self.assertLess(group['positions'][0][1],min(y for x,y in group['positions'][1:]))
  self.assertTrue(any(child(child(i,'pbg'),'$PBGNAME').value=='upgrade_melee_damage_i' and child(i,'y_position').value<3 for g in at(self.old,'default/codex_bag/tech_tree').value for i in child(g,'items').value))
 def test_both_native_views_agree_and_real_tier_links_exist(self):
  for variant in ('default','campaign'):
   bag=at(self.new,variant+'/codex_bag');flat={child(child(i,'pbg'),'$PBGNAME').value for g in child(bag,'tech_tree').value for i in child(g,'items').value};legacy={n for p,f,n,_ in refs(child(bag,'root_item').value) if n}
   self.assertEqual(flat,legacy)
   self.assertGreater(sum(bool(child(child(i,'upgrade_pbg'),'$PBGNAME').value) for g in child(bag,'tech_tree').value for i in child(g,'items').value),3)
 def test_only_requested_army_ui_and_race_small_icon_changed(self):
  for family in ('army','racebps'):
   for p in (ROOT/'source/tables/attrib'/family).rglob('*.json'):
    old=rgd.read(import_table(read_json(ROOT/'docs/update_012/before'/p.relative_to(ROOT))));new=rgd.read(import_table(read_json(p)))
    def protected(d):
     return {path:(n.kind,n.value) for path,n in rgd.flatten(d.nodes) if not isinstance(n.value,list) and not (family=='army' and '/army_bag/ui/' in path) and not (family=='racebps' and path.endswith('/icon_small'))}
    self.assertEqual(protected(old),protected(new))
    if family=='racebps':
     for path,n in rgd.flatten(new.nodes):
      if path.endswith('/icon_small'):self.assertEqual(n.value,'')
    else:
     for variant in ('default','campaign'):
      traits=at(new,variant+'/army_bag/ui/global_traits_summary').value
      self.assertGreaterEqual(len(traits),7)
      for trait in traits[1:]:self.assertFalse(child(trait,'icon').value.startswith('garrison\\'))
 def test_native_world_media_unchanged_and_audio_paths_only(self):
  old=read_json(ROOT/'docs/update_012/before/inputs/native-manifest.json');new=read_json(ROOT/'inputs/native-manifest.json')
  for m,row in old.items():
   if not m.startswith('audio/'):self.assertEqual(row,new[m])
  if self.cfg['race']!='berbers':self.assertEqual(old,new);return
  recipe=read_json(ROOT/'source/audio-012-recipe.json')['files'];replacements={r['original']:n for n,r in recipe.items()}
  for p in (ROOT/'docs/update_012/before/source/scar').rglob('*.scar'):
   expected=p.read_text(encoding='utf-8')
   for a,b in replacements.items():expected=expected.replace(a,b)
   self.assertEqual(expected,(ROOT/'source/scar'/p.relative_to(ROOT/'docs/update_012/before/source/scar')).read_text(encoding='utf-8'))
  self.assertTrue(all(abs(r['full_decode_frames']-r['frames'])<=2048 for r in recipe.values()))
if __name__=='__main__':unittest.main()
