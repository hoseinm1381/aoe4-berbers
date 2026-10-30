"""Fresh native040 model-reference keys and assembled principal/flag stamps."""
import re,shutil,sys,xml.etree.ElementTree as ET
from pathlib import Path
from berber_040_integrate import ROOT,OUT,CORE,ARCH,EDITOR,NativeTree,decompile,read,write,run,sha
STAGE=OUT/'reflect-source';SOURCE=STAGE/'source'

def prepare():
 manifests=[read(p) for p in sorted((OUT/'integration/model-manifests').glob('*-media.json'))]
 assert manifests,'No admitted native media'
 SOURCE.mkdir(parents=True,exist_ok=True);models=set();payloads={};stamps=[]
 for manifest in manifests:
  for row in manifest['payloads']:
   if row['member'] in payloads:assert payloads[row['member']]['sha256']==row['sha256']
   payloads[row['member']]=row
   if row['member'].endswith('.rgm'):models.add(row['member'].removesuffix('.rgm'))
  if manifest.get('stamp_source'):
   stamp=SOURCE/(manifest['primary_stamp']+'.rdo');stamp.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(manifest['stamp_source'],stamp)
   stamps.append({'member':manifest['primary_stamp']+'.bin','source':str(stamp),'source_sha256':sha(stamp)})
 for row in payloads.values():
  assert sha(row['file'])==row['sha256'];dest=SOURCE/row['member'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(row['file'],dest)
  if dest.suffix=='.rrmaterial':shutil.copy2(dest,dest.with_suffix('.material'))
 tree=NativeTree(ROOT/'output/berber_update_0_2_5/integration/stock/art/stamps/civ_mal/mal_gristmill.bin')
 main=next(tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/') for o in tree.objects.values() if o['type']=='VisualStampBlueprint' and 'mal_gristmill_control' in tree.field(o,o['fields']['m_blueprint'])['text'])
 probes=[]
 for index,model in enumerate(sorted(models)):
  xml=ET.fromstring(decompile(tree,{main:model}));parent=next(n for n in xml.iter('DataProperty') if n.get('Name')=='m_blueprints')
  principal=next(n for n in parent.findall('DataObject') if n.get('Type')=='VisualStampBlueprint' and any(p.get('Name')=='m_blueprint' and p.get('Value','').replace('\\','/')==model for p in n.findall('DataProperty')))
  for child in list(parent):
   if child is not principal and not(child.tag=='DataValue' and child.text==principal.get('Id')):parent.remove(child)
  # Distinct IDs per probe are required when multiple stamps share one archive.
  from landmark_027_export_assemble import rebase_ids
  rebase_ids(xml.find('DataObject'),'040-probe:'+model,None)
  member=f'art/stamps/garrison/berber_buildings_040/key_{index:02}'
  path=SOURCE/(member+'.rdo');path.parent.mkdir(parents=True,exist_ok=True);ET.indent(xml);path.write_bytes(ET.tostring(xml,encoding='utf8'))
  probes.append({'model':model,'member':member+'.bin','source':str(path),'source_sha256':sha(path)})
 template=ROOT/'output/berber_update_0_2_6/integration/s'
 burn=(template/'source/_default.burnproj').read_text(encoding='utf-8-sig')
 burn=re.sub(r'<BurnRule>.*?</BurnRule>',lambda m:m.group().replace('<IsEnabled>true</IsEnabled>','<IsEnabled>false</IsEnabled>'),burn,flags=re.S)
 include='art\\stamps\\garrison\\berber_buildings_040\\*.rdo'
 rule='<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner><Configurations>Debug Release Profile RTM</Configurations><Excludes i:nil="true"/><Includes>'+include+'</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters><PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>'
 assert burn.count('</Rules>')==1;(SOURCE/'_default.burnproj').write_text(burn.replace('</Rules>',rule+'</Rules>'),encoding='utf8')
 shutil.copy2(template/'buildings.aoe4mod',STAGE/'stamps.aoe4mod')
 write(STAGE/'reflect-plan.json',{'probes':probes,'stamps':stamps,'models':sorted(models),'payload_hashes':{m:r['sha256'] for m,r in payloads.items()}})
 print('040_REFLECT_SOURCE',len(probes),'keys;',len(stamps),'actual stamps')

def cook(attempt='01'):
 plan=read(STAGE/'reflect-plan.json');runroot=OUT/('reflect-native-'+attempt)
 for row in plan['probes']+plan['stamps']:assert sha(row['source'])==row['source_sha256']
 run(CORE,'essence','build-mod','--editor',EDITOR,'--mod',STAGE/'stamps.aoe4mod','--run-root',runroot,'--timeout','600')
 state=read(runroot/'run.json');assert state['status']=='succeeded' and state['exit_code']==0
 archives=list((runroot/'output').rglob('*.sga'));assert len(archives)==1
 back=OUT/('reflect-readback-'+attempt);keys={};compiled=[]
 for row in plan['probes']+plan['stamps']:
  target=back/row['member'];target.parent.mkdir(parents=True,exist_ok=True);run(ARCH,'extract-member',archives[0],row['member'],target)
  tree=NativeTree(target)
  if 'model' in row:
   hits=[tree.field(o,o['fields']['m_blueprint']) for o in tree.objects.values() if o['type']=='VisualStampBlueprint' and tree.field(o,o['fields']['m_blueprint'])['text'].replace('\\','/')==row['model']]
   assert len(hits)==1;keys[row['model'].replace('/','\\')]={**hits[0],'kind':'Reflect::ReflectStringHash'}
  else:compiled.append({'member':row['member'],'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size})
 write(OUT/'native-model-key-table.json',{'status':'passed','keys':keys,'archive':str(archives[0]),'archive_sha256':sha(archives[0]),'native_run':str(runroot/'run.json'),'compiled_stamps':compiled})
 print('040_NATIVE_KEYS_AND_STAMPS',len(keys),len(compiled))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
