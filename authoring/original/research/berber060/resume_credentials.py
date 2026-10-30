"""Explicit resume after the human restored a shared-account key. No paid calls."""
from pathlib import Path
from datetime import datetime,timezone
from common import OUT,ART,read,write
from account import request
from batch_generation import job_key
from generation import Budget

def resume():
    # Must be invoked only after the prior coordinator process has stopped.
    body,_=request('/v2/voices?page_size=1')
    lock=OUT/'generation.lock'
    if lock.exists():
        root=OUT.resolve();source=lock.resolve()
        if source.parent!=root:raise ValueError('Unexpected generation lock target')
        lock.rename(OUT/('generation-stopped-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.lock'))
    plan=read(ART/'recording-plan.json');p=ART/'credential-retries.json';epochs=read(p) if p.exists() else {}
    budget=Budget(OUT/'budget.json',100);keys=set();jobs=[]
    for j in plan['jobs']:
        rp=OUT/'receipts'/f'{job_key(j)}.json'
        if not rp.exists():continue
        r=read(rp)
        if r.get('error')!='ElevenLabs HTTP 401; status=invalid_api_key':continue
        epochs[j['id']]=epochs.get(j['id'],0)+1;jobs.append(j['id'])
        key=r.get('batch_id') or r.get('attempt_key') or r['request_id'];keys.add(key)
    released=0
    for key in keys:
        if key not in budget.data['reservations']:continue
        row=budget.data['reservations'][key]
        if row.get('status')=='provider_explicit_refusal':continue
        released+=row['reserved_usd'];row['refused_request_estimate_usd']=row['reserved_usd']
        row.update(reserved_usd=0,status='provider_explicit_refusal',provider_character_cost=0,
            reconciliation='HTTP401 explicitly rejected authorization; no generated audio response')
    write(budget.path,budget.data);write(p,epochs)
    result={'authentication_check':'passed; no paid synthesis','jobs_requeued_after_explicit_refusal':len(jobs),
        'released_unbilled_estimate_usd':released,'conservative_paid_or_uncertain_reserved_usd':budget.spent,
        'unknown_requests':'Not requeued blindly; retained for reconciliation'}
    write(OUT/'credential-resume.json',result);print(result);return result

if __name__=='__main__':resume()
