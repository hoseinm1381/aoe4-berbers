"""Opaque fixture bytes exercise deployment safety; never target game audio."""
import hashlib, json, os, pathlib, shutil, subprocess, tempfile, unittest

ROOT=pathlib.Path(__file__).absolute().parents[2]
SCRIPT=pathlib.Path(__file__).with_name('Install-BerberNativeAudio.ps1')
SCRATCH=(ROOT/'output/berber_update_0_6_0/installer-tests').resolve()
PWSH=os.environ.get('BERBER_INSTALLER_TEST_POWERSHELL') or shutil.which('pwsh') or 'powershell'

def quote(value):return "'"+str(value).replace("'","''")+"'"

class InstallerTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=SCRATCH)
        self.root=pathlib.Path(self.temp.name)
        self.package=self.root/'package';self.package.mkdir()
        self.audio=self.root/'audio';self.audio.mkdir()
        self.spd='malian_b01xxx.spd'
        self.wem='civ_malian/malian_b01xxx/test.wem'
        self.alias='civ_malian/malian_b01xxx/alternate.wem'
        self.manifest={'schema':'berber-native-audio/v1','profiles':[
            {'family':'villager','speaker':'b01xxx','race':'malian','path':self.spd}], 'files':[]}
        for native,payload,content in [(self.spd,'blobs/profile',b'fixture SPD'),
                (self.wem,'blobs/wem',b'fixture WEM'),(self.alias,'blobs/wem',b'fixture WEM')]:
            target=self.package/payload;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
            self.manifest['files'].append({'path':native,'payload':payload,'bytes':len(content),
                'sha256':hashlib.sha256(content).hexdigest()})
        self.save()

    def tearDown(self):self.temp.cleanup()
    def save(self):
        (self.package/'native-audio-manifest.json').write_text(json.dumps(self.manifest),encoding='utf8')

    def run_action(self,action,extra='',running=False):
        # Shadow only the process query. Tests cannot stop/start a real game.
        proc="[pscustomobject]@{Id=1}" if running else '@()'
        command=f'function Get-Process {{ param($Name,$ErrorAction) {proc} }}; '+extra+f' & {quote(SCRIPT)} -Action {quote(action)} -PackageRoot {quote(self.package)} -AudioRoot {quote(self.audio)}'
        return subprocess.run([PWSH,'-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,timeout=30)

    def assert_ok(self,result):self.assertEqual(0,result.returncode,result.stdout+result.stderr)
    def assert_failed(self,result):self.assertNotEqual(0,result.returncode,result.stdout+result.stderr)
    def files(self):return sorted(p.relative_to(self.audio).as_posix() for p in self.audio.rglob('*') if p.is_file())

    def test_validate_install_verify_uninstall_and_hardlinks(self):
        self.assert_ok(self.run_action('Validate'));self.assertEqual([],self.files())
        unrelated=self.audio/'tuarg.spd';unrelated.write_bytes(b'old rollback audio')
        installed=self.run_action('Install');self.assert_ok(installed)
        self.assertEqual((self.audio/self.wem).read_bytes(),(self.audio/self.alias).read_bytes())
        # exFAT is a supported copy-fallback destination; NTFS reports links.
        report=json.loads(installed.stdout)
        if report['hardlinks']:
            self.assertTrue(os.path.samefile(self.audio/self.wem,self.audio/self.alias))
        result=self.run_action('Install');self.assert_ok(result)
        self.assertEqual(3,json.loads(result.stdout)['adopted_files'])
        self.assert_ok(self.run_action('Verify'))
        self.assert_ok(self.run_action('Uninstall'));self.assertEqual(['tuarg.spd'],self.files())

    def test_corrupt_source_preflight_no_writes(self):
        (self.package/'blobs/wem').write_bytes(b'corrupt')
        self.assert_failed(self.run_action('Install'));self.assertEqual([],self.files())

    def test_conflict_preflight_no_changes(self):
        target=self.audio/self.wem;target.parent.mkdir(parents=True);target.write_bytes(b'foreign edit')
        self.assert_failed(self.run_action('Install'))
        self.assertEqual([self.wem],self.files());self.assertEqual(b'foreign edit',target.read_bytes())

    def test_edited_owned_file_survives_uninstall(self):
        self.assert_ok(self.run_action('Install'))
        (self.audio/self.wem).unlink();(self.audio/self.wem).write_bytes(b'edited separately')
        self.assert_failed(self.run_action('Uninstall'))
        self.assertEqual(b'edited separately',(self.audio/self.wem).read_bytes())
        self.assertTrue((self.audio/'berber060-install-state.json').exists())

    def test_adopt_identical_existing_private_file(self):
        (self.audio/self.spd).write_bytes(b'fixture SPD')
        self.assert_ok(self.run_action('Install'));self.assert_ok(self.run_action('Verify'))

    def test_unsafe_and_case_duplicate_paths(self):
        for invalid in ['../escape.spd','C:/escape.spd','/escape.spd','bad:stream','bad./x','CON/x']:
            with self.subTest(invalid=invalid):
                previous=self.manifest['files'][0]['path'];self.manifest['files'][0]['path']=invalid;self.save()
                self.assert_failed(self.run_action('Install'));self.assertEqual([],self.files())
                self.manifest['files'][0]['path']=previous
        self.manifest['files'].append(dict(self.manifest['files'][0],path=self.spd.upper()));self.save()
        self.assert_failed(self.run_action('Install'));self.assertEqual([],self.files())

    def test_foreign_namespace_and_payload_escape(self):
        self.manifest['files'][1]['path']='civ_malian/malian_tuarg/test.wem';self.save()
        self.assert_failed(self.run_action('Install'));self.assertEqual([],self.files())
        self.manifest['files'][1]['path']=self.wem
        self.manifest['files'][1]['payload']='../outside';self.save()
        self.assert_failed(self.run_action('Install'));self.assertEqual([],self.files())

    def test_profile_spd_required_and_stock_identity_refused(self):
        saved=self.manifest['files'];self.manifest['files']=saved[1:];self.save()
        self.assert_failed(self.run_action('Validate'));self.assertEqual([],self.files())
        self.manifest['files']=saved
        self.manifest['profiles'][0]['speaker']='tuarg';self.save()
        self.assert_failed(self.run_action('Install'));self.assertEqual([],self.files())

    def test_separate_media_identity_and_same_family_guard(self):
        identity='malian_b01xxxxxxxxxxx'
        self.manifest['profiles'][0]['media_identity']=identity
        self.manifest['files'][1]['path']=f'civ_malian/{identity}/test.wem'
        self.manifest['files'][2]['path']=f'civ_malian/{identity}/alternate.wem';self.save()
        self.assert_ok(self.run_action('Validate'));self.assert_ok(self.run_action('Install'))
        self.assert_ok(self.run_action('Verify'));self.assert_ok(self.run_action('Uninstall'))
        for invalid in ['malian_b02xxxxxxxxxxx','abbasid_b01xxxxxxxxxxx','../malian_b01xxx','malian_tuarg']:
            self.manifest['profiles'][0]['media_identity']=invalid;self.save()
            self.assert_failed(self.run_action('Validate'));self.assertEqual([],self.files())

    def test_state_cannot_claim_foreign_namespace(self):
        self.assert_ok(self.run_action('Install'))
        state=self.audio/'berber060-install-state.json'
        content=json.loads(state.read_text());content['files'][0]['path']='tuarg.spd'
        state.write_text(json.dumps(content))
        foreign=self.audio/'tuarg.spd';foreign.write_bytes(b'rollback companion')
        before=self.files();self.assert_failed(self.run_action('Uninstall'))
        self.assertEqual(before,self.files());self.assertEqual(b'rollback companion',foreign.read_bytes())

    def test_running_game_refuses_install_and_uninstall(self):
        self.assert_failed(self.run_action('Install',running=True));self.assertEqual([],self.files())
        self.assert_ok(self.run_action('Install'))
        before=self.files();self.assert_failed(self.run_action('Uninstall',running=True));self.assertEqual(before,self.files())

    def test_write_failure_rolls_back_only_new_files(self):
        old=self.audio/self.spd;old.write_bytes(b'fixture SPD')
        injection="function Move-Item { param($LiteralPath,$Destination,$ErrorAction) if ($Destination -like '*.wem') { throw 'fixture write fault' }; Microsoft.PowerShell.Management\\Move-Item -LiteralPath $LiteralPath -Destination $Destination -ErrorAction Stop };"
        self.assert_failed(self.run_action('Install',injection))
        self.assertEqual([self.spd],self.files());self.assertEqual(b'fixture SPD',old.read_bytes())

    def test_write_failure_removes_prior_new_owned_files(self):
        injection="function Move-Item { param($LiteralPath,$Destination,$ErrorAction) if ($Destination -like '*.wem') { throw 'fixture write fault' }; Microsoft.PowerShell.Management\\Move-Item -LiteralPath $LiteralPath -Destination $Destination -ErrorAction Stop };"
        result=self.run_action('Install',injection)
        self.assert_failed(result);self.assertIn('fixture write fault',result.stderr)
        self.assertEqual([],self.files())

    def test_existing_output_junction_chain_refused(self):
        logical=ROOT/'output/berber_update_0_6_0/installer-tests'/self.root.name/'package'
        if logical == self.package:self.skipTest('Workspace output has no junction')
        original=self.package;self.package=logical
        try:
            result=self.run_action('Validate')
            self.assert_failed(result);self.assertIn('Reparse point refused',result.stderr)
        finally:self.package=original

    def test_junction_destination_and_package_rejected(self):
        outside=self.root/'outside';outside.mkdir()
        parent=self.audio/'civ_malian'
        result=subprocess.run(['cmd','/c','mklink','/J',str(parent),str(outside)],capture_output=True)
        if result.returncode:self.skipTest('Junction creation unavailable')
        try:
            self.assert_failed(self.run_action('Install'));self.assertEqual([],list(outside.iterdir()))
        finally:parent.rmdir()
        payload=self.package/'blobs';shutil.rmtree(payload)
        subprocess.run(['cmd','/c','mklink','/J',str(payload),str(outside)],capture_output=True,check=True)
        try:self.assert_failed(self.run_action('Validate'))
        finally:payload.rmdir()

if __name__=='__main__':unittest.main()
