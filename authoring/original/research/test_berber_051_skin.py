import tempfile
import unittest
from pathlib import Path
from PIL import Image
from berber_050_common import sha
from berber_051_skin import OUT,extract,replace_skin_lut,rename_texture,verify_png
from berber_050_materials import rc,texture_pairs
from garrison_shared import rrtex_decoder


class SkinOnlyRevision(unittest.TestCase):
    def test_native_material_changes_only_skin_slot_and_exact_inverse(self):
        candidates=list((OUT/'baseline-inputs/materials').glob('*trader_age02*.rrmaterial'))
        if not candidates:
            candidates=[extract('art/scenario/garrison/berber_units_050/trader_age02/trader_age02.rrmaterial',OUT/'baseline-inputs/materials/test-trader_age02.rrmaterial')]
        source=candidates[0].read_bytes()
        result,proof=replace_skin_lut(source)
        self.assertNotEqual(result,source)
        self.assertTrue(proof['exact_native_roundtrip'])
        a=[p for c in rc.walk(rc.parse(source).roots) if c.tag==b'PbTe' for p in texture_pairs(c.payload) if p[0]!='skinTintLUT']
        b=[p for c in rc.walk(rc.parse(result).roots) if c.tag==b'PbTe' for p in texture_pairs(c.payload) if p[0]!='skinTintLUT']
        self.assertEqual(a,b)

    def test_native_texture_identity_retains_all_mips_and_stream(self):
        source=OUT/'baseline-inputs/albedo.rrtex'
        if not source.exists():extract('art/scenario/garrison/tuareg_refined_art/units/tuareg_age1/body/albedo.rrtex',source)
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'renamed.rrtex';target.write_bytes(rename_texture(source.read_bytes(),'art/scenario/garrison/berber_skin_051/test.rrtex'))
            old=rrtex_decoder.decode_rrtex(source,validate_stream=True);new=rrtex_decoder.decode_rrtex(target,validate_stream=True)
            self.assertEqual(old['mips'],new['mips']);self.assertEqual(old['projection']['sha256'],new['projection']['sha256'])

    def test_rejects_outside_skin_and_owner_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            source=Image.new('RGBA',(2,2),(100,70,50,255));source.save(folder/'source.png')
            edited=source.copy();edited.putpixel((0,0),(220,180,160,255));edited.save(folder/'edited.png')
            mask=Image.new('L',(2,2),0);mask.save(folder/'mask.png')
            owner=Image.new('RGB',(2,2),(0,0,0));owner.save(folder/'owner.png')
            def row():
                return {'source_png':str(folder/'source.png'),'source_png_sha256':sha(folder/'source.png'),
                    'authored_png':str(folder/'edited.png'),'sha256':sha(folder/'edited.png'),
                    'mask_png':str(folder/'mask.png'),'mask_sha256':sha(folder/'mask.png'),
                    'source_owner_pattern':str(folder/'owner.png'),'source_owner_pattern_sha256':sha(folder/'owner.png'),'changed_pixels':1}
            with self.assertRaises(ValueError):verify_png(row())
            mask.putpixel((0,0),255);mask.save(folder/'mask.png')
            self.assertEqual(verify_png(row())['changed_pixels'],1)
            owner.putpixel((0,0),(255,0,0));owner.save(folder/'owner.png')
            with self.assertRaises(ValueError):verify_png(row())


if __name__=='__main__':unittest.main()
