"""Compile AI mappings with Content Editor; retain only scoped AI output for graft."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys,zipfile,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'output/berber_update_1_0_4';WORK=OUT/'work';PROJECT=WORK/'native-project'
CORE=Path(r'C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com\garrison\bin\core\garrison-core.exe')
EDITOR=Path(r'E:\Games\steamapps\common\Age of Empires IV\EssenceEditor.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
 assert not PROJECT.exists()
 PROJECT.mkdir(parents=True)
 snapshot=HERE/'cook-reference-inputs.zip'
 if snapshot.exists():
  record=json.loads((HERE/'cook-inputs.json').read_text())
  assert sha(snapshot)==record['snapshot_sha256']
  with zipfile.ZipFile(snapshot) as z:
   assert z.testzip() is None;z.extractall(PROJECT)
  for p in (HERE/'source/attrib/instances').rglob('*.xml'):
   target=PROJECT/'assets/attrib/instances'/p.relative_to(HERE/'source/attrib/instances');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  return
 sources=[ROOT/'Berber_future_kingdom.aoe4mod']
 for folder in ['assets/attrib','assets/locdb']:
  sources += [p for p in (ROOT/folder).rglob('*') if p.is_file()]
 sources += list((ROOT/'assets').glob('*.rdo'))
 snapshot=HERE/'cook-reference-inputs.zip'
 assert not snapshot.exists()
 with zipfile.ZipFile(snapshot,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sources:z.write(p,p.relative_to(ROOT).as_posix())
 with zipfile.ZipFile(snapshot) as z:
  assert z.testzip() is None;z.extractall(PROJECT)
 for p in (HERE/'source/attrib/instances').rglob('*.xml'):
  target=PROJECT/'assets/attrib/instances'/p.relative_to(HERE/'source/attrib/instances');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 (HERE/'cook-inputs.json').write_text(json.dumps({'snapshot_sha256':sha(snapshot),'inputs':{str(p.relative_to(ROOT)):sha(p) for p in sources},'editor':str(EDITOR),'editor_sha256':sha(EDITOR)},indent=2)+'\n')
def build():
 # Compile attributes only; all shipped media stays in the pinned release base.
 burn=((HERE/'_default.burnproj') if (HERE/'_default.burnproj').exists() else (ROOT/'assets/_default.burnproj')).read_text(encoding='utf-8-sig')
 def scope(match):
  text=match.group()
  return text if '<Burner>Mod Attributes</Burner>' in text else text.replace('<IsEnabled>true</IsEnabled>','<IsEnabled>false</IsEnabled>')
 burn=re.sub(r'<BurnRule>.*?</BurnRule>',scope,burn,flags=re.S)
 # Native validation requires all referenced local blueprints to participate;
 # excluding them produces dangling-reference errors. Supply their real local
 # media dependencies, compile normally, and select only AI RGDs at graft time.
 media=HERE/'cook-media-inputs.zip'
 if not media.exists():
  diagnostic=(WORK/'native-cook-2/logs/stderr.log').read_text()
  required=set()
  for group in re.findall(r"file that doesn't exist \(([^\r\n]+)\)\.",diagnostic):
   candidates=[ROOT/'assets'/value for value in group.split('; ')]
   existing=next((p for p in candidates if p.is_file()),None)
   assert existing is not None,group
   required.add(existing)
  with zipfile.ZipFile(media,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for p in sorted(required):z.write(p,p.relative_to(ROOT/'assets').as_posix())
  (HERE/'cook-media-inputs.json').write_text(json.dumps({'snapshot_sha256':sha(media),'inputs':{str(p.relative_to(ROOT)):sha(p) for p in sorted(required)}},indent=2)+'\n')
 assert sha(media)==json.loads((HERE/'cook-media-inputs.json').read_text())['snapshot_sha256']
 with zipfile.ZipFile(media) as z:
  assert z.testzip() is None;z.extractall(PROJECT/'assets')
 (HERE/'_default.burnproj').write_text(burn,encoding='utf8')
 (PROJECT/'assets/_default.burnproj').write_text(burn,encoding='utf8')
 for p in (HERE/'source/attrib/instances').rglob('*.xml'):
  target=PROJECT/'assets/attrib/instances'/p.relative_to(HERE/'source/attrib/instances');shutil.copyfile(p,target)
 run_root=WORK/'native-cook'
 number=1
 while run_root.exists():number+=1;run_root=WORK/('native-cook-'+str(number))
 args=[str(CORE),'essence','build-mod','--editor',str(EDITOR),'--mod',str(PROJECT/'Berber_future_kingdom.aoe4mod'),'--run-root',str(run_root),'--timeout','600','--console-burn-log']
 p=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=660)
 (OUT/'native-cook.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf8')
 (OUT/'native-cook-result.json').write_text(json.dumps({'exit_code':p.returncode,'run_root':str(run_root),'command':args,'stdout_tail':p.stdout[-3000:],'stderr_tail':p.stderr[-2000:]},indent=2)+'\n')
 print('COOK_EXIT',p.returncode);print(p.stdout[-3500:]);print(p.stderr[-1500:]);assert p.returncode==0,'See native-cook.log'
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='build':build()
