"""Allowlisted native economic building remixes; preserve accepted 0.2.4."""
import copy,hashlib,json,os,shutil,sqlite3,struct,subprocess,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/berber_update_0_2_5';OUT.mkdir(exist_ok=True)
INT=OUT/'integration';INT.mkdir(exist_ok=True)
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT));sys.path.insert(0,str(ROOT/'art/house_remix_0_2_2'))
from garrison_shared import rgd,model_variants as mv
from archive_contract import validate_house_namespaces
from economy_025_native_stamp import NativeTree,decompile,clone_id
ARCH=EXT/'bin/sga-archiver.exe';CORE=EXT/'bin/core/garrison-core.exe'
KEY='berber_economy_025';GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
LIB=INT/'library';PROJECT=LIB/'Mods'/KEY;STAMP_SOURCE=INT/'stamp-source'
STAMP_RUN=INT/'stamp-build-v5'
OFFICIAL=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
FAMILIES={
 'mill':{'actor':'building_econ_food_mal','tier':'civilizations/malian/buildings/econ_food_mal/tier1_econ_food_control_mal','stamp':'civ_mal/mal_gristmill'},
 'lumber':{'actor':'building_econ_wood_mal','tier':'civilizations/english/buildings/econ_wood_eng/tier1_econ_wood_control_eng','stamp':'civ_common/com_lumber_camp'},
 'mining':{'actor':'building_econ_mining_camp_mal','tier':'civilizations/english/buildings/econ_mining_camp_eng/tier1_econ_mining_camp_control_eng','stamp':'civ_common/com_mining_camp'}}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def run(label,args,timeout=600):
 p=INT/(label+'.log')
 with p.open('w',encoding='utf-8') as f:r=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 assert r.returncode==0,(label,r.returncode,p)
 return p.read_text(encoding='utf-8')
def baseline():
 d=read(ROOT/'output/berber_update_0_2_4/delivery.json');p=Path(d['archive'])
 assert sha(p)==d['archive_sha256']=='3246e2bbe002502ffb087c49af5ac83ffde75c4b956c918fe99881ac80d771c3'
 return p
def mapping(kind):
 p=OUT/'authors'/kind/'integration-manifest.json'
 if p.exists():return read(p)['model_mapping']
 recipe=read(ROOT/f'art/economy_remix_0_2_5/{kind}/recipe.json')
 return {str(Path(m['source']).with_suffix('')).replace('\\','/'):mv.art_stem(recipe['key'],m['name']).replace('\\','/') for m in recipe['models'] if kind!='mining' or m['name']=='combined'}
def source():
 baseline()
 if not (PROJECT/'mod-project.json').exists():run('create-project',[CORE,'mod-project','create','--library',LIB,'--name',KEY])
 record=read(PROJECT/'mod-project.json');names={r['name'] for r in record.get('derived_blueprints',[])}
 for kind,f in FAMILIES.items():
  if kind+'_tier' not in names:run('derive-'+kind,[CORE,'mod-project','derive','--project',PROJECT,'--source','attachments/attachment_lists/'+f['tier'],'--name',kind+'_tier'])
 shutil.copytree(PROJECT/'project/source',STAMP_SOURCE/'source',dirs_exist_ok=True)
 shutil.copy2(PROJECT/f'project/{KEY}.aoe4mod',STAMP_SOURCE/'economic_stamps.aoe4mod')
 burn=STAMP_SOURCE/'source/_default.burnproj';text=burn.read_text(encoding='utf-8')
 assert text.count('</Rules>')==1
 rule=f'<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true" /><Includes>art\\stamps\\garrison\\{KEY}\\*.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true" /><Target>Archive</Target></BurnRule>'
 burn.write_text(text.replace('</Rules>',rule+'</Rules>'),encoding='utf-8')
 report=[]
 for kind,f in FAMILIES.items():
  p=INT/'stock/art/stamps'/Path(f['stamp']+'.bin');tree=NativeTree(p);maps=mapping(kind)
  consumed={tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/') for o in tree.objects.values() if o['type']=='VisualStampBlueprint'}
  assert set(maps)<=consumed,(kind,set(maps)-consumed)
  data=decompile(tree,maps);target=STAMP_SOURCE/f'source/art/stamps/garrison/{KEY}/{kind}.rdo';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  report.append({'building':kind,'stock':str(p),'stock_sha256':sha(p),'source':str(target),'source_sha256':sha(target),'mapping':maps,'native_objects':len(tree.objects),'unchanged_assembly_scale':True})
 write(INT/'stamp-source.json',{'status':'passed','stamps':report})
 print('PRIVATE_STAMP_SOURCE_READY',flush=True)
def semantics(doc):return [(n.key,n.hash,n.kind,semantics(n.value) if isinstance(n.value,list) else n.value) for n in doc]
def encode(doc):
 keys={h:k for h,k in doc.keys}
 for _,n in rgd.flatten(doc.nodes):
  if n.key is not None:keys[n.hash]=n.key
 doc.keys=list(keys.items());b=rgd.write(doc);assert semantics(rgd.read(b).nodes)==semantics(doc.nodes);return b
def validate_stamp(old,new,maps):
 """Compare every original reflected field, including pointer-array ordering."""
 a=NativeTree(old);b=NativeTree(new);changed=[]
 for oid,o in a.objects.items():
  new_id=oid if oid in b.objects else clone_id(a,oid)
  n=b.objects[new_id];assert o['type']==n['type']
  assert n['owner']==(0 if not o['owner'] else o['owner'] if new_id==oid else clone_id(a,o['owner']))
  for name,f in o['fields'].items():
   g=n['fields'][name];kind=f.get('FieldTypeName');assert kind==g.get('FieldTypeName')
   if kind in ['util::ReflectString<StdTraits>','Reflect::ReflectStringHash']:
    v=a.field(o,f)['text'];w=b.field(n,g)['text'];expected=maps.get(v.replace('\\','/'),v).replace('/','\\') if name=='m_blueprint' else v
    assert w==expected,(oid,name,v,w,expected)
    if w!=v:changed.append({'object':oid,'from':v,'to':w})
   elif kind.startswith('util::ReflectArray<'):
    va=a.field(o,f);vb=b.field(n,g);assert va['count']==vb['count']
    if kind!='util::ReflectArray<IStampBlueprint *,StdTraits>':
     element=kind[len('util::ReflectArray<'):].rsplit(',StdTraits>',1)[0]
     types=[t for t in a.types.values() if t.get('Name')==element];assert len(types)==1,(kind,element)
     size=int(types[0].get('Size'));assert a.bytes(va['data_address'],va['count']*size)==b.bytes(vb['data_address'],vb['count']*size),(oid,name)
     continue
    def children(t,v):
     result=[]
     for i in range(v['count']):
      slot=v['data_address']+i*8;dest=slot+struct.unpack('<q',t.bytes(slot,8))[0]
      matches=[x['id'] for x in t.objects.values() if x['offset']==dest and x['type'].endswith('StampBlueprint')];assert len(matches)==1;result+=matches
     return result
    ca=children(a,va);cb=children(b,vb)
    assert ([clone_id(a,x) for x in ca] if new_id!=oid else ca)==cb
   else:
    size=int(f.get('BaseSize'));av=a.bytes(o['offset']+int(f.get('Offset')),size);bv=b.bytes(n['offset']+int(g.get('Offset')),size)
    if name=='m_objectID' and new_id!=oid:assert struct.unpack('<Q',bv)[0]==new_id
    else:assert av==bv,(oid,o['type'],name,av.hex(),bv.hex())
 assert len(changed)==len(maps),(old,changed,maps)
 return {'status':'passed','original_objects':len(a.objects),'native_fields':'byte-preserved except deterministic private object identities and mapped model paths','object_graph_and_array_order':'preserved','model_changes':changed}
def stage_media():
 rows=[]
 for kind in FAMILIES:
  d=read(OUT/'authors'/kind/'integration-manifest.json');assert d['status']=='passed'
  assert d['model_mapping']==mapping(kind)
  for p in d['payloads']:
   assert sha(p['file'])==p['sha256'];dest=STAMP_SOURCE/'source'/p['member'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p['file'],dest)
  rows.append({'building':kind,'cook':d['cook'],'payload_count':len(d['payloads'])})
 write(INT/'media-cooks.json',rows)
 # Native model definitions are generic-source validation dependencies. They
 # stay stock references in the final stamps and are excluded from delivery.
 db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
 dependencies=[]
 for kind,f in FAMILIES.items():
  tree=NativeTree(INT/'stock/art/stamps'/Path(f['stamp']+'.bin'));maps=mapping(kind)
  for obj in tree.objects.values():
   if obj['type']=='SplatStampBlueprint':
    stem='art/scenarios/textures/splats/'+tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/')
    member=stem+'.rrmaterial';found=db.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(member,)).fetchall();assert found,(kind,member)
    dest=STAMP_SOURCE/'source'/(stem+'.material');dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():run('splat-dependency-'+str(len(dependencies)),[ARCH,'extract-member',found[0][0],member,dest])
    # Reflect FileNameValidationRule declares .material for splats; native
    # archives supply .rrmaterial. Stage the actual stock bytes under that
    # validation suffix only. No material burner uses or ships this alias.
    dependencies.append({'member':member,'archive':found[0][0],'source_validation_alias':str(dest),'sha256':sha(dest),'delivery':'unchanged native splat reference; validation alias excluded from cook and final package'})
    continue
   if obj['type']!='VisualStampBlueprint':continue
   stem=tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/')
   if stem in maps:continue
   for suffix in ['.rgo','.rgm','.rrmaterial','.rrgeom']:
    member=stem+suffix;found=db.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(member,)).fetchall()
    if not found:
     assert suffix!='.rgo',(kind,member)
     continue
    dest=STAMP_SOURCE/'source'/member;dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():run('dependency-'+str(len(dependencies)),[ARCH,'extract-member',found[0][0],member,dest])
    dependencies.append({'member':member,'archive':found[0][0],'sha256':sha(dest),'delivery':'stock reference only; not in allowlist'})
 db.close();write(INT/'stock-cook-dependencies.json',dependencies)
def compose():
 base=baseline();runmeta=read(STAMP_RUN/'run.json');assert runmeta['status']=='succeeded' and runmeta['exit_code']==0
 # The owned run supplies exactly one new archive; refuse stale ambiguous outputs.
 archives=list((STAMP_RUN/'output').rglob('*.sga'));assert len(archives)==1,archives
 cooked=archives[0];fresh=INT/'stamp-cooked-readback';run('unpack-stamp-cook',[ARCH,'unpack',cooked,'--output',fresh])
 prior=INT/'baseline-readback';run('unpack-baseline',[ARCH,'unpack',base,'--output',prior])
 payload=INT/'payload';report={'status':'running','payloads':[],'actors':[],'stamps':[]}
 def save(member,data):
  p=payload/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);report['payloads'].append({'member':member,'file':str(p),'sha256':sha(p)})
 for kind,f in FAMILIES.items():
  author=read(OUT/'authors'/kind/'integration-manifest.json');assert author['status']=='passed'
  for r in author['payloads']:assert sha(r['file'])==r['sha256'];save(r['member'],Path(r['file']).read_bytes())
  stampmember=f'art/stamps/garrison/{KEY}/{kind}.bin';old=INT/'stock/art/stamps'/Path(f['stamp']+'.bin')
  proof=validate_stamp(old,fresh/stampmember,author['model_mapping']);report['stamps'].append({'building':kind,**proof});save(stampmember,(fresh/stampmember).read_bytes())
  tiermember=f'attrib/attachments/attachment_lists/garrison/{KEY}/{kind}_tier.rgd'
  tiercook=read(PROJECT/'mod-project.json')['cooks'][-1];assert not tiercook['live_reload'] and sha(tiercook['archive'])==tiercook['sha256']
  tierfresh=INT/'tier-cooked-readback'/tiercook['sha256'][:16]
  if not tierfresh.exists():run('unpack-private-tiers',[ARCH,'unpack',tiercook['archive'],'--output',tierfresh])
  generated=rgd.read((tierfresh/tiermember).read_bytes());identity=rgd.find(generated.nodes,'default/pbgid');assert identity
  stockmember='attrib/attachments/attachment_lists/'+f['tier']+'.rgd';stock=rgd.read((INT/'official'/stockmember).read_bytes());oldstock=copy.deepcopy(stock);replaced=0
  for table in stock.nodes:
   if table.kind!='List' or table.key=='instance_version':continue
   pbg=rgd.find(table.value,'pbgid');assert pbg;pbg.value=identity.value
   for _,n in rgd.flatten(table.value):
    if n.kind=='CString' and n.key=='stamp' and n.value=='art\\stamps\\'+f['stamp'].replace('/','\\'):
     n.value=f'art\\stamps\\garrison\\{KEY}\\{kind}';replaced+=1
  assert replaced>0
  # Exact clone proof after restoring only intended identities and stamp paths.
  restored=copy.deepcopy(stock)
  for table in restored.nodes:
   if table.kind!='List' or table.key=='instance_version':continue
   rgd.find(table.value,'pbgid').value=rgd.find(oldstock.nodes,table.key+'/pbgid').value
   for _,n in rgd.flatten(table.value):
    if n.kind=='CString' and n.value==f'art\\stamps\\garrison\\{KEY}\\{kind}':n.value='art\\stamps\\'+f['stamp'].replace('/','\\')
  assert semantics(restored.nodes)==semantics(oldstock.nodes)
  save(tiermember,encode(stock))
  actor_member=f"attrib/ebps/races/malian/buildings/{f['actor']}.rgd";actorpath=prior/actor_member
  if not actorpath.exists():actorpath=INT/'official'/actor_member
  actor=rgd.read(actorpath.read_bytes());before=copy.deepcopy(actor);count=0
  for _,n in rgd.flatten(actor.nodes):
   if n.kind=='CString' and n.key=='$PBGNAME' and n.value==f['tier'].split('/')[-1]:n.value=GUID+':'+kind+'_tier';count+=1
  assert count>0
  back=copy.deepcopy(actor)
  for _,n in rgd.flatten(back.nodes):
   if n.kind=='CString' and n.value==GUID+':'+kind+'_tier':n.value=f['tier'].split('/')[-1]
  assert semantics(back.nodes)==semantics(before.nodes)
  save(actor_member,encode(actor));report['actors'].append({'building':kind,'member':actor_member,'rebound_tier_references':count,'healthy_stamp_variants':replaced,'pbgid':identity.value,'all_other_fields':'identical','baseline_source':'0.2.4' if (prior/actor_member).exists() else 'current official stock inherited by 0.2.4'})
 assert len({r['member'] for r in report['payloads']})==len(report['payloads'])
 report.update(status='passed',stamp_cook_archive=str(cooked),stamp_cook_sha256=sha(cooked),private_tier_cook=tiercook);write(INT/'bindings-report.json',report);print('PRIVATE_BINDINGS_AND_STAMP_READBACK_PASSED',flush=True)
def package():
 base=baseline();bindings=read(INT/'bindings-report.json');assert bindings['status']=='passed'
 for kind in FAMILIES:assert read(OUT/'reviews'/f'{kind}.json')['status']=='approved'
 folder=OUT/'package';folder.mkdir(exist_ok=True);final=folder/'Berber_future_kingdom.sga';mid=INT/'media-candidate.sga'
 allowed={r['member'] for r in bindings['payloads']}
 for alias,prefix in [('data','art/'),('attrib','attrib/')]:
  rows=[r for r in bindings['payloads'] if r['member'].startswith(prefix)]
  for r in rows:assert sha(r['file'])==r['sha256']
  path=INT/(alias+'-members.txt');path.write_text('\n'.join(r['member']+'='+r['file'] for r in rows)+'\n',encoding='utf-8')
 run('set-media',[ARCH,'set-members',base,INT/'data-members.txt',mid,'--alias','data'])
 run('set-attributes',[ARCH,'set-members',mid,INT/'attrib-members.txt',final,'--alias','attrib'])
 old=json.loads(run('baseline-inventory',[ARCH,'list',base,'--verify']));new=json.loads(run('final-inventory',[ARCH,'list',final,'--verify']))
 assert new['archive']['verification']['verified'];assert new['archive']['name'].replace('-','').lower()==GUID;validate_house_namespaces(new)
 before={r['path']:r for r in old['members']};after={r['path']:r for r in new['members']};assert set(after)==set(before)|allowed
 fresh=OUT/'final-readback';run('unpack-final',[ARCH,'unpack',final,'--output',fresh]);prior=INT/'baseline-readback'
 changed=[];unchanged=[]
 for member,r in before.items():
  assert after[member]['toc']==r['toc'],member
  if sha(fresh/member)==sha(prior/member):unchanged.append(member)
  else:assert member in allowed;changed.append(member)
 expected={f"attrib/ebps/races/malian/buildings/{FAMILIES[k]['actor']}.rgd" for k in ['mill','mining']};assert set(changed)==expected,changed
 for r in bindings['payloads']:
  member=r['member'];assert sha(fresh/member)==r['sha256'];assert after[member]['toc']==('attrib' if member.startswith('attrib/') else 'data')
  if member.endswith('.rgd'):
   decoded=OUT/'readback-bindings'/Path(member).with_suffix('.xml');decoded.parent.mkdir(parents=True,exist_ok=True)
   run('decode-'+Path(member).stem,[ARCH,'decode-rgd',fresh/member,decoded])
 # Re-read every native stamp from the delivery archive, not only its cook donor.
 for kind,f in FAMILIES.items():validate_stamp(INT/'stock/art/stamps'/Path(f['stamp']+'.bin'),fresh/f'art/stamps/garrison/{KEY}/{kind}.bin',mapping(kind))
 evidence={'version':'0.2.5','status':'fresh media and stamp cooks, independent reviews and final archive readback passed','archive':str(final),'archive_sha256':sha(final),'project_guid':GUID,'baseline_sha256':sha(base),'baseline_unchanged_members':len(unchanged),'changed_existing_members':sorted(changed),'new_members':sorted(set(after)-set(before)),'member_count':len(after),'house_tent_Tuareg_SCAR_audio':'all baseline members outside allowlist byte-identical','native_acceptance':'pending user game test','geometry':'stock native topology UVs normals and assemblies retained; material-only remixes','scale':'stock native stamp scale/placement preserved; earlier undersized primitive recipes excluded','known_limits':['Stock construction/wreck auxiliary stamps, decals and resource outskirts retained.','Blender material preview approximates native layered shader.','Stock model age behaviour preserved; no invented four-age variants.','Native two-colour, construction, damage/destruction, drop-off and pathing tests pending.']}
 manifest=read(ROOT/'output/berber_update_0_2_4/package/garrison.json');manifest['members'][0]['sha256']=sha(final)
 manifest['details'].update(version='0.2.5',updated='2026-10-13',summary='Berber mill, lumber camp and mining camp material remixes',description='Native stock economic buildings repainted with warm earth, dark timber and woven surfaces. Original geometry, construction states and player-colour layers retained. Accepted 0.2.4 house, tent, Tuareg and existing gameplay preserved.',changelog='Three economic building material remixes with private native stamps and tier bindings. Complete assemblies and stock age progression retained; all unrelated baseline resources preserved.')
 write(folder/'garrison.json',manifest);write(folder/'EVIDENCE.json',evidence)
 (folder/'INSTALL_AND_TEST.txt').write_text('''BERBER 0.2.5 — ECONOMIC BUILDING REMIXES
Close AoE4. Import berber_future_kingdom-0.2.5.zip into Garrison, confirm version 0.2.5, enable it, and launch through Play.
Start a FRESH match: Tuning Pack The Berber Dynasties; Game Mode Berber Civilization; Civilization Malians.
Build a mill, lumber camp and mining camp in Age I. Check earth/plaster, dark timber, restrained trim, visibility, ground contact and native proportions beside the accepted house/villagers.
Check construction, cancellation/rebuild, selection, close/far views, damage/burning/destruction and nearby villager movement. Test two player colours.
Through Ages II-IV inspect existing buildings and newly constructed buildings. These assets retain stock age progression; stock donors do not gain invented new age silhouettes.
Send villagers to gather/drop food, wood, gold and stone. Check existing economic technologies and mill influence. No gameplay fields are changed.
Recheck 0.2.4 house size/appearance, Tribal Tent influence/free villagers and Tuareg training/movement/combat. Their resources are byte-identical to 0.2.4.
Retained stock construction/wreck stamps, resource outskirts and decals may look stock. Native shader appearance, owner colours, pathing and destruction require this game test; package/static proof is not native acceptance.
If anything fails, report building, age, player colour, existing/new status and screenshots; preserve warnings.log. Rollback: close AoE4 and reimport retained 0.2.4 ZIP.
''',encoding='utf-8')
 shutil.copy2(INT/'bindings-report.json',folder/'bindings-report.json');shutil.copytree(OUT/'reviews',folder/'reviews',dirs_exist_ok=True)
 for kind in FAMILIES:shutil.copy2(OUT/'authors'/kind/'integration-manifest.json',folder/f'{kind}-asset-evidence.json')
 zpath=OUT/'berber_future_kingdom-0.2.5.zip'
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(folder.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(folder).as_posix())
 with zipfile.ZipFile(zpath) as z:assert z.testzip() is None and hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
 evidence.update(zip=str(zpath),zip_sha256=sha(zpath));write(OUT/'delivery.json',evidence)
 print('BERBER_0_2_5_VERIFIED_ZIP_READY',zpath,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
