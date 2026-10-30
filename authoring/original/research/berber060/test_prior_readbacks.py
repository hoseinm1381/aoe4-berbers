"""Tiny, isolated fixtures; never capture or clean the actual release."""
import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import prior_readbacks as p
from common import read,write,sha

def digest(raw):return hashlib.sha256(raw).hexdigest()

class PriorReadbackTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'release';self.root.mkdir()
        self.base=Path(self.temp.name)/'base.sga';self.base.write_bytes(b'protected base')
        self.tool=Path(self.temp.name)/'archiver.exe';self.tool.write_bytes(b'fixed tool')
        for name,value in [('BASE',self.base),('BASE_SHA',sha(self.base)),('ARCH',self.tool)]:
            setting=patch.object(p,name,value);setting.start();self.addCleanup(setting.stop)
        self.archive=self.root/'candidate.sga';self.archive.write_bytes(b'old composed archive')
        self.archive_sha=sha(self.archive)
        self.back=self.root/'integration'/('candidate-readback-'+self.archive_sha[:12]);self.back.mkdir(parents=True)
        original={'art/base.bin':b'old art','attrib/base.rgd':b'base attrib'}
        self.baseline={name:digest(raw) for name,raw in original.items()}
        self.payloads=[]
        for i in range(84):
            member=f'attrib/ebps/a{i:02}.rgd';source=self.root/'bindings'/f'a{i:02}.rgd';source.parent.mkdir(exist_ok=True)
            raw=f'binding{i}'.encode();source.write_bytes(raw);original[member]=raw
            self.payloads.append({'member':member,'file':str(source),'sha256':sha(source)})
        self.scar=self.root/'art/old-scar.scar';self.scar.parent.mkdir();self.scar.write_bytes(b'old voice count snapshot')
        self.payloads.append({'member':p.SCAR,'file':str(self.scar),'sha256':sha(self.scar)})
        original[p.SCAR]=self.scar.read_bytes()
        for name,raw in original.items():
            path=self.back/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        write(self.root/'baseline-member-sha256.json',self.baseline)
        self.report={'status':'passed','base_sha256':sha(self.base),'archive':str(self.archive),'archive_sha256':self.archive_sha,
            'payloads':self.payloads,'changed_members':[x['member'] for x in self.payloads]}
        write(self.root/'composition-report.json',self.report)
        self.folder=self.root/'prior-compositions'/self.archive_sha
        self.base_back=self.root/'integration/base-readback'
        for name,raw in {'art/base.bin':b'old art','attrib/base.rgd':b'base attrib'}.items():
            path=self.base_back/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        def inventory(tool,command,archive,verify):
            self.assertEqual((tool,command,verify),(self.tool,'list','--verify'))
            names=set(self.baseline) if archive==self.base else set(self.baseline)|{r['member'] for r in self.payloads}
            return json.dumps({'archive':{'verification':{'verified':True}},'members':[{'path':name} for name in sorted(names)]})
        setting=patch.object(p,'run',side_effect=inventory);setting.start();self.addCleanup(setting.stop)

    def capture(self):return p.capture_existing(self.root)
    def admitted(self):return p.validated_prior_readbacks(self.root,'f'*64)

    def test_compact_capture_saves_exact_old_metadata_and_full_member_map(self):
        result=self.capture()
        self.assertEqual(result['archive_sha256'],self.archive_sha)
        self.assertEqual(len(list(self.folder.iterdir())),10)
        self.assertEqual((self.folder/'old-tuareg_voice_profile.scar').read_bytes(),self.scar.read_bytes())
        self.assertEqual(read(self.folder/'member-sha256.json'),{**self.baseline,**{x['member']:x['sha256'] for x in self.payloads}})
        self.assertEqual(self.admitted()[0]['target'],self.back)
        self.assertTrue(self.archive.exists());self.assertTrue(self.back.exists())

    def test_unpack_nonmembers_are_losslessly_preserved_separately_from_native_map(self):
        extra=self.back/'attrib/helper.xml';extra.write_bytes(b'unpacked candidate helper')
        base_extra=self.base_back/'project.aoe4mod';base_extra.write_bytes(b'unpacked base helper')
        proof=self.capture()
        self.assertEqual((proof['preserved_nonmember_files'],proof['preserved_base_nonmember_files']),(1,1))
        self.assertNotIn('attrib/helper.xml',read(self.folder/'member-sha256.json'))
        self.assertIn('attrib/helper.xml',read(self.folder/'readback-file-sha256.json'))
        with zipfile.ZipFile(self.folder/'unpack-sidecar-evidence.zip') as archive:
            self.assertEqual(archive.read('attrib/helper.xml'),extra.read_bytes())
        with zipfile.ZipFile(self.folder/'base-unpack-sidecar-evidence.zip') as archive:
            self.assertEqual(archive.read('project.aoe4mod'),base_extra.read_bytes())
        self.assertEqual(p.validated_base_readback(self.root)['target'],self.base_back)
        base_extra.write_bytes(b'modified after capture')
        with self.assertRaisesRegex(ValueError,'Base unpack differs'):p.validated_base_readback(self.root)

    def test_unverified_or_wrong_archive_inventory_never_admitted(self):
        with patch.object(p,'run',return_value=json.dumps({'archive':{'verification':{'verified':False}},'members':[]})):
            with self.assertRaisesRegex(ValueError,'verification'):self.capture()
        with patch.object(p,'run',return_value=json.dumps({'archive':{'verification':{'verified':True}},'members':[{'path':'unrelated'}]})):
            with self.assertRaisesRegex(ValueError,'inventory differs'):self.capture()
        self.assertFalse(self.folder.exists())

    def test_saved_proof_survives_original_scar_and_old_archive_supersession(self):
        proof=self.capture();self.scar.write_bytes(b'new voice snapshot');self.archive.write_bytes(b'new archive')
        self.assertEqual(self.capture(),proof)
        self.assertEqual(self.admitted()[0]['target'],self.back)

    def test_missing_archive_or_changed_input_blocks_initial_capture(self):
        self.archive.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'archive changed'):self.capture()
        self.assertFalse(self.folder.exists())
        self.archive.write_bytes(b'old composed archive');self.scar.write_bytes(b'changed input')
        with self.assertRaisesRegex(ValueError,'payload changed'):self.capture()
        self.assertFalse(self.folder.exists())

    def test_extra_missing_or_modified_readback_is_never_admitted(self):
        self.capture();path=self.back/'art/base.bin';raw=path.read_bytes()
        path.write_bytes(b'modified')
        with self.assertRaisesRegex(ValueError,'extra, missing, or modified'):self.admitted()
        path.write_bytes(raw);path.unlink()
        with self.assertRaisesRegex(ValueError,'extra, missing, or modified'):self.admitted()
        path.write_bytes(raw);extra=self.back/'extra.bin';extra.write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError,'extra, missing, or modified'):self.admitted()

    def test_changed_retained_binding_base_tool_or_snapshot_blocks_admission(self):
        self.capture()
        for path in (Path(self.payloads[0]['file']),self.base,self.tool,self.folder/'old-tuareg_voice_profile.scar'):
            raw=path.read_bytes();path.write_bytes(b'changed')
            with self.assertRaises(ValueError):self.admitted()
            path.write_bytes(raw)

    def test_unproved_or_current_readbacks_are_not_selected(self):
        self.assertEqual(self.admitted(),[])
        self.capture()
        self.assertEqual(p.validated_prior_readbacks(self.root,self.archive_sha),[])

    def test_reparse_and_namespace_spoof_fail_closed(self):
        self.capture();original=Path.is_junction
        def junction(path):return path==self.back or original(path)
        with patch.object(Path,'is_junction',junction):
            with self.assertRaisesRegex(ValueError,'reparse'):self.admitted()
        proof=read(self.folder/'proof.json');proof['readback']=str(self.root/'integration/candidate-readback-unproved');write(self.folder/'proof.json',proof)
        with self.assertRaisesRegex(ValueError,'namespace'):self.admitted()

    def test_compose_calls_capture_before_any_metadata_generation(self):
        import release
        class StopCapture(Exception):pass
        with patch.object(release,'BASE',self.base),patch.object(release,'BASE_SHA',sha(self.base)),\
             patch.object(p,'capture_existing',side_effect=StopCapture),\
             patch.object(release,'metadata_payload',side_effect=AssertionError('Metadata must not run before capture')) as metadata:
            with self.assertRaises(StopCapture):release.compose()
            metadata.assert_not_called()

if __name__=='__main__':unittest.main()
