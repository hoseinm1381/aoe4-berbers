"""Reuse verified060 recordings: one take per action/delivery, shared all ages."""
import sys
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'research/berber060'))
from common import OUT as OLD,ART,read,write,sha
from profiles import qualify,clone_private,parse_profile,parse_media
OUT=ROOT/'output/berber_update_0_6_1'
SPEAKERS={'villager':'b27xxxxxxxxx','trader':'b28xxxxxxxxx'}

def select_one(rows):
 selected={};order={'lowest':0,'low':1,'med':2,'high':3,'none':4}
 for row in sorted(rows,key=lambda r:(order[r['age']],r['take'],r['id'])):
  if row['status']=='accepted':selected.setdefault((row['event'],row['delivery']),row)
 return selected

def build():
 from batch_generation import job_key,single_identity
 coverage=read(OLD/'coverage.json');plan=read(ART/'recording-plan.json')
 if coverage['plan_sha256']!=sha(ART/'recording-plan.json'):raise ValueError('Coverage uses older plan')
 jobs={j['id']:j for j in plan['jobs']};assignments={r['path'].replace('\\','/').lower():r for r in plan['assignments']};enc=read(OLD/'wem/Medium/encoding-manifest.json')
 source_manifest=read(OLD/'profiles/manifest.json');files=[];profiles=[];proofs=[];sources={}
 for family,speaker in SPEAKERS.items():
  selected=select_one([r for r in coverage['jobs'] if r['family']==family]);verified={}
  for key,row in selected.items():
   job=jobs[row['id']];request=job_key(job);rp=OLD/'receipts'/(request+'.json');receipt=read(rp)
   if receipt['request_id']!=request or receipt['identity']!=single_identity(job) or receipt['status']!='accepted_acoustic':raise ValueError('Receipt changed')
   for path,digest in [(receipt['source'],receipt['source_sha256']),(receipt['native_path'],receipt['native_wav']['sha256'])]:
    if sha(path)!=digest:raise ValueError('Accepted source changed')
   e=enc[request];wem=Path(e['wem'])
   if e['source_sha256']!=receipt['native_wav']['sha256'] or sha(wem)!=e['sha256']:raise ValueError('Encoding changed')
   verified[key]=(wem,e)
   proofs.append({'family':family,'event':key[0],'delivery':key[1],'source_job':job['id'],'source_age':job['age'],'request_id':request,'source_sha256':receipt['source_sha256'],'wem_sha256':e['sha256'],'all_ages_shared':True,'takes':1})
  profile=next(p for p in source_manifest['families'] if p['family']==family)
  original=Path(profile['profile_path']).read_bytes()
  if sha(profile['profile_path'])!=profile['profile_sha256']:raise ValueError('Profile changed')
  identity='malian_'+speaker;data,_=clone_private(original,qualify(original),speaker,identity)
  spd=OUT/'audio-profiles'/(identity+'.spd');spd.parent.mkdir(parents=True,exist_ok=True);spd.write_bytes(data)
  digest=sha(spd);payload='payloads/'+digest+'.spd';sources[payload]=str(spd)
  files.append({'path':spd.name,'payload':payload,'sha256':digest,'bytes':spd.stat().st_size})
  profiles.append({'family':family,'race':'malian','speaker':speaker,'media_identity':identity,'path':spd.name})
  refs={m['text'].replace('\\','/').lower() for r in parse_profile(data) for m in r['media']}
  for ref in sorted(refs):
   parsed=parse_media(ref)
   if not parsed['parsed']:raise ValueError('Unparsed native media')
   oldref=ref.replace(identity,profile['private_media_identity'].lower())
   assigned=assignments[oldref];semantic_job=jobs[assigned['job_id']]
   if semantic_job['family']!=family:raise ValueError('Cross-family native assignment')
   key=(semantic_job['event'],semantic_job['delivery'])
   if key not in verified:raise ValueError('No accepted recording for '+repr(key))
   wem,e=verified[key];payload='payloads/'+e['sha256']+'.wem';sources[payload]=str(wem)
   files.append({'path':ref,'payload':payload,'sha256':e['sha256'],'bytes':e['bytes']})
 manifest={'schema':'berber-native-audio/v1','profiles':profiles,'files':files,'fallbacks':[],
   'native_playback':'pending','policy':'One existing accepted take per event/delivery shared across all age/take/alternate slots; efforts remain nonverbal'}
 write(OUT/'audio-patch/native-audio-manifest.json',manifest)
 installer=(ROOT/'research/berber060/Install-BerberNativeAudio.ps1').read_text(encoding='utf8')
 installer=installer.replace('berber060-install-state.json','berber061-install-state.json').replace('Berber060','Berber061').replace('.berber060-','.berber061-')
 (OUT/'audio-patch/Install-BerberNativeAudio.ps1').write_text(installer,encoding='utf-8-sig')
 report={'status':'passed','families':2,'native_files':len(files),'unique_recordings':len(proofs),'sources':sources,'selected_recordings':proofs,'paid_requests':0,'all_ages_shared':True,'takes_per_event_delivery':1,'native_playback':'pending'}
 write(OUT/'audio-patch-validation.json',report)
 print('061_AUDIO_PATCH',len(files),'files',len(proofs),'shared recordings')
 return report

if __name__=='__main__':build()
