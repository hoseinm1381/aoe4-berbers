"""Small hash-proven external-audio pilot. No encoding, API, install or cleanup."""
import json,sys,wave,subprocess
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'research/berber060'))
from common import OUT as OLD,ART,read,write,sha
from batch_generation import job_key,single_identity
OUT=ROOT/'output/berber_update_0_7_1/pilot'
CLIENT=Path.home()/'AppData/Local/Garrison/current'
ACTIONS={'select':('select','norm'),'move':('movegc','norm'),'attack':('attack','norm'),'stop':('stop','norm'),'work':('resourcegather','norm'),'pain':('effortpain','high'),'death':('effortdeath','high')}
def build(destination=OUT):
 destination=Path(destination);planpath=ART/'recording-plan.json';plan=read(planpath);coverage=read(OLD/'coverage.json')
 if coverage['plan_sha256']!=sha(planpath):raise ValueError('Coverage plan mismatch')
 jobs={j['id']:j for j in plan['jobs']};accepted={r['id'] for r in coverage['jobs'] if r['status']=='accepted'}
 proof061=ROOT/'output/berber_update_0_6_1/audio-patch-validation.json';chosen061=read(proof061)['selected_recordings']
 backend=CLIENT/'garrison-audio-backend.exe';help_result=subprocess.run([str(backend),'--help'],capture_output=True,text=True,check=True)
 rows=[];missing=[];payloads={}
 for family in ('villager','tuareg'):
  for action,(event,delivery) in ACTIONS.items():
   age='none' if action in ('pain','death') else 'lowest'
   if family=='villager':
    exact=[r for r in chosen061 if r['family']==family and r['event']==event and r['delivery']==delivery]
    options=[jobs[r['source_job']] for r in exact if r['source_job'] in accepted and r['source_age']==age]
   else:options=[j for j in jobs.values() if j['family']==family and j['event']==event and j['delivery']==delivery and j['age']==age and j['take']==1 and j['id'] in accepted]
   if not options:
    missing.append({'family':family,'action':action,'event':event,'delivery':delivery,'age':age,'reason':'No exact accepted requested semantic event; no generic substitution'});continue
   job=sorted(options,key=lambda j:(j['take'],j['id']))[0];key=job_key(job);rp=OLD/'receipts'/(key+'.json');receipt=read(rp)
   if receipt['request_id']!=key or receipt['job_id']!=job['id'] or receipt['identity']!=single_identity(job) or receipt['status']!='accepted_acoustic':raise ValueError('Receipt identity/status mismatch')
   source=Path(receipt['native_path']);digest=sha(source)
   if digest!=receipt['native_wav']['sha256'] or sha(receipt['source'])!=receipt['source_sha256']:raise ValueError('Source hash mismatch')
   normalization=Path(receipt['normalization_provenance']) if isinstance(receipt.get('normalization_provenance'),str) else None
   with wave.open(str(source),'rb') as w:
    if (w.getnchannels(),w.getframerate(),w.getsampwidth(),w.getcomptype())!=(1,48000,2,'NONE'):raise ValueError('Pilot requires mono 48k16 PCM WAV')
    duration=w.getnframes()/48000
   member='audio/berber071/'+digest+'.wav';target=destination/member;target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() and sha(target)!=digest:raise ValueError('Existing pilot payload changed')
   if not target.exists():target.write_bytes(source.read_bytes())
   if sha(target)!=digest:raise ValueError('Staged copy mismatch')
   payloads[member]={'member':member,'file':str(target),'sha256':digest,'bytes':target.stat().st_size}
   rows.append({'family':family,'action':action,'event':event,'delivery':delivery,'age':job['age'],'take':job['take'],'job_id':job['id'],'request_id':key,'member':member,'source':str(source),'source_sha256':digest,'master':receipt['source'],'master_sha256':receipt['source_sha256'],'receipt':str(rp),'receipt_sha256':sha(rp),'expected_text':job.get('text'),'nonverbal':job.get('nonverbal',action in ('pain','death')),'duration_seconds':duration,'source_selection':'061 one-take exact event/delivery' if family=='villager' else '060 exact lowest take1 (efforts native none age)'})
 report={'schema':'berber071-external-audio-pilot/v1','status':'passed_with_explicit_unavailable_context' if missing else 'passed','sources':rows,'payloads':list(payloads.values()),'missing_contexts':missing,'plan_sha256':sha(planpath),'coverage_sha256':sha(OLD/'coverage.json'),'villager061_selection_sha256':sha(proof061),'backend':{'path':str(backend),'sha256':sha(backend),'cli_help':help_result.stdout,'offline_decode_probe':'Unavailable: CLI has no decode/inspect command; compressed formats not qualified'},'client':{'path':str(CLIENT/'Garrison.exe'),'sha256':sha(CLIENT/'Garrison.exe'),'package_version_xml':(CLIENT/'sq.version').read_text()},'format':'mono48000Hz16bitPCM WAV byte-exact normalized source copies','gates':{'source_identity_hashes':'passed','wav_format':'passed','stage_hashes':'passed','archive_composition':'not performed','backend_audible_playback':'pending','game_native_event_mapping':'pending'},'paid_calls':0,'cleanup_performed':False}
 write(destination/'audio-assets-manifest.json',report);return report
if __name__=='__main__':
 r=build();print(json.dumps({'status':r['status'],'clips':len(r['sources']),'missing':r['missing_contexts'],'manifest':str(OUT/'audio-assets-manifest.json')},indent=2))
