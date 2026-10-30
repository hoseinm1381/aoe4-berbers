"""Root-run production adapter. assemble/prepare/finish never start the Editor.

After stable author handoff and cook-family KIND:
  python landmark_027_export_actual.py assemble KIND
Run the printed prepared-stamp-command.json in the root's serialized cook slot.
  python landmark_027_export_actual.py finish KIND
Readbacks/staging are regenerable; retain recipes, original sources and reports.
"""
import json,shutil,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
from landmark_027_export_assemble import assemble,EXT,sha
from landmark_027_export_finish import finish_assembled
ROOT=Path(__file__).resolve().parents[1]
INT=ROOT/'output/berber_update_0_2_7/integration'
ART=ROOT/'art/landmarks_0_2_7'
KEYS={'ribat':'br027_ribat','funduq':'bf027_funduq'}
ARCH=EXT/'bin/sga-archiver.exe';CORE=EXT/'bin/core/garrison-core.exe'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2),encoding='utf8')
def unpack(archive,dest):
 subprocess.run([str(ARCH),'unpack',str(archive),'--output',str(dest)],check=True,capture_output=True)
def records(kind):
 rows=[read(INT/kind/f'cook-lod{i}.json') for i in range(3)]
 for r in rows:
  assert r['live_reload'] is False and sha(Path(r['archive']).read_bytes())==r['sha256']
  source=Path(r['source']);expected=r['source_files_sha256']
  observed={str(p.relative_to(source)):sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
  assert observed==expected,'Author source changed after fresh cook: '+str(source)
 assert len({r['sha256'] for r in rows})==1,'Use cook-family to cook all stable LODs together'
 return rows
def assemble_actual(kind):
 key=KEYS[kind];out=INT/kind;rows=records(kind)
 cooked=out/('cooked-readback-'+rows[0]['sha256'][:16]);unpack(rows[0]['archive'],cooked)
 project=INT/'library/Mods'/key
 original=project/f'project/source/art/stamps/garrison/{key}/{kind}_lod0.rdo'
 assert original.exists(),'Original supported Garrison source RDO required'
 source_parts=read(ART/kind/'export_lod0/building.json')['parts']
 validation=read(ART/kind/'source-validation.json');flag=validation['flag_transform']
 for lod in range(3):
  current=read(ART/kind/f'export_lod{lod}/building.json')['parts']
  assert [(r['name'],r['first_stage']) for r in current]==[(r['name'],r['first_stage']) for r in source_parts]
 report=assemble(kind,key,[cooked]*3,source_parts,out,flag,stamp_source=original)
 report['original_stamp_source_sha256']=sha(original.read_bytes())
 report['source_cook_records']=rows
 report['known_limits']=['Runtime uses the exact fresh compiler LOD0 geometry and per-triangle collections. Lower LOD sources are delivered but native lower-LOD activation is unsupported.','Native team-colour appearance requires in-game acceptance.','Intact new architecture persists through damage; native auxiliary wreck visuals retained.']
 write(out/'media-manifest.json',report)
 # Stage only configuration/attribute inputs, not fresh FBX sources: a second
 # model burn must not overwrite the assembled actual graph or three LOD buffers.
 stage=out/'stamp-source';target=stage/'source'
 assert not stage.exists(),'Use a fresh stamp-source path; inspect any existing run before retrying'
 for p in (project/'project/source').rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(project/'project/source')
  if rel.as_posix().startswith(('art/scenario/','art/stamps/')):continue
  dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 config=stage/(kind+'.aoe4mod');shutil.copy2(project/f'project/{key}.aoe4mod',config)
 for row in report['payloads']:
  dest=target/row['member'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(row['file'],dest)
  if dest.suffix=='.rrmaterial':shutil.copy2(dest,dest.with_suffix('.material'))
 stamp=target/(report['primary_stamp']+'.rdo');stamp.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(report['stamp_source'],stamp)
 tree=ET.parse(stamp)
 assert not any(p.get('Type')=='Object' and p.get('Value') is not None for p in tree.iter('DataProperty'))
 burn=target/'_default.burnproj';text=burn.read_text(encoding='utf-8-sig');assert text.count('</Rules>')==1
 include=(report['primary_stamp']+'.rdo').replace('/','\\')
 rule='<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true"/><Includes>'+include+'</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>'
 text=text.replace('</Rules>',rule+'</Rules>')
 # Compiled model/material aliases are Reflect validator dependencies only.
 # Burning them as author-source materials causes a native LoadMaterial failure.
 import re
 def restrict_rule(match):
  block=match.group();burner=re.search(r'<Burner>(.*?)</Burner>',block).group(1)
  includes=re.search(r'<Includes>(.*?)</Includes>',block,re.S).group(1)
  allow=burner in ['AttributeBurner','UCSBurner','LuaBurner'] or (burner=='ReflectBurner' and includes==include)
  return block if allow else block.replace('<IsEnabled>true</IsEnabled>','<IsEnabled>false</IsEnabled>')
 text=re.sub(r'<BurnRule>.*?</BurnRule>',restrict_rule,text,flags=re.S)
 burn.write_text(text,encoding='utf8')
 command=[str(CORE),'essence','build-mod','--editor','C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--mod',str(config),'--run-root',str(out/'stamp-native'),'--timeout','600']
 write(out/'prepared-stamp-command.json',command)
 print(json.dumps({'status':'assembled and staged; no native cook started','command':command},indent=2))
 return report
def finish_actual(kind):
 out=INT/kind;rows=records(kind);command=read(out/'prepared-stamp-command.json');run_root=Path(command[command.index('--run-root')+1]);run=run_root/'run.json';native=read(run)
 assert native['status']=='succeeded' and native['exit_code']==0
 archives=list((run_root/'output').rglob('*.sga'));assert len(archives)==1
 readback=out/'stamp-readback';unpack(archives[0],readback)
 report=finish_assembled(out,readback,run,rows)
 report['stamp_archive_sha256']=sha(archives[0].read_bytes())
 report['stamp_source_sha256']=sha(Path(report['stamp_source']).read_bytes())
 write(out/'media-manifest.json',report)
 print('ACTUAL_MEDIA_VERIFIED',kind,len(report['payloads']),flush=True)
 return report
if __name__=='__main__':
 stage,kind=sys.argv[1:];assert kind in KEYS
 assert stage in ['assemble','finish'];(assemble_actual if stage=='assemble' else finish_actual)(kind)
