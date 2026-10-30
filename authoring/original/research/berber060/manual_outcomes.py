"""Explicit bounded replacements after unrecoverable interrupted requests.

This is a deliberate new performance, not an automatic retry. The uncertain
original reservation remains counted in full. No provider call is made here.
"""
import argparse,math,re
from pathlib import Path
from common import OUT,ART,read,write,sha
from batch_generation import job_key,single_identity,batch_identity
from generation import request_id

TRANSPORT_EVIDENCE_SHA256='556cc8f76dca35c1d1bb992742fafc83c113e853e49e508035024d6516f5efb6'
CAPTURED_BULK_SHA256='65e39a63644b3b885a42a1d2aca2ee1f14b6beb598c45e7a9468f2c562fdf7f3'


def transport_error(error):
    return isinstance(error,str) and (bool(re.fullmatch(r'IncompleteRead\([0-9]+ bytes read, [0-9]+ more expected\)',error))
        or error=='Remote end closed connection without response'
        or error=='<urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1032)>')


def reviewed_transport_targets():
    path=OUT/'manual-outcomes-review-evidence.json'
    if sha(path)!=TRANSPORT_EVIDENCE_SHA256:raise ValueError('Reviewed transport evidence fingerprint changed')
    evidence=read(path)
    if evidence['bulk_results_sha256']!=CAPTURED_BULK_SHA256:raise ValueError('Unexpected reviewed bulk snapshot')
    return [{'id':row.get('batch_id') or row['request_id'],'kind':'batch' if row.get('batch_id') else 'single',
             'job_ids':[row['job_id']],'prior_request_id':row['request_id'],'error':row['error'],
             'status':'explicit_reviewed_transport','exact_matches':0,
             'evidence_sha256':TRANSPORT_EVIDENCE_SHA256,'bulk_results_sha256':CAPTURED_BULK_SHA256}
            for row in evidence['non_dns_transport_unknown_records'] if transport_error(row.get('error'))]


def assert_no_local_recoverable_audio(job,key,receipt,target):
    records=[receipt]
    paths=[ART/'masters'/f'{key}.wav',OUT/'wav'/f'{key}.wav']
    if target['kind']=='batch':
        batch=read(OUT/'batches'/target['id']/'receipt.json')
        if (batch.get('identity')!=batch_identity(batch['jobs'])
                or request_id(batch['identity'])!=target['id']
                or key not in {job_key(j) for j in batch['jobs']}
                or batch.get('error')!=target['error']):
            raise ValueError('Reviewed transport batch evidence changed')
        records.append(batch)
        paths.extend([ART/'batch-masters'/f'{target["id"]}.wav',OUT/'batches'/target['id']/'alignment.json'])
    for record in records:
        paths.extend(Path(record[k]) for k in
            ('source','native_path','master','alignment','batch_master','batch_alignment') if record.get(k))
    if any(path.exists() for path in paths):
        raise ValueError('Local audio/alignment evidence requires recovery review before a new performance')


def _prepare_locked(transport_reviewed=False):
    if transport_reviewed:targets=reviewed_transport_targets()
    else:
        history=read(OUT/'history-reconciliation/report.json')
        if history['status']!='completed_readonly':raise ValueError('History investigation incomplete')
        targets=history['results']
    budget=read(OUT/'budget.json');reserved=sum(r['reserved_usd'] for r in budget['reservations'].values())
    if budget['cap_usd']!=100 or not math.isfinite(reserved) or reserved<0:
        raise ValueError('Invalid authorized spending ceiling or reservations')
    plan=read(ART/'recording-plan.json');jobs={j['id']:j for j in plan['jobs']}
    path=ART/'retake-overrides.json';overrides=read(path) if path.exists() else {}
    report_path=ART/'manual-retake-decisions.json'
    previous=read(report_path).get('decisions',[]) if report_path.exists() else []
    decided={row['prior_request_id'] for row in previous}
    # If a prior process persisted its decision but not the override file, replay
    # that exact committed override, never commission an additional performance.
    restored_overrides=False
    for decision in previous:
        saved=decision.get('replacement_override')
        if saved and overrides.get(decision['job_id'],{})==decision.get('prior_override',{}):
            overrides[decision['job_id']]=saved;restored_overrides=True
    decisions=[]
    for target in targets:
        if target['status'] not in ('held_no_unique_settings_and_time_match','explicit_reviewed_transport') or target['exact_matches']:
            continue
        for jid in target['job_ids']:
            # A compiled replacement plan no longer names the original receipt.
            # Skip prior decisions before looking up that fresh request identity.
            if transport_reviewed and target['prior_request_id'] in decided:continue
            if not transport_reviewed and overrides.get(jid,{}).get('manual_outcome_replacement'):
                continue
            job=jobs[jid];key=job_key(job)
            if transport_reviewed and key!=target['prior_request_id']:
                raise ValueError('Reviewed transport current request identity changed')
            receipt=read(OUT/'receipts'/f'{key}.json')
            if receipt.get('request_id')!=key or receipt.get('identity')!=single_identity(job) or receipt.get('job_id')!=jid:
                raise ValueError('Interrupted receipt identity changed')
            allowed=('failed_or_unknown','rejected_or_unknown') if transport_reviewed else ('started','started_batch','failed_or_unknown')
            if receipt['status'] not in allowed:
                continue
            if transport_reviewed:
                if receipt.get('error')!=target['error']:raise ValueError('Reviewed transport receipt error changed')
                assert_no_local_recoverable_audio(job,key,receipt,target)
            investigated=receipt.get('batch_id') if target.get('kind')=='batch' else key
            if (target.get('kind') not in ('single','batch') or target['id']!=investigated
                    or bool(receipt.get('batch_id'))!=(target['kind']=='batch')):
                raise ValueError('History investigation does not match interrupted request')
            attempt=receipt.get('batch_id') or receipt.get('attempt_key') or key
            if target['kind']=='single' and attempt!=key and not re.fullmatch(re.escape(key)+r':retry[1-9][0-9]*',attempt):
                raise ValueError('Original attempt identity mismatch')
            if attempt not in budget['reservations']:
                raise ValueError('Original uncertain attempt reservation missing')
            replacement=dict(job,seed=(job['seed']+700000)%(2**32))
            replacement_key=job_key(replacement)
            if replacement_key in budget['reservations'] or (OUT/'receipts'/f'{replacement_key}.json').exists():
                raise ValueError('Replacement performance identity already attempted')
            reason=('Explicit replacement after interrupted original: saved files and scoped provider history '
                'could not recover a verified performance. Original charge remains uncertain and its full '
                'reservation is retained; this separate seeded performance is bounded by the authorized $100 ceiling.')
            if transport_reviewed:
                reason=('Explicit reviewed new performance after non-DNS transport/partial-read outcome: no local '
                    'source/master/alignment can be recovered. Provider history was not checked for this request. '
                    'Original uncertain reservation remains counted in full; this separately seeded performance '
                    'is bounded by the authorized $100 ceiling, not a blind resend or charge refund.')
            prior=overrides.get(jid,{})
            override={**prior,'seed_offset':prior.get('seed_offset',0)+700000,'attempt':prior.get('attempt',0)+1,'force_single':True,'reason':reason,
                'prior_request_id':key,'manual_outcome_replacement':True}
            decisions.append({'job_id':jid,'prior_request_id':key,'reviewed_request_target':target['id'],
                'original_attempt_key':attempt,'original_reserved_usd':budget['reservations'][attempt]['reserved_usd'],
                'replacement_request_id':replacement_key,
                'replacement_override':dict(override),
                'prior_override':dict(prior),
                'new_estimated_upper_bound_usd':len(job['generation_text'])*.30/1000,'reason':reason})
            decisions[-1].update(basis='explicit_reviewed_transport' if transport_reviewed else 'scoped_history_unrecoverable',
                original_receipt_sha256=sha(OUT/'receipts'/f'{key}.json'))
            if transport_reviewed:
                decisions[-1].update(transport_evidence_sha256=target['evidence_sha256'],
                    captured_bulk_sha256=target['bulk_results_sha256'],provider_history_checked=False)
            else:decisions[-1]['investigated_history_target']=target['id']
            overrides[jid]=override
            decided.add(key)
    new_cost=sum(r['new_estimated_upper_bound_usd'] for r in decisions)
    if not decisions and report_path.exists():
        if restored_overrides:write(path,overrides)
        return read(report_path)
    # Keep even an entire further baseline plus retry allowance available.
    remainder=plan['estimate']['conservative_usd_with_20_percent_retry']
    if not math.isfinite(remainder) or remainder<0 or reserved+new_cost+remainder>budget['cap_usd']:
        raise ValueError('Insufficient conservative prepaid headroom')
    report={'decisions':previous+decisions,'reserved_before_usd':reserved,'replacement_estimate_usd':sum(r['new_estimated_upper_bound_usd'] for r in previous+decisions),
        'ceiling_usd':budget['cap_usd'],'original_reservations':'unchanged, including unknown outcomes',
        'provider_calls':0,'basis':'Reviewed recovery evidence; explicitly commission new performances rather than silently resending unknown requests'}
    write(report_path,report);write(path,overrides)
    print('EXPLICIT_OUTCOME_REPLACEMENTS',len(decisions),'additional conservative USD',round(new_cost,6))
    return report


def prepare(transport_reviewed=False):
    lock=OUT/'generation.lock'
    try:
        with lock.open('x',encoding='utf8') as stream:stream.write('offline explicit replacement planning')
    except FileExistsError:raise ValueError('Wait for synthesis to stop') from None
    try:return _prepare_locked(transport_reviewed)
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--transport-reviewed',action='store_true')
    prepare(parser.parse_args().transport_reviewed)
