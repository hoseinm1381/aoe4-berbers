"""Real old Codex fixture and scoped native start/presentation regression."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from runtime import read_json,import_table,rgd,at,child
from codex import build,validate_native_layout
class Update011(unittest.TestCase):
 def test_old_actual_codex_and_new_layout(self):
  cfg=read_json(ROOT/'project.json');old=rgd.read((ROOT/'tests/fixtures/codex-before-011.rgd').read_bytes())
  with self.assertRaises(ValueError):validate_native_layout(old)
  tables={p.relative_to(ROOT/'source/tables').as_posix()[:-5]:rgd.read(import_table(read_json(p))) for p in (ROOT/'source/tables').rglob('*.rgd.json')}
  new,report=build(tables,cfg);validate_native_layout(new);self.assertTrue(report['native_bounds_verified'])
  # 0.1.2 explicitly replaces these Codex UI sections; preserve every other native field.
  reviewed=('tech_tree','root_item','unique_units','unique_techs','special_items','landmark_count')
  def unchanged(doc):return [(path,n.kind,n.value) for path,n in rgd.flatten(doc.nodes) if not isinstance(n.value,list) and not any('/codex_bag/'+key in path for key in reviewed)]
  self.assertEqual(unchanged(old),unchanged(new))
 def test_only_worker_scout_positions_and_loading_reference_changed_in_army(self):
  p=next((ROOT/'source/tables/attrib/army').rglob('*.json'))
  old=rgd.read(import_table(read_json(ROOT/'docs/update_011/before'/p.relative_to(ROOT))))
  new=rgd.read(import_table(read_json(p)));a=dict(rgd.flatten(old.nodes));b=dict(rgd.flatten(new.nodes));self.assertEqual({p for p in a if '/army_bag/ui/' not in p},{p for p in b if '/army_bag/ui/' not in p})
  for path,n in b.items():
   if isinstance(n.value,list) or '/army_bag/ui/' in path:continue
   if '/starting_units_spawner/spawn_positions/' in path and n.key in ('x','y'):continue
   if path.endswith('/ui/background_image'):continue
   self.assertEqual((a[path].kind,a[path].value),(n.kind,n.value),path)
  expected=[(-2.200000047683716,0),(-3.299999952316284,-2),(-1,-2),(-2,-4),(0,-4),(-1,-6)]
  for variant in ('default','campaign'):
   bag=at(new,variant+'/army_bag');units=child(bag,'starting_units').value;positions=child(child(bag,'starting_units_spawner'),'spawn_positions').value;workers=[]
   oldpos=child(child(at(old,variant+'/army_bag'),'starting_units_spawner'),'spawn_positions').value
   for i,(unit,pos) in enumerate(zip(units,positions)):
    name=child(unit,'$PBGNAME').value;xy=tuple(child(pos,k).value for k in ('x','y'))
    if 'villager' in name:workers.append(xy)
    elif 'scout' in name:self.assertEqual(xy,(-4,10))
    else:self.assertEqual(xy,tuple(child(oldpos[i],k).value for k in ('x','y')))
   self.assertEqual(workers,expected)
 def test_client_card_and_full_hd_loading(self):
  import struct
  card=read_json(ROOT/'source/client-card.json');self.assertIn(card['civilization']['difficulty'],(1,2,3));self.assertGreater(len(card['description']),150);self.assertGreater(len(card['civilization']['bonuses']),2)
  self.assertLessEqual((ROOT/'source/presentation/cover.png').stat().st_size,4*1024*1024)
  data=(ROOT/'source/presentation/derived_011/flag_loading.png').read_bytes();self.assertEqual(struct.unpack('>II',data[16:24]),(1920,1080))
if __name__=='__main__':unittest.main()
