"""Real stock fixtures pin per-material isolation and team-colour preservation."""
import unittest,json,sys,os
from pathlib import Path
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT))
from garrison_shared import relic_chunky as rc,model_variants as mv
from native_materials import rewrite_scoped
ROOT=Path(__file__).resolve().parents[2]
class ScopedMaterialTest(unittest.TestCase):
    def setUp(self):
        d=json.loads((ROOT/'output/berber_update_0_2_2/stock/a9a752db305fef70848f/decoded-static.json').read_text())
        self.raw=Path(d['material']['source']['path']).read_bytes()
    def roots(self,raw):return {c.decoded_name:rc.pack_document([rc.pack_chunk(c.kind,c.tag,c.payload,version=c.version,name=c.name)]) for c in rc.parse(raw).roots}
    def test_noop_is_byte_identical(self):self.assertEqual(rewrite_scoped(self.raw,{}),self.raw)
    def test_main_change_does_not_repaint_extra_material(self):
        target='art/scenario/garrison/berber_house_022/test_earth.rrtex'
        out=rewrite_scoped(self.raw,{'main':{'textures':{'albedoTex2':target},'parameters':{}}})
        before=self.roots(self.raw);after=self.roots(out)
        self.assertEqual(before['extra'],after['extra'])
        self.assertEqual(before['extra_collection'],after['extra_collection'])
        self.assertNotEqual(before['main'],after['main'])
        for name in ['main','main_collection']:
            slots=mv.material_slots(after[name]);self.assertEqual(slots['textures']['albedoTex2'].replace('\\','/'),target)
            original=mv.material_slots(before[name])
            self.assertEqual(slots['textures']['albedoTex5'],original['textures']['albedoTex5'])
            for k,v in original['parameters'].items():
                if k.endswith('5'):self.assertEqual(slots['parameters'][k],v)
    def test_unknown_material_refused(self):
        with self.assertRaises(ValueError):rewrite_scoped(self.raw,{'missing':{'textures':{},'parameters':{}}})
    def test_tonal_parameters_are_changed_in_binary_and_text_blocks(self):
        values=['0.84','0.84','0.84','1']
        out=rewrite_scoped(self.raw,{'main':{'textures':{},'parameters':{'midtoneColor2':values}}})
        for name in ['main','main_collection']:
            slots=mv.material_slots(self.roots(out)[name])
            self.assertEqual([float(v) for v in slots['parameters']['midtoneColor2']['values']],[.84,.84,.84,1])
        self.assertEqual(self.roots(out)['extra'],self.roots(self.raw)['extra'])
    def test_recipe_has_cross_block_tonal_edits_without_team_edits(self):
        recipe=json.loads((Path(__file__).parent/'recipe.json').read_text())
        for age in recipe['ages']:
            d=json.loads(Path(age['decode']).read_text())
            for mat in age['materials']:
                stock=next(m for m in d['material']['materials'] if m['name']==mat['name'])
                names={p['name'] for b in stock['blocks'] for p in b.get('parameters',[])}
                expected={f'{label}Color'+('1' if edit['slot']=='albedoTex' else edit['slot'].removeprefix('albedoTex')) for edit in mat['textures'] for label in ['highlight','midtone','shadow']}&names
                self.assertEqual(set(mat['parameters']),expected)
                for slot in mat['team_slots_preserved']:
                    layer='1' if slot=='albedoTex' else slot.removeprefix('albedoTex')
                    self.assertTrue(all(f'{label}Color{layer}' not in mat['parameters'] for label in ['highlight','midtone','shadow']))
if __name__=='__main__':unittest.main()
