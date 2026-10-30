"""Scoped GET-only history reconciliation; no synthesis or production writes.

Run in the root chat's credential context. Raw account lists are never persisted.
Only exact voice/text/model/TTS/today/settings/time matches may be saved locally.
No recovered item is automatically promoted into production receipts or masters.
"""
import hashlib,io,json,re,wave,math
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode,quote
from common import OUT,ART,read,write,sha
from account import request
from batch_generation import job_key

DOCS=['https://elevenlabs.io/docs/api-reference/history/'+p for p in ('list','get','get-audio')]


def targets():
    plan={j['id']:j for j in read(ART/'recording-plan.json')['jobs']};result=[];batches=set()
    for unresolved in read(OUT/'retake-preparation.json')['unresolved']:
        job=plan[unresolved['job_id']];receipt_path=OUT/'receipts'/(job_key(job)+'.json');receipt=read(receipt_path)
        if receipt.get('status') not in ('started','started_batch','failed_or_unknown'):continue
        batch=receipt.get('batch_id')
        if batch:
            if batch in batches:continue
            batches.add(batch);path=OUT/'batches'/batch/'receipt.json';record=read(path)
            result.append({'id':batch,'kind':'batch','job_ids':[j['id'] for j in record['jobs']],
                'identity':record['identity'],'receipt_mtime':path.stat().st_mtime,'alignment_available':Path(record['alignment']).is_file()})
        else:result.append({'id':receipt['request_id'],'kind':'single','job_ids':[job['id']],
            'identity':receipt['identity'],'receipt_mtime':receipt_path.stat().st_mtime})
    return result


def matching(item,target,start,end):
    expected=target['identity'];settings=item.get('settings') or {}
    return (item.get('voice_id')==expected['voice_id'] and item.get('text')==expected['text'] and
        item.get('model_id')==expected['model_id'] and item.get('source')=='TTS' and
        start<=item.get('date_unix',0)<end and abs(item.get('date_unix',0)-target['receipt_mtime'])<=300 and
        all(settings.get(k)==v for k,v in expected['voice_settings'].items()) and
        ('seed' not in settings or settings['seed']==expected['seed']))


def diagnostics(items,target,start,end):
    expected=target['identity'];current=list(items);counts={'returned':len(current)}
    steps=[('voice',lambda x:x.get('voice_id')==expected['voice_id']),
        ('text',lambda x:x.get('text')==expected['text']),
        ('model',lambda x:x.get('model_id')==expected['model_id']),
        ('source',lambda x:x.get('source')=='TTS'),
        ('date',lambda x:start<=x.get('date_unix',0)<end),
        ('time',lambda x:abs(x.get('date_unix',0)-target['receipt_mtime'])<=300),
        ('settings',lambda x:all((x.get('settings') or {}).get(k)==v for k,v in expected['voice_settings'].items()))]
    for name,predicate in steps:
        current=[x for x in current if predicate(x)];counts[name]=len(current)
    # No IDs, text, actor details or settings values from account history retained.
    exact=[]
    for x in items:
        if x.get('voice_id')!=expected['voice_id'] or x.get('text')!=expected['text']:continue
        settings=x.get('settings') or {}
        exact.append({'missing_settings_keys':sorted(k for k in expected['voice_settings'] if k not in settings),
            'differing_settings_keys':sorted(k for k,v in expected['voice_settings'].items() if k in settings and settings[k]!=v),
            'time_delta_seconds':x.get('date_unix',0)-target['receipt_mtime'],
            'alignment_present':isinstance(x.get('alignments'),dict)})
    return {'sequential_filter_counts':counts,'exact_voice_text_candidates':exact}


def alignment_summary(item):
    value=item.get('alignments')
    if not isinstance(value,dict):return {'available':False,'schema_valid':False}
    def valid(row):
        if not isinstance(row,dict):return False
        keys=('characters','character_start_times_seconds','character_end_times_seconds')
        if not all(isinstance(row.get(k),list) for k in keys):return False
        chars,starts,ends=(row[k] for k in keys)
        if not chars or not len(chars)==len(starts)==len(ends):return False
        return all(isinstance(c,str) and isinstance(a,(int,float)) and isinstance(b,(int,float)) and
            math.isfinite(a) and math.isfinite(b) and 0<=a<=b for c,a,b in zip(chars,starts,ends))
    tables=[value]+[r for r in value.values() if isinstance(r,dict)]
    valid_tables=[row for row in tables if valid(row)]
    return {'available':True,'schema_valid':bool(valid_tables),'valid_tables':len(valid_tables),
        'keys':sorted(value),'acceptance':'Root must verify exact batch text, timing, PCM source and safe split; metadata presence alone is insufficient'}


def audio_format(data,metadata,headers=None):
    # HTTP response type describes the returned bytes; metadata can describe a
    # default compressed history representation. Neither alone proves PCM rate.
    response_type=next((v.split(';',1)[0].strip().lower() for k,v in (headers or {}).items() if k.lower()=='content-type'),None)
    content_type=response_type or str(metadata.get('content_type','')).lower()
    if data[:4]==b'RIFF':
        try:
            with wave.open(io.BytesIO(data),'rb') as w:
                if (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,24000):
                    return {'format':'mono_pcm_s16le_24000_wave','lossless':True,'frames':w.getnframes()}
        except (wave.Error,EOFError):pass
        return {'format':'unproven_or_lossy','lossless':False,'reason':'WAVE is invalid or not mono s16le24k'}
    compressed=(data[:3]==b'ID3' or data[:4] in (b'OggS',b'fLaC') or (len(data)>1 and data[0]==255 and data[1]&224==224))
    if not compressed and metadata.get('output_format')=='pcm_24000' and content_type in ('audio/pcm','audio/x-pcm') and data and len(data)%2==0:
        return {'format':'raw_pcm_s16le_24000','lossless':True,'frames':len(data)//2,'response_content_type':content_type}
    return {'format':'unproven_or_lossy','lossless':False,'reason':'Cannot prove original PCM24000; compressed/octet-stream bytes are never guessed to be raw PCM'}


def reconcile():
    destination=OUT/'history-reconciliation';now=datetime.now(timezone(timedelta(hours=3,minutes=30)))
    day=now.replace(hour=0,minute=0,second=0,microsecond=0);start=int(day.timestamp());end=int((day+timedelta(days=1)).timestamp())
    report={'status':'running','scope':'today Tehran; exact voice/text; source TTS; model eleven_v3',
        'http_requests':0,'synthesis_calls':0,'budget_changed':False,'production_receipts_changed':False,
        'unrelated_history_saved':False,'documentation':DOCS,'results':[]}
    def get(path):
        if not path.startswith('/v1/history'):raise ValueError('Only history GET routes authorized')
        body,headers=request(path);report['http_requests']+=1;return body,headers
    try:
        for target in targets():
            identity=target['identity'];query={'voice_id':identity['voice_id'],'search':identity['text'],
                'source':'TTS','model_id':'eleven_v3','date_after_unix':start,'date_before_unix':end,'page_size':100}
            matches=[];pages=0;scoped_items=[]
            while True:
                body,_=get('/v1/history?'+urlencode(query));page=json.loads(body);pages+=1
                scoped_items.extend(page.get('history',[]))
                matches.extend(item for item in page.get('history',[]) if matching(item,target,start,end))
                if not page.get('has_more'):break
                cursor=page.get('last_history_item_id')
                if not cursor or pages>=10:raise ValueError('Scoped history pagination incomplete; uniqueness unproven')
                query['start_after_history_item_id']=cursor
            row={k:target[k] for k in ('id','kind','job_ids')};row.update(exact_matches=len(matches),pages=pages,diagnostics=diagnostics(scoped_items,target,start,end))
            if len(matches)!=1:
                row['status']='held_no_unique_settings_and_time_match';report['results'].append(row);continue
            history_id=matches[0]['history_item_id']
            if not re.fullmatch(r'[A-Za-z0-9_-]+',history_id):raise ValueError('Unsafe history identity')
            body,_=get('/v1/history/'+quote(history_id));item=json.loads(body)
            if not matching(item,target,start,end):raise ValueError('History details changed or no longer match')
            folder=destination/target['id'];write(folder/'metadata.json',item)
            row.update(history_item_id=history_id,metadata_sha256=sha(folder/'metadata.json'))
            # Fetch only this exact matched original item. No format conversion request.
            audio,headers=get('/v1/history/'+quote(history_id)+'/audio');fmt=audio_format(audio,item,headers)
            extension='.wav' if fmt['format'].endswith('_wave') else '.pcm' if fmt['lossless'] else '.unverified-audio'
            path=folder/('original'+extension);path.write_bytes(audio)
            row.update(audio=fmt,audio_path=str(path),audio_sha256=sha(path),audio_bytes=len(audio),
                response_content_type=next((v for k,v in headers.items() if k.lower()=='content-type'),None))
            if target['kind']=='batch':
                summary=alignment_summary(item)
                row.update(status='batch_candidate_for_root_review' if summary['schema_valid'] and fmt['lossless'] else 'held_batch_source_or_alignment_unproven',
                    local_alignment_available=target.get('alignment_available',False),history_alignment=summary)
            else:row['status']='lossless_candidate_for_root_review' if fmt['lossless'] else 'held_lossless_original_not_proven'
            report['results'].append(row)
        report['status']='completed_readonly'
    except (RuntimeError,ValueError,OSError,KeyError) as error:
        report.update(status='blocked_permissions' if 'missing_permissions' in str(error) else 'blocked',error=str(error))
    write(destination/'report.json',report)
    print(json.dumps({'status':report['status'],'http_requests':report['http_requests'],'results':[(r['kind'],r['status']) for r in report['results']],'error':report.get('error')}))
    return report

if __name__=='__main__':reconcile()
