"""Build one sharing download without changing native bindings or recordings."""
import hashlib,json,zipfile
from pathlib import Path
from common import OUT,sha,write

SETUP=r'''param([ValidateSet('Install','Verify','Uninstall')][string]$Action='Install',[string]$GameRoot)
$ErrorActionPreference='Stop'
try {
    if (-not $GameRoot) {
        Add-Type -AssemblyName System.Windows.Forms
        $picker=New-Object System.Windows.Forms.FolderBrowserDialog
        $picker.Description='Select your Age of Empires IV installation folder (contains cardinal). Close the game first.'
        if ($picker.ShowDialog() -ne 'OK') { throw 'Cancelled. No installation started.' }
        $GameRoot=$picker.SelectedPath
    }
    $audio=Join-Path $GameRoot 'cardinal\audio'
    if (-not (Test-Path -LiteralPath $audio -PathType Container)) { throw 'Wrong folder: cardinal\audio was not found. Select the game installation folder.' }
    $installer=Join-Path $PSScriptRoot 'NativeAudio\Install-BerberNativeAudio.ps1'
    $payload=Join-Path $PSScriptRoot 'NativeAudio'
    if ($Action -eq 'Install') {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Action Validate -PackageRoot $payload -AudioRoot $audio
        if ($LASTEXITCODE -ne 0) { throw 'Package validation failed. Installation stopped.' }
    }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Action $Action -PackageRoot $payload -AudioRoot $audio
    if ($LASTEXITCODE -ne 0) { throw ($Action+' failed. Read the error above.') }
    if ($Action -eq 'Install') {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -Action Verify -PackageRoot $payload -AudioRoot $audio
        if ($LASTEXITCODE -ne 0) { throw 'Installed-file verification failed.' }
        Write-Host 'Voices installed and verified. Now import Garrison\Berber-0.6.0.zip in Garrison. Restart AoE4 completely.'
    }
    exit 0
} catch { Write-Host $_.Exception.Message -ForegroundColor Red; exit 1 }
'''
README='''BERBER 0.6.0 — COMPLETE SHARING PACKAGE

1. Extract this entire ZIP to an ordinary local folder first.
   Do NOT import this outer sharing ZIP into Garrison.
2. Close Age of Empires IV. Double-click INSTALL-VOICES.cmd.
   Select your game installation folder, the folder containing cardinal.
   Steam: Library > AoE IV > Properties > Installed Files > Browse.
   Wait for both installation and verification to finish. Keep the window open;
   validating thousands of files can take several minutes. If access is denied,
   use an account with write access to the game folder or run the installer as administrator.
3. In Garrison, import ONLY Garrison\Berber-0.6.0.zip and enable it.
4. Restart the game completely. Select The Berber Dynasties tuning pack,
   Berber Civilization game mode and Malians civilization as for the existing mod.

Both steps 2 and 3 are required on every new computer. Garrison cannot install
native speech files from its mod ZIP. All recordings and profiles are included;
no ElevenLabs account, API key, Python or Wwise installation is needed.
AoE4 and a compatible Garrison client (0.1.4 or compatible) are required.
The game folder must contain cardinal\audio. Other installation layouts have
not been qualified. The installer never changes stock audio archives.

VERIFY-VOICES.cmd checks saved installed files.
UNINSTALL-VOICES.cmd removes only unchanged files owned by this voice install;
then disable/remove the mod in Garrison. Changed files are preserved and reported.
Keep the extracted folder for maintenance. No automatic update or cleanup runs.

KNOWN LIMITATIONS: Villager and Trader were reported to retain Malian voices.
They are deliberately unchanged in this package. See VOICE_GAPS.md for 21 reused
takes, shared early-age banks, Arabic fallback and pending pronunciation checks.
Other units were reported working; full gameplay and fresh-computer installation
are not certified by ZIP/hash checks. Local native installation and verification passed.
'''

def build():
    native=OUT/'native-package';manifest=json.loads((native/'native-audio-manifest.json').read_text(encoding='utf8'))
    mod=OUT/'READY_TO_IMPORT/Berber-0.6.0.zip'
    single=json.loads((OUT/'single-import-validation.json').read_text(encoding='utf8'))
    if sha(mod)!=single['sha256']:raise ValueError('Import ZIP changed')
    files={'Garrison/Berber-0.6.0.zip':mod,'NativeAudio/native-audio-manifest.json':native/'native-audio-manifest.json',
           'NativeAudio/Install-BerberNativeAudio.ps1':native/'Install-BerberNativeAudio.ps1','VOICE_GAPS.md':OUT/'VOICE_GAPS.md'}
    for row in manifest['files']:
        p=native/row['payload']
        if p.stat().st_size!=row['bytes']:raise ValueError('Payload size differs')
        files['NativeAudio/'+row['payload']]=p
    for name,p in files.items():
        if p.is_symlink() or p.is_junction():raise ValueError('Linked payload refused')
    expected={name:sha(p) for name,p in files.items()}
    for row in manifest['files']:
        if expected['NativeAudio/'+row['payload']]!=row['sha256']:raise ValueError('Payload hash differs')
    texts={'START-HERE.txt':README,'Setup-BerberVoices.ps1':SETUP}
    for action in ('Install','Verify','Uninstall'):
        texts[action.upper()+'-VOICES.cmd']='@echo off\r\npowershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Setup-BerberVoices.ps1" -Action '+action+'\r\nset "BERBER_SETUP_RESULT=%ERRORLEVEL%"\r\npause\r\nexit /b %BERBER_SETUP_RESULT%\r\n'
    target=OUT/'Berber-0.6.0-COMPLETE-PORTABLE.zip';tmp=target.with_suffix('.pending.zip')
    if target.exists() or tmp.exists():raise ValueError('Existing portable output preserved')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,p in sorted(files.items()):z.write(p,name)
        for name,value in texts.items():
            data=value.encode('utf-8-sig') if name.endswith('.ps1') else value.encode('utf8')
            z.writestr(name,data);expected[name]=hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(tmp) as z:
        if set(z.namelist())!=set(expected) or z.testzip():raise ValueError('Portable ZIP member/CRC failure')
        for name,digest in expected.items():
            with z.open(name) as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise ValueError('Portable member changed')
    tmp.replace(target)
    report={'status':'passed','zip':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'members':expected,
        'unique_voice_payloads':len({r['payload'] for r in manifest['files']}),'native_alias_files':len(manifest['files']),
        'source_mod_sha256':single['sha256'],'bindings_and_audio_changed':False,'villager_trader':'Known reported issue unchanged',
        'crc_and_member_sha256':'passed','fresh_computer_interactive_install':'pending','cleanup':'paused by user'}
    write(OUT/'portable-validation.json',report)
    print({k:v for k,v in report.items() if k!='members'})

if __name__=='__main__':build()
