"""Scoped 040 shared native integration. Every native cook is explicitly invoked."""
import hashlib,json,os,re,shutil,subprocess,sys,struct
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/berber_update_0_4_0'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe'; ARCH=EXT/'bin/sga-archiver.exe'
EDITOR=Path(os.environ['LOCALAPPDATA'])/'Garrison/Kit/tools/essence-object-editor/EssenceEditor.exe'
sys.path[:0]=[str(ROOT/'research'),str(EXT)]
from economy_025_native_stamp import NativeTree,decompile
from garrison_shared import relic_chunky as rc

def prune_native_visuals(tree,retain_ids):
 """Compact root pointer array in-place. Other records and chunks stay exact."""
 root=next(o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner'])
 field=root['fields']['m_blueprints'];array=tree.field(root,field)
 original=[];kept=[];removed=[]
 for i in range(array['count']):
  slot=array['data_address']+8*i; rel=struct.unpack('<q',tree.bytes(slot,8))[0]
  obj=tree.by_offset[slot+rel];original.append(obj)
  if obj['type']=='VisualStampBlueprint' and obj['id'] not in retain_ids:removed.append(obj)
  else:kept.append(obj)
 assert set(retain_ids)<={o['id'] for o in original if o['type']=='VisualStampBlueprint'}
 memory=bytearray(tree.memory.payload)
 at=root['offset']+int(field.get('Offset'))-tree.memory.payload_offset
 struct.pack_into('<II',memory,at+8,len(kept),array['capacity'])
 for i,obj in enumerate(kept):
  slot=array['data_address']+8*i
  struct.pack_into('<q',memory,slot-tree.memory.payload_offset,obj['offset']-slot)
 for i in range(len(kept),array['count']):struct.pack_into('<q',memory,array['data_address']+8*i-tree.memory.payload_offset,0)
 raw=rc.rebuild(tree.document,lambda c:bytes(memory) if c.offset==tree.memory.offset else None)
 return raw,{'removed_visual_ids':[str(o['id']) for o in removed], 'retained_visual_ids':[str(o['id']) for o in kept if o['type']=='VisualStampBlueprint'], 'preserved_nonvisual_ids':[str(o['id']) for o in tree.objects.values() if o['type']!='VisualStampBlueprint'], 'native_array_before':len(original),'native_array_after':len(kept),'unreachable_visual_records_retained':True,'other_record_bytes':'identical; root array header and pointer slots only changed'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def run(*args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
 if p.returncode:raise RuntimeError(str(args)+'\n'+p.stdout[-2000:]+'\n'+p.stderr[-3000:])
 return p.stdout

def prune_visuals(raw,retain_ids):
 """Prune explicit visual subtrees only; preserve every functional object."""
 root=ET.fromstring(raw);retain={str(i) for i in retain_ids}
 visuals={n.get('Id'):n for n in root.iter('DataObject') if n.get('Type')=='VisualStampBlueprint'}
 assert retain<=visuals.keys(),retain-visuals.keys()
 nonvisual={n.get('Id'):ET.tostring(n) for n in root.iter('DataObject') if n.get('Type')!='VisualStampBlueprint' and not any(x is n for v in visuals.values() for x in list(v.iter())[1:])}
 removed=set(visuals)-retain
 for parent in root.iter():
  for child in list(parent):
   if child.tag=='DataObject' and child.get('Id') in removed:parent.remove(child)
   elif child.tag=='DataValue' and child.get('Name')=='VisualStampBlueprint' and child.text in removed:parent.remove(child)
 remaining={n.get('Id'):n for n in root.iter('DataObject')}
 assert set(nonvisual)<=remaining.keys(),'Functional object removed'
 for oid,before in nonvisual.items():
  if remaining[oid].get('Type')!='StampBlueprint':assert ET.tostring(remaining[oid])==before,oid
 ET.indent(root)
 return ET.tostring(root,encoding='utf8'),{'removed_visual_ids':sorted(removed),'retained_visual_ids':sorted(retain),'preserved_nonvisual_ids':sorted(nonvisual)}

def qualify_source():
 old=ROOT/'output/berber_update_0_3_1'; q=OUT/'qualification'; source=q/'source'
 spec=next(s for s in read(old/'binding-specs.json')['specs'] if s['family']=='keep' and s['age']==3)
 name=next(v for p,v in spec['stock_stamp_fields'] if p.startswith('default/') and p.endswith('stamp_attachment/stamp'))
 stock=ROOT/'output/shared_stock_cache/buildings_031/stamps'/(name.replace('\\','/')+'.bin')
 tree=NativeTree(stock)
 visuals=[o for o in tree.objects.values() if o['type']=='VisualStampBlueprint']
 principal=[o for o in visuals if '/structures/' in tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/') and '/debris/' not in tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/')]
 assert len(principal)==1
 raw,report=prune_native_visuals(tree,{principal[0]['id']})
 native=q/'pruned-keep.bin';native.parent.mkdir(parents=True,exist_ok=True);native.write_bytes(raw)
 principal_model=tree.field(principal[0],principal[0]['fields']['m_blueprint'])['text'].replace('\\','/')
 probe=NativeTree(ROOT/'output/berber_update_0_2_5/integration/stock/art/stamps/civ_mal/mal_gristmill.bin')
 probe_main=next(probe.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/') for o in probe.objects.values() if o['type']=='VisualStampBlueprint' and 'mal_gristmill_control' in probe.field(o,o['fields']['m_blueprint'])['text'])
 raw=decompile(probe,{probe_main:principal_model})
 xml=ET.fromstring(raw)
 principal_node=next(n for n in xml.iter('DataObject') if n.get('Type')=='VisualStampBlueprint' and any(p.get('Name')=='m_blueprint' and p.get('Value','').replace('\\','/')==principal_model for p in n.findall('DataProperty')))
 parent=next(n for n in xml.iter('DataProperty') if n.get('Name')=='m_blueprints')
 for child in list(parent):
  if child is not principal_node and not (child.tag=='DataValue' and child.text==principal_node.get('Id')):parent.remove(child)
 # Use the actual shipped private native model as the fresh validator input.
 actual_model=next(m for m in read(old/'native-art-payload-report.json')['models'] if m['family']=='keep' and m['age']==3)['private']
 next(p for p in principal_node.findall('DataProperty') if p.get('Name')=='m_blueprint').set('Value',actual_model.replace('/','\\'))
 raw=ET.tostring(xml,encoding='utf8');principal_model=actual_model
 template=ROOT/'output/berber_update_0_2_6/integration/s'
 source.mkdir(parents=True,exist_ok=True)
 # Existing compiler-produced dependencies are validator inputs, never reburned.
 media=old/'garrison-cook-readback'
 for item in (media/Path(actual_model).parent).rglob('*'):
  if item.is_file():
   dest=source/item.relative_to(media);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(item,dest)
   if dest.suffix=='.rrmaterial':shutil.copy2(dest,dest.with_suffix('.material'))
 burn=(template/'source/_default.burnproj').read_text(encoding='utf-8-sig')
 def disable(m):return m.group().replace('<IsEnabled>true</IsEnabled>','<IsEnabled>false</IsEnabled>')
 burn=re.sub(r'<BurnRule>.*?</BurnRule>',disable,burn,flags=re.S)
 member='art/stamps/garrison/berber_buildings_040/qualification_keep'
 rule='<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true"/><Includes>'+member.replace('/','\\')+'.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>'
 assert burn.count('</Rules>')==1
 (source/'_default.burnproj').write_text(burn.replace('</Rules>',rule+'</Rules>'),encoding='utf8')
 target=source/(member+'.rdo');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 shutil.copy2(template/'buildings.aoe4mod',q/'qualification.aoe4mod')
 command=[str(CORE),'essence','build-mod','--editor',str(EDITOR),'--mod',str(q/'qualification.aoe4mod'),'--run-root',str(OUT/'qualification-native-02'),'--timeout','600']
 write(q/'source-contract.json',{'stock':str(stock),'stock_sha256':sha(stock),'pruned_native':str(native),'pruned_native_sha256':sha(native),'source':str(target),'source_sha256':sha(target),'member':member,'principal_model':principal_model,'principal_id':principal[0]['id'],'objects_before':len(tree.objects),**report,'command':command})
 print('040_QUALIFICATION_SOURCE',len(visuals),'visuals reduced to 1; functional objects retained')

def qualify_cook():
 q=OUT/'qualification'; report=read(q/'source-contract.json');run(*report['command'])
 state=read(OUT/'qualification-native-02/run.json');assert state['status']=='succeeded' and state['exit_code']==0
 archives=list((OUT/'qualification-native-02/output').rglob('*.sga'));assert len(archives)==1
 target=q/'readback'/ (report['member']+'.bin');target.parent.mkdir(parents=True,exist_ok=True)
 run(ARCH,'extract-member',archives[0],report['member']+'.bin',target)
 probe=NativeTree(target)
 assert any(probe.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/')==report['principal_model'] for o in probe.objects.values() if o['type']=='VisualStampBlueprint')
 tree=NativeTree(report['pruned_native']); ids=set(map(str,tree.objects));assert set(report['preserved_nonvisual_ids'])<=ids
 original=NativeTree(report['stock']);assert tree.objects.keys()==original.objects.keys()
 for oid,obj in tree.objects.items():
  if obj['type']!='StampBlueprint':
   size=int(tree.types[obj['type_id']].get('Size'))
   assert tree.bytes(obj['offset'],size)==original.bytes(original.objects[oid]['offset'],size),oid
 root=next(o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner'])
 array=tree.field(root,root['fields']['m_blueprints']);actual=set()
 for i in range(array['count']):
  slot=array['data_address']+8*i;obj=tree.by_offset[slot+struct.unpack('<q',tree.bytes(slot,8))[0]]
  if obj['type']=='VisualStampBlueprint':actual.add(str(obj['id']))
 assert actual==set(report['retained_visual_ids'])
 write(q/'qualification-result.json',{'status':'passed','layer':'fresh native principal-reference Reflect cook plus exact native stamp pointer-array readback','archive':str(archives[0]),'archive_sha256':sha(archives[0]),'probe_stamp_sha256':sha(target),'pruned_stamp_sha256':sha(report['pruned_native']),'visual_ids':sorted(actual),'functional_record_bytes_preserved':True,'source_contract':report,'runtime':'unverified','qualification_limit':'Final pruned native stamp is byte-preserving pointer mutation, not a full Reflect round-trip; native visual activation remains a match gate.'})
 print('040_COMPLETE_STAMP_QUALIFIED',len(tree.objects),'native records; functional bytes exact')

BASE=ROOT/'output/berber_update_0_3_1/package/Berber_future_kingdom.sga'
BASE_SHA='782234abffec0a54cb9133067d69ba95d29e06a5a734cedcb4f7054093773f6f'
def extract(member,dest=None):
 target=Path(dest) if dest else OUT/'baseline-inputs'/member
 target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():run(ARCH,'extract-member',BASE,member,target)
 return target

def active_visuals(tree):
 root=next(o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner'])
 array=tree.field(root,root['fields']['m_blueprints']);rows=[]
 for i in range(array['count']):
  slot=array['data_address']+8*i;obj=tree.by_offset[slot+struct.unpack('<q',tree.bytes(slot,8))[0]]
  if obj['type']=='VisualStampBlueprint':
   transform=bytes.fromhex(tree.field(obj,obj['fields']['m_transform'])['raw'])
   rows.append({'id':obj['id'],'model':tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/'),'transform':list(struct.unpack('<10f',transform))})
 return rows

def audit_and_repairs():
 assert sha(BASE)==BASE_SHA
 old=ROOT/'output/berber_update_0_3_1'; specs=read(old/'binding-specs.json')['specs']; art=read(old/'native-art-payload-report.json')['models']
 audit=[];payloads=[]
 for spec in specs:
  family=spec['family']; age=spec['age'];member=spec['private_stamp']+'.bin'
  source=extract(member);tree=NativeTree(source);rows=active_visuals(tree)
  principal=next(m['private'] for m in art if m['family']==family and m['age']==age)
  main=next(r for r in rows if r['model']==principal)
  flags=[r for r in rows if '/flags/' in r['model'] or 'owner_flag' in r['model']]
  changed=None;description='byte-preserved accepted031 control'
  if family in ('keep','marrakech','siege'):
   raw,changed=prune_native_visuals(tree,{main['id']}|{r['id'] for r in flags})
   description='complete donor architecture only; inherited native flags retained; competing visible models removed'
  elif family=='tlemcen':
   description='completed model/stamp bytes preserved exactly; preCastle actor binding corrected separately'
  if changed:
   target=OUT/'integration/payload'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
   final=NativeTree(target);after=active_visuals(final)
   assert final.objects.keys()==tree.objects.keys()
   payloads.append({'member':member,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size})
  else:after=rows
  audit.append({'family':family,'age':age,'stamp':member,'baseline_stamp_sha256':sha(source),'principal':principal,'visuals_before':rows,'visuals_after':after,'functional_object_ids_preserved':True,'action':description,'changes':changed})
  print('040_AUDIT',family,age,len(rows),'->',len(after),flush=True)
 controls=[]
 for release in ('0_2_7','0_3_0','0_3_1'):
  p=ROOT/f'output/berber_update_{release}'
  for path in p.glob('*.zip'):controls.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size})
 write(OUT/'baseline-audit.json',{'baseline':str(BASE),'baseline_sha256':BASE_SHA,'variants':audit,'retained_release_hashes':controls,'source_working_root':'current checkout required because untracked031 source is absent from git worktree; no git state changes','native_acceptance':'pending'})
 write(OUT/'integration/repair-payloads.json',{'payloads':payloads,'baseline_sha256':BASE_SHA})

def tlemcen_binding():
 from garrison_shared import rgd
 from build_berber_update_0_2_5 import encode,semantics
 import copy
 member='attrib/ebps/races/malian/buildings/landmarks/great_mosque_of_tlemcen/building_landmark_age2_landmarkc_control_mal.rgd'
 original=rgd.read(extract(member).read_bytes());doc=copy.deepcopy(original);changes=[]
 for path,node in rgd.flatten(doc.nodes):
  if node.kind=='CString' and path.startswith('default/tier_ext/tier_group_list/tier_group/') and path.endswith('/attachments/$PBGNAME') and node.value in ('tier1_unit_religious_control_sul','tier2_unit_religious_control_sul'):
   changes.append({'path':path,'before':node.value,'after':'1d3145e8f1b2427f8bb0067851fcf0f1:v031_tlemcen_age03_tier'})
   node.value=changes[-1]['after']
 assert len(changes)==2
 restored=copy.deepcopy(doc)
 for change in changes:rgd.find(restored.nodes,change['path']).value=change['before']
 assert semantics(restored.nodes)==semantics(original.nodes)
 target=OUT/'integration/payload'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(encode(doc))
 readback=rgd.read(target.read_bytes())
 for change in changes:assert rgd.find(readback.nodes,change['path']).value==change['after']
 scale=rgd.find(readback.nodes,'default/entity_blueprint_ext/animator_scale').value
 write(OUT/'integration/tlemcen-binding.json',{'status':'passed compiled structural readback','member':member,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'changes':changes,'actor_animator_scale_preserved':scale,'completed_stamp_model_geometry_bytes':'unchanged from shipped031','gameplay_semantics':'identical after restoring two visual attachment references','native_transition':'pending solo match'})

def archive():
 assert sha(BASE)==BASE_SHA
 integ=OUT/'integration';entries=read(integ/'repair-payloads.json')['payloads']
 entries.append({k:v for k,v in read(integ/'tlemcen-binding.json').items() if k in ('member','file','sha256','bytes')})
 for manifest in sorted((integ/'model-manifests').glob('*.json')):entries.extend(read(manifest)['payloads'])
 payloads={}
 for row in entries:
  assert sha(row['file'])==row['sha256'],row['member']
  if row['member'] in payloads:assert payloads[row['member']]['sha256']==row['sha256'],row['member']
  payloads[row['member']]=row
 current=BASE
 for alias,prefix in [('data','art/'),('attrib','attrib/')]:
  rows=[r for r in payloads.values() if r['member'].startswith(prefix)]
  if not rows:continue
  mapping=integ/(alias+'-members.txt');mapping.write_text('\n'.join(r['member']+'='+r['file'] for r in rows)+'\n',encoding='utf8')
  target=integ/(alias+'-candidate.sga');run(ARCH,'set-members',current,mapping,target,'--alias',alias);current=target
 final=integ/'candidate/Berber_future_kingdom.sga';final.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(current,final)
 before=read_inventory(BASE);after=read_inventory(final)
 old={r['path']:r for r in before['members']};new={r['path']:r for r in after['members']}
 assert set(new)==set(old)|set(payloads)
 assert after['archive']['name'].replace('-','').lower()=='1d3145e8f1b2427f8bb0067851fcf0f1'
 baseline=integ/'baseline-readback';readback=integ/'candidate-readback'
 if not baseline.exists():run(ARCH,'unpack',BASE,'--output',baseline)
 if readback.exists():raise RuntimeError('New candidate readback required; preserve old evidence and choose attempt path')
 run(ARCH,'unpack',final,'--output',readback)
 changed=[]
 for member in old:
  if sha(baseline/member)!=sha(readback/member):
   assert member in payloads,member;changed.append(member)
 for member,row in payloads.items():assert sha(readback/member)==row['sha256']
 write(integ/'composition-report.json',{'status':'passed','baseline':str(BASE),'baseline_sha256':BASE_SHA,'archive':str(final),'archive_sha256':sha(final),'project_guid':after['archive']['name'],'baseline_members':len(old),'candidate_members':len(new),'changed_existing_members':sorted(changed),'unchanged_existing_members':len(old)-len(changed),'new_members':sorted(set(new)-set(old)),'all_unrelated_members_sha256_identical':True,'archive_crc_sha1_verified':True,'payloads':list(payloads.values()),'native_runtime':'unverified'})
 print('040_CANDIDATE_VERIFIED',len(old)-len(changed),'unchanged;',len(changed),'changed;',len(set(new)-set(old)),'new')

def read_inventory(path):
 result=json.loads(run(ARCH,'list',path,'--verify'));assert result['archive']['verification']['verified'];return result

def validate_media_dependencies():
 import sqlite3
 payloads={}
 for manifest in sorted((OUT/'integration/model-manifests').glob('*.json')):
  for row in read(manifest).get('payloads',[]):
   assert sha(row['file'])==row['sha256'];payloads[row['member']]=row
 assert payloads
 db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
 dependencies=[];models=[]
 for member,row in payloads.items():
  if member.endswith('.rrmaterial'):
   raw=Path(row['file']).read_bytes();refs=set(v.decode().replace('\\','/') for v in re.findall(rb'art[\\/][A-Za-z0-9_./\\-]+\.rrtex',raw));assert refs,member
   for ref in refs:
    if ref in payloads:resolution='private verified payload'
    else:
     found=db.execute('select archive_path from resolved_assets where lower(logical_path)=lower(?)',(ref,)).fetchone();assert found and Path(found[0]).exists(),(member,ref);resolution='official native archive'
    dependencies.append({'material':member,'texture':ref,'resolution':resolution})
  elif member.endswith('.rgm'):
   doc=rc.load(row['file']);bana=[c for c in rc.walk(doc.roots) if c.tag==b'BANA'];assert len(bana)==1,member
   stem,at=rc.read_lp_string(bana[0].payload,0);stem=stem.replace('\\','/')
   for suffix in ('.rrgeom','.rrmaterial'):assert stem+suffix in payloads,(member,stem+suffix)
   assert member.removesuffix('.rgm')+'.rgo' in payloads,member
   models.append({'member':member,'native_geometry_material_stem':stem,'source_sha256':row['sha256']})
 db.close();write(OUT/'media-dependency-validation.json',{'status':'passed','models':models,'material_texture_dependencies':dependencies,'native_game':'unverified'})
 print('040_MEDIA_DEPENDENCIES_PASSED',len(models),'models;',len(dependencies),'texture refs')

if __name__=='__main__':globals()[sys.argv[1]]()


