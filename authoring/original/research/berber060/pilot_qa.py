"""Supplementary ASR checks; no claim of native pronunciation or audible routing."""
import json,re,urllib.request,urllib.error,uuid
from pathlib import Path
from common import OUT,ART,read,write,sha
from account import credential
from generation import Budget
from batch_generation import job_key

def transcribe(job,receipt):
    key=receipt['request_id'];target=OUT/'pilot-asr'/f'{key}.json'
    if target.exists():
        old=read(target)
        if old.get('source_sha256')!=sha(receipt['source']):raise ValueError('Cached ASR source changed')
        return old
    if (OUT/'generation.lock').exists():raise ValueError('ASR must share the single budget coordinator; wait for synthesis to stop')
    budget=Budget(OUT/'budget.json',100)
    if 'asr:'+key in budget.data['reservations']:
        raise ValueError('Existing ASR reservation without receipt; explicit reconciliation required')
    budget.reserve('asr:'+key,.05)
    boundary='berber'+uuid.uuid4().hex
    data=Path(receipt['source']).read_bytes();chunks=[]
    for k,v in [('model_id','scribe_v2'),('language_code','ar'),('tag_audio_events','true')]:
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="pilot.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()+data+b'\r\n')
    chunks.append(f'--{boundary}--\r\n'.encode())
    req=urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text',data=b''.join(chunks),headers={'xi-api-key':credential(),'Content-Type':'multipart/form-data; boundary='+boundary})
    result={'job_id':job['id'],'family':job['family'],'expected':job['script']['text'],'nonverbal':job['script']['nonverbal'],'source_sha256':sha(receipt['source']),'acceptance':'supplementary_transcription_only'}
    try:
        with urllib.request.urlopen(req,timeout=120) as response:result['asr']=json.loads(response.read())
        budget.finish('asr:'+key,'response_received')
        text=result['asr'].get('text','')
        if job['script']['nonverbal'] and re.search(r'grunt|brief|wordless|cough|gasp|cry|effort|dying',text,re.I):result['flag']='possible_spoken_direction_tag'
    except urllib.error.HTTPError as e:
        result['error']='Speech-to-text HTTP '+str(e.code);budget.finish('asr:'+key,'failed_or_unknown')
    except Exception:
        result['error']='Speech-to-text transport failure; not automatically retried';budget.finish('asr:'+key,'failed_or_unknown')
    write(target,result);return result

def main():
    jobs=read(OUT/'character-pilot-jobs.json');results=[]
    for family in ('tuareg','handgunner','imam'):
        for job in [j for j in jobs if j['family']==family][:5]:
            path=OUT/'receipts'/f'{job_key(job)}.json'
            r=read(path)
            if r['status']!='accepted_acoustic':continue
            result=transcribe(job,r);results.append(result)
            print(json.dumps({'family':family,'event':job['event'],'expected':result['expected'],'heard_by_ASR':result.get('asr',{}).get('text'),'flag':result.get('flag'),'error':result.get('error')},ensure_ascii=False),flush=True)
    write(OUT/'pilot-asr-summary.json',results)

if __name__=='__main__':main()
