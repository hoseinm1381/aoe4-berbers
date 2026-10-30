"""Explicit idle-queue DNS reconciliation; default probe is read-only, never TTS.

Reviewed legacy errors can receive replacement seed epochs, but their original
reservations remain uncertain. Only new typed preconnect proof releases a charge.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import re
from common import OUT, ART, read, write, sha
from account import request, DNS_ERROR, DNS_PROOF
from batch_generation import job_key, single_identity, batch_identity
from generation import request_id
from jobs import NETWORK_SEED_STEP

LEGACY_DNS='<urlopen error [Errno 11001] getaddrinfo failed>'


def classification(record,include_reviewed_legacy=False):
    if record.get('status') not in ('failed_or_unknown','rejected_or_unknown'):return None
    if (record.get('error')==DNS_ERROR and record.get('failure_kind')=='preconnect_dns'
            and record.get('transport_proof')==DNS_PROOF):return 'typed_preconnect'
    if include_reviewed_legacy and record.get('error')==LEGACY_DNS:return 'reviewed_legacy_uncertain'
    return None


def no_response_evidence(record):
    if any(record.get(k) for k in ('provider_receipt','source_sha256','master_sha256','alignment_sha256')):
        return False
    return not any(Path(record[k]).exists() for k in ('source','native_path','master','alignment') if record.get(k))


def reconcile(plan,budget,epochs,out,include_reviewed_legacy=False):
    """Pure planning: validate exact refusal/attempt evidence; mutate no files."""
    out=Path(out);updated=deepcopy(budget);next_epochs=dict(epochs)
    selected=[];skipped=[];release={}
    reservations=updated['reservations']
    for job in plan['jobs']:
        key=job_key(job);path=out/'receipts'/f'{key}.json'
        if not path.exists():continue
        member=read(path);kind=classification(member,include_reviewed_legacy)
        if kind is None:continue
        try:
            if member.get('request_id')!=key or member.get('identity')!=single_identity(job):
                raise ValueError('Current member identity mismatch')
            if not no_response_evidence(member):raise ValueError('Member has connected/returned-audio evidence')
            record=member;proof_path=path
            if member.get('batch_id'):
                attempt=member['batch_id'];proof_path=out/'batches'/attempt/'receipt.json';record=read(proof_path)
                if classification(record,include_reviewed_legacy)!=kind:raise ValueError('Batch/member DNS proof mismatch')
                if not no_response_evidence(record):raise ValueError('Batch has connected/returned-audio evidence')
                if request_id(batch_identity(record['jobs']))!=attempt or record.get('identity')!=batch_identity(record['jobs']):
                    raise ValueError('Batch identity mismatch')
                if key not in {job_key(j) for j in record['jobs']}:raise ValueError('Member not present in batch')
            else:
                attempt=member.get('attempt_key')
                if not attempt:
                    if member.get('previous_attempts'):raise ValueError('Retry attempt not identified')
                    attempt=key
                if attempt!=key and not re.fullmatch(re.escape(key)+r':retry[1-9][0-9]*',attempt):
                    raise ValueError('Invalid attempt identity')
            reservation=reservations.get(attempt)
            if reservation is None:raise ValueError('No matching attempt reservation')
            if reservation.get('status') not in ('failed_or_unknown','rejected_or_unknown','reserved_before_request','preconnect_dns_refusal'):
                raise ValueError('Reservation has connected/other outcome')
            current=job.get('network_retry_epoch',0)
            target=max(next_epochs.get(job['id'],0),current+1)
            if not isinstance(target,int) or isinstance(target,bool) or target<1:raise ValueError('Invalid network epoch')
            # Do not collide with a previously attempted payload, even after seed wrapping.
            for _ in range(100):
                replacement=dict(job,seed=(job['seed']+NETWORK_SEED_STEP*(target-current))%(2**32))
                replacement_key=job_key(replacement)
                if replacement_key not in reservations and not (out/'receipts'/f'{replacement_key}.json').exists():break
                target+=1
            else:raise ValueError('No clean replacement request identity')
            next_epochs[job['id']]=target
            selected.append({'job_id':job['id'],'old_request_id':key,'replacement_request_id':replacement_key,
                'attempt_key':attempt,'classification':kind,'network_retry_epoch':target,
                'receipt':str(path),'receipt_sha256':sha(path),'attempt_proof':str(proof_path),
                'attempt_proof_sha256':sha(proof_path)})
            if kind=='typed_preconnect':release[attempt]=deepcopy(reservation)
        except (OSError,ValueError,KeyError,TypeError) as error:
            skipped.append({'job_id':job['id'],'request_id':key,'reason':str(error)})
    released=0
    for attempt,previous in release.items():
        row=reservations[attempt]
        if row.get('status')=='preconnect_dns_refusal':continue
        released+=row['reserved_usd']
        row.update(preconnect_unbilled_estimate_usd=row['reserved_usd'],reserved_usd=0,
                   status='preconnect_dns_refusal',provider_character_cost=0,
                   reconciliation='Typed socket.gaierror during initial open; redirects disabled; body not transmitted')
    proof={'selected':selected,'skipped':skipped,'released_attempts':release,
        'released_unbilled_estimate_usd':released,
        'reviewed_legacy_jobs':sum(r['classification']=='reviewed_legacy_uncertain' for r in selected),
        'legacy_rule':'Reviewed legacy errors get replacement epochs; original reservation retained because old redirects/preconnect stage were not recorded.',
        'unknown_rule':'Other transport, partial reads, provider responses, or ambiguous attempts are never requeued/released.'}
    return updated,next_epochs,proof


def reset(include_reviewed_legacy=False,out=None,art=None,probe=None):
    out=Path(out or OUT);art=Path(art or ART);lock=out/'generation.lock'
    # Never rename/bypass an existing lock. Root must establish idle state first.
    with lock.open('x',encoding='utf8') as stream:stream.write('offline DNS reconciliation '+datetime.now(timezone.utc).isoformat())
    try:
        (probe or request)('/v2/voices?page_size=1')
        plan_path=art/'recording-plan.json';budget_path=out/'budget.json';epoch_path=art/'network-retries.json'
        plan=read(plan_path);budget=read(budget_path)
        if budget['cap_usd']!=100:raise ValueError('Unexpected authorized budget ceiling')
        epochs=read(epoch_path) if epoch_path.exists() else {}
        updated,next_epochs,proof=reconcile(plan,budget,epochs,out,include_reviewed_legacy)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        proof.update(utc=stamp,auth_probe='read-only request succeeded; no synthesis',
                     input_plan_sha256=sha(plan_path),input_budget_sha256=sha(budget_path),
                     conservative_retained_usd=sum(r['reserved_usd'] for r in updated['reservations'].values()))
        proof_path=out/'dns-reconciliation'/f'{stamp}.json'
        write(proof_path,proof)  # Preserve evidence before any reconciliation mutation.
        write(epoch_path,next_epochs)
        if proof['released_unbilled_estimate_usd']:write(budget_path,updated)
        print({'jobs_requeued':len(proof['selected']),'reviewed_legacy_jobs':proof['reviewed_legacy_jobs'],
               'released_usd':proof['released_unbilled_estimate_usd'],'proof':str(proof_path),
               'next_step':'Recompile jobs before a new generation process; old receipts unchanged'})
        return proof
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--include-reviewed-legacy',action='store_true')
    reset(parser.parse_args().include_reviewed_legacy)
