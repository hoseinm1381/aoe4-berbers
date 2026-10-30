import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'research'))
from berber070_package import verify,put,sha
OUT=ROOT/'output/berber_update_0_7_2'
OLD=ROOT/'output/berber_update_0_7_0'
SGA_SHA='48f09ed61020740932b0a653e165710fda49d25aa7739d05f6486b79dbe661bb'
def build():
 if not (OLD/'Berber-0.7.0-MAIN-GARRISON.zip').exists():
  raise RuntimeError('Historical ZIP chain retired. Use research/next_release.py and REBUILD_NEXT.md for the supported next-release path.')
 OUT.mkdir(exist_ok=True)
 main=OUT/'Berber-0.7.2-MAIN-GARRISON.zip'; voices=OUT/'Berber-0.7.2-VOICES-INSTALLER.zip'
 if main.exists() or voices.exists():raise FileExistsError('Preserve existing delivery')
 reports={}
 with zipfile.ZipFile(OLD/'Berber-0.7.0-MAIN-GARRISON.zip') as source:
  data=source.read('Berber_future_kingdom.sga')
  if hashlib.sha256(data).hexdigest()!=SGA_SHA:raise ValueError('Wrong base SGA')
  manifest=json.loads(source.read('garrison.json'))
  manifest['details'].update(version='0.7.2',summary='Native voices with Steam-aware install and uninstall',description='Install the separate Berber 0.7.2 native voice package, then enable this mod. Preserves 0.6.1 gameplay, voices and enlarged Castle landmarks. No external voice overlay.',changelog='Steam-aware folder detection for native voice installation, verification and uninstall. Removes experimental external playback by using the retained 0.6.1 archive.')
  expected={}
  with zipfile.ZipFile(main,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   put(z,'Berber_future_kingdom.sga',data,expected)
   put(z,'garrison.json',(json.dumps(manifest,indent=2)+'\n').encode(),expected)
  reports['main']=verify(main,expected)
 with zipfile.ZipFile(OLD/'Berber-0.7.0-VOICES-INSTALLER.zip') as source:
  setup=source.read('Setup-BerberVoices.ps1').decode('utf-8-sig').replace('0.7.0','0.7.2')
  setup=setup.replace("    $audio=Join-Path $GameRoot 'cardinal\\audio'", "    . (Join-Path $PSScriptRoot 'Find-Aoe4.ps1')\n    $GameRoot=Resolve-Aoe4Root $GameRoot\n    Write-Host ('Game found: '+$GameRoot)\n    $audio=Join-Path $GameRoot 'cardinal\\audio'")
  setup=setup.replace('Select your Age of Empires IV installation folder (contains cardinal). Close the game first.','Select Steam, a Steam library, or any folder inside Age of Empires IV. Close the game first.')
  if 'Resolve-Aoe4Root $GameRoot' not in setup:raise ValueError('Setup insertion failed')
  expected={}
  with zipfile.ZipFile(voices,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for item in source.infolist():
    if item.filename.startswith(('NativeAudio/','NativePatch/')) or item.filename.endswith('-VOICES.cmd'):
     put(z,item.filename,source.read(item),expected)
   put(z,'Setup-BerberVoices.ps1',setup.encode('utf-8-sig'),expected)
   put(z,'Find-Aoe4.ps1',Path(__file__).with_name('Find-Aoe4.ps1').read_bytes(),expected)
   put(z,'START-HERE.txt',b'''BERBER 0.7.2 - NATIVE VOICES
1. Extract this entire voice ZIP. Close AoE4 completely.
2. Double-click INSTALL-VOICES.cmd. Select Steam, a Steam library, the
   AoE4 game folder, or a folder inside it (including cardinal/audio).
   Steam libraryfolders.vdf is followed for libraries on other drives.
   The game is validated automatically. Multiple installs require selecting
   inside the desired game folder. No whole-disk search is performed.
3. Import only Berber-0.7.2-MAIN-GARRISON.zip in Garrison. Replace/disable
   the 0.7.1 pilot. Enable the Berber mod and use its normal lobby selections.
4. Restart AoE4 completely after installing or uninstalling voices.

VERIFY-VOICES.cmd checks installation. UNINSTALL-VOICES.cmd removes unchanged
owned Berber voice files; edited or foreign files are preserved and reported.
Keep this extracted folder for uninstall. Prior 0.6.0/0.6.1/0.7.0 native
installations share ownership state and are upgraded/uninstalled together.
Normal games retain stock sounds; no reinstall/uninstall is needed per match.
Stock archives are untouched. No Python, paid API, or network access is needed.
Write access to the selected game is required. If denied, run the CMD as
administrator only if you trust this package. The game is never stopped for you.

Retains 0.6.1: Villager/Trader one take per action/delivery shared across ages,
Castle landmarks enlarged 25%, other native voice banks and content unchanged.
Inherited limits: 21 reused takes, four early-age bank limits, Arabic fallback
and pending human pronunciation review. Fresh-PC audible checks remain pending.
No experimental external audio overlay is included.
''',expected)
  reports['voices']=verify(voices,expected)
 report=dict(status='package_verified',version='0.7.2',sga_sha256=SGA_SHA,**reports,paid_requests=0,game_installation_modified=False,audible_gameplay='pending',cleanup='No disposable build copies created; ZIPs verified directly; retained editable scripts and compact evidence')
 (OUT/'release-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:{f:r[f] for f in ('zip','bytes','sha256')} for k,r in reports.items()}),flush=True)
if __name__=='__main__':build()
