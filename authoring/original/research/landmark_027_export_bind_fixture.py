"""Fresh private reflected landmark stamps, then actual baseline actor bindings."""
import os,sys,json,shutil,subprocess,hashlib,xml.etree.ElementTree as ET,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7/qualification'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';CORE=EXT/'bin/core/garrison-core.exe';ARCH=EXT/'bin/sga-archiver.exe'
options=argparse.ArgumentParser();options.add_argument('--prepare-only',action='store_true');options.add_argument('--finish-only',action='store_true');options.add_argument('--run-root',default=str(OUT/'reflect-native-v3'));args=options.parse_args()
SOURCE=OUT/'reflect-source';PROJECT=OUT/'l/Mods/lf027';BASE=ROOT/'output/berber_update_0_2_6/package/Berber_future_kingdom.sga';NATIVE=Path(args.run_root)
def run(label,args):
 with (OUT/(label+'.log')).open('w',encoding='utf8') as f:r=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=900)
 assert r.returncode==0,(label,r.returncode)
 print(label,'passed',flush=True)
if not args.finish_only:
 shutil.copytree(PROJECT/'project/source',SOURCE/'source',dirs_exist_ok=True)
 shutil.copy2(PROJECT/'project/lf027.aoe4mod',SOURCE/'fixture.aoe4mod')
 # Keep three independently-cooked canonical sources. The earlier cap trial is not reused.
 for lod in range(3):shutil.copy2(OUT/f'lod{lod}-source/model.fbx',SOURCE/f'source/art/scenario/garrison/lf027/buildings/fixture_lod{lod}/model.fbx')
 reports=[]
 for kind in ['ribat','funduq']:
  report=json.loads((OUT/kind/'media-manifest.json').read_text());reports.append(report)
  for p in report['payloads']:
   assert hashlib.sha256(Path(p['file']).read_bytes()).hexdigest()==p['sha256']
   dest=SOURCE/'source'/p['member'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p['file'],dest)
   if dest.suffix=='.rrmaterial':shutil.copy2(dest,dest.with_suffix('.material'))
  dest=SOURCE/'source'/(report['primary_stamp']+'.rdo');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(report['stamp_source'],dest)
  doc=ET.parse(dest)
  assert not any(p.get('Type')=='Object' and p.get('Value') is not None for p in doc.iter('DataProperty'))
 burn=SOURCE/'source/_default.burnproj';text=burn.read_text(encoding='utf-8-sig');assert text.count('</Rules>')==1
 rule='<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true"/><Includes>art\\stamps\\garrison\\lf027\\ribat.rdo;art\\stamps\\garrison\\lf027\\funduq.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>'
 burn.write_text(text.replace('</Rules>',rule+'</Rules>'),encoding='utf8')
 command=[str(CORE),'essence','build-mod','--editor','C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--mod',str(SOURCE/'fixture.aoe4mod'),'--run-root',str(NATIVE),'--timeout','600']
 (OUT/'prepared-reflect-command.json').write_text(json.dumps(command,indent=2))
 if args.prepare_only:print(json.dumps({'status':'prepared; no Editor started','command':command},indent=2));sys.exit(0)
 run('private-binding-reflect-cook',command)
assert json.loads((NATIVE/'run.json').read_text())['status']=='succeeded'
archives=list((NATIVE/'output').rglob('*.sga'));assert len(archives)==1
run('private-binding-stamp-readback',[ARCH,'unpack',archives[0],'--output',OUT/'reflect-readback'])
# Use the freshly generated private original-category tier identities. Change only stamp strings.
sys.path.insert(0,str(EXT));sys.path.insert(0,str(ROOT/'research'))
from garrison_shared import rgd
from build_berber_update_0_2_5 import semantics,encode
payload=OUT/'binding-payload';bindings=[]
guid='1d3145e8f1b2427f8bb0067851fcf0f1'
for kind,relative in [('ribat','ribat_of_sanhaja/building_landmark_age1_landmarka_mal'),('funduq','funduq/building_landmark_age1_landmarkb_mal')]:
 tier_member=f'attrib/attachments/attachment_lists/garrison/lf027/qual_{kind}.rgd'
 tier_source=OUT/'independent-lod-readback'/tier_member
 parsed=rgd.read(tier_source.read_bytes());before=semantics(parsed.nodes);changes=[]
 for path,n in rgd.flatten(parsed.nodes):
  if n.kind=='CString' and n.value==r'art\stamps\garrison\lf027\fixture_lod0':n.value=f'art\\stamps\\garrison\\lf027\\{kind}';changes.append(path)
 data=encode(parsed);dst=payload/tier_member;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
 actor_member='attrib/ebps/races/malian/buildings/landmarks/'+relative+'.rgd';actor=OUT/'baseline-bindings'/actor_member;actor.parent.mkdir(parents=True,exist_ok=True)
 run('baseline-actor-'+kind,[ARCH,'extract-member',BASE,actor_member,actor])
 old=rgd.read(actor.read_bytes());allowed=[]
 expected={'ribat':r'attachments\attachment_lists\civilizations\malian\buildings\mal_landmark_b_02','funduq':r'attachments\attachment_lists\civilizations\abbasid\buildings\tech_unit_ranged_abb\tier3_tech_unit_ranged_control_abb'}[kind]
 for path,n in rgd.flatten(old.nodes):
  if n.kind=='CString' and n.key=='$PBGNAME' and n.value in [expected,expected.rsplit('\\',1)[-1]] and '/attachments/' in path:n.value=guid+':qual_'+kind;allowed.append(path)
 new=payload/actor_member;new.parent.mkdir(parents=True,exist_ok=True);new.write_bytes(encode(old))
 assert changes and allowed
 bindings.append({'kind':kind,'tier_member':tier_member,'tier_strings_changed':changes,'actor_member':actor_member,'actor_strings_changed':allowed,'schema_and_core_animator':'unchanged','native_runtime':'pending'})
(OUT/'binding-fixture-evidence.json').write_text(json.dumps({'status':'fresh stamp cook passed; private baseline bindings encoded and decoded readback pending','bindings':bindings,'stamp_cook':json.loads((NATIVE/'run.json').read_text()),'stamp_archive_sha256':hashlib.sha256(archives[0].read_bytes()).hexdigest()},indent=2))
