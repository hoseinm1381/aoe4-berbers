"""Verify native AI RGDs and graft only those records onto pinned final 1.0.3."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,shutil,stat,subprocess,sys,zipfile
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'output/berber_update_1_0_4';WORK=OUT/'work'
BASE=ROOT/'output/berber_update_1_0_3/Berber_future_kingdom.sga'
BASE_ZIP=BASE.with_name('Berber-1.0.3.zip')
BASE_SHA='7f724f8f577e5f4214ea09e536433ee3742ea0d884c4e03893cd0287ff2e13dc'
BASE_ZIP_SHA='511c14c037b44bd3a749ee4b1b133c39ef70a56e19ba4b75300ec4110765ce72'
FINAL=OUT/'Berber_future_kingdom.sga';ZIP=OUT/'Berber-1.0.4.zip'
GM='scar/winconditions/berber_future_kingdom_gm.scar'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
TEST_COUNT=11
spec=importlib.util.spec_from_file_location('native_pipeline',ROOT/'research/berber0110/pipeline.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
sha=pipeline.sha;write=pipeline.write;run=pipeline.run;ARCH=pipeline.ARCH
sys.path.insert(0,str(pipeline.EXT));from garrison_shared import rgd

def mapping():return json.loads((HERE/'mapping.json').read_text())
def patch_sources():
 return {**{'attrib/'+str(p.relative_to(HERE/'source/attrib/instances')).replace('\\','/')[:-4]+'.rgd':HERE/'compiled-ai'/p.relative_to(HERE/'source/attrib/instances').with_suffix('.rgd') for p in (HERE/'source/attrib/instances').rglob('*.xml')},GM:HERE/GM}

def checks():
 result=subprocess.run([sys.executable,'-B',str(HERE/'test_native.py')],capture_output=True,text=True)
 (OUT/'mapping-tests.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
 m=mapping()
 for p,h in m['source_hashes'].items():assert sha(HERE/p)==h,('source drift',p)
 for p,h in m['reference_project_hashes'].items():assert sha(p)==h,('reference project changed',p)
 # Audit the actual exposed production/research lists, beyond the legacy catalog.
 with zipfile.ZipFile(HERE/'cook-reference-inputs.zip') as z:
  exposed=set();ability_owners={}
  for name in z.namelist():
   if not name.startswith('assets/attrib/instances/') or not name.endswith('.xml'):continue
   root=E.fromstring(z.read(name))
   for ext in root.iter('template_reference'):
    kind=ext.get('value','').rsplit('\\',1)[-1]
    if kind in ('spawner_ext','upgrade_ext'):
     exposed.update(n.get('value') for n in ext.iter('instance_reference') if n.get('value','').startswith(('sbps\\','upgrade\\')))
    if kind in ('ability_ext','squad_ability_ext'):
     for n in ext.iter('instance_reference'):
      if n.get('value','').startswith('abilities\\'):ability_owners.setdefault(n.get('value'),[]).append(name)
  econ=E.parse(HERE/'source/attrib/instances/ai/ai_economy/complete/default_economy.xml').getroot()
  coverage=[]
  for variant in [econ,*econ.findall('variant')]:
   bag=variant.find('group');refs={n.get('value').rsplit('\\',1)[-1] for n in bag.iter('instance_reference')}
   missing=[p for p in exposed if p.rsplit('\\',1)[-1] not in refs];assert not missing,(variant.get('name','default'),missing)
   coverage.append({'variant':variant.get('name','default'),'exposed_unit_upgrade_names':len(exposed),'missing':missing})
  abilities=[]
  for name in z.namelist():
   if not name.startswith('assets/attrib/instances/abilities/') or not name.endswith('.xml'):continue
   r=E.fromstring(z.read(name));path=name[len('assets/attrib/instances/'):-4].replace('/','\\')
   activation=r.find("group/enum[@name='activation']").get('value')
   if path not in ability_owners:classification='not exposed by local ability extensions'
   elif activation=='always_on':classification='automatic passive; no AI activation needed'
   elif path.endswith('civ_bonus_berber'):classification='civilization information UI; no gameplay activation needed'
   else:
    classification='native AI ability mapping'
    assert any(path==n.get('value') for p in (HERE/'source/attrib/instances/ai/ai_ability').glob('*.xml') for n in E.parse(p).getroot().iter('instance_reference')),(path,'missing active ability')
   abilities.append({'path':path,'activation':activation,'owners':ability_owners.get(path,[]),'classification':classification})
 # Follow packaged imports, starting from the actual shipped GM replacement.
 sources={str(p.relative_to(ROOT/'research/berber103')).replace('\\','/').lower():p for p in (ROOT/'research/berber103/scar').rglob('*.scar')};sources[GM]=HERE/GM
 visited=set();queue=[GM];imports=[]
 while queue:
  name=queue.pop()
  if name in visited:continue
  visited.add(name);text=sources[name].read_text(encoding='utf8')
  assert not re.search(r'\b(?:AI_Enable|AI_SetDifficulty|BerberAI\w*)\s*[.(]',text),('AI control reachable',name)
  for target in re.findall(r'\bimport\s*\(\s*[\"\']([^\"\']+)[\"\']\s*\)',text):
   target='scar/'+target.replace('\\','/').lower()
   if target in sources:queue.append(target);imports.append({'caller':name,'packaged':target})
 assert not any(n.startswith('scar/ai/') for n in visited)
 mcp=json.loads((OUT/'mcp-check.json').read_text());resolutions={}
 for name in mcp['unknown_calls']:
  definitions=[key for key in visited if re.search(r'\bfunction\s+'+re.escape(name)+r'\s*\(',sources[key].read_text(encoding='utf8'))]
  assert definitions,('unresolved MCP call',name);resolutions[name]=definitions
 write(OUT/'mcp-resolutions.json',{'status':'passed','unknown_calls_resolved_to_reachable_project_definitions':resolutions,'new_native_calls':[]})
 from lupa.lua53 import LuaRuntime
 lua=LuaRuntime(unpack_returned_tuples=True);compile=lua.eval('function(s,n) local f,e=load(s,n);return f~=nil,e end')
 for name in visited:
  ok,error=compile(sources[name].read_text(encoding='utf8'),name);assert ok,(name,error)
 before=(ROOT/'research/berber103'/GM).read_text(encoding='utf8');after=(HERE/GM).read_text(encoding='utf8')
 assert before.replace('import("ai/berber_ai_controller.scar")','-- Berber1.0.4: native AI owns computer players from match start.')==after
 write(OUT/'source-validation.json',{'status':'passed','mapping_tests':TEST_COUNT,'exposed_coverage':coverage,'custom_abilities':abilities,'reachable_packaged_scar':sorted(visited),'imports':imports,'unreachable_scripted_ai_preserved_for_rollback':True,'gm_change':'one controller import removed','source_hashes':m['source_hashes']})
 print('SOURCE_CHECKS_PASSED',len(visited),'reachable SCAR;',len(exposed),'exposed production/research references',flush=True)

def compiled():
 result=json.loads((OUT/'native-cook-result.json').read_text());assert result['exit_code']==0
 cooked=Path(result['run_root'])/'output/extension/Berber_future_kingdom/Berber_future_kingdom.sga'
 assert cooked.is_file()
 inventory=json.loads(run(ARCH,'list',cooked,'--verify'));assert inventory['archive']['verification']['verified']
 rows=[]
 for source_rel,h in mapping()['source_hashes'].items():
  source=HERE/source_rel;relative=source.relative_to(HERE/'source/attrib/instances').with_suffix('.rgd');member='attrib/'+relative.as_posix()
  dest=HERE/'compiled-ai'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
  raw=WORK/'compiled-inspection'/relative;raw.parent.mkdir(parents=True,exist_ok=True)
  assert raw.resolve().is_relative_to(WORK.resolve())
  if raw.exists():raw.unlink()
  run(ARCH,'extract-member',cooked,member,raw)
  if dest.exists():assert sha(dest)==sha(raw),'Retained compiled input changed; inspect before replacing'
  else:shutil.copyfile(raw,dest)
  document=rgd.read(dest.read_bytes());flat={p:n.value for p,n in rgd.flatten(document.nodes) if not isinstance(n.value,list)}
  root=E.parse(source).getroot();pbg=int(root.find('uniqueid').get('value'));assert flat['default/pbgid']==pbg
  custom={GUID+':'+n.get('value').rsplit('\\',1)[-1] for n in root.iter('instance_reference') if n.get('mod')==GUID}
  assert custom<=set(v for v in flat.values() if isinstance(v,str)),('compiled GUID references',member)
  if member.endswith('/default_economy.rgd'):
   for variant in [root,*root.findall('variant')]:
    v=variant.get('name','default');prefix=v+'/ai_economy_bag/production_groups/'
    actual={}
    for path,value in flat.items():
     if path.startswith(prefix) and path.endswith('/lua_binding'):
      parent=path[:-len('/lua_binding')];actual.setdefault(value,set()).update(v for p,v in flat.items() if p.startswith(parent+'/members/') and p.endswith('/$PBGNAME'))
    for group in variant.find("group/list[@name='production_groups']"):
     binding=group.find("string[@name='lua_binding']").get('value')
     for n in group.find("list[@name='members']"):
      if n.get('mod')==GUID:assert GUID+':'+n.get('value').rsplit('\\',1)[-1] in actual[binding],(v,binding,n.attrib)
  if member.endswith('/berber_alliances.rgd'):
   donor=rgd.read((HERE/'official/compiled/monastery_create_relic.rgd').read_bytes())
   official={p:n.value for p,n in rgd.flatten(donor.nodes) if not isinstance(n.value,list)}
   assert flat['default/ai_ability_bag/ability_type']==official['default/ai_ability_bag/ability_type']==1
   req=[v for p,v in flat.items() if '/tactic_filter_start_requirements/' in p and p.endswith('/is_present')];assert req==[False]*3
  if member.endswith('/berber_defensive_combat.rgd'):
   assert flat['default/ai_ability_bag/ability_type']==0
   assert flat['default/ai_ability_bag/tactic_info_default/tactic_info/class/tactic_Combat'] is True
  if member.endswith('/berber_tribal_tent.rgd'):assert GUID+':building_hut_ayy' in custom
  rows.append({'member':member,'sha256':sha(dest),'bytes':dest.stat().st_size,'source_sha256':h,'pbgid':pbg,'custom_reference_names':sorted(custom)})
 write(OUT/'compiled-validation.json',{'status':'passed','cook_exit_code':0,'cook_archive_sha256':sha(cooked),'cook_run_root':result['run_root'],'native_verification':inventory['archive']['verification'],'records':rows,'source_hashes':mapping()['source_hashes']})
 print('COMPILED_READBACK_PASSED',len(rows),'AI records',flush=True)

def compose():
 assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
 assert not FINAL.exists() and not ZIP.exists(),'Never overwrite an existing delivery'
 proof=json.loads((OUT/'compiled-validation.json').read_text());assert proof['status']=='passed' and proof['source_hashes']==mapping()['source_hashes']
 patches=patch_sources();expected={r['member']:r['sha256'] for r in proof['records']}
 for n,p in patches.items():
  if n!=GM:assert sha(p)==expected[n]
 WORK.mkdir(parents=True,exist_ok=True)
 listing=WORK/'set-members.txt';listing.write_text('\n'.join(n+'='+str(p.resolve()) for n,p in patches.items())+'\n')
 run(ARCH,'set-members',BASE,listing,FINAL,'--alias','data')
 inventory=json.loads(run(ARCH,'list',FINAL,'--verify'));assert inventory['archive']['verification']['verified'];write(OUT/'archive-inventory.json',inventory)
 baseline=json.loads((BASE.parent/'member-sha256-proof.json').read_text());assert baseline['archive_sha256']==BASE_SHA
 before=baseline['after'];after,method=pipeline.archive_hashes(FINAL,WORK/'final-readback',[r['path'] for r in inventory['members']])
 changed=sorted(n for n in before if n in after and before[n]!=after[n]);new=sorted(set(after)-set(before));removed=sorted(set(before)-set(after))
 assert changed==[GM] and new==sorted(set(patches)-{GM}) and not removed,(changed,new,removed)
 for n,p in patches.items():assert after[n]==sha(p)
 write(OUT/'member-sha256-proof.json',{'status':'passed','baseline_sha256':BASE_SHA,'archive_sha256':sha(FINAL),'before':before,'after':after,'changed_existing':changed,'new_members':new,'removed_members':removed,'unchanged_existing_members':len(before)-len(changed),'all_existing_art_audio_gameplay_tuning_22_uv_repairs_preserved':True,'method':method,'native_verification':inventory['archive']['verification']})
 print('ARCHIVE_VERIFIED',len(before)-len(changed),'unchanged;',len(new),'new AI;',len(changed),'changed GM',flush=True)

def package():
 proof=json.loads((OUT/'member-sha256-proof.json').read_text())
 assert proof['status']=='passed' and proof['archive_sha256']==sha(FINAL) and proof['baseline_sha256']==BASE_SHA
 notes=(HERE/'RELEASE_NOTES.md').read_bytes()
 with zipfile.ZipFile(BASE_ZIP) as z:
  assert z.testzip() is None
  files={n:z.read(n) for n in z.namelist() if n!='Berber_future_kingdom.sga' and not re.match(r'NATIVE_.*_ACCEPTANCE\.md$',n)}
 manifest=json.loads(files['garrison.json']);assert len(manifest['members'])==1
 manifest['members'][0]['sha256']=sha(FINAL)
 manifest['details'].update(version='1.0.4',updated='2026-10-19',summary='Native AI from match start, with Berber buildings, units, research and abilities mapped.',description='Berber Dynasty 1.0.4 native AI candidate. Removes scripted AI ownership and adds native tuning mappings. All delivered art, voices, music and player gameplay values preserved. Native acceptance pending.',changelog='Native AI owns computer players from initialization. Adds role-correct Berber production, research, landmark, Tribal Tent, alliance and defensive ability mappings. Removes custom controller import; preserves legacy sources for rollback.')
 files['garrison.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 for n in ('START-HERE.txt','RELEASE_NOTES.md'):files[n]=notes
 files['AI_CHANGES.md']=notes
 files['AI_BUILD_ORDER.md']=b'# Berber 1.0.4 native AI\n\nThe game AI owns economy, production, research, scouting and military orders from match initialization. There is no custom scripted build order, 15-second handoff or custom difficulty override. Native AI chooses its actions using the tuning mappings and the selected lobby difficulty. Actual Berber competence requires fresh native-match testing.\n'
 files['NATIVE_1_0_4_ACCEPTANCE.md']=(HERE/'NATIVE_ACCEPTANCE.md').read_bytes()
 with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.write(FINAL,'Berber_future_kingdom.sga')
  for n,raw in files.items():z.writestr(n,raw)
 hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()};hashes['Berber_future_kingdom.sga']=sha(FINAL)
 member_proof=json.loads((OUT/'member-sha256-proof.json').read_text())
 write(OUT/'release-validation.json',{'status':'candidate_native_acceptance_pending','version':'1.0.4','zip':str(ZIP),'zip_bytes':ZIP.stat().st_size,'zip_sha256':sha(ZIP),'sga_bytes':FINAL.stat().st_size,'sga_sha256':sha(FINAL),'zip_members':hashes,'mapping_tests':TEST_COUNT,'baseline_sha256':BASE_SHA,'changed_existing_members':member_proof['changed_existing'],'new_members':member_proof['new_members'],'unchanged_existing_members':member_proof['unchanged_existing_members'],'native_testing':'user will import and test; not performed'})
 (OUT/'RELEASE_NOTES.md').write_bytes(notes);(OUT/'NATIVE_ACCEPTANCE.md').write_bytes((HERE/'NATIVE_ACCEPTANCE.md').read_bytes())
 (OUT/'SHA256SUMS.txt').write_text(sha(ZIP)+'  '+ZIP.name+'\n'+sha(FINAL)+'  '+FINAL.name+'\n')
 verify()

def verify():
 assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
 r=json.loads((OUT/'release-validation.json').read_text());assert sha(FINAL)==r['sga_sha256'] and sha(ZIP)==r['zip_sha256']
 with zipfile.ZipFile(ZIP) as z:
  assert z.testzip() is None
  names=z.namelist();assert len(names)==len(set(names)) and set(names)==set(r['zip_members'])
  assert sum(Path(n).name.lower()=='garrison.json' for n in names)==1
  for n,h in r['zip_members'].items():
   with z.open(n) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==h,n
  manifest=json.loads(z.read('garrison.json'));assert manifest['details']['version']=='1.0.4'
  assert manifest['members'][0]['sha256']==r['sga_sha256'] and manifest['members'][0]['path']=='Berber_future_kingdom.sga'
  assert manifest['schema']=='garrison.mod/v1' and manifest['details']['updated']=='2026-10-19'
 for p,h in mapping()['reference_project_hashes'].items():assert sha(p)==h
 print('DELIVERY_VERIFIED',r['zip_sha256'],flush=True);return r

def cleanup():
 verify()
 target=WORK.resolve();expected=Path(r'F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\berber_update_1_0_4\work').resolve()
 assert target==expected and target.parent==OUT.resolve() and target.is_dir(),target
 rows=[]
 for parent,dirs,files in os.walk(target,followlinks=False):
  for name in dirs+files:
   p=Path(parent)/name;assert not (p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT),('reparse point',p)
  for name in files:
   p=Path(parent)/name;assert p.resolve().is_relative_to(target);rows.append({'path':str(p),'bytes':p.stat().st_size})
 # Retain compact logs and exact compiled records instead of complete cook trees.
 for folder in target.glob('native-cook*'):
  for p in (folder/'logs').glob('*.log'):
   raw=p.read_bytes();dest=OUT/'cook-evidence'/folder.name/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
   dest.write_bytes(raw if len(raw)<=250000 else raw[-250000:])
 protected=[p for p in HERE.rglob('*') if p.is_file()]+[BASE,BASE_ZIP,FINAL,ZIP]
 hashes={str(p.resolve()):sha(p) for p in protected};total=sum(r['bytes'] for r in rows)
 write(OUT/'cleanup-plan.json',{'status':'verified_targets','physical_target':str(target),'files':rows,'bytes_before':total,'protected_hashes':hashes,'dependency_review':'All 7 exact compiled AI RGDs, author XML, editor identities, official references, cook reference/media snapshots and frozen baseline retained. Final composition uses retained compiled records; recook restores snapshots. Shared caches, source bundles, art and audio are outside the target.'})
 shutil.rmtree(target);assert not target.exists()
 for p,h in hashes.items():assert sha(p)==h,('protected input changed',p)
 verify()
 write(OUT/'cleanup-report.json',{'status':'passed','bytes_before':total,'bytes_after':0,'bytes_reclaimed':total,'bytes_reclaimed_E':0,'bytes_reclaimed_F':total,'physical_target':str(target),'protected_inputs_rehashed':len(hashes),'temporary_cache_retained':0,'retained_inputs':'Final ZIP/SGA; final1.0.3 rollback; seven compiled AI records; author XML, official references, editor allocations, source/media snapshots, scripts/tests/notes. Shared caches untouched.'})
 print('CLEANUP_PASSED',total,flush=True)

if __name__=='__main__':
 action=sys.argv[1]
 if action=='checks':checks()
 elif action=='compiled':compiled()
 elif action=='build':checks();compiled();compose();package()
 elif action=='compose':checks();compose();package()
 elif action=='package':checks();package()
 elif action=='verify':verify()
 elif action=='cleanup':cleanup()
