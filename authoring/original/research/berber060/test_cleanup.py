"""Cleanup safety tests operate only in temporary fixtures."""
import hashlib,tempfile,unittest,zipfile
from pathlib import Path
import cleanup
from unittest.mock import patch
from types import SimpleNamespace
from common import write,sha

class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.sga=self.root/'candidate.sga';self.sga.write_bytes(b'current archive')
        reports={}
        for label,name,members in [('garrison','main.zip',{'Berber_future_kingdom.sga':b'current archive','garrison.json':b'{}'}),('native_audio','audio.zip',{'native-audio-manifest.json':b'{}','payloads/test.wem':b'wem'})]:
            for required in (cleanup.MAIN_REQUIRED if label=='garrison' else cleanup.AUDIO_REQUIRED):members.setdefault(required,b'review documentation')
            zpath=self.root/name
            with zipfile.ZipFile(zpath,'w') as z:
                for k,v in members.items():z.writestr(k,v)
            reports[label]={'zip':str(zpath),'sha256':sha(zpath),'bytes':zpath.stat().st_size,'members':{k:hashlib.sha256(v).hexdigest() for k,v in members.items()}}
        reports.update(status='passed',sga_sha256=sha(self.sga))
        write(self.root/'release-validation.json',reports)
        write(self.root/'composition-report.json',{'status':'passed','archive':str(self.sga),'archive_sha256':sha(self.sga)})
    def test_verified_zip_and_current_sga(self):self.assertEqual(cleanup.verify_delivery(self.root)['sga_sha256'],sha(self.sga))
    def test_modified_zip_or_current_sga_blocks_cleanup(self):
        self.sga.write_bytes(b'changed')
        with self.assertRaises(ValueError):cleanup.verify_delivery(self.root)
    def test_member_hash_claim_is_checked(self):
        import json
        report=json.loads((self.root/'release-validation.json').read_text());report['native_audio']['members']['payloads/test.wem']='0'*64
        write(self.root/'release-validation.json',report)
        with self.assertRaises(ValueError):cleanup.verify_delivery(self.root)
    def test_containment_and_reparse_refused(self):
        with self.assertRaises(ValueError):cleanup.safe(self.root,self.root.parent/'outside')
        link=self.root/'link'
        try:link.symlink_to(self.root/'candidate.sga')
        except OSError:self.skipTest('Symlink privilege unavailable')
        with self.assertRaises(ValueError):cleanup.safe(self.root,link)
    def test_junction_is_refused_even_with_no_symlink_privilege(self):
        from unittest.mock import patch
        with patch.object(Path,'is_junction',return_value=True):
            with self.assertRaises(ValueError):cleanup.safe(self.root,self.sga)
    def test_changed_inventory_file_cannot_be_deleted(self):
        disposable=self.root/'cache';disposable.mkdir();f=disposable/'x';f.write_bytes(b'cache')
        rows=cleanup.tree(self.root,disposable);f.write_bytes(b'edited')
        with self.assertRaises(ValueError):cleanup.remove_checked(self.root,rows)
        self.assertTrue(f.exists())
    def test_safe_file_inventory_and_removal(self):
        disposable=self.root/'cache';disposable.mkdir();f=disposable/'x';f.write_bytes(b'cache')
        rows=cleanup.tree(self.root,disposable);cleanup.remove_checked(self.root,rows)
        self.assertFalse(f.exists());self.assertTrue(self.sga.exists())

    def test_all_active_work_locks_and_decoder_process_block_cleanup(self):
        for name in ('generation.lock','normalization.lock','encoding.lock'):
            lock=self.root/name;lock.write_text('active')
            with self.assertRaisesRegex(ValueError,'active'):cleanup.ensure_idle(self.root)
            lock.unlink()
        with patch.object(cleanup.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='1')):
            with self.assertRaisesRegex(ValueError,'active'):cleanup.ensure_idle(self.root)
        with patch.object(cleanup.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='')):
            with self.assertRaisesRegex(ValueError,'unavailable'):cleanup.ensure_idle(self.root)
        with patch.object(cleanup.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='0')):
            cleanup.ensure_idle(self.root)

    def encoding_cleanup_fixture(self,invalid_medium=False):
        art=self.root/'art';art.mkdir()
        for name in ('release.py','package_audio.py','encoding.py','generation.py','Install-BerberNativeAudio.ps1'):
            p=self.root/'research/berber060'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('retained')
        for p in (art/'recording-plan.json',self.root/'profiles/manifest.json',self.root/'bindings/payload-manifest.json',self.root/'baseline-member-sha256.json'):
            write(p,{})
        source=self.root/'wav/good.wav';source.parent.mkdir();source.write_bytes(b'normalized retained WAV')
        paid=art/'masters/paid.wav';paid.parent.mkdir();paid.write_bytes(b'paid lossless master')
        shared=self.root/'shared_stock_cache/cache.bin';shared.parent.mkdir();shared.write_bytes(b'shared')
        decoded=self.root/'decoded-qa/good.wav';decoded.parent.mkdir();decoded.write_bytes(b'decoded evidence')
        for quality in ('Medium','Low'):
            folder=self.root/'wem'/quality;wem=folder/'Windows/good.wem';wem.parent.mkdir(parents=True);wem.write_bytes(b'encoded')
            rows={'good':{'source':str(source),'source_sha256':sha(source),'wem':str(wem),'sha256':sha(wem)}}
            if quality=='Medium' and invalid_medium:
                bad=folder/'Windows/bad.wem';bad.write_bytes(b'changed')
                rows['bad']={'source':str(source),'source_sha256':sha(source),'wem':str(bad),'sha256':'f'*64}
            write(folder/'encoding-manifest.json',rows)
        return art,decoded,source,paid,shared

    def fixture_plan(self,art):
        with patch.object(cleanup,'physical_root',return_value=self.root),patch.object(cleanup,'ensure_idle'),\
             patch.object(cleanup,'ROOT',self.root),patch.object(cleanup,'ART',art),\
             patch.object(cleanup,'BASE',self.sga),patch.object(cleanup,'BASE_SHA',sha(self.sga)),patch.object(cleanup,'ARCH',self.sga):
            return cleanup.build_plan()

    def test_invalid_medium_never_deletes_decoded_evidence_via_valid_low_stem(self):
        art,decoded,*_=self.encoding_cleanup_fixture(invalid_medium=True)
        plan=self.fixture_plan(art);targets={c['target'] for c in plan['candidates']}
        self.assertNotIn(str(decoded),targets)
        self.assertTrue(any(r['path']==str(decoded) and 'hash-validated' in r['reason'] for r in plan['retained']))

    def test_valid_medium_allows_only_regenerable_decode_and_preserves_inputs(self):
        art,decoded,normalized,paid,shared=self.encoding_cleanup_fixture()
        plan=self.fixture_plan(art);selected={self.root/r['path'] for c in plan['candidates'] for r in c['files']}
        self.assertIn(decoded,selected)
        for protected in (normalized,paid,shared,self.sga):self.assertNotIn(protected,selected);self.assertTrue(protected.exists())

if __name__=='__main__':unittest.main()
