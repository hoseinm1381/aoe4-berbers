"""Prepare explicit bounded retakes for hash-proved returned quality failures."""
from pathlib import Path
from common import OUT,ART,read,write,sha
from batch_generation import job_key,single_identity,batch_identity,QUALITY_FAILURES
from generation import request_id

REFUSALS={'ElevenLabs HTTP 409; status=already_running',
          'ElevenLabs HTTP 429; status=too_many_concurrent_requests'}
QUALITY_ERRORS=QUALITY_FAILURES|{'Truncated PCM response','Unexpected source PCM'}


def checked(path,expected):
    if not expected or not Path(path).is_file() or sha(path)!=expected:
        raise ValueError('Returned source/alignment missing or digest changed')
    return expected


def quality_proof(job,receipt):
    if receipt.get('error') and receipt['error'] not in QUALITY_ERRORS:return None
    quality=receipt.get('quality',{})
    bad=bool(quality.get('clipped_samples',0) or quality.get('duration_seconds',0)>8)
    if not bad and receipt.get('error') not in QUALITY_ERRORS:return None
    if receipt.get('batch_id'):
        batch=read(OUT/'batches'/receipt['batch_id']/'receipt.json')
        identity=batch_identity(batch['jobs'])
        if (batch.get('identity')!=identity or request_id(identity)!=receipt['batch_id']
                or job_key(job) not in {job_key(j) for j in batch['jobs']}
                or batch.get('error') not in QUALITY_ERRORS):
            raise ValueError('Returned batch identity/quality evidence differs')
        return {'batch_id':receipt['batch_id'],
            'master_sha256':checked(batch['master'],batch.get('master_sha256')),
            'alignment_sha256':checked(batch['alignment'],batch.get('alignment_sha256'))}
    return {'source_sha256':checked(receipt['source'],receipt.get('source_sha256'))}


def _prepare_locked():
    plan=read(ART/'recording-plan.json');path=ART/'retake-overrides.json'
    overrides=read(path) if path.exists() else {};changes=[];unknown=[]
    budget=read(OUT/'budget.json')
    if budget['cap_usd']!=100:raise ValueError('Unexpected authorized spending ceiling')
    reservations=budget['reservations']
    for job in plan['jobs']:
        key=job_key(job);rp=OUT/'receipts'/f'{key}.json'
        if not rp.exists():continue
        try:
            receipt=read(rp)
            if (receipt.get('request_id')!=key or receipt.get('identity')!=single_identity(job)
                    or receipt.get('job_id')!=job['id'] or receipt.get('family')!=job['family']):
                raise ValueError('Current receipt family/job/request identity differs')
            prior=overrides.get(job['id'],{})
            if prior.get('prepared_from_request_id')==key or prior.get('prior_request_id')==key:continue
            state=receipt['status']
            if state not in ('accepted_acoustic','review_required','failed_or_unknown','rejected_or_unknown','rejected'):
                unknown.append({'job_id':job['id'],'status':state,'reason':'Unattempted/interrupted work requires separate review'})
                continue
            proof=quality_proof(job,receipt)
            if proof:
                reason='Hash-proved returned source failed timing/acoustic gate: '+str(receipt.get('error') or receipt.get('review_flag') or 'clipping/duration')
            elif state!='accepted_acoustic' and receipt.get('error') in REFUSALS:
                reason='Provider explicitly refused generation; retry separately';proof={'explicit_refusal':receipt['error']}
            elif state=='accepted_acoustic':continue
            else:
                unknown.append({'job_id':job['id'],'status':state,'error':receipt.get('error'),
                    'reason':'No verified returned quality failure; unknown outcomes need explicit review'})
                continue
            attempt=prior.get('attempt',0)+1
            if attempt>2:
                unknown.append({'job_id':job['id'],'status':'retake_limit','reason':reason});continue
            original_attempt=receipt.get('batch_id') or receipt.get('attempt_key') or key
            if original_attempt not in reservations:raise ValueError('Original attempt reservation missing')
            # Extend offsets without dropping manual or network/credential epochs.
            for multiplier in range(1,101):
                delta=100000*multiplier
                replacement=dict(job,seed=(job['seed']+delta)%(2**32));new_key=job_key(replacement)
                if new_key not in reservations and not (OUT/'receipts'/f'{new_key}.json').exists():break
            else:raise ValueError('No noncolliding replacement identity')
            history=prior.get('retake_history',[])+[{'request_id':key,'receipt_sha256':sha(rp),
                'previous_prior_request_id':prior.get('prior_request_id'),'previous_reason':prior.get('reason'),
                'seed_offset_before':prior.get('seed_offset',0),'seed_delta':delta,'proof':proof,
                'original_attempt_key':original_attempt,
                'credential_retry_epoch':job.get('credential_retry_epoch',0),
                'network_retry_epoch':job.get('network_retry_epoch',0)}]
            overrides[job['id']]={**prior,'seed_offset':prior.get('seed_offset',0)+delta,
                'attempt':attempt,'force_single':True,'reason':reason,'prior_request_id':key,
                'prepared_from_request_id':key,'replacement_request_id':new_key,'retake_history':history}
            changes.append({'job_id':job['id'],**overrides[job['id']]})
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:
            unknown.append({'job_id':job['id'],'status':'held_invalid_evidence','error':str(error)})
    if changes:write(path,overrides)
    report={'retakes':changes,'unresolved':unknown,'provider_calls':0,'budget_changed':False,
        'policy':'Only exact current hash-proved quality failures or explicit concurrency refusals; at most two existing attempt-count deliberate replacements per job; all original reservations retained'}
    write(OUT/'retake-preparation.json',report)
    print('Prepared retakes',len(changes),'unknown',len(unknown));return report


def prepare_retakes():
    lock=OUT/'generation.lock'
    try:
        with lock.open('x',encoding='utf8') as stream:stream.write('offline quality retake planning')
    except FileExistsError:raise ValueError('Wait for active generation before preparing retakes') from None
    try:return _prepare_locked()
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':prepare_retakes()
