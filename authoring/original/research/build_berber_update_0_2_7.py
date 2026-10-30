"""Reviewable 0.2.7 landmark integration; native cooks invoked only by root.

Usage: prepare | cook KIND LOD | cook-family KIND | compose | archive | package.
Media admission consumes integration/KIND/media-manifest.json from the qualified
landmark export helper. Cook caches/readbacks are regenerable and not rebuild inputs.
"""
import copy, hashlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/berber_update_0_2_7'; INT=OUT/'integration'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path[:0]=[str(EXT),str(ROOT/'research'),str(ROOT/'art/house_remix_0_2_2')]
from garrison_shared import rgd
from build_berber_update_0_2_5 import semantics,encode
from archive_contract import validate_house_namespaces
ARCH=EXT/'bin/sga-archiver.exe'; CORE=EXT/'bin/core/garrison-core.exe'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
BASE=ROOT/'output/berber_update_0_2_6/package/Berber_future_kingdom.sga'
BASE_SHA='cf9c73bdc0a64c655525f943f7e7b4ddfd1338124216ec7bf75eb331614f8123'
ART=ROOT/'art/landmarks_0_2_7'
SPECS={
 'ribat':{'key':'br027_ribat','actor':'attrib/ebps/races/malian/buildings/landmarks/ribat_of_sanhaja/building_landmark_age1_landmarka_mal.rgd','tier':'attachments/attachment_lists/civilizations/malian/buildings/mal_landmark_b_02','old_ref':'mal_landmark_b_02','old_stamp':'art/stamps/civ_mal/mal_landmark_b_age_02'},
 'funduq':{'key':'bf027_funduq','actor':'attrib/ebps/races/malian/buildings/landmarks/funduq/building_landmark_age1_landmarkb_mal.rgd','tier':'attachments/attachment_lists/civilizations/abbasid/buildings/tech_unit_ranged_abb/tier3_tech_unit_ranged_control_abb','old_ref':'tier3_tech_unit_ranged_control_abb','old_stamp':'art/stamps/civ_abbasid/abb_arsenal_03'}}
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def run(label,args,timeout=900):
 INT.mkdir(parents=True,exist_ok=True);log=INT/(label+'.log')
 with log.open('w',encoding='utf8') as f:r=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 assert r.returncode==0,(label,r.returncode,str(log))
 return log.read_text(encoding='utf8')
def baseline():assert sha(BASE)==BASE_SHA

def project(kind):return INT/'library/Mods'/SPECS[kind]['key']
def fetch(member,official=False):
 archive=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga') if official else BASE
 p=INT/'stock'/member;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():run('extract-'+hashlib.sha1(member.encode()).hexdigest()[:12],[ARCH,'extract-member',archive,member,p])
 return p

def prepare():
 baseline();write(INT/'specs.json',SPECS)
 for kind,spec in SPECS.items():
  p=project(kind)
  if not (p/'mod-project.json').exists():run('create-'+kind,[CORE,'mod-project','create','--library',INT/'library','--name',spec['key']])
  run('settings-'+kind,[CORE,'mod-project','settings','--project',p,'--live-reload','off','--mod-id','1d3145e8-f1b2-427f-8bb0-067851fcf0f1'])
  record=read(p/'mod-project.json');names={r['name'] for r in record.get('derived_blueprints',[])}
  if kind+'_tier' not in names:run('derive-'+kind,[CORE,'mod-project','derive','--project',p,'--source',spec['tier'],'--name',kind+'_tier'])
  run('derive-stamp-'+kind,[CORE,'mod-project','derive-change','--project',p,'--name',kind+'_tier','--field','attachment_lists/attachment_lists/attachment_list/attachment_list/stamp_attachment/stamp','--value','art\\stamps\\garrison\\'+spec['key']+'\\'+kind+'_lod0'])
 print('PRIVATE_LANDMARK_PROJECTS_PREPARED',flush=True)

def cook(kind,lod):
 baseline();assert kind in SPECS;lod=int(lod);assert lod in range(3)
 source=ART/kind/('export_lod'+str(lod));assert (source/'building.json').exists(),source
 partrows=read(source/'building.json')['parts'];assert partrows and all('first_stage' in r for r in partrows)
 p=project(kind);prior_count=len(read(p/'mod-project.json').get('cooks',[]))
 run('building-'+kind+'-'+str(lod),[CORE,'mod-project','building','--project',p,'--source',source,'--name',kind+'_lod'+str(lod),'--profile','english-house','--integration','script'])
 run('cook-'+kind+'-'+str(lod),[CORE,'mod-project','cook','--project',p,'--editor','C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--timeout','600'])
 record=read(p/'mod-project.json');assert len(record['cooks'])>prior_count,'cook did not append a fresh record';c=record['cooks'][-1]
 assert not c['live_reload'];assert sha(c['archive'])==c['sha256'];dest=INT/kind/('cook-lod'+str(lod)+'.json');write(dest,{**c,'source':str(source),'source_files_sha256':{str(f.relative_to(source)):sha(f) for f in source.rglob('*') if f.is_file()}})
 print('FRESH_LANDMARK_COOK',kind,lod,c['sha256'],flush=True)

def cook_family(kind):
 """Cook all three distinct source LOD recipes once, with fresh source evidence."""
 baseline();assert kind in SPECS
 p=project(kind);prior_count=len(read(p/'mod-project.json').get('cooks',[]));sources=[]
 for lod in range(3):
  source=ART/kind/('export_lod'+str(lod));assert (source/'building.json').exists(),source
  rows=read(source/'building.json')['parts'];assert rows and all('first_stage' in r for r in rows)
  sources.append(source)
  run('building-'+kind+'-'+str(lod),[CORE,'mod-project','building','--project',p,'--source',source,'--name',kind+'_lod'+str(lod),'--profile','english-house','--integration','script'])
 run('cook-family-'+kind,[CORE,'mod-project','cook','--project',p,'--editor','C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--timeout','600'])
 record=read(p/'mod-project.json');assert len(record['cooks'])>prior_count
 c=record['cooks'][-1];assert not c['live_reload'] and sha(c['archive'])==c['sha256']
 for lod,source in enumerate(sources):
  write(INT/kind/('cook-lod'+str(lod)+'.json'),{**c,'source':str(source),'source_files_sha256':{str(f.relative_to(source)):sha(f) for f in source.rglob('*') if f.is_file()}})
 print('FRESH_LANDMARK_FAMILY_COOK',kind,c['sha256'],flush=True)

def compose():
 baseline();report={'status':'running','payloads':[],'actors':[],'attachments':[],'media':[]}
 def save(member,data):
  assert member.startswith(('attrib/','art/')),member
  p=INT/'payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  report['payloads'].append({'member':member,'file':str(p),'sha256':sha(p)})
 for kind,s in SPECS.items():
  # Helper produces freshly cooked private stamps/flag, exact native LOD0 geometry,
  # actual native lifecycle RGO and verified construction/damage RGM selectors.
  media=read(INT/kind/'media-manifest.json');assert media['status']=='passed'
  required=['fresh_cooks_verified','authored_lods_three','native_geometry_collection_contract_preserved','construction_visibility_verified','dynamic_owner_colour_preserved','native_graph_preserved','dependencies_resolved']
  assert all(media.get(k) is True for k in required),(kind,media)
  assert media['native_lod_count']==1 and media['native_declared_lod_count']==1
  assert media['geometry_mode']=='native-compatible-single' and media['lod_count_three'] is False
  for row in media['payloads']:
   assert sha(row['file'])==row['sha256'];assert row['member'].startswith('art/')
   assert row['member'].startswith(('art/scenario/garrison/'+s['key']+'/', 'art/stamps/garrison/'+s['key']+'/')),row['member']
   save(row['member'],Path(row['file']).read_bytes())
  report['media'].append(media)
  newstamp=media['primary_stamp'].removesuffix('.bin');assert newstamp+'.bin' in {r['member'] for r in media['payloads']}
  cookrow=read(INT/kind/'cook-lod2.json');assert sha(cookrow['archive'])==cookrow['sha256'];assert not cookrow['live_reload']
  private='attrib/attachments/attachment_lists/garrison/'+s['key']+'/'+kind+'_tier.rgd'
  fresh=INT/kind/('private-tier-'+cookrow['sha256'][:16]+'.rgd');fresh.parent.mkdir(parents=True,exist_ok=True)
  if not fresh.exists():run('tier-readback-'+kind,[ARCH,'extract-member',cookrow['archive'],private,fresh])
  identity=rgd.find(rgd.read(fresh.read_bytes()).nodes,'default/pbgid').value
  old=rgd.read(fetch('attrib/'+s['tier']+'.rgd',official=True).read_bytes());doc=copy.deepcopy(old);changes=[]
  for path,n in rgd.flatten(doc.nodes):
   if n.key=='pbgid':n.value=identity
   elif n.kind=='CString' and n.key=='stamp' and n.value.replace('\\','/')==s['old_stamp']:
    before=n.value;n.value=newstamp.replace('/','\\');changes.append((path,before,n.value))
  assert changes,(kind,'no original principal stamp refs')
  restored=copy.deepcopy(doc)
  for path,n in rgd.flatten(restored.nodes):
   if n.key=='pbgid':n.value=rgd.find(old.nodes,path).value
   for k,v,_ in changes:
    if path==k:n.value=v
  assert semantics(restored.nodes)==semantics(old.nodes)
  save(private,encode(doc));report['attachments'].append({'member':private,'pbgid':identity,'changes':changes,'retained_auxiliary_refs':True})
  actor=rgd.read(fetch(s['actor']).read_bytes());original=copy.deepcopy(actor);achanges=[]
  for path,n in rgd.flatten(actor.nodes):
   if n.kind=='CString' and n.key=='$PBGNAME' and n.value==s['old_ref'] and '/attachments/' in path:
    n.value=GUID+':'+kind+'_tier';achanges.append(path)
  assert len(achanges)==1,(kind,achanges)
  restored=copy.deepcopy(actor)
  for path in achanges:rgd.find(restored.nodes,path).value=s['old_ref']
  assert semantics(restored.nodes)==semantics(original.nodes)
  save(s['actor'],encode(actor));report['actors'].append({'member':s['actor'],'visual_reference_fields':achanges,'all_other_fields':'byte-semantic identical including schema footprint and animator_scale'})
 assert len(report['payloads'])==len({r['member'] for r in report['payloads']});report['status']='passed';write(INT/'bindings-report.json',report)
 write(INT/'allowlist.json',{'existing':[s['actor'] for s in SPECS.values()],'all':[r['member'] for r in report['payloads']]})
 print('LANDMARK_BINDINGS_COMPOSED',len(report['payloads']),flush=True)

def archive():
 baseline();b=read(INT/'bindings-report.json');assert b['status']=='passed';allowed={r['member'] for r in b['payloads']}
 final=INT/'candidate/Berber_future_kingdom.sga';final.parent.mkdir(parents=True,exist_ok=True);mid=INT/'media-candidate.sga'
 for alias,prefix in [('data','art/'),('attrib','attrib/')]:
  rows=[r for r in b['payloads'] if r['member'].startswith(prefix)];assert rows
  for r in rows:assert sha(r['file'])==r['sha256']
  (INT/(alias+'-members.txt')).write_text('\n'.join(r['member']+'='+r['file'] for r in rows)+'\n')
 run('set-data',[ARCH,'set-members',BASE,INT/'data-members.txt',mid,'--alias','data']);run('set-attrib',[ARCH,'set-members',mid,INT/'attrib-members.txt',final,'--alias','attrib'])
 before=json.loads(run('baseline-list',[ARCH,'list',BASE,'--verify']));after=json.loads(run('candidate-list',[ARCH,'list',final,'--verify']))
 assert after['archive']['verification']['verified'];assert after['archive']['name'].replace('-','').lower()==GUID;validate_house_namespaces(after)
 old={r['path']:r for r in before['members']};new={r['path']:r for r in after['members']};assert set(new)==set(old)|allowed
 basefiles=INT/'baseline-readback';candidate=INT/'candidate-readback'
 run('unpack-baseline',[ARCH,'unpack',BASE,'--output',basefiles]);run('unpack-candidate',[ARCH,'unpack',final,'--output',candidate])
 changed=[];unchanged=[]
 for m,r in old.items():
  assert r['toc']==new[m]['toc'],m
  if sha(basefiles/m)==sha(candidate/m):unchanged.append(m)
  else:assert m in allowed;changed.append(m)
 assert set(changed)=={s['actor'] for s in SPECS.values()},changed
 for row in b['payloads']:
  m=row['member'];assert sha(candidate/m)==row['sha256'];assert new[m]['toc']==('attrib' if m.startswith('attrib/') else 'data')
  if m.endswith('.rgd'):
   dest=INT/'decoded-bindings'/Path(m).with_suffix('.xml');dest.parent.mkdir(parents=True,exist_ok=True);run('decode-'+hashlib.sha1(m.encode()).hexdigest()[:12],[ARCH,'decode-rgd',candidate/m,dest])
 evidence={'status':'candidate verified; independent reviews pending','version':'0.2.7','archive':str(final),'archive_sha256':sha(final),'baseline_sha256':BASE_SHA,'project_guid':GUID,'baseline_unchanged_members':len(unchanged),'changed_existing_members':changed,'new_members':sorted(set(new)-set(old)),'member_count':len(new),'native_acceptance':'pending user game test','gameplay':'all nonvisual actor fields preserved; all other baseline members byte-identical','known_limits':['Historical reconstructions rather than replicas.','Native-compatible full-detail LOD0 only: repaired authored LOD1/2 retained; native lower-LOD switching unsupported.','Four obsolete decorative Funduq furnace-smoke actions omitted; native functional markers and lifecycle retained.','Native two-owner appearance motion pathfinding construction transitions remain pending game test.','Custom intact principal persists under damage; retained native effects and auxiliary wreck/scaffolding visuals.']}
 write(INT/'candidate-evidence.json',evidence);print('LANDMARK_ARCHIVE_VERIFIED',len(new),flush=True)

def package():
 for kind in ['ribat','funduq','final-package']:assert read(OUT/'reviews'/(kind+'.json'))['status']=='approved',kind
 e=read(INT/'candidate-evidence.json');source=Path(e['archive']);assert sha(source)==e['archive_sha256'];baseline()
 folder=OUT/'package';folder.mkdir(exist_ok=True);final=folder/'Berber_future_kingdom.sga';shutil.copy2(source,final)
 manifest=read(ROOT/'output/berber_update_0_2_6/package/garrison.json');manifest['members'][0]['sha256']=sha(final)
 manifest['details'].update(version='0.2.7',updated='2026-10-14',summary='New historical Berber Feudal landmarks: Ribat of the Sanhaja and Funduq of Sijilmasa.',description='Original fortified ribat and caravanserai models, native owner-colour flags, explicit construction stages and native-compatible full-detail geometry. Three editable source LODs are included separately; native lower-LOD switching is unsupported. Existing gameplay and accepted assets preserved.',changelog='Replace two Feudal landmark visuals with original historical reconstructions.')
 write(folder/'garrison.json',manifest);e.update(archive=str(final),status='release verified; native acceptance pending',cleanup='Final mandatory cleanup result is recorded in the adjacent release cleanup-report.json after ZIP verification.');write(folder/'EVIDENCE.json',e)
 (folder/'INSTALL_AND_TEST.txt').write_text('''BERBER 0.2.7\nClose AoE4. Import berber_future_kingdom-0.2.7.zip through Garrison. Fresh match: Tuning Pack The Berber Dynasties, Game Mode Berber Civilization, Civilization Malians.\nTest both Feudal landmark choices: construction/completion/cancel, healthy appearance Ages II-IV, existing/new buildings, two player colours, near/far appearance, damage/destruction, selection, villager movement. Test ribat training/rally and Funduq resource drop-off/influence and all existing technologies.\nRegression-check accepted house, barracks/outpost/Town Center/dock/windmill sail motion, lumber/mining camps, Tribal Tent and Tuareg.\nBoth designs are historical reconstructions, not replicas. Native acceptance pending these game tests. Native stock damage/fire, auxiliary wreck/scaffold visuals retained; intact custom architecture persists in damage states.\nRuntime uses exact freshly compiled LOD0 geometry and per-triangle collections. Reduced native LOD switching is unsupported; repaired LOD1/LOD2 sources are retained for future export work. Four obsolete Funduq furnace-smoke actions are omitted; stock lifecycle actions and functional markers remain.\nRollback: close AoE4 and reimport preserved 0.2.6 ZIP.\n''',encoding='utf8')
 shutil.copy2(INT/'bindings-report.json',folder/'bindings-report.json');shutil.copy2(OUT/'inventory/compact-manifest.json',folder/'donor-provenance.json')
 for kind in ['ribat','funduq','final-package']:
  target=folder/'reviews'/(kind+'.json');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(OUT/'reviews'/(kind+'.json'),target)
 target=OUT/'berber_future_kingdom-0.2.7.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(folder.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(folder).as_posix())
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None;assert {'garrison.json','Berber_future_kingdom.sga','INSTALL_AND_TEST.txt','EVIDENCE.json'}<=set(z.namelist());assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
 e.update(zip=str(target),zip_sha256=sha(target));write(OUT/'delivery.json',e);print('LANDMARK_027_ZIP_VERIFIED_CLEANUP_REQUIRED',target,flush=True)
if __name__=='__main__':
 stage=sys.argv[1]
 if stage=='cook':cook(*sys.argv[2:])
 elif stage=='cook-family':cook_family(sys.argv[2])
 else:assert stage in ['prepare','compose','archive','package'];globals()[stage]()
