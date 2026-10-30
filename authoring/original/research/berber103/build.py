"""Compose Berber1.0.3 as exactly3SCAR replacements on frozen1.0.2."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,shutil,subprocess,sys,zipfile,platform
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pipeline102',ROOT/'research/berber0110/pipeline.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
BASE=ROOT/'output/berber_update_1_0_2/Berber_future_kingdom.sga'
BASE_ZIP=BASE.parent/'Berber-1.0.2.zip'
BASE_SHA='80be99cae34dc1c5ce772c1a748c6a5f86d328597961373ba02662776d43723b'
BASE_ZIP_SHA='3c496646edb269fe6bb81948bb73ccc2b4328b72e32e32e047bcfec5aa54e2c9'
OUT=ROOT/'output/berber_update_1_0_3';WORK=OUT/'work'
FINAL=OUT/'Berber_future_kingdom.sga';ZIP=OUT/'Berber-1.0.3.zip'
PATCHES={n:SOURCE/n for n in ('scar/ai/berber_ai_engine.scar','scar/ai/berber_ai_economy.scar','scar/ai/berber_ai_controller.scar')}
sha=pipeline.sha;write=pipeline.write;run=pipeline.run

NOTES=(SOURCE/'RELEASE_NOTES.md').read_text(encoding='utf8')


def checks():
 import checks as suite
 from lupa.lua53 import LuaRuntime
 count=suite.run()
 files=sorted((SOURCE/'scar').rglob('*.scar'))
 lua=LuaRuntime(unpack_returned_tuples=True)
 compile=lua.eval('function(s,n) local f,e=load(s,n);return f~=nil,e end')
 for p in files:
  ok,error=compile(p.read_text(encoding='utf8'),str(p));assert ok,(p,error)
 write(OUT/'syntax-validation.json',{'status':'passed','files':len(files),'runtime':'Lua5.3 compile only'})
 p=subprocess.run([sys.executable,'-B','C:/Users/RS/.codex/skills/aoe4-game-mode-skill/scripts/validate_scar.py',*map(str,files),'--project-root',str(SOURCE/'scar'),'--json',str(OUT/'static-validation.json')],capture_output=True,text=True,encoding='utf8',errors='replace')
 (OUT/'static-validation.log').write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,p.stdout+p.stderr
 audit=json.loads((OUT/'function-audit.json').read_text());assert not audit['arity_review']
 assert len(audit['files'])==34
 for f in audit['files']:assert sha(SOURCE/f['file'])==f['sha256']
 assert all(i['resolution'] in ('packaged','official') for i in audit['imports'])
 mcp=json.loads((OUT/'mcp-checks.json').read_text(encoding='utf8'));assert len(mcp['files'])==3
 for row in mcp['files']:assert row['result']['status']=='ok' and not row['result']['missing_locdb_ids']
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
  'unchanged_existing_members':len(before)-len(PATCHES),'all_art_audio_tuning_22_uv_repairs_preserved':True,'method':method,
  'native_verification':inventory['archive']['verification']})

def package(count):
 with zipfile.ZipFile(BASE_ZIP) as z:
  assert z.testzip() is None
  files={n:z.read(n) for n in z.namelist() if n!='Berber_future_kingdom.sga'}
 manifest=json.loads(files['garrison.json']);manifest['members'][0]['sha256']=sha(FINAL)
 manifest['details'].update(version='1.0.3',summary='Fix animal gathering and add native AI fallback after more than 15 seconds without active gatherers.',
  description='Berber Dynasty1.0.3 repairs animal gathering and transfers stalled scripted economies permanently to native AI. All1.0.2 tuning, art and audio retained. Native-match candidate.',
  changelog='Uses squad commands for living animal deposits and retains edible corpses. A per-player watchdog enables native AI after more than 15 continuous seconds with no active gatherers, stops scripted orders, removes scripted income bonuses and survives restore. Native acceptance pending.')
 files.pop('NATIVE_1_0_2_ACCEPTANCE.md',None)
 files['garrison.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 for name in ('START-HERE.txt','RELEASE_NOTES.md'):files[name]=NOTES.encode()
 files['NATIVE_1_0_3_ACCEPTANCE.md']=NOTES.encode()
 with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(FINAL,'Berber_future_kingdom.sga')
  for n,raw in files.items():z.writestr(n,raw)
 hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()};hashes['Berber_future_kingdom.sga']=sha(FINAL)
 write(OUT/'release-validation.json',{'status':'candidate_native_acceptance_pending','version':'1.0.3','zip':str(ZIP),
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
  assert m['details']['version']=='1.0.3' and m['members'][0]['sha256']==r['sga_sha256']
  assert z.read('cover.png')==base.read('cover.png')
  for k in set(m)-{'details','members'}:assert m[k]==old[k]
 return r

def cleanup():
 r=verify();target=WORK.resolve();physical=OUT.resolve()
 assert physical==Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/berber_update_1_0_3')
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
  'rebuild':'Exact1.0.2 base+3retained source SCARs; no model/voice/music recook; native donor cache and source bundles untouched'})
 shutil.rmtree(target);assert not target.exists()
 for p,h in hashes.items():assert sha(p)==h
 verify();write(OUT/'cleanup-report.json',{'status':'passed','bytes_before':total,'bytes_after':0,'bytes_reclaimed':total,
  'drive':'F:','protected_inputs_rehashed':len(hashes),'temporary_cache_retained':0,'retained':'1.0.3 ZIP/SGA,1.0.2 rollback,patch/baseline sources/tests/recipes,all original art/audio inputs; shared caches unchanged'})
 print('CLEANUP_PASSED',total)

if __name__=='__main__':
 action=sys.argv[1]
 if action=='checks':checks()
 elif action=='build':count=checks();compose();package(count);print('PACKAGE_VERIFIED',sha(ZIP))
 elif action=='verify':print('DELIVERY_VERIFIED',verify()['zip_sha256'])
 elif action=='cleanup':cleanup()
