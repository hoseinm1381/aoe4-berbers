"""Optional timestamp batches. Importing/planning/tests never contact the provider."""
import base64, json, math, re, time, unicodedata, wave
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from common import OUT, ART, read, write, sha
from account import request, PreconnectDNSError, DNS_PROOF
from generation import Budget, request_id, pcm_quality, wave_bytes, prepare_native, synthesize, provider_stop_reason

RATE=24000
VERSION='timestamp-split-v1'
TIMING_QUANTIZATION_SECONDS=.040

def single_identity(job):
    # Keep byte-for-byte semantic parity with generation.synthesize identity.
    payload={'text':job['generation_text'],'model_id':job.get('model_id','eleven_v3'),
        'language_code':'ar','seed':job['seed'],'use_pvc_as_ivc':True,
        'voice_settings':{'stability':.5,'similarity_boost':.78,'style':0,'use_speaker_boost':False,'speed':1.0}}
    return {'voice_id':job['voice_id'],'output_format':'pcm_24000',**payload}

def job_key(job): return request_id(single_identity(job))

def spoken(job):
    return not (job.get('force_single') or job.get('script',{}).get('nonverbal') or job.get('nonverbal') or job.get('event','').lower().startswith('effort'))

def plan_batches(jobs):
    """Stable groups; actors serialized by scheduler, including nonverbal singles."""
    groups=defaultdict(list);seen=set()
    for job in jobs:
        key=job_key(job)
        if key in seen: continue
        seen.add(key)
        if spoken(job):
            group=(job['family'],job['voice_id'],job['age'],job['delivery'],job.get('model_id','eleven_v3'))
        else: group=('single',key)
        groups[group].append(job)
    return [group[i:i+8] for group in groups.values() for i in range(0,len(group),8)]

def batch_identity(jobs):
    if not 2<=len(jobs)<=8 or not all(spoken(j) for j in jobs): raise ValueError('Batch requires 2–8 spoken jobs')
    if len({(j['family'],j['voice_id'],j['age'],j['delivery'],j.get('model_id','eleven_v3')) for j in jobs})!=1:
        raise ValueError('Mixed family/actor/age/delivery/model batch')
    # Original text remains exact inside each phrase; punctuation is added only as a separator.
    text='\n\n'.join(j['generation_text'].rstrip()+('' if j['generation_text'].rstrip().endswith(('.', '!', '?', '؟', '。')) else '.') for j in jobs)
    identity=single_identity(jobs[0]);identity['text']=text
    return {'version':VERSION,'endpoint':'with-timestamps','member_request_ids':[job_key(j) for j in jobs],**identity}

def _normalized(text):
    """Retain letters/digits/diacritics; normalize only tags, spacing and punctuation."""
    text=re.sub(r'\[[^\[\]\r\n]*\]','',text)
    return ''.join(c for c in unicodedata.normalize('NFKC',text).casefold()
                   if c.isalnum() or unicodedata.category(c).startswith('M'))

def quiet_boundary(signal,left,right,rate):
    """Choose a bounded quiet cut, without changing peak/RMS acceptance limits."""
    gap=right-left
    if gap<.12:raise ValueError('Insufficient clean interphrase gap')
    midpoint=(left+right)/2;bound=min(.1,gap/6)
    steps=math.floor((bound+1e-9)/.005)
    offsets=[0.0]+[sign*step*.005 for step in range(1,steps+1) for sign in (-1,1)]
    for offset in offsets:
        center=midpoint+offset
        first=math.ceil((center-.02)*rate-1e-9)
        last=math.floor((center+.02)*rate+1e-9)
        if first<0 or last>len(signal) or first<math.ceil(left*rate) or last>math.floor(right*rate):continue
        window=signal[first:last]
        if len(window)<math.floor(rate*.04)-1:continue
        peak=float(np.max(np.abs(window)));rms=float(np.sqrt(np.mean(window*window)))
        if peak>.012 or rms>.003:continue
        # Actual adjoining cuts both lie in the verified 40ms quiet window.
        previous_end=math.floor((center-.005)*rate+1e-9)
        next_start=math.ceil((center+.005)*rate-1e-9)
        return {'method':'bounded-quiet-center-v2','gap_start_seconds':left,'gap_end_seconds':right,
            'midpoint_seconds':midpoint,'search_bound_seconds':bound,'search_step_seconds':.005,
            'selected_center_seconds':center,'offset_seconds':offset,'window_start_sample':first,
            'window_end_sample':last,'peak':peak,'rms':rms,
            'previous_end_sample':previous_end,'next_start_sample':next_start}
    raise ValueError('Interphrase boundary is not quiet')


def aligned_splits(jobs,alignment,pcm,rate=RATE,allow_partial=False):
    """Exact normalized character coverage plus clean, nonoverlapping phrase gaps."""
    chars=alignment.get('characters');starts=alignment.get('character_start_times_seconds');ends=alignment.get('character_end_times_seconds')
    if not isinstance(chars,list) or not chars or not isinstance(starts,list) or not isinstance(ends,list) or len(chars)!=len(starts) or len(chars)!=len(ends):
        raise ValueError('Missing or mismatched timing arrays')
    if len(pcm)%2: raise ValueError('Truncated batch PCM')
    duration=len(pcm)/2/rate
    if not 0<duration<=8*len(jobs)+4: raise ValueError('Batch duration outside bound')
    raw_starts=list(starts);raw_ends=list(ends)
    for i,(ch,start,end) in enumerate(zip(chars,raw_starts,raw_ends)):
        if not isinstance(ch,str) or len(ch)!=1: raise ValueError('Alignment is not character based')
        if isinstance(start,bool) or isinstance(end,bool) or not isinstance(start,(int,float)) or not isinstance(end,(int,float)) or not math.isfinite(start) or not math.isfinite(end) or start < -TIMING_QUANTIZATION_SECONDS-1e-9 or end<start or end>duration+TIMING_QUANTIZATION_SECONDS+1e-9:
            raise ValueError('Invalid alignment time')
        if i and (start<raw_starts[i-1] or end<raw_ends[i-1]): raise ValueError('Nonmonotonic alignment')
    # Provider timestamps may round a short tail past actual PCM. Preserve raw
    # alignment on disk and clamp only bounded quantization, never audio samples.
    starts=[max(0,min(duration,t)) for t in raw_starts]
    ends=[max(0,min(duration,t)) for t in raw_ends]
    # Remove bracketed directions from alignment while retaining original timing indices.
    joined=''.join(chars);tag_indices=set()
    for match in re.finditer(r'\[[^\[\]\r\n]*\]',joined):tag_indices.update(range(match.start(),match.end()))
    tokens=[];cluster=[]
    def flush_cluster():
        if cluster:
            value=_normalized(''.join(ch for _,ch in cluster))
            tokens.extend((c,cluster[0][0],cluster[-1][0]) for c in value)
            cluster.clear()
    for index,ch in enumerate(chars):
        if index in tag_indices:
            flush_cluster();continue
        if not unicodedata.category(ch).startswith('M'): flush_cluster()
        cluster.append((index,ch))
    flush_cluster()
    expected=[_normalized(j['generation_text']) for j in jobs]
    if any(not text for text in expected) or ''.join(t[0] for t in tokens)!=''.join(expected):
        raise ValueError('Normalized alignment does not exactly cover input phrases')
    spans=[];cursor=0
    for job,text in zip(jobs,expected):
        first=tokens[cursor][1];last=tokens[cursor+len(text)-1][2];cursor+=len(text)
        spans.append({'request_id':job_key(job),'first_character_index':first,'last_character_index':last,
            'speech_start_seconds':starts[first],'speech_end_seconds':ends[last],
            'raw_speech_start_seconds':raw_starts[first],'raw_speech_end_seconds':raw_ends[last],
            'timing_clamps':[{'character_index':i,'raw_start_seconds':raw_starts[i],
                'raw_end_seconds':raw_ends[i],'start_seconds':starts[i],'end_seconds':ends[i]}
                for i in range(first,last+1) if raw_starts[i]!=starts[i] or raw_ends[i]!=ends[i]],
            'normalized_text':text})
    if allow_partial:
        return _partial_splits(spans,pcm,rate)
    signal=np.frombuffer(pcm,dtype='<i2').astype(float)/32768
    boundaries={i:quiet_boundary(signal,spans[i-1]['speech_end_seconds'],span['speech_start_seconds'],rate)
                for i,span in enumerate(spans) if i}
    for i,span in enumerate(spans):
        start=span['speech_start_seconds'];end=span['speech_end_seconds']
        if end<=start: raise ValueError('Empty phrase timing')
        previous=spans[i-1]['speech_end_seconds'] if i else 0
        following=spans[i+1]['speech_start_seconds'] if i+1<len(spans) else duration
        if start<previous or end>following: raise ValueError('Coarticulation or neighboring timing overlap')
        # Exterior guards remain bounded; interior cuts use the measured quiet window.
        left=min(.08,(start-previous)/3);right=min(.08,(following-end)/3)
        first=max(0,math.ceil((start-left)*rate-1e-9));last=min(len(signal),math.floor((end+right)*rate+1e-9))
        if i:
            first=boundaries[i]['next_start_sample'];left=start-first/rate
            span['left_boundary']=boundaries[i]
        if i+1 in boundaries:
            last=boundaries[i+1]['previous_end_sample'];right=last/rate-end
            span['right_boundary']=boundaries[i+1]
        if first>math.floor(start*rate+1e-9) or last<math.ceil(end*rate-1e-9):
            raise ValueError('Quiet cut would remove aligned speech')
        if i and first<spans[i-1]['end_sample']: raise ValueError('Split guards overlap')
        span.update(start_sample=first,end_sample=last,left_guard_seconds=left,right_guard_seconds=right)
        part=pcm[first*2:last*2];quality=pcm_quality(part,rate)
        if quality['duration_seconds']>8: raise ValueError('Clip too long for RTS response')
        if quality['clipped_samples']: raise ValueError('Clip contains clipped samples')
        span['quality']=quality
    return spans

def _partial_splits(spans,pcm,rate):
    """Same strict cut criteria, with per-boundary/per-clip failure isolation.

    Called only after the unchanged global character/timing/text validation.
    Never writes audio/receipts. A bad boundary rejects both touching members.
    """
    signal=np.frombuffer(pcm,dtype='<i2').astype(float)/32768
    duration=len(signal)/rate
    for i,span in enumerate(spans):
        if span['speech_end_seconds']<=span['speech_start_seconds']:
            raise ValueError('Empty phrase timing')
        if i and span['speech_start_seconds']<spans[i-1]['speech_end_seconds']:
            raise ValueError('Coarticulation or neighboring timing overlap')
    boundaries={};boundary_errors={};errors=defaultdict(list)
    for i in range(1,len(spans)):
        try:boundaries[i]=quiet_boundary(signal,spans[i-1]['speech_end_seconds'],spans[i]['speech_start_seconds'],rate)
        except ValueError as error:
            detail={'boundary_index':i,'error':str(error)};boundary_errors[i]=detail
            errors[i-1].append(detail);errors[i].append(detail)
    accepted=[];rejected=[]
    for i,span in enumerate(spans):
        if not errors[i]:
            try:
                start=span['speech_start_seconds'];end=span['speech_end_seconds']
                previous=spans[i-1]['speech_end_seconds'] if i else 0
                following=spans[i+1]['speech_start_seconds'] if i+1<len(spans) else duration
                left=min(.08,(start-previous)/3);right=min(.08,(following-end)/3)
                first=max(0,math.ceil((start-left)*rate-1e-9));last=min(len(signal),math.floor((end+right)*rate-1e-9))
                if i:
                    first=boundaries[i]['next_start_sample'];left=start-first/rate;span['left_boundary']=boundaries[i]
                if i+1<len(spans):
                    last=boundaries[i+1]['previous_end_sample'];right=last/rate-end;span['right_boundary']=boundaries[i+1]
                if first>math.floor(start*rate+1e-9) or last<math.ceil(end*rate-1e-9):
                    raise ValueError('Quiet cut would remove aligned speech')
                span.update(start_sample=first,end_sample=last,left_guard_seconds=left,right_guard_seconds=right)
                quality=pcm_quality(pcm[first*2:last*2],rate)
                if quality['duration_seconds']>8:raise ValueError('Clip too long for RTS response')
                if quality['clipped_samples']:raise ValueError('Clip contains clipped samples')
                span['quality']=quality
                accepted.append(span)
            except ValueError as error:errors[i].append({'clip_index':i,'error':str(error)})
        if errors[i]:rejected.append({'clip_index':i,'request_id':span['request_id'],'errors':errors[i]})
    if any(a['end_sample']>=b['start_sample'] for a,b in zip(accepted,accepted[1:])):
        raise ValueError('Split guards overlap')
    return {'status':'partial' if rejected else 'all_passed','splits':accepted,'rejected':rejected,
        'boundary_errors':[boundary_errors[i] for i in sorted(boundary_errors)],
        'proof_policy':'Unchanged global alignment checks and strict per-clip cuts/acoustics; bad boundaries reject both adjacent members',
        'sample_rate':rate,'timing_quantization_tolerance_seconds':TIMING_QUANTIZATION_SECONDS}


def _receipt(job,batch_id,charge=0):
    key=job_key(job)
    return {'request_id':key,'job_id':job['id'],'family':job['family'],'identity':single_identity(job),
        'status':'started_batch','batch_id':batch_id,'reserved_usd':charge,
        'source':str(ART/'masters'/f'{key}.wav'),'native_path':str(OUT/'wav'/f'{key}.wav'),
        'native_playback':'not_tested','language_review':'pending'}

def _load_pcm(path):
    with wave.open(str(path),'rb') as stream:
        if (stream.getnchannels(),stream.getsampwidth(),stream.getframerate())!=(1,2,RATE): raise ValueError('Batch master PCM format changed')
        return stream.readframes(stream.getnframes())

def restore_batch(record,batch_path):
    """Lossless local reconstruction only; never sends a provider request."""
    master=Path(record['master']);alignment=Path(record['alignment'])
    if sha(master)!=record['master_sha256'] or sha(alignment)!=record['alignment_sha256']:
        raise ValueError('Saved batch source or alignment changed')
    pcm=_load_pcm(master);jobs=record['jobs']
    spans=aligned_splits(jobs,read(alignment),pcm)
    # Validate every cut before accepting any member.
    proof={'version':VERSION,'batch_id':record['batch_id'],'master_sha256':record['master_sha256'],
           'alignment_sha256':record['alignment_sha256'],'sample_rate':RATE,
           'timing_quantization_tolerance_seconds':TIMING_QUANTIZATION_SECONDS,'splits':spans}
    proof_path=OUT/'batches'/record['batch_id']/'split-proof.json';write(proof_path,proof)
    results=[]
    for job,span in zip(jobs,spans):
        item=_receipt(job,record['batch_id']);source=Path(item['source']);native=Path(item['native_path'])
        wave_bytes(source,pcm[span['start_sample']*2:span['end_sample']*2],RATE)
        item.update(status='accepted_acoustic',source_sha256=sha(source),quality=span['quality'],
            native_wav=prepare_native(source,native),provider_receipt=record.get('provider_receipt',{}),
            split_proof=str(proof_path),batch_master=str(master),batch_alignment=str(alignment),
            generation_mode='timestamp_batch',batch_seed=record['identity']['seed'],
            identity_note='Single-job cache identity retained; audio rendered in batch context with batch seed')
        write(OUT/'receipts'/f'{item["request_id"]}.json',item);results.append(item)
    if record.get('error'):
        record['prior_rejection']=record.pop('error')
    record.update(status='accepted_acoustic',split_proof=str(proof_path));write(batch_path,record)
    return results

def synthesize_batch(jobs,budget):
    identity=batch_identity(jobs);key=request_id(identity)
    folder=OUT/'batches'/key;batch_path=folder/'receipt.json'
    if batch_path.exists():
        record=read(batch_path)
        if record['identity']!=identity: raise ValueError('Batch resume identity changed')
        if record['status'] in ('response_saved','accepted_acoustic'):
            return restore_batch(record,batch_path)
        results=[]
        for job in jobs:
            path=OUT/'receipts'/f'{job_key(job)}.json'
            if path.exists(): item=read(path)
            else:
                # An interruption may occur between atomic batch/member writes.
                item=_receipt(job,key);item.update(status='failed_or_unknown',
                    error='Existing started/unknown batch; explicit reconciliation required')
                write(path,item)
            results.append(item)
        return results
    # A surviving reservation without receipt may have been billed before interruption.
    if key in budget.data['reservations']:
        results=[]
        for job in jobs:
            item=_receipt(job,key);item.update(status='failed_or_unknown',error='Existing batch reservation; explicit reconciliation required')
            write(OUT/'receipts'/f'{job_key(job)}.json',item);results.append(item)
        return results
    # Never overwrite a prior single or another batch's member identity.
    if any((OUT/'receipts'/f'{job_key(j)}.json').exists() for j in jobs):
        raise ValueError('Batch includes an existing job receipt; plan remaining jobs first')
    charge=max(1,len(identity['text']))*.30/1000
    budget.reserve(key,charge)
    record={'batch_id':key,'identity':identity,'jobs':jobs,'status':'started','reserved_usd':charge,
            'master':str(ART/'batch-masters'/f'{key}.wav'),'alignment':str(folder/'alignment.json')}
    write(batch_path,record)
    for job in jobs: write(OUT/'receipts'/f'{job_key(job)}.json',_receipt(job,key))
    try:
        payload={k:v for k,v in identity.items() if k not in ('version','endpoint','member_request_ids','voice_id','output_format')}
        body,headers=request('/v1/text-to-speech/'+jobs[0]['voice_id']+'/with-timestamps?output_format=pcm_24000',payload)
        response=json.loads(body)
        pcm=base64.b64decode(response['audio_base64'],validate=True)
        alignment=response.get('alignment')
        if not isinstance(alignment,dict): raise ValueError('Timestamp response missing raw alignment')
        record['provider_receipt']={k.lower():v for k,v in headers.items() if k.lower() in ('request-id','history-item-id','character-cost','content-type')}
        # Preserve returned source and alignment even when split validation rejects it.
        wave_bytes(Path(record['master']),pcm,RATE);write(Path(record['alignment']),alignment)
        record.update(status='response_saved',master_sha256=sha(record['master']),alignment_sha256=sha(record['alignment']))
        write(batch_path,record)
        budget.finish(key,'response_received',record['provider_receipt'].get('character-cost'))
        return restore_batch(record,batch_path)
    except Exception as error:
        reason=provider_stop_reason(error)
        if reason:budget.abort(reason)
        if isinstance(error,PreconnectDNSError):
            record.update(failure_kind='preconnect_dns',transport_proof=dict(DNS_PROOF))
        record.update(status='rejected_or_unknown',error=str(error)[:300]);write(batch_path,record)
        budget.finish(key,'rejected_or_unknown')
        results=[]
        for job in jobs:
            item=_receipt(job,key);item.update(status='rejected_or_unknown',error=record['error'])
            if record.get('failure_kind')=='preconnect_dns':
                item.update(failure_kind='preconnect_dns',transport_proof=dict(record['transport_proof']))
            write(OUT/'receipts'/f'{job_key(job)}.json',item);results.append(item)
        return results

QUALITY_FAILURES={
    'Missing or mismatched timing arrays','Truncated batch PCM','Batch duration outside bound',
    'Alignment is not character based','Invalid alignment time','Nonmonotonic alignment',
    'Normalized alignment does not exactly cover input phrases','Empty phrase timing',
    'Coarticulation or neighboring timing overlap','Insufficient clean interphrase gap',
    'Interphrase boundary is not quiet','Quiet cut would remove aligned speech',
    'Split guards overlap','Clip too long for RTS response','Clip contains clipped samples',
    'Generation too short','Generation is silent or nearly silent'}


def received_quality_failure(group):
    """Count only an explicit local rejection of hash-verified returned audio."""
    identity=batch_identity(group);key=request_id(identity)
    path=OUT/'batches'/key/'receipt.json'
    try:
        record=read(path)
        return (record.get('identity')==identity and record.get('status')=='rejected_or_unknown'
            and record.get('error') in QUALITY_FAILURES
            and sha(record['master'])==record['master_sha256']
            and sha(record['alignment'])==record['alignment_sha256'])
    except (OSError,ValueError,KeyError,TypeError,AttributeError):return False


def never_requested_group(group,budget):
    """Fallback must not bypass surviving single or batch request evidence."""
    key=request_id(batch_identity(group))
    return (key not in budget.data['reservations']
        and not (OUT/'batches'/key/'receipt.json').exists()
        and all(job_key(j) not in budget.data['reservations']
                and not (OUT/'receipts'/f'{job_key(j)}.json').exists() for j in group))


def generate_batches(jobs,workers=4):
    """Explicit opt-in execution. Per actor serialization; shared single-generator lock."""
    if not 1<=workers<=4: raise ValueError('Workers must be 1–4')
    OUT.mkdir(parents=True,exist_ok=True);lock=OUT/'generation.lock'
    with lock.open('x',encoding='utf8') as stream: stream.write(str(time.time()))
    try:
        budget=Budget(OUT/'budget.json',100);cached={};pending=[];restored=set()
        for job in jobs:
            key=job_key(job);path=OUT/'receipts'/f'{key}.json'
            if not path.exists(): pending.append(job);continue
            old=read(path)
            if old.get('batch_id') and old['batch_id'] not in restored:
                bp=OUT/'batches'/old['batch_id']/'receipt.json'
                if bp.exists():
                    batch=read(bp)
                    if batch['status'] in ('response_saved','accepted_acoustic'):
                        restore_batch(batch,bp)
                restored.add(old['batch_id']);old=read(path)
            # Cached accepted records still get the same source/native hash checks as singles.
            if old['status']=='accepted_acoustic':
                if old.get('quality',{}).get('clipped_samples',0) or old.get('quality',{}).get('duration_seconds',0)>8:
                    old.update(status='review_required',review_flag='clipping_or_excessive_duration');write(path,old)
                source=Path(old['source']);native=Path(old['native_path'])
                if not source.is_file() or sha(source)!=old['source_sha256']:raise ValueError('Cached accepted source changed')
                if not native.is_file() or sha(native)!=old['native_wav']['sha256']:
                    old['native_wav']=prepare_native(source,native);write(path,old)
            cached[key]=old
        actors=defaultdict(list)
        for group in plan_batches(pending): actors[group[0]['voice_id']].append(group)
        def actor_sequence_work(groups):
            result=[];quality_failures=0
            for group in groups:
                stopped=getattr(budget,'stopped',None)
                if stopped is not None and stopped.is_set():break
                if len(group)==1:
                    # Nonverbal and orphan spoken jobs retain the existing singles route.
                    result.append(synthesize(group[0],budget))
                elif quality_failures>=2 and never_requested_group(group,budget):
                    # Only later never-requested groups switch route. Failed batch
                    # members keep their original receipts for explicit repair.
                    for job in group:
                        if budget.stopped.is_set():break
                        result.append(synthesize(job,budget))
                else:
                    result.extend(synthesize_batch(group,budget))
                    if received_quality_failure(group):quality_failures+=1
                print('BATCH_PROGRESS',group[0]['family'],len(result),
                      'accepted='+str(sum(r['status']=='accepted_acoustic' for r in result)),
                      'reserved_usd='+str(round(budget.spent,4)),flush=True)
            return result
        def actor_sequence(groups):
            try:return actor_sequence_work(groups)
            except Exception:
                # A local write/allocation failure is not a provider refusal.
                # Stop other actor workers before propagating, retaining exact
                # receipts/reservations rather than inventing a retryable result.
                budget.abort('Unexpected local generation failure; existing outcomes retained')
                raise
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for result in pool.map(actor_sequence,actors.values()):
                for item in result:cached[item['request_id']]=item
        return [cached.get(job_key(j),{'request_id':job_key(j),'job_id':j['id'],
            'family':j['family'],'status':'not_generated','reason':getattr(budget,'stop_reason',None)}) for j in jobs]
    finally: lock.unlink(missing_ok=True)
