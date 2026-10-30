"""Focused complete-stamp contract regression using the actual Keep stamp."""
import unittest
import tempfile,json,sys
from unittest.mock import patch
import xml.etree.ElementTree as ET
from pathlib import Path
from berber_040_integrate import prune_visuals,NativeTree,OUT,read,active_visuals

class ReleaseAdmission(unittest.TestCase):
    def test_040_single_authored_lod_keeps_actual_fresh_geometry_exact(self):
        from berber_040_integrate_models import single_lod0_geometry,PROJECT
        cook=read(OUT/'art-cook.json')
        path=Path(cook['readback'])/f'art/scenario/garrison/{PROJECT.name}/buildings/koutoubia_lod0/model.rrgeom'
        raw=path.read_bytes();output,report=single_lod0_geometry([raw]*3)
        self.assertEqual(output,raw);self.assertEqual(report['native_lod_count'],1)
        self.assertFalse(report['authored_lods_three']);self.assertEqual(len(report['source_levels']),1)
        with self.assertRaises(AssertionError):single_lod0_geometry([raw,raw,raw+b'x'])

    def test_native_non_utf8_failure_retains_error_message(self):
        from berber_040_integrate import run
        with self.assertRaisesRegex(RuntimeError,'native-failure'):
            run(sys.executable,'-c',"import sys;sys.stderr.buffer.write(bytes([183])+b'native-failure');sys.exit(1)")

    def test_non_power_of_two_maps_rejected_before_native_cook(self):
        from PIL import Image
        from berber_040_integrate_models import validate_texture_dimensions
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'albedo.png';Image.new('RGB',(2560,1024)).save(path)
            with self.assertRaises(AssertionError):validate_texture_dimensions(directory)
            Image.new('RGB',(2048,1024)).save(path);validate_texture_dimensions(directory)

    def test_repairs_only_composition_cannot_admit_four_passed_bindings(self):
        from berber_040_integrate_release import admit_payloads
        bindings=[{'status':'passed','payloads':[{'member':kind+'.rgd','sha256':kind}]} for kind in ('university','koutoubia','fez','grand_keep')]
        with self.assertRaises(AssertionError):admit_payloads({'payloads':[]},bindings)
        report={'payloads':[dict(row) for binding in bindings for row in binding['payloads']]}
        self.assertEqual(len(admit_payloads(report,bindings)),4)
        report['payloads'][0]['sha256']='stale'
        with self.assertRaises(AssertionError):admit_payloads(report,bindings)

    def test_authoritative_imperial_export_and_hash_required(self):
        import berber_040_integrate_models as models
        for kind in ('fez','grand_keep'):
            self.assertEqual(models.static_source(kind).name,'export_lod0_v2')
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);source=base/'fez/export_lod0_v2';source.mkdir(parents=True)
            (source/'building.json').write_text('{}')
            record={'source':str(base/'fez/export_lod0'),'source_files_sha256':{'building.json':models.sha(source/'building.json')}}
            with patch.object(models,'ART',base),patch.object(models,'read',return_value=record):
                with self.assertRaises(AssertionError):models.verify_prepared_source('fez')
                record['source']=str(source)
                self.assertEqual(models.verify_prepared_source('fez'),source)
                (source/'building.json').write_text('{"changed":true}')
                with self.assertRaises(AssertionError):models.verify_prepared_source('fez')

class StampContract(unittest.TestCase):
    def test_only_explicit_visuals_retained_functional_objects_preserved(self):
        raw=b'<DataWarehouse><DataObject Id="1" Type="StampBlueprint"><DataProperty Name="m_blueprints" Type="Object"><DataValue Name="VisualStampBlueprint">2</DataValue><DataObject Id="2" Type="VisualStampBlueprint"><DataProperty Name="m_blueprint" Value="core"/></DataObject><DataValue Name="VisualStampBlueprint">3</DataValue><DataObject Id="3" Type="VisualStampBlueprint"><DataProperty Name="m_blueprint" Value="overlay"/></DataObject><DataValue Name="MarkerStampBlueprint">4</DataValue><DataObject Id="4" Type="MarkerStampBlueprint"/></DataProperty></DataObject></DataWarehouse>'
        output,report=prune_visuals(raw,{2})
        self.assertEqual({n.get('Id') for n in ET.fromstring(output).iter('DataObject')},{'1','2','4'})
        self.assertEqual(report['removed_visual_ids'],['3'])
        self.assertEqual(report['preserved_nonvisual_ids'],['1','4'])

    def test_actual_qualified_native_keep_has_single_reachable_principal(self):
        report=read(OUT/'qualification/source-contract.json')
        before=NativeTree(report['stock']);after=NativeTree(report['pruned_native'])
        self.assertEqual(len(active_visuals(after)),1)
        self.assertEqual(active_visuals(after)[0]['id'],report['principal_id'])
        self.assertEqual(before.objects.keys(),after.objects.keys())
        for oid,obj in before.objects.items():
            if obj['type']=='StampBlueprint':continue
            size=int(before.types[obj['type_id']].get('Size'))
            self.assertEqual(before.bytes(obj['offset'],size),after.bytes(after.objects[oid]['offset'],size))

if __name__=='__main__':unittest.main()
