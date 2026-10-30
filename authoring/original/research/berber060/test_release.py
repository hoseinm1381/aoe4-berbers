"""Composition isolation and atomic publication, using tiny offline fixtures."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import release as r
from common import sha,write,read

class ComposeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name);self.art=self.out/'art';self.art.mkdir()
        self.base=self.out/'base.sga';self.base.write_bytes(b'base')
        self.canonical=self.out/'candidate.sga';self.canonical.write_bytes(b'old candidate')
        self.work=self.out/'integration';self.work.mkdir()
        self.old=self.work/'attrib-candidate.sga';self.old.write_bytes(b'old intermediate')
        profile=self.out/'profiles/manifest.json';write(profile,{})
        payload=self.out/'binding';payload.write_bytes(b'binding')
        scar=self.out/'metadata';scar.write_bytes(b'metadata')
        self.payload={'member':'attrib/a','file':str(payload),'sha256':sha(payload)}
        self.metadata={'member':'scar/a','file':str(scar),'sha256':sha(scar)}
        write(self.out/'bindings/payload-manifest.json',{'status':'passed','base_sha256':sha(self.base),'profile_manifest_sha256':sha(profile),'payloads':[self.payload]})
        write(self.art/'recording-plan.json',{})
        self.baseline={'art/a':'unchanged','attrib/a':'old'}
        self.final={**self.baseline,'attrib/a':sha(payload),'scar/a':sha(scar)}
        self.outputs=[];self.fail_tool=False;self.bad_map=False
        for name,value in [('OUT',self.out),('ART',self.art),('BASE',self.base),('BASE_SHA',sha(self.base))]:
            p=patch.object(r,name,value);p.start();self.addCleanup(p.stop)
        for target,kwargs in [('prior_readbacks.capture_existing',{'return_value':None}),('release.metadata_payload',{'return_value':self.metadata}),('release.run',{'side_effect':self.tool}),('release.member_hashes',{'side_effect':self.members})]:
            p=patch(target,**kwargs);p.start();self.addCleanup(p.stop)
    def tool(self,*args):
        if args[1]=='list':return json.dumps({'archive':{'verification':{'verified':True}}})
        target=Path(args[4]);self.assertFalse(target.exists(),'archiver refuses overwrite')
        self.outputs.append(target)
        if self.fail_tool and args[-1]=='data':raise RuntimeError('tool refusal')
        target.write_bytes(('fresh '+str(len(self.outputs))).encode())
    def members(self,archive,folder):
        if archive==self.base:return {},self.baseline
        return {},{**self.final,**({'unexpected':'hash'} if self.bad_map else {})}
    def test_fresh_outputs_repeat_success_without_overwriting_old_intermediate(self):
        first=r.compose();second=r.compose()
        self.assertEqual(len(set(self.outputs)),4)
        self.assertEqual(self.old.read_bytes(),b'old intermediate')
        self.assertFalse(self.outputs[0].exists());self.assertFalse(self.outputs[2].exists())
        self.assertEqual(second['archive'],str(self.canonical));self.assertEqual(second['archive_sha256'],sha(self.canonical))
        self.assertEqual(read(self.out/'composition-report.json'),second)
    def test_tool_refusal_preserves_canonical_and_failed_intermediate(self):
        self.fail_tool=True
        with self.assertRaisesRegex(RuntimeError,'tool refusal'):r.compose()
        self.assertEqual(self.canonical.read_bytes(),b'old candidate');self.assertTrue(self.outputs[0].exists())
        self.assertFalse((self.out/'composition-report.json').exists())
    def test_invalid_final_member_map_preserves_canonical_and_evidence(self):
        self.bad_map=True
        with self.assertRaisesRegex(ValueError,'member set'):r.compose()
        self.assertEqual(self.canonical.read_bytes(),b'old candidate')
        self.assertTrue(all(p.exists() for p in self.outputs))
    def test_promotion_refusal_preserves_canonical_and_fresh_final(self):
        original=Path.replace
        def deny(path,target):
            if Path(target)==self.canonical:raise PermissionError('busy')
            return original(path,target)
        with patch.object(Path,'replace',deny),patch.object(r.time,'sleep'):
            with self.assertRaises(PermissionError):r.compose()
        self.assertEqual(self.canonical.read_bytes(),b'old candidate')
        self.assertTrue(all(p.exists() for p in self.outputs))

if __name__=='__main__':unittest.main()
