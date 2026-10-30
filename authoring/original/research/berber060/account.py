"""Read-only account discovery; explicitly supplied session credential stays in memory."""
import json, os, re, socket, http.client, urllib.request, urllib.error
from pathlib import Path
from functools import lru_cache
from common import OUT, write

DNS_ERROR='ElevenLabs preconnect DNS failure; request not transmitted'
DNS_PROOF={'stage':'open_before_response','kind':'socket.gaierror','redirects':'disabled',
           'request_body_transmitted':False}


class PreconnectDNSError(RuntimeError):
    def __init__(self):super().__init__(DNS_ERROR)


class TransportOutcomeUnknown(RuntimeError):
    def __init__(self,message='ElevenLabs transport error; outcome unknown'):super().__init__(message)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        # Otherwise a second-host DNS error could follow an already-sent POST.
        raise urllib.error.HTTPError(req.full_url,code,'API redirect refused',headers,fp)

@lru_cache(maxsize=1)
def credential():
    value=os.environ.get('ELEVENLABS_API_KEY')
    if value: return value
    # The desktop process may predate a newly set user environment variable.
    # Read only the exact credential variable the human was instructed to set.
    if os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as env_key:
                value,kind=winreg.QueryValueEx(env_key,'ELEVENLABS_API_KEY')
            if kind in (winreg.REG_SZ,winreg.REG_EXPAND_SZ) and value.strip():return value.strip()
        except FileNotFoundError:pass
    # Only this chat, only its human messages; never search unrelated sessions or stores.
    tid=os.environ.get('CODEX_THREAD_ID','')
    if not re.fullmatch(r'[0-9a-f-]{36}',tid): raise RuntimeError('Session credential unavailable')
    candidates=list((Path.home()/'.codex/sessions/2026/10/16').glob('*'+tid+'.jsonl'))
    if len(candidates)!=1: raise RuntimeError('Exact authorized session not found')
    result=None
    with candidates[0].open(encoding='utf8') as f:
        for line in f:
            item=json.loads(line); payload=item.get('payload',{})
            if item.get('type')!='response_item' or payload.get('role')!='user': continue
            for block in payload.get('content',[]):
                for value in re.findall(r'\bsk_[a-f0-9]{40,80}\b',block.get('text','')): result=value
    if not result: raise RuntimeError('Provided credential not present in this chat')
    return result

def request(path,payload=None):
    key=credential()
    req=urllib.request.Request('https://api.elevenlabs.io'+path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'xi-api-key':key,'Content-Type':'application/json'})
    try:
        response=urllib.request.build_opener(NoRedirect()).open(req,timeout=120)
    except urllib.error.HTTPError as e:
        # Never surface request headers, body or credential-bearing exception repr.
        try: detail=json.loads(e.read()).get('detail',{})
        except Exception: detail={}
        status=detail.get('status','unknown') if isinstance(detail,dict) else 'unknown'
        raise RuntimeError(f'ElevenLabs HTTP {e.code}; status={status}') from None
    except urllib.error.URLError as error:
        if isinstance(error.reason,socket.gaierror):raise PreconnectDNSError() from None
        raise TransportOutcomeUnknown() from None
    except (OSError,http.client.HTTPException):
        raise TransportOutcomeUnknown() from None
    # An exception after receiving response headers is never proof of an unsent request.
    try:
        with response as r:return r.read(),dict(r.headers)
    except Exception:
        raise TransportOutcomeUnknown('ElevenLabs response read error; outcome unknown') from None

def discover():
    results={}
    for name,path in [('subscription','/v1/user/subscription'),('models','/v1/models'),('voices','/v2/voices?page_size=100')]:
        try:
            body,_=request(path); value=json.loads(body)
            write(OUT/'account'/f'{name}.json',value)
            if name=='subscription':
                results[name]={k:value.get(k) for k in ('tier','character_count','character_limit','can_extend_character_limit','status','max_voice_add_edits')}
            elif name=='models':results[name]=[m.get('model_id') for m in value]
            else:results[name]={'count':len(value.get('voices',[])),'has_more':value.get('has_more')}
        except RuntimeError as e:results[name]={'error':str(e)}
    write(OUT/'account/discovery.json',results)
    print(json.dumps(results,indent=2))

if __name__=='__main__':discover()
