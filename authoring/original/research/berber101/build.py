"""Compose Berber1.0.1 as exactly3SCAR replacements on frozen1.0.0."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,shutil,subprocess,sys,zipfile,platform
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pipeline101',ROOT/'research/berber0110/pipeline.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
BASE=ROOT/'output/berber_update_1_0_0/Berber_future_kingdom.sga'
BASE_ZIP=BASE.parent/'Berber-1.0.0.zip'
BASE_SHA='a96adced078ff7a1d97a7e22e6980165f723a1551abb8794b9a016738c68d42a'
BASE_ZIP_SHA='86425e4746cd1bdcf1b4fb66e73de0b5148c60b853ca5fd72c35596e8e70da09'
OUT=ROOT/'output/berber_update_1_0_1';WORK=OUT/'work'
FINAL=OUT/'Berber_future_kingdom.sga';ZIP=OUT/'Berber-1.0.1.zip'
PATCHES={'scar/ai/berber_ai_military.scar':SOURCE/'ai/berber_ai_military.scar',
 'scar/units/saharan_trader.scar':SOURCE/'saharan_trader.scar',
 'scar/music/berber_music.scar':SOURCE/'music/berber_music.scar'}
sha=pipeline.sha;write=pipeline.write;run=pipeline.run

NOTES='''BERBER DYNASTY1.0.1 - fresh-match test candidate

Fixes the supplied AI observation failure: Entity BP did not have cost_ext.
Military observation now values valid squads through the official squad-cost
route, treats costless marker/decorative entities as zero, and counts a squad
only once. All other AI modules are inherited from final1.0.0.

Custom music defaults to25percent. The top-right Original button restores the
game's normal civilization music and becomes Berber. Click Berber to return to
the custom soundtrack at the retained gain and a legal random music entry.
Original music uses the normal game music-volume slider; custom +/- controls
are disabled while Original is selected. Unit voices keep their shared session.
No new songs were encoded; all145playback files remain byte-identical.

Saharan Traders now earn cumulative +0.08metres/second every30simulationseconds
of their own life, without a cap. Each is discovered within1second and starts
its own clock. After5minutes from discovery, +0.80m/s is earned (approximately
+0.20 on the displayed speed stat). New traders do not inherit earlier bonuses.
Owned total modifiers replace older totals, preventing duplicated grants on
repeated callbacks/restore. Conversion away removes this module's bonus.

Close AoE4, import Berber-1.0.1.zip in normal Garrison, enable and Play.
Select Berber Game Mode AND Tuning Pack; choose Malians for Berber.
Start a FRESH match, including the AI mix from the reported crash. Do not use
an old1.0.0 save to qualify the changed script. Final1.0.0 is the rollback.

Only3existingSCARs changed; no archive member added/removed. Art/audio/voices,
all22UVrepairs, tuning and remainingAI are byte-identical to final1.0.0.
No raw ContentEditor recook or installed game-file change was performed.

NATIVE ACCEPTANCE: verify multi-AI startup, trader cohorts at30/60/300seconds,
late-spawn traders, death/conversion, pause/speed, save/load and multiplayer.
Test Original/Berber toggle while peaceful/in combat/after age-up and after
restore, and check music/voice overlap and volume. Native resumes through the
official force-music/silence controls; actual playback/UI remain native gates.
Static/Lua/mock/native-archive/ZIP proof is not a new native match result.
'''

def checks():
 import checks as suite
 count=suite.run()
 args=[sys.executable,'-B','C:/Users/RS/.codex/skills/aoe4-game-mode-skill/scripts/validate_scar.py',
       *map(str,PATCHES.values()),'--project-root',str(SOURCE),'--json',str(OUT/'static-validation.json')]
 p=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace')
 (OUT/'static-validation.log').write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,p.stdout+p.stderr
 # Pin official signatures and wrapper definition locations for every call.
 api=Path('E:/Games/steamapps/common/Age of Empires IV/scardocs/api/Essence_ScarFunctions.api')
 signatures={}
 for i,line in enumerate(api.read_text(encoding='utf8').splitlines(),1):
  m=re.match(r'(\w+)\(',line)
  if m:signatures[m[1]]={'file':str(api),'line':i,'signature':line}
 for f in (pipeline.LIB/'scripts/scar').rglob('*.scar'):
  for i,line in enumerate(f.read_text(encoding='utf8',errors='replace').splitlines(),1):
   m=re.match(r'\s*function\s+(\w+)\s*\(',line)
   if m:signatures.setdefault(m[1],{'file':str(f),'line':i,'signature':line.strip()})
 text='\n'.join(p.read_text() for p in PATCHES.values());text=re.sub(r'--[^\n]*','',text)
 calls=set(re.findall(r'(?<![.\w])([A-Z]\w*)\s*\(',text))-set(re.findall(r'function\s+([A-Z]\w*)\s*\(',text))
 unresolved=sorted(calls-signatures.keys());assert not unresolved,unresolved
 write(OUT/'official-api-evidence.json',{'status':'passed','contracts':{n:signatures[n] for n in sorted(calls)},
  'analogue_squad_cost':'official gameplay/score.scar:248-250',
  'analogue_native_music':'official music.scar:133-161, force-music1second on resume',
  'modifier_handles':'official modifiers.scar:108-166; project Zenata_Lancer.scar:85-87',
  'unresolved':unresolved,'native_runtime':'pending'})
 return count

def compose():
 assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
 assert not FINAL.exists() and not ZIP.exists()
 old=json.loads((BASE.parent/'member-sha256-proof.json').read_text());assert old['archive_sha256']==BASE_SHA
 WORK.mkdir(parents=True,exist_ok=True)
 for member,source in PATCHES.items():
  assert sha(SOURCE/'baseline-source'/source.name)==old['after'][member]
  target=WORK/'payload'/member;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 listing=WORK/'set-members.txt';listing.write_text('\n'.join(n+'='+str((WORK/'payload'/n).resolve()) for n in PATCHES)+'\n')
 run(pipeline.ARCH,'set-members',BASE,listing,FINAL,'--alias','data')
 inventory=json.loads(run(pipeline.ARCH,'list',FINAL,'--verify'));assert inventory['archive']['verification']['verified']
 write(OUT/'archive-inventory.json',inventory)
 names=[m['path'] for m in inventory['members']]
 # Verified OS family avoids the known Python WMI-probe hang in this reader.
 assert os.name=='nt';platform.system=lambda:'Windows'
 after,method=pipeline.archive_hashes(FINAL,WORK/'readback',names)
 before=old['after'];assert set(before)==set(after)
 changed=sorted(n for n in before if before[n]!=after[n]);assert changed==sorted(PATCHES),changed
 for n,p in PATCHES.items():assert after[n]==sha(p)
 write(OUT/'member-sha256-proof.json',{'status':'passed','baseline_sha256':BASE_SHA,'archive_sha256':sha(FINAL),
  'before':before,'after':after,'changed_existing':changed,'new_members':[],'removed_members':[],
  'unchanged_existing_members':len(before)-3,'all_art_audio_tuning_22_uv_repairs_preserved':True,'method':method,
  'native_verification':inventory['archive']['verification']})

def package(count):
 with zipfile.ZipFile(BASE_ZIP) as z:
  assert z.testzip() is None
  files={n:z.read(n) for n in z.namelist() if n!='Berber_future_kingdom.sga'}
 manifest=json.loads(files['garrison.json']);manifest['members'][0]['sha256']=sha(FINAL)
 manifest['details'].update(version='1.0.1',summary='AI cost crash fix, cumulative individual trader speed,25% music and Original/Berber toggle.',
  description='Berber Dynasty with fixed AI observation, per-trader +0.08m/s per30seconds, all-age custom music and original-game music toggle. Fresh-match candidate.',
  changelog='Fixes arbitrary entity cost_ext crash and one-time trader bonus. Sets25percent music default and adds native/custom toggle. Models,22UVrepairs, voices and playback files unchanged.')
 files['garrison.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 for name in ('START-HERE.txt','RELEASE_NOTES.md'):files[name]=NOTES.encode()
 files['NATIVE_1_0_1_ACCEPTANCE.md']=NOTES.encode()
 with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(FINAL,'Berber_future_kingdom.sga')
  for n,raw in files.items():z.writestr(n,raw)
 hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()};hashes['Berber_future_kingdom.sga']=sha(FINAL)
 write(OUT/'release-validation.json',{'status':'candidate_native_acceptance_pending','version':'1.0.1','zip':str(ZIP),
  'zip_bytes':ZIP.stat().st_size,'zip_sha256':sha(ZIP),'sga_bytes':FINAL.stat().st_size,'sga_sha256':sha(FINAL),
  'zip_members':hashes,'tests':count,'baseline_sha256':BASE_SHA,'changed_existing_members':sorted(PATCHES),
  'unchanged_existing_members':8519,'native_gameplay_ui_music_save_multiplayer':'pending'})
 (OUT/'RELEASE_NOTES.md').write_text(NOTES,encoding='utf8')
 (OUT/'SHA256SUMS.txt').write_text(sha(ZIP)+'  '+ZIP.name+'\n'+sha(FINAL)+'  '+FINAL.name+'\n')
 verify()

def verify():
 assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
 r=json.loads((OUT/'release-validation.json').read_text());assert sha(FINAL)==r['sga_sha256'] and sha(ZIP)==r['zip_sha256']
 with zipfile.ZipFile(ZIP) as z,zipfile.ZipFile(BASE_ZIP) as base:
  assert z.testzip() is None
  assert set(z.namelist())==set(r['zip_members']) and len(z.namelist())==len(set(z.namelist()))
  for n,h in r['zip_members'].items():
   with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
  m=json.loads(z.read('garrison.json'));old=json.loads(base.read('garrison.json'))
  assert m['details']['version']=='1.0.1' and m['members'][0]['sha256']==r['sga_sha256']
  assert z.read('cover.png')==base.read('cover.png')
  for k in set(m)-{'details','members'}:assert m[k]==old[k]
 return r

def cleanup():
 r=verify();target=WORK.resolve();physical=OUT.resolve()
 assert physical==Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/berber_update_1_0_1')
 assert target==physical/'work'
 for p in (physical,target,*target.parents):assert not p.is_junction() and not p.is_symlink()
 rows=[]
 for folder,dirs,files in os.walk(target,followlinks=False):
  for n in dirs+files:
   p=Path(folder)/n;assert not p.lstat().st_file_attributes&0x400
   assert p.resolve().is_relative_to(target)
   if p.is_file():rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
 protect=[BASE,BASE_ZIP,FINAL,ZIP,*[p for p in SOURCE.rglob('*') if p.is_file()],
   *[p for p in (ROOT/'art/music_dark_age_20261018').rglob('*') if p.is_file()],
   *[p for p in (ROOT/'art/music_next_ages_20261018').rglob('*') if p.is_file()]]
 hashes={str(p):sha(p) for p in protect};total=sum(x['bytes'] for x in rows)
 write(OUT/'cleanup-plan.json',{'files':rows,'bytes_before':total,'protected_hashes':hashes,
  'rebuild':'Exact1.0.0 base+3retained source SCARs; no model/voice/music recook; native donor cache and source bundles untouched'})
 shutil.rmtree(target);assert not target.exists()
 for p,h in hashes.items():assert sha(p)==h
 verify();write(OUT/'cleanup-report.json',{'status':'passed','bytes_before':total,'bytes_after':0,'bytes_reclaimed':total,
  'drive':'F:','protected_inputs_rehashed':len(hashes),'temporary_cache_retained':0,'retained':'1.0.1 ZIP/SGA,1.0.0 rollback,patch/baseline sources/tests/recipes,all original art/audio inputs; shared caches unchanged'})
 print('CLEANUP_PASSED',total)

if __name__=='__main__':
 action=sys.argv[1]
 if action=='checks':checks()
 elif action=='build':count=checks();compose();package(count);print('PACKAGE_VERIFIED',sha(ZIP))
 elif action=='verify':print('DELIVERY_VERIFIED',verify()['zip_sha256'])
 elif action=='cleanup':cleanup()
