"""Split the verified061 release into070 Garrison and click-to-install voice ZIPs."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).absolute().parents[1]
SOURCE=ROOT/'output/berber_update_0_6_1'
OUT=ROOT/'output/berber_update_0_7_0'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(path,expected):
 with zipfile.ZipFile(path) as z:
  if len(z.namelist())!=len(set(z.namelist())) or set(z.namelist())!=set(expected) or z.testzip():raise ValueError('ZIP member/CRC mismatch')
  for name,digest in expected.items():
   with z.open(name) as f:
    if hashlib.file_digest(f,'sha256').hexdigest()!=digest:raise ValueError('Packaged member SHA mismatch: '+name)
 return {'zip':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'members':expected,'crc':'passed','member_sha256':'passed'}
def put(z,name,data,expected):
 z.writestr(name,data);expected[name]=hashlib.sha256(data).hexdigest()
def build():
 if not (SOURCE/'Berber-0.6.1-COMPLETE-PORTABLE.zip').exists():
  raise RuntimeError('Historical ZIP chain retired. Use research/next_release.py and REBUILD_NEXT.md for the supported next-release path.')
 OUT.mkdir(exist_ok=True)
 validation=json.loads((SOURCE/'release-validation.json').read_text(encoding='utf8'))
 source=SOURCE/'Berber-0.6.1-COMPLETE-PORTABLE.zip'
 if validation['status']!='passed' or sha(source)!=validation['portable']['sha256']:raise ValueError('Unverified061 portable source')
 main=OUT/'Berber-0.7.0-MAIN-GARRISON.zip';voices=OUT/'Berber-0.7.0-VOICES-INSTALLER.zip'
 if main.exists() or voices.exists():raise FileExistsError('Existing deliveries preserved')
 with zipfile.ZipFile(SOURCE/'Berber-0.6.1.zip') as z:manifest=json.loads(z.read('garrison.json'))
 sga=SOURCE/'Berber_future_kingdom.sga'
 if sha(sga)!=validation['sga_sha256']:raise ValueError('061 SGA changed')
 manifest['details'].update(version='0.7.0',summary='Berber voices and larger Castle landmarks; separate click-to-install voices',description='0.6.1 content preserved. Install the separately supplied0.7.0 voice package once, then import this main ZIP into Garrison.',changelog='Packaging release: separate main mod and double-click native voice installer. Retains061 Villager/Trader routing and +25% Castle landmark visuals.')
 expected={}
 with zipfile.ZipFile(main,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(sga,'Berber_future_kingdom.sga');expected['Berber_future_kingdom.sga']=sha(sga)
  put(z,'garrison.json',(json.dumps(manifest,indent=2)+'\n').encode('utf8'),expected)
 main_report=verify(main,expected);expected={}
 with zipfile.ZipFile(source) as old,zipfile.ZipFile(voices,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for item in old.infolist():
   name=item.filename
   if not name.startswith(('NativeAudio/','NativePatch/')):continue
   h=hashlib.sha256()
   with old.open(item) as reader,z.open(name,'w',force_zip64=True) as writer:
    while block:=reader.read(1024*1024):h.update(block);writer.write(block)
   expected[name]=h.hexdigest()
   if expected[name]!=validation['portable']['members'][name]:raise ValueError('Source member changed')
  setup=old.read('Setup-BerberVoices.ps1').decode('utf-8-sig').replace('0.6.1','0.7.0')
  setup=setup.replace("    Write-Host 'Completed. Import Garrison\\Berber-0.7.0.zip in Garrison and restart AoE4 completely.'", "    Write-Host 'Completed. Import Berber-0.7.0-MAIN-GARRISON.zip in Garrison and restart AoE4 completely.'")
  put(z,'Setup-BerberVoices.ps1',setup.encode('utf-8-sig'),expected)
  for action in ('Install','Verify','Uninstall'):
   data=old.read(action.upper()+'-VOICES.cmd');put(z,action.upper()+'-VOICES.cmd',data,expected)
  readme='''BERBER 0.7.0 VOICE INSTALLER — DO NOT IMPORT THIS ZIP INTO GARRISON

1. Extract this ENTIRE voice ZIP to an ordinary local folder.
2. Close Age of Empires IV completely.
3. Double-click INSTALL-VOICES.cmd and select the game installation folder
   containing cardinal (Steam: Properties > Installed Files > Browse).
4. Wait for installation and verification to finish; this may take several minutes.
5. Import the SEPARATE Berber-0.7.0-MAIN-GARRISON.zip in Garrison, enable it,
   then restart AoE4 completely and select your normal Berber mode/tuning settings.

Every new computer needs the voices installed once. No API key, account,
Python or Wwise is needed. AoE4 and compatible Garrison0.1.4 are required.
The selected game folder must contain cardinal/audio. Write access is needed;
use administrator privileges only if your game-folder permissions require it.
No network access or paid generation occurs. Stock sound archives are untouched.
Normal games continue using stock voices; no reinstall/uninstall per play is needed.

VERIFY-VOICES.cmd checks installed hashes. UNINSTALL-VOICES.cmd removes only
unchanged files owned by both Berber voice components; changed files are preserved.
It also removes the shared0.6.0/0.6.1 voice installation. Disable the mod in Garrison
after uninstall. Keep this extracted folder for maintenance.

Upgrades from the supplied0.6.0/0.6.1 installer are supported using the same
ownership states.0.7.0 changes packaging only; audio/bindings/landmark content
is identical to0.6.1. Full native audible/visual acceptance remains pending.
Inherited limits: authored Arabic fallback, pending human pronunciation review,
21 reused takes elsewhere and four shared early-age native banks.
'''
  put(z,'START-HERE.txt',readme.encode('utf8'),expected)
 voice_report=verify(voices,expected)
 report={'status':'passed','version':'0.7.0','main':main_report,'voices':voice_report,'sga_sha256':sha(sga),'content_base':'0.6.1 unchanged archive and voice payloads','paid_requests':0,'cleanup':'not requested','fresh_computer_installation':'pending','native_audible_visual_acceptance':'pending'}
 (OUT/'release-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:{f:r[f] for f in ('zip','bytes','sha256')} for k,r in [('main',main_report),('voices',voice_report)]}),flush=True)
if __name__=='__main__':build()
