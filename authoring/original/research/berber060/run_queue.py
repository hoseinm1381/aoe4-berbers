"""Dispatch only absent current receipt identities; never rebuild cached batches.

Normal reports verify receipt identity, not source/native audio. Dispatch-only
reports never read existing receipts or claim their acceptance/identity/hash state.
Full coverage, normalization, encoding, and packaging checks remain mandatory.
Only explicit execution calls generate_batches; selection/aggregation are offline.
"""
import argparse
from collections import Counter
from pathlib import Path
from common import OUT, ART, write
from coverage import snapshot
from batch_generation import generate_batches, job_key, single_identity


def unique_jobs(jobs):
    seen={};ids={};unique=[];duplicates=[]
    for job in jobs:
        key=job_key(job);jid=job['id']
        if jid in ids and ids[jid]!=key:raise ValueError('Conflicting current identities for one job ID')
        if key in seen:
            if seen[key]!=jid:raise ValueError('One request identity assigned to distinct job IDs')
            duplicates.append({'job_id':jid,'request_id':key});continue
        seen[key]=jid;ids[jid]=key;unique.append(job)
    return unique,duplicates


def current_record(job,path):
    record,digest=snapshot(path)
    if (not isinstance(record,dict) or record.get('request_id')!=job_key(job)
            or record.get('identity')!=single_identity(job)
            or record.get('job_id')!=job['id'] or record.get('family')!=job['family']):
        raise ValueError('Receipt family/job/request identity differs from current plan')
    return record,digest


def select_missing(jobs,receipts):
    """An existing malformed/unknown receipt is held, never treated as absent."""
    unique,duplicates=unique_jobs(jobs);pending=[];existing=[];held=[]
    for job in unique:
        key=job_key(job);path=Path(receipts)/(key+'.json')
        if not path.exists():pending.append(job);continue
        try:
            record,digest=current_record(job,path)
            existing.append({'job_id':job['id'],'request_id':key,'status':record.get('status'),
                             'receipt_sha256':digest})
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:
            held.append({'job_id':job['id'],'request_id':key,'reason':str(error)})
    return {'pending':pending,'existing':existing,'held_existing':held,'duplicates_skipped':duplicates}


def select_absent_paths(jobs,receipts):
    """Fast dispatch selection: existence always holds a path, without reading it."""
    unique,duplicates=unique_jobs(jobs);pending=[];existing=[]
    for job in unique:
        key=job_key(job)
        if (Path(receipts)/(key+'.json')).exists():
            existing.append({'job_id':job['id'],'request_id':key})
        else:pending.append(job)
    return {'pending':pending,'existing':existing,'duplicates_skipped':duplicates}


def aggregate(jobs,receipts,dispatch_results=None):
    """Read actual final receipt snapshots without restoring or modifying them."""
    unique,duplicates=unique_jobs(jobs)
    returned={row['request_id']:row for row in dispatch_results or []}
    rows=[];digests={}
    for job in unique:
        key=job_key(job);path=Path(receipts)/(key+'.json')
        if not path.exists():
            result={'request_id':key,'job_id':job['id'],'family':job['family'],'status':'not_generated',
                    'reason':returned.get(key,{}).get('reason','No current receipt; still pending')}
        else:
            try:
                result,digest=current_record(job,path);digests[key]=digest
            except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:
                result={'request_id':key,'job_id':job['id'],'family':job['family'],
                        'status':'held_invalid_receipt','reason':str(error)}
        rows.append(result)
    return {'results':rows,'receipt_sha256':digests,'duplicates_skipped':duplicates,
        'receipt_status_counts':dict(Counter(row.get('status','unknown') for row in rows)),
        'verification':'Exact current receipt identity only; source/native SHA256 and acoustic quality require the full coverage/normalization/package gates.',
        'source_hashes_verified':False,'native_playback':'not_verified'}


def run(plan_path=None,workers=4,dispatch_only=False):
    """Explicit production entry point; shared generator owns locking and Budget."""
    if (OUT/'generation.lock').exists():raise ValueError('Generation already active')
    plan_path=Path(plan_path or ART/'recording-plan.json')
    plan,plan_sha=snapshot(plan_path)
    selected=(select_absent_paths if dispatch_only else select_missing)(plan['jobs'],OUT/'receipts')
    # generate_batches retains its exclusive lock, global reservations, orphan
    # guards, actor serialization and stop gates. Cached receipts never enter it.
    dispatched=generate_batches(selected['pending'],workers) if selected['pending'] else []
    final_plan,final_sha=snapshot(plan_path)
    if dispatch_only:
        stable=snapshot(plan_path)[1]==final_sha
        return {'schema':'berber060-queue-dispatch-only/v1','dispatch_only':True,
            'input_plan_sha256':plan_sha,'snapshot_plan_sha256':final_sha,
            'plan_changed_during_run':final_sha!=plan_sha,'plan_changed_during_final_snapshot':not stable,
            'generation_lock_present_at_snapshot_end':(OUT/'generation.lock').exists(),
            'initial_pending_requests':len(selected['pending']),
            'initial_existing_paths_held_unread':len(selected['existing']),
            'duplicates_skipped':selected['duplicates_skipped'],'dispatch_result_count':len(dispatched),
            'dispatch_results':dispatched,
            'dispatch_status_counts':dict(Counter(row.get('status','unknown') for row in dispatched)),
            'existing_receipts_read':False,'source_hashes_verified':False,
            'verification':'Dispatch results only. Existing canonical paths held unread; no existing receipt identity, total acceptance, audio hash or native playback claim. Full coverage/normalization/package checks remain mandatory.'}
    final=aggregate(final_plan['jobs'],OUT/'receipts',dispatched)
    stable=snapshot(plan_path)[1]==final_sha
    return {'schema':'berber060-queue-run/v1','input_plan_sha256':plan_sha,
        'snapshot_plan_sha256':final_sha,'plan_changed_during_run':final_sha!=plan_sha,
        'plan_changed_during_final_snapshot':not stable,
        'generation_lock_present_at_snapshot_end':(OUT/'generation.lock').exists(),
        'initial_pending_requests':len(selected['pending']),
        'initial_existing_requests':len(selected['existing']),
        'initial_held_existing':selected['held_existing'],
        'dispatch_result_count':len(dispatched),**final}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,default=ART/'recording-plan.json')
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--dispatch-only',action='store_true')
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    output=args.output or OUT/('queue-dispatch.json' if args.dispatch_only else 'queue-run.json')
    result=run(args.plan,args.workers,args.dispatch_only);write(output,result)
    fields=('initial_pending_requests','dispatch_result_count','plan_changed_during_run')
    fields+=('initial_existing_paths_held_unread','dispatch_status_counts') if args.dispatch_only else ('initial_existing_requests','receipt_status_counts')
    print({k:result[k] for k in fields})
