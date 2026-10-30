"""Resumable, conservatively budgeted synthesis. No account configuration changes."""
import argparse, hashlib, json, threading, time, wave, math, re, http.client
from pathlib import Path, PurePosixPath
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from scipy.signal import resample_poly
from common import OUT, ART, write, read, sha
from account import request, PreconnectDNSError, DNS_PROOF, TransportOutcomeUnknown

def request_id(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def provider_stop_reason(error):
    """Shared-account authorization/payment refusals stop new reservations."""
    if isinstance(error,PreconnectDNSError):return 'API preconnect DNS failure'
    if isinstance(error,(TransportOutcomeUnknown,http.client.IncompleteRead)):
        return 'API transport outcome unknown; explicit reconciliation required'
    match=re.fullmatch(r'ElevenLabs HTTP (\d{3}); status=([A-Za-z0-9_]+)',str(error))
    if not match:return None
    code,status=match.groups()
    if code=='401':return 'API authentication rejected'
    if code=='402' or status in ('quota_exceeded','insufficient_credits'):
        return 'API prepaid quota or payment rejected'
    return None


def safe_relative(value):
    value=value.replace('\\','/')
    p=PurePosixPath(value)
    if ':' in value or p.is_absolute() or any(x in ('','.','..') for x in value.split('/')):raise ValueError('Unsafe relative path')
    return p.as_posix()

class Budget:
    def __init__(self,path,cap):
        self.path=Path(path);self.lock=threading.RLock()
        self.stopped=threading.Event();self.stop_reason=None
        if self.path.exists():
            self.data=read(self.path)
            if self.data['cap_usd']!=cap:raise ValueError('Existing spend ceiling differs; explicit budget review required')
        else:
            self.data={'cap_usd':cap,'basis':'human-authorized $100 ceiling; conservative reservation at $0.30/1000 characters, above current $0.08 list rate','rate_usd_per_1000_upper_bound':.30,'reservations':{},'actual_account_balance':'API user_read permission unavailable'}
            write(self.path,self.data)
    @property
    def spent(self):
        with self.lock:return sum(r['reserved_usd'] for r in self.data['reservations'].values())
    def reserve(self,key,cost):
        with self.lock:
            if self.stopped.is_set():raise ValueError('Generation stopped: '+str(self.stop_reason))
            if key in self.data['reservations']:return
            if not math.isfinite(cost) or cost<0 or self.spent+cost>self.data['cap_usd']+1e-9:raise ValueError('Hard spending ceiling reached')
            self.data['reservations'][key]={'reserved_usd':cost,'status':'reserved_before_request'}
            write(self.path,self.data)
    def abort(self,reason):
        with self.lock:self.stop_reason=reason;self.stopped.set()
    def finish(self,key,status,credit_cost=None):
        with self.lock:
            self.data['reservations'][key].update(status=status,provider_character_cost=credit_cost)
            write(self.path,self.data)

def pcm_quality(data,rate):
    if len(data)%2:raise ValueError('Truncated PCM response')
    a=np.frombuffer(data,dtype='<i2').astype(float)/32768
    if len(a)<rate*.15:raise ValueError('Generation too short')
    peak=float(np.max(np.abs(a)));rms=float(np.sqrt(np.mean(a*a)))
    if rms<.0007:raise ValueError('Generation is silent or nearly silent')
    return {'duration_seconds':len(a)/rate,'peak':peak,'rms':rms,'clipped_samples':int(np.count_nonzero(np.abs(a)>=.999))}

def wave_bytes(path,data,rate):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)

def prepare_native(source,target):
    with wave.open(str(source),'rb') as w:
        if (w.getnchannels(),w.getsampwidth())!=(1,2):raise ValueError('Unexpected source PCM')
        rate=w.getframerate();a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
    if rate!=48000:
        import math
        g=math.gcd(48000,rate);a=resample_poly(a,48000//g,rate//g)
    # Trim only sustained near-silence and retain 80ms guards around voice.
    active=np.flatnonzero(np.abs(a)>.003)
    if len(active):a=a[max(0,active[0]-3840):min(len(a),active[-1]+3841)]
    peak=np.max(np.abs(a));gain=min(1.5,.89/max(peak,1e-9))
    a=np.clip(a*gain,-.95,.95)
    data=(a*32767).astype('<i2').tobytes();wave_bytes(target,data,48000)
    return {**pcm_quality(data,48000),'gain':float(gain),'format':'mono 48000Hz s16le','sha256':sha(target)}

def synthesize(job,budget):
    payload={'text':job['generation_text'],'model_id':job.get('model_id','eleven_v3'),
        'language_code':'ar','seed':job['seed'], 'use_pvc_as_ivc':True,
        'voice_settings':{'stability':.5,'similarity_boost':.78,'style':0,'use_speaker_boost':False,'speed':1.0}}
    identity={'voice_id':job['voice_id'],'output_format':'pcm_24000',**payload}
    key=request_id(identity);receipt=OUT/'receipts'/f'{key}.json'
    source=ART/'masters'/f'{key}.wav';native=OUT/'wav'/f'{key}.wav'
    previous=[]
    if not receipt.exists() and key in budget.data['reservations']:
        old={'request_id':key,'job_id':job['id'],'family':job['family'],'identity':identity,
            'status':'failed_or_unknown','error':'Existing reservation without receipt; explicit reconciliation required'}
        write(receipt,old);return old
    if receipt.exists():
        old=read(receipt)
        if old['status']=='accepted_acoustic':
            if old.get('quality',{}).get('clipped_samples',0) or old.get('quality',{}).get('duration_seconds',0)>8:
                old.update(status='review_required',review_flag='clipping_or_excessive_duration');write(receipt,old);return old
            if not source.is_file() or sha(source)!=old['source_sha256']:raise ValueError('Cached accepted source changed')
            if not native.is_file() or sha(native)!=old['native_wav']['sha256']:old['native_wav']=prepare_native(source,native);write(receipt,old)
            return old
        # These explicit refusal responses did not start generation. Never retry
        # unknown transport outcomes, interrupted calls or paid rejected audio.
        if old.get('error') not in ('ElevenLabs HTTP 409; status=already_running','ElevenLabs HTTP 429; status=too_many_concurrent_requests'):
            return old
        previous=old.get('previous_attempts',[])+[{k:v for k,v in old.items() if k!='previous_attempts'}]
        if len(previous)>=3:return old
        time.sleep(2)
    charge=max(1,len(payload['text']))*.30/1000
    attempt_key=key if not previous else key+':retry'+str(len(previous))
    if attempt_key in budget.data['reservations']:
        old={'request_id':key,'job_id':job['id'],'family':job['family'],'identity':identity,
            'status':'failed_or_unknown','error':'Existing attempt reservation without matching started receipt; explicit reconciliation required',
            'previous_attempts':previous}
        write(receipt,old);return old
    budget.reserve(attempt_key,charge)
    record={'request_id':key,'attempt_key':attempt_key,'job_id':job['id'],'family':job['family'],'identity':identity,'status':'started','reserved_usd':charge,'source':str(source),'native_path':str(native),'native_playback':'not_tested','language_review':'pending','previous_attempts':previous}
    write(receipt,record)
    try:
        body,headers=request('/v1/text-to-speech/'+job['voice_id']+'?output_format=pcm_24000',payload)
        metadata={k.lower():v for k,v in headers.items() if k.lower() in ('request-id','history-item-id','character-cost','content-type')}
        record['provider_receipt']=metadata
        wave_bytes(source,body,24000)
        record['source_sha256']=sha(source)
        quality=pcm_quality(body,24000)
        record.update(status='accepted_acoustic',source_sha256=sha(source),quality=quality,native_wav=prepare_native(source,native))
        if quality['duration_seconds']>8 or quality['clipped_samples']:
            record.update(status='review_required',review_flag='clipping_or_excessive_duration')
        budget.finish(attempt_key,'response_received',metadata.get('character-cost'))
    except Exception as e:
        # request() removes credential-bearing HTTP details; local messages contain no auth.
        record.update(status='failed_or_unknown',error=str(e)[:300])
        if isinstance(e,PreconnectDNSError):record.update(failure_kind='preconnect_dns',transport_proof=dict(DNS_PROOF))
        reason=provider_stop_reason(e)
        if reason:budget.abort(reason)
        budget.finish(attempt_key,'failed_or_unknown')
    write(receipt,record)
    return record

def generate(jobs,workers=2):
    OUT.mkdir(exist_ok=True,parents=True)
    lock=OUT/'generation.lock'
    with lock.open('x',encoding='utf8') as f:f.write(str(time.time()))
    try:
        budget=Budget(OUT/'budget.json',100)
        result=[]
        from collections import defaultdict
        groups=defaultdict(list)
        for job in jobs:groups[job['voice_id']].append(job)
        progress_lock=threading.Lock()
        def voice_group(group):
            for job in group:
                if budget.stopped.is_set():break
                r=synthesize(job,budget)
                with progress_lock:
                    result.append(r)
                    print(f"{len(result)}/{len(jobs)} {r['family']} {r['status']} reserved=${budget.spent:.4f}",flush=True)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(voice_group,g) for g in groups.values()]
            for f in as_completed(futures):f.result()
        return result
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('jobs',type=Path);p.add_argument('--limit',type=int);p.add_argument('--workers',type=int,default=2);a=p.parse_args()
    jobs=read(a.jobs);jobs=jobs['jobs'] if isinstance(jobs,dict) else jobs
    if a.limit:jobs=jobs[:a.limit]
    generate(jobs,a.workers)
