"""Private stock building remixes and house reduction over immutable 0.2.5."""
import os,sys,json,hashlib,subprocess,shutil,copy,struct,sqlite3,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/berber_update_0_2_6';INT=OUT/'integration'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path[:0]=[str(EXT),str(ROOT/'art/house_remix_0_2_2')]
from garrison_shared import rgd
from economy_025_native_stamp import NativeTree,decompile
from building_026_native_rebind import rebind
from build_berber_update_0_2_5 import semantics,encode,validate_stamp
from archive_contract import validate_house_namespaces
ARCH=EXT/'bin/sga-archiver.exe';CORE=EXT/'bin/core/garrison-core.exe'
OFFICIAL=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga');DATA=OFFICIAL.with_name('Data.sga')
KEY='b026';GUID='1d3145e8f1b2427f8bb0067851fcf0f1';PROJECT=INT/'l/Mods'/KEY;SOURCE=INT/'s';RUN=INT/'stamp-build'
BASE=ROOT/'output/berber_update_0_2_5/package/Berber_future_kingdom.sga';PRIOR=ROOT/'output/berber_update_0_2_5/final-readback'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def run(label,args,timeout=900):
 INT.mkdir(parents=True,exist_ok=True);p=INT/(label+'.log')
 with p.open('w',encoding='utf8') as f:r=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 assert r.returncode==0,(label,r.returncode,p)
 return p.read_text(encoding='utf8')
def fetch(member,archive=OFFICIAL):
 p=INT/'official'/member;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():run('extract-'+hashlib.sha1(member.encode()).hexdigest()[:12],[ARCH,'extract-member',archive,member,p])
 return p
def baseline():
 assert sha(BASE)=='91b486656ed4194cdbd366a96cb4f539800ecb0634e87e40bd49afcbe1cefc0d'
def specs():
 graph=read(INT/'actor-graph.json');bindings=[];stamps={}
 for a in graph:
  actor=a['actor'];kind=next(k for token,k in [('unit_infantry','barracks'),('unit_naval','dock'),('outpost','outpost'),('town_center','towncenter'),('econ_food','windmill')] if token in actor)
  for t in a['attachments']:
   leaf=t['leaf'];changes={}
   for _,v in t['strings']:
    v=v.replace('\\','/')
    if '/civ_mal/mal_barracks_age_' in v:donor=v.replace('/civ_mal/mal_barracks','/civ_abbasid/abb_barracks')
    elif '/civ_mal/mal_dock_age_' in v:donor=v.replace('/civ_mal/mal_dock','/civ_abbasid/abb_dock')
    elif '/civ_mal/mal_town_center_age_' in v:donor=v.replace('/civ_mal/mal_town_center','/civ_abbasid/abb_town_center')
    elif v in ['art/stamps/civ_abbasid/abb_outpost','art/stamps/civ_abbasid/abb_outpost_stone']:donor=v
    elif v=='art/stamps/garrison/berber_economy_025/mill':donor='art/stamps/civ_common/com_gristmill'
    else:continue
    name=kind+'_'+Path(donor).name;private=f'art/stamps/garrison/{KEY}/{name}'
    changes[v]=private;stamps[name]={'kind':kind,'donor':donor,'private':private}
   if changes:
    name=kind+'_'+leaf.split(':')[-1];item={'kind':kind,'name':name,'source':t['member'],'old_ref':leaf,'stamp_changes':changes,'actors':[actor]}
    previous=next((b for b in bindings if b['name']==name),None)
    if previous:previous['actors'].append(actor)
    else:bindings.append(item)
 return {'bindings':bindings,'stamps':stamps}
def prepare():
 baseline();d=specs();write(INT/'specs.json',d)
 if not (PROJECT/'mod-project.json').exists():run('create',[CORE,'mod-project','create','--library',INT/'l','--name',KEY])
 existing={r['name'] for r in read(PROJECT/'mod-project.json').get('derived_blueprints',[])}
 for b in d['bindings']:
  # Existing private 0.2.5 mill is replaced by a fresh clone of its official source.
  source=b['source'].removeprefix('attrib/').removesuffix('.rgd')
  if b['kind']=='windmill':source='attachments/attachment_lists/civilizations/malian/buildings/econ_food_mal/tier1_econ_food_control_mal'
  if b['name'] not in existing:run('derive-'+b['name'],[CORE,'mod-project','derive','--project',PROJECT,'--source',source,'--name',b['name']])
 print('PRIVATE_TIER_RECIPES_READY',len(d['bindings']))
def tiercook():
 run('tier-cook',[CORE,'mod-project','cook','--project',PROJECT,'--editor','C:/Users/RS/AppData/Local/Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe','--timeout','600'])
def source():
 baseline();d=read(INT/'specs.json');shutil.copytree(PROJECT/'project/source',SOURCE/'source',dirs_exist_ok=True)
 shutil.copy2(PROJECT/f'project/{KEY}.aoe4mod',SOURCE/'buildings.aoe4mod')
 burn=SOURCE/'source/_default.burnproj';text=burn.read_text();assert text.count('</Rules>')==1
 rule=''.join('<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true" /><Includes>art\\stamps\\garrison\\'+folder+'\\*.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true" /><Target>Archive</Target></BurnRule>' for folder in ['b026','berber_house_022'])
 burn.write_text(text.replace('</Rules>',rule+'</Rules>'))
 models={};reports=[]
 for kind in ['windmill','barracks','towncenter','outpost','dock']:
  author=read(OUT/'authors'/kind/'integration-manifest.json');assert author['status']=='passed'
  models.update(author['model_mapping'])
  for r in author['payloads']:
   assert sha(r['file'])==r['sha256'];dest=SOURCE/'source'/r['member'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r['file'],dest)
 db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True);deps=[]
 for name,s in d['stamps'].items():
  stock=fetch(s['donor']+'.bin',DATA);tree=NativeTree(stock)
  consumed={tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/') for o in tree.objects.values() if o['type']=='VisualStampBlueprint'}
  mapping={k:v for k,v in models.items() if k in consumed};assert mapping,(name,consumed)
  reports.append({**s,'name':name,'stock':str(stock),'mapping':mapping,'stock_sha256':sha(stock),'source_contract':'Native graph/terrain spline storage retained; reference dialect independently freshly cooked'})
  for o in tree.objects.values():
   if o['type']=='SplatStampBlueprint':
    stem='art/scenarios/textures/splats/'+tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/');suffixes=[('.rrmaterial','.material')]
   elif o['type']=='VisualStampBlueprint':
    stem=tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/')
    if stem in mapping:continue
    suffixes=[(s,s) for s in ['.rgo','.rgm','.rrmaterial','.rrgeom']]
   else:continue
   for suffix,alias in suffixes:
    member=stem+suffix;found=db.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(member,)).fetchall()
    if not found:assert suffix!='.rgo',(name,member);continue
    dest=SOURCE/'source'/(stem+alias);dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():run('dep-'+hashlib.sha1(member.encode()).hexdigest()[:12],[ARCH,'extract-member',found[0][0],member,dest])
    deps.append({'member':member,'archive':found[0][0],'alias':str(dest),'sha256':sha(dest),'package':'native reference only; staged validator aliases excluded'})
 db.close()
 # Native terrain StripStamp splines contain typed value/float arrays which
 # the earlier economic RDO emitter did not qualify. Keep their exact binary
 # storage and cook private reference probes from the already qualified mill
 # schema instead of reconstructing or dropping any native terrain machinery.
 probe_stock=ROOT/'output/berber_update_0_2_5/integration/stock/art/stamps/civ_mal/mal_gristmill.bin'
 probe_tree=NativeTree(probe_stock);probe_model=next(probe_tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/') for o in probe_tree.objects.values() if o['type']=='VisualStampBlueprint' and 'mal_gristmill_control' in probe_tree.field(o,o['fields']['m_blueprint'])['text'])
 for i,private in enumerate(sorted(set(models.values()))):
  xml=ET.fromstring(decompile(probe_tree,{probe_model:private}));ids={n.get('Id'):str(int.from_bytes(hashlib.sha256((private+':'+n.get('Id')).encode()).digest()[:8],'little')) for n in xml.iter('DataObject')}
  for n in xml.iter():
   for a in ['Id','OwnerId']:
    if n.get(a) in ids:n.set(a,ids[n.get(a)])
   if n.tag=='DataValue' and n.text in ids:n.text=ids[n.text]
   if n.tag=='DataProperty' and n.get('Name')=='m_objectID' and n.get('Value') in ids:n.set('Value',ids[n.get('Value')])
  target=SOURCE/f'source/art/stamps/garrison/{KEY}/probe_{i:02}.rdo';target.parent.mkdir(parents=True,exist_ok=True);ET.indent(xml);target.write_bytes(ET.tostring(xml,encoding='utf8'))
 for o in probe_tree.objects.values():
  if o['type']=='SplatStampBlueprint':
   stem='art/scenarios/textures/splats/'+probe_tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/');member=stem+'.rrmaterial';dest=SOURCE/'source'/(stem+'.material')
   if not dest.exists():
    db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True);archive=db.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(member,)).fetchone()[0];db.close();dest.parent.mkdir(parents=True,exist_ok=True);run('probe-dep',[ARCH,'extract-member',archive,member,dest])
 # Existing private house model definitions are validation inputs, not recooked payload.
 for p in (PRIOR/'art').rglob('*'):
  if p.is_file() and p.suffix in ['.rgo','.rgm','.rrgeom','.rrmaterial'] and 'house' in str(p).lower():
   target=SOURCE/'source'/p.relative_to(PRIOR);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 houses=[]
 for age in range(1,5):
  old=ROOT/f'output/berber_update_0_2_4/stamp-source/source/art/stamps/garrison/berber_house_022/house_age{age}.rdo';doc=ET.parse(old)
  scale=next(n for n in doc.iter('DataProperty') if n.get('Name')=='m_scale');values=[n for n in scale.iter('DataProperty') if n.get('Name') in ['x','y','z']];assert len(values)==3
  for n in values:assert abs(float(n.get('Value'))-1.38)<1e-7;n.set('Value','1.104')
  dest=SOURCE/f'source/art/stamps/garrison/berber_house_022/house_age{age}.rdo';dest.parent.mkdir(parents=True,exist_ok=True);doc.write(dest,encoding='utf8')
  houses.append({'age':age,'source_sha256':sha(dest),'scale':1.104,'ratio':.8})
 write(INT/'stamp-source.json',reports);write(INT/'stock-cook-dependencies.json',deps);write(INT/'house-source.json',houses)
 print('ASSEMBLY_AND_HOUSE_SOURCE_READY',len(reports))
def stampcook():run('stamp-cook',[CORE,'essence','build-mod','--editor','E:/Games/steamapps/common/Age of Empires IV/EssenceEditor.exe','--mod',SOURCE/'buildings.aoe4mod','--run-root',RUN,'--timeout','600'])
def compose():
 baseline();assert read(RUN/'run.json')['status']=='succeeded';archives=list((RUN/'output').rglob('*.sga'));assert len(archives)==1
 fresh=INT/'stamp-readback';run('unpack-stamps',[ARCH,'unpack',archives[0],'--output',fresh])
 tiercook=read(PROJECT/'mod-project.json')['cooks'][-1];assert not tiercook['live_reload'] and sha(tiercook['archive'])==tiercook['sha256'];tiers=INT/'tier-readback';run('unpack-tiers',[ARCH,'unpack',tiercook['archive'],'--output',tiers])
 report={'status':'running','payloads':[],'actors':[],'stamps':[],'attachments':[]}
 def save(member,data):
  p=INT/'payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);report['payloads'].append({'member':member,'file':str(p),'sha256':sha(p)})
 for kind in ['windmill','barracks','towncenter','outpost','dock']:
  for r in read(OUT/'authors'/kind/'integration-manifest.json')['payloads']:assert sha(r['file'])==r['sha256'];save(r['member'],Path(r['file']).read_bytes())
 key_table={}
 for p in (fresh/f'art/stamps/garrison/{KEY}').glob('probe_*.bin'):
  t=NativeTree(p)
  for o in t.objects.values():
   if o['type']!='VisualStampBlueprint':continue
   f=o['fields']['m_blueprint'];v=t.field(o,f)
   if '/scenario/garrison/' in v['text'].replace('\\','/'):key_table[v['text']]={**v,'kind':f.get('FieldTypeName')}
 assert len(key_table)==len({v for k in ['windmill','barracks','towncenter','outpost','dock'] for v in read(OUT/'authors'/k/'integration-manifest.json')['model_mapping'].values()})
 write(INT/'fresh-native-reference-table.json',key_table)
 for s in read(INT/'stamp-source.json'):
  member=s['private']+'.bin';data,encoding=rebind(NativeTree(s['stock']),s['mapping'],key_table);target=INT/'encoded-stamps'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  proof=validate_stamp(s['stock'],target,s['mapping']);report['stamps'].append({**s,**proof,'encoding':encoding});save(member,data)
 d=read(INT/'specs.json');actors={}
 for b in d['bindings']:
  source=PRIOR/b['source']
  if not source.exists():source=fetch(b['source'])
  doc=rgd.read(source.read_bytes());old=copy.deepcopy(doc);private=f'attrib/attachments/attachment_lists/garrison/{KEY}/{b["name"]}.rgd'
  identity=rgd.find(rgd.read((tiers/private).read_bytes()).nodes,'default/pbgid').value;changed=[]
  for path,n in rgd.flatten(doc.nodes):
   if n.key=='pbgid':n.value=identity
   elif n.kind=='CString' and n.key=='stamp' and n.value.replace('\\','/') in b['stamp_changes']:
    before=n.value;n.value=b['stamp_changes'][before.replace('\\','/')].replace('/','\\');changed.append((path,before,n.value))
  assert changed,b
  restored=copy.deepcopy(doc)
  for path,n in rgd.flatten(restored.nodes):
   if n.key=='pbgid':n.value=rgd.find(old.nodes,path).value
   for p,v,w in changed:
    if p==path:n.value=v
  assert semantics(restored.nodes)==semantics(old.nodes)
  save(private,encode(doc));report['attachments'].append({**b,'private':private,'pbgid':identity,'changes':changed})
  for member in b['actors']:
   if member not in actors:actors[member]=rgd.read((PRIOR/member).read_bytes())
   count=0
   for path,n in rgd.flatten(actors[member].nodes):
    if n.kind=='CString' and n.key=='$PBGNAME' and n.value==b['old_ref'] and ('/attachments/' in path or '/animator_attachments/' in path):n.value=GUID+':'+b['name'];count+=1
   assert count>0,(member,b)
 for member,doc in actors.items():
  original=rgd.read((PRIOR/member).read_bytes());restored=copy.deepcopy(doc);changed=[]
  for path,n in rgd.flatten(restored.nodes):
   if n.kind=='CString' and n.value.startswith(GUID+':'):
    binding=next((b for b in d['bindings'] if n.value==GUID+':'+b['name']),None)
    if binding:changed.append(path);n.value=binding['old_ref']
  assert semantics(restored.nodes)==semantics(original.nodes);save(member,encode(doc));report['actors'].append({'member':member,'visual_reference_fields':changed,'all_other_fields':'identical'})
 for age in range(1,5):
  member=f'art/stamps/garrison/berber_house_022/house_age{age}.bin';old=NativeTree(PRIOR/member);new=NativeTree(fresh/member);assert set(old.objects)==set(new.objects)
  edits=[];expected_memory=bytearray(old.memory.payload)
  for oid,o in old.objects.items():
   n=new.objects[oid];assert o['type']==n['type']
   assert (n['type_id'],n['offset'],n['owner'])==(o['type_id'],o['offset'],o['owner'])
   for name,f in o['fields'].items():
    size=int(f.get('BaseSize'));a=old.bytes(o['offset']+int(f.get('Offset')),size);b=new.bytes(n['offset']+int(f.get('Offset')),size)
    if name=='m_scale' and a!=b:
     assert all(abs(v-1.38)<1e-6 for v in struct.unpack('<3f',a));assert all(abs(v-1.104)<1e-6 for v in struct.unpack('<3f',b));edits.append(oid)
     at=o['offset']+int(f.get('Offset'))-old.memory.payload_offset;expected_memory[at:at+size]=b
  assert bytes(expected_memory)==new.memory.payload
  for tag,c in old.chunks.items():
   if tag!=b'RFCI':assert c.payload==new.chunks[tag].payload,(age,tag)
  assert len(edits)==1;save(member,(fresh/member).read_bytes())
 assert len(report['payloads'])==len({r['member'] for r in report['payloads']});report.update(status='passed',stamp_cook=str(archives[0]),stamp_cook_sha256=sha(archives[0]),tier_cook=tiercook);write(INT/'bindings-report.json',report);print('ALL_BINDINGS_COMPOSED',len(report['payloads']))
def archive():
 baseline();bindings=read(INT/'bindings-report.json');assert bindings['status']=='passed'
 allowed={r['member'] for r in bindings['payloads']};mid=INT/'media-candidate.sga';final=INT/'candidate/Berber_future_kingdom.sga';final.parent.mkdir(parents=True,exist_ok=True)
 for alias,prefix in [('data','art/'),('attrib','attrib/')]:
  rows=[r for r in bindings['payloads'] if r['member'].startswith(prefix)]
  for r in rows:assert sha(r['file'])==r['sha256']
  (INT/(alias+'-members.txt')).write_text('\n'.join(r['member']+'='+r['file'] for r in rows)+'\n')
 run('set-media',[ARCH,'set-members',BASE,INT/'data-members.txt',mid,'--alias','data'])
 run('set-attrib',[ARCH,'set-members',mid,INT/'attrib-members.txt',final,'--alias','attrib'])
 old=json.loads(run('baseline-inventory',[ARCH,'list',BASE,'--verify']));new=json.loads(run('candidate-inventory',[ARCH,'list',final,'--verify']))
 assert new['archive']['verification']['verified'];assert new['archive']['name'].replace('-','').lower()==GUID;validate_house_namespaces(new)
 before={r['path']:r for r in old['members']};after={r['path']:r for r in new['members']};assert set(after)==set(before)|allowed
 fresh=OUT/'final-readback';run('unpack-candidate',[ARCH,'unpack',final,'--output',fresh]);changed=[];unchanged=[]
 for member,r in before.items():
  assert after[member]['toc']==r['toc'],member
  if sha(fresh/member)==sha(PRIOR/member):unchanged.append(member)
  else:assert member in allowed;changed.append(member)
 expected={r['member'] for r in bindings['actors']}|{f'art/stamps/garrison/berber_house_022/house_age{age}.bin' for age in range(1,5)}
 assert set(changed)==expected,(changed,expected)
 for r in bindings['payloads']:
  member=r['member'];assert sha(fresh/member)==r['sha256'];assert after[member]['toc']==('attrib' if member.startswith('attrib/') else 'data')
  if member.endswith('.rgd'):
   decoded=OUT/'readback-bindings'/Path(member).with_suffix('.xml');decoded.parent.mkdir(parents=True,exist_ok=True);run('decode-'+Path(member).stem,[ARCH,'decode-rgd',fresh/member,decoded])
 for s in read(INT/'stamp-source.json'):validate_stamp(s['stock'],fresh/(s['private']+'.bin'),s['mapping'])
 evidence={'version':'0.2.6','status':'candidate archive and decoded binding verification passed; review gates pending','archive':str(final),'archive_sha256':sha(final),'project_guid':GUID,'baseline_sha256':sha(BASE),'baseline_unchanged_members':len(unchanged),'changed_existing_members':sorted(changed),'new_members':sorted(set(after)-set(before)),'member_count':len(after),'native_acceptance':'pending user game test','house_linear_ratio':.8,'house_stamp_scale':1.104,'geometry_route':'Fresh native known-span geometry encoding retaining opaque stock state/motion data; not a generic ModelBurner geometry rebuild.','stamp_route':'Family stamps newly encoded from complete native graphs retaining terrain splines and state storage. Private reference fixtures and reduced house stamps freshly cooked; private attribute identities and material textures separately freshly cooked.','unchanged':'lumber camp mining camp Tribal Tent Tuareg gameplay SCAR audio and every member outside explicit allowlist byte-identical','known_limits':['Stock construction/wreck auxiliary stamps, ground decals and resource outskirts retained.','Blender layered material preview approximates native shader; decoded collection fragments are not a native healthy selector pose.','Native two-colour states animation gameplay and pathing acceptance pending user test.']}
 write(INT/'candidate-evidence.json',evidence);print('CANDIDATE_ARCHIVE_VERIFIED',len(after),len(unchanged))
def package():
 for kind in ['windmill','barracks','towncenter','outpost','dock']:assert read(OUT/'reviews'/f'{kind}.json')['status']=='approved',kind
 assert read(OUT/'reviews/final-package.json')['status']=='approved'
 evidence=read(INT/'candidate-evidence.json');candidate=Path(evidence['archive']);assert sha(candidate)==evidence['archive_sha256'];baseline()
 folder=OUT/'package';folder.mkdir(exist_ok=True);final=folder/'Berber_future_kingdom.sga';shutil.copy2(candidate,final)
 manifest=read(ROOT/'output/berber_update_0_2_5/package/garrison.json');manifest['members'][0]['sha256']=sha(final)
 manifest['details'].update(version='0.2.6',updated='2026-10-14',summary='Berber barracks, outpost, Town Center, dock and redesigned windmill; house size reduced20%',description='Stock-derived native building remixes retaining state machinery and dynamic owner colour. Existing lumber/mining camps and gameplay preserved.',changelog='Moderate stock building geometry and material remixes; mill replaced by moving-sail Berber windmill; house stamp scale1.38 to1.104.')
 write(folder/'garrison.json',manifest);evidence.update(status='independent building and final archive reviews approved; package verified; native acceptance pending',archive=str(final));write(folder/'EVIDENCE.json',evidence)
 (folder/'INSTALL_AND_TEST.txt').write_text('''BERBER0.2.6
Close AoE4. Import berber_future_kingdom-0.2.6.zip through Garrison, confirm0.2.6 and launch.
Fresh match: Tuning Pack The Berber Dynasties; Game Mode Berber Civilization; Civilization Malians.
Check barracks/outpost/Town Center/dock/windmill in every reachable age and upgrade, existing and newly built structures, construction/completion/cancel/damage/destruction/selection, close/far views and two player colours.
Check barracks training/rally; outpost garrison/weapon upgrades; starting/capital and additional Town Centers production/garrison/drop-off; dock coastline placement/ship spawning/rally/fishing drop-off; mill food drop-off/economic technologies and moving sails.
House is80% previous linear dimensions for all four ages. Footprint/pathfinding unchanged. Check ground contact and villagers beside houses/buildings.
Recheck unchanged lumber/mining resource drop-off, Tribal Tent and Tuareg. Native acceptance pending this test; stock auxiliary construction/wreck/decals/outskirts retained.
Geometry and full family stamps are newly encoded native known spans; stock skeleton/selectors/terrain splines preserved. Fresh materials, private binding identities, private reference fixtures and reduced house stamp cooks verified separately. Decoded source views include native construction fragments and do not establish the healthy game pose.
Report building/age/upgrade/playercolour/existing-or-new/screenshots and warnings.log if problems occur.
Rollback: close AoE4 and reimport retained0.2.5 ZIP.
''',encoding='utf8')
 shutil.copy2(INT/'bindings-report.json',folder/'bindings-report.json');(folder/'reviews').mkdir(exist_ok=True)
 for kind in ['windmill','barracks','towncenter','outpost','dock','final-package']:
  shutil.copy2(OUT/'reviews'/(kind+'.json'),folder/'reviews'/(kind+'.json'))
  notes=OUT/'reviews'/(kind+'-notes.md')
  if notes.exists():shutil.copy2(notes,folder/'reviews'/notes.name)
 for kind in ['windmill','barracks','towncenter','outpost','dock']:shutil.copy2(OUT/'authors'/kind/'integration-manifest.json',folder/(kind+'-evidence.json'))
 target=OUT/'berber_future_kingdom-0.2.6.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(folder.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(folder).as_posix())
 with zipfile.ZipFile(target) as z:assert z.testzip() is None;assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
 evidence.update(zip=str(target),zip_sha256=sha(target));write(OUT/'delivery.json',evidence);print('BERBER_026_VERIFIED_ZIP_READY',target)
if __name__=='__main__':globals()[sys.argv[1]]()
