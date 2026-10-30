"""Compose the narrowly admitted061 patch and make complete sharing ZIPs."""
import sys,json,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'research/berber060'))
from common import OUT as OLD,ARCH,sha,read,write,run
from release import member_hashes
from portable import SETUP as OLD_SETUP
BASE=OLD/'candidate.sga';BASE_SHA='6e4a4f3fcb00627df40f5a50fbf128c949cc281f54b4cf1a424f6bdfc9370f51'
OUT=ROOT/'output/berber_update_0_6_1'

def make_zip(target,files,texts):
 if target.exists():raise FileExistsError('Existing delivery retained')
 expected={name:sha(p) for name,p in files.items()}
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,p in sorted(files.items()):z.write(p,name)
  for name,value in texts.items():
   data=value.encode('utf-8-sig') if name.endswith('.ps1') else value.encode('utf8')
   z.writestr(name,data);expected[name]=hashlib.sha256(data).hexdigest()
 with zipfile.ZipFile(target) as z:
  if set(z.namelist())!=set(expected) or z.testzip():raise ValueError('ZIP CRC/member failure')
  for name,digest in expected.items():
   with z.open(name) as f:
    if hashlib.file_digest(f,'sha256').hexdigest()!=digest:raise ValueError('Packaged hash differs')
 return {'zip':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'members':expected,'crc':'passed','member_sha256':'passed'}

def compose():
 if sha(BASE)!=BASE_SHA:raise ValueError('060 base changed')
 reports=[read(OUT/'landmarks/payload-manifest.json'),read(OUT/'voice-bindings/payload-manifest.json')]
 if any(r['status']!='passed' for r in reports):raise ValueError('Unverified patch')
 payloads=[p for r in reports for p in r['payloads']]
 expected={p['member']:p['sha256'] for p in payloads}
 if len(expected)!=len(payloads):raise ValueError('Conflicting patch owners')
 for p in payloads:
  if sha(p['file'])!=p['sha256']:raise ValueError('Patch bytes changed')
 _,baseline=member_hashes(BASE,OLD/'integration/candidate-readback-6e4a4f3fcb00')
 listing=OUT/'members.txt';listing.write_text(''.join(p['member']+'='+p['file']+'\n' for p in payloads),encoding='utf8')
 target=OUT/'Berber_future_kingdom.sga'
 if target.exists():raise FileExistsError('Existing061 archive retained')
 run(ARCH,'set-members',BASE,listing,target,'--alias','attrib')
 _,candidate=member_hashes(target,OUT/'readback')
 if set(candidate)!=set(baseline)|set(expected):raise ValueError('Unexpected archive members')
 changed={p for p,h in candidate.items() if baseline.get(p)!=h}
 if changed!=set(expected) or any(candidate[p]!=h for p,h in expected.items()):raise ValueError('Non-admitted archive difference')
 report={'status':'passed','version':'0.6.1','base_sha256':BASE_SHA,'sga_sha256':sha(target),'changed_members':sorted(changed),'base_members':len(baseline),'candidate_members':len(candidate),'payloads':payloads,'all_other060_members_identical':True,'audible_gameplay':'pending','native_landmark_visuals':'pending','cleanup':'not requested'}
 write(OUT/'composition-report.json',report);print('061_COMPOSED',report['sga_sha256'],flush=True)
 return report

def package(report):
 with zipfile.ZipFile(OLD/'READY_TO_IMPORT/Berber-0.6.0.zip') as z:manifest=json.loads(z.read('garrison.json'))
 manifest['members'][0]['sha256']=report['sga_sha256']
 manifest['details'].update(version='0.6.1',summary='Villager/trader voice routing; Castle landmarks 25% larger',description='0.6.0 content retained. Villager and Trader use one existing take per action/delivery shared across all ages. Complete native voice installer included in the sharing download.',changelog='Correct canonical Villager/Trader squad speech paths and private profiles; Great Mosque of Tlemcen and Marrakech visual size +25%.')
 main=make_zip(OUT/'Berber-0.6.1.zip',{'Berber_future_kingdom.sga':OUT/'Berber_future_kingdom.sga'},{'garrison.json':json.dumps(manifest,indent=2)+'\n'})
 patch=read(OUT/'audio-patch-validation.json');native=OLD/'native-package'
 files={'Garrison/Berber-0.6.1.zip':OUT/'Berber-0.6.1.zip','NativePatch/native-audio-manifest.json':OUT/'audio-patch/native-audio-manifest.json','NativePatch/Install-BerberNativeAudio.ps1':OUT/'audio-patch/Install-BerberNativeAudio.ps1'}
 base_audio=read(native/'native-audio-manifest.json')
 files['NativeAudio/native-audio-manifest.json']=native/'native-audio-manifest.json'
 files['NativeAudio/Install-BerberNativeAudio.ps1']=native/'Install-BerberNativeAudio.ps1'
 for row in base_audio['files']:files['NativeAudio/'+row['payload']]=native/row['payload']
 for payload,source in patch['sources'].items():files['NativePatch/'+payload]=Path(source)
 # Reuse the qualified base installer, then apply the isolated061 voice patch.
 setup=OLD_SETUP.replace('0.6.0','0.6.1')
 start=setup.index("    $installer=Join-Path")
 end=setup.index("    exit 0",start)
 setup=setup[:start]+r'''
    $parts=if($Action -eq 'Uninstall') { @('NativePatch','NativeAudio') } else { @('NativeAudio','NativePatch') }
    foreach($part in $parts) {
        $payload=Join-Path $PSScriptRoot $part
        $installer=Join-Path $payload 'Install-BerberNativeAudio.ps1'
        if($Action -eq 'Install') {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Action Validate -PackageRoot $payload -AudioRoot $audio
            if($LASTEXITCODE -ne 0) { throw ($part+' validation failed') }
        }
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Action $Action -PackageRoot $payload -AudioRoot $audio
        if($LASTEXITCODE -ne 0) { throw ($part+' '+$Action+' failed. Earlier completed components are retained; rerun safely after resolving the error.') }
        if($Action -eq 'Install') {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Action Verify -PackageRoot $payload -AudioRoot $audio
            if($LASTEXITCODE -ne 0) { throw ($part+' verification failed') }
        }
    }
    Write-Host 'Completed. Import Garrison\Berber-0.6.1.zip in Garrison and restart AoE4 completely.'
'''+setup[end:]
 texts={'Setup-BerberVoices.ps1':setup,'START-HERE.txt':'''BERBER 0.6.1 COMPLETE PORTABLE PACKAGE
1. Extract this ENTIRE sharing ZIP to an ordinary local folder.
2. Close AoE4. Double-click INSTALL-VOICES.cmd and select the game folder
   containing cardinal. Wait for installation and verification to finish.
   This works for fresh installs and updates from the supplied0.6.0 voices.
3. Import ONLY Garrison\\Berber-0.6.1.zip into Garrison and enable it.
   Never import this outer sharing ZIP or the NativeAudio/NativePatch folders.
4. Restart AoE4 completely. Use your normal Berber game-mode/tuning selections.

No API key, paid generation, Python or Wwise is required by the recipient.
AoE4 and compatible Garrison0.1.4 are required. Select the actual game folder,
not Documents or a Garrison library folder. Write access to cardinal/audio is
required; use administrator privileges only if your installation needs them.
VERIFY-VOICES.cmd checks both components; UNINSTALL-VOICES.cmd removes unchanged
owned voice files, including the base0.6.0 component. Disable the mod in Garrison
after uninstall. Stock audio archives are untouched. Normal games retain stock audio.

0.6.1 changes: Villager/Trader canonical speech routing, one existing recording
per action/delivery shared across ages/takes; Castle landmarks Tlemcen and
Marrakech +25% visual size. Footprints/stats and other content unchanged.
Native audible/visual acceptance of this patch remains pending.
0.6.0 inherited limitations:21 reused takes across other voice slots, four shared
early-age native banks, authored Arabic fallback; human pronunciation review pending.
Both base and patch installers are local file/hash operations, no network access.
'''}
 for action in ('Install','Verify','Uninstall'):
  texts[action.upper()+'-VOICES.cmd']='@echo off\r\npowershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Setup-BerberVoices.ps1" -Action '+action+'\r\nset "BERBER_SETUP_RESULT=%ERRORLEVEL%"\r\npause\r\nexit /b %BERBER_SETUP_RESULT%\r\n'
 shared=make_zip(OUT/'Berber-0.6.1-COMPLETE-PORTABLE.zip',files,texts)
 validation={'status':'passed','version':'0.6.1','garrison':main,'portable':shared,'sga_sha256':report['sga_sha256'],'audio_patch_recordings':patch['unique_recordings'],'paid_requests':0,'gameplay_acceptance':'pending','cleanup':'not requested'}
 write(OUT/'release-validation.json',validation)
 print('061_DELIVERY_VERIFIED',shared['bytes'],shared['sha256'],flush=True)
 return validation

if __name__=='__main__':package(compose())
