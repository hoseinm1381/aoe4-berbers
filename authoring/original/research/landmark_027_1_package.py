"""Package a SCAR-only landmark preload fix over verified0.2.7; preserve every media byte."""
import hashlib,json,os,shutil,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_7_1';BASE=ROOT/'output/berber_update_0_2_7/package/Berber_future_kingdom.sga';BASE_SHA='bbc965d9797c37e79aa95626bca1a83eb17874945671d9bd0b8ca463076c3b91'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison';ARCH=EXT/'bin/sga-archiver.exe'
MEMBERS=['scar/winconditions/berber_future_kingdom_gm.scar','scar/buildings/berber_landmark_visual_precache.scar']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args):return subprocess.run(list(map(str,args)),capture_output=True,text=True,check=True).stdout
def write(p,o):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(o,indent=2),encoding='utf8')
def compose():
 assert sha(BASE)==BASE_SHA
 native=json.loads((OUT/'precache-native/run.json').read_text());assert native['status']=='succeeded' and native['exit_code']==0
 cooks=list((OUT/'precache-native/output').rglob('*.sga'));assert len(cooks)==1
 cooked=json.loads(run([ARCH,'list',cooks[0],'--verify']));assert cooked['archive']['verification']['verified'];assert {m['path'].lower() for m in cooked['members']}=={m.lower() for m in MEMBERS}; cooked_names={m['path'].lower():m['path'] for m in cooked['members']}
 before=json.loads(run([ARCH,'list',BASE,'--verify']));readback=OUT/'readback';rows=[]
 for m in MEMBERS:
  p=OUT/'cooked-source'/m;p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists():run([ARCH,'extract-member',cooks[0],cooked_names[m.lower()],p])
  assert p.read_bytes()==(ROOT/'assets'/m).read_bytes();rows.append({'member':m,'file':str(p),'sha256':sha(p)})
 manifest=OUT/'source-members.txt';manifest.write_text('\n'.join(r['member']+'='+r['file'] for r in rows)+'\n')
 package=OUT/'package';package.mkdir(exist_ok=True);final=package/'Berber_future_kingdom.sga'
 if not final.exists():run([ARCH,'set-members',BASE,manifest,final,'--alias','data'])
 after=json.loads(run([ARCH,'list',final,'--verify']));assert after['archive']['verification']['verified'];assert after['archive']['name']==before['archive']['name']
 old={m['path']:m for m in before['members']};new={m['path']:m for m in after['members']};assert set(new)==set(old)|set(MEMBERS)
 run([ARCH,'unpack',BASE,'--output',readback/'baseline']);run([ARCH,'unpack',final,'--output',readback/'final'])
 changed=[];unchanged=[]
 for m in old:
  assert old[m]['toc']==new[m]['toc']
  if sha(readback/'baseline'/m)==sha(readback/'final'/m):unchanged.append(m)
  else:changed.append(m)
 assert changed==[MEMBERS[0]] or set(changed)=={MEMBERS[0]};assert len(unchanged)==722
 for r in rows:assert sha(readback/'final'/r['member'])==r['sha256'] and new[r['member']]['toc']=='data'
 original=(readback/'baseline'/MEMBERS[0]).read_bytes();actual=(readback/'final'/MEMBERS[0]).read_bytes();line=b'import("buildings/berber_landmark_visual_precache.scar")\r\n';assert actual.count(line)==1 and actual.replace(line,b'')==original
 evidence={'status':'fresh SCAR cook and integrated archive verified; independent review/native game retest pending','version':'0.2.7.1','cause':'Native placeholder explicitly states model has not been precached; packaged027 game mode did not register either new landmark for prematch resource loading.','fix':'One helper imported by the existing game mode queues both actual landmark EBPS with Scar_PrecachePrematchResource from a Scar_AddInit loading hook.','baseline_sha256':BASE_SHA,'archive_sha256':sha(final),'fresh_cook_sha256':sha(cooks[0]),'fresh_cook':native,'live_reload':False,'project_guid':'1d3145e8f1b2427f8bb0067851fcf0f1','member_count':len(new),'baseline_unchanged_members':len(unchanged),'changed_existing_members':changed,'new_members':sorted(set(new)-set(old)),'source_members':rows,'all_models_materials_textures_bindings_gameplay_byte_identical':True,'discarded_hypothesis':'Material-name shortening probe is excluded. Original027 media remain byte-identical.','registration':'Scar_AddInit, before loading completes, as current official rogue.scar21-28 and Garrison getting_started.scar22-28.','native_acceptance':'Pending user fresh-match retest; queued REQUESTED log is not native completion acknowledgement.'}
 write(OUT/'fix-evidence.json',evidence);print('SCAR_ONLY_ARCHIVE_VERIFIED',len(new),len(unchanged))
def package():
 review=json.loads((OUT/'reviews/precache-fix.json').read_text());assert review['source_and_archive_approved'] is True
 e=json.loads((OUT/'fix-evidence.json').read_text());p=OUT/'package';assert sha(p/'Berber_future_kingdom.sga')==e['archive_sha256']
 g=json.loads((ROOT/'output/berber_update_0_2_7/package/garrison.json').read_text());g['details'].update(version='0.2.7.1',updated='2026-10-15',summary='Berber landmark preload fix',description='Explicit prematch preload for both Feudal landmark visual families. All0.2.7models, material media, bindings and gameplay remain byte-identical.',changelog='Queue Ribat of the Sanhaja and Funduq of Sijilmasa during match loading to prevent the not-precached placeholder.')
 g['members'][0]['sha256']=e['archive_sha256'];write(p/'garrison.json',g);write(p/'EVIDENCE.json',e)
 (p/'INSTALL_AND_TEST.txt').write_text('''BERBER0.2.7.1 - landmark precache fix
1. Close Age of Empires IV completely before importing the new ZIP in Garrison; enable the updated Berber package.
2. Start a NEW match: Tuning Pack The Berber Dynasties; Game Mode Berber Civilization; Civilization Malians.
3. Build Ribat of the Sanhaja. Check placement preview, construction and completed model; the pink not-precached cube should disappear. Also retest Funduq, both player colours and AgesII-IV, damage/wrecks and landmark functions.
4. The game log should contain BERBER_LANDMARK_PRECACHE_REQUESTED for both landmark blueprint names. This proves the request was queued; visible models in game establish rendering acceptance. PRECACHE_UNAVAILABLE means the companion tuning pack/blueprint was unavailable during loading.
All models/media/bindings and gameplay from0.2.7 are unchanged. Native lower-LOD switching remains unsupported; full-detail nativeLOD0 retained.
Rollback: close the game and reimport retained0.2.7 ZIP. Native fix acceptance remains pending your fresh-match test.
''',encoding='utf8')
 shutil.copy2(OUT/'reviews/precache-fix.json',p/'review.json')
 zpath=OUT/'berber_future_kingdom-0.2.7.1.zip'
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(p.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(p).as_posix())
 with zipfile.ZipFile(zpath) as z:
  assert z.testzip() is None;assert hashlib.sha256(z.read('Berber_future_kingdom.sga')).hexdigest()==e['archive_sha256'];assert {'garrison.json','INSTALL_AND_TEST.txt','EVIDENCE.json','review.json'}<=set(z.namelist())
 e.update(zip=str(zpath),zip_sha256=sha(zpath),status='release ZIP verified; native fix acceptance and mandatory cleanup pending');write(OUT/'delivery.json',e);print('PRELOAD_FIX_ZIP_VERIFIED',zpath)
if __name__=='__main__':globals()[__import__('sys').argv[1]]()
