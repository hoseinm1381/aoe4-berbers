"""Offline preview of explicit same-context existing-take substitutions.

Never synthesizes, updates a plan/receipt/budget, or counts reused audio as new.
CLI refuses an active generation lock and writes a report only with --output.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from common import OUT, ART, write
from coverage import inspect_job, key_for, identity, snapshot, verified_file
from batch_generation import QUALITY_FAILURES, batch_identity
from generation import request_id

QUALITY_ERRORS=QUALITY_FAILURES|{'Truncated PCM response','Unexpected source PCM'}


def contract(job):
    script=job.get('script',{})
    nonverbal=bool(script.get('nonverbal') or job.get('nonverbal') or job['event'].lower().startswith('effort'))
    semantic=script.get('semantic') or ('nonverbal:'+job['event'] if nonverbal else job['event'])
    return tuple(job[k] for k in ('family','event','age','delivery','voice_id'))+(nonverbal,semantic)


def current_receipt(job,receipts):
    key=key_for(job);path=Path(receipts)/(key+'.json')
    if not path.exists():return None
    record,checksum=snapshot(path)
    if (record.get('request_id')!=key or record.get('identity')!=identity(job)
            or record.get('job_id')!=job['id'] or record.get('family')!=job['family']):
        raise ValueError('Receipt is not the exact current family/job/request identity')
    record['_preview_receipt_sha256']=checksum
    return record


def received_quality_failure(job,record,receipts):
    """Explicit quality refusal needs preserved, hash-verified returned input."""
    if record.get('status') not in ('review_required','failed_or_unknown','rejected_or_unknown','rejected'):return False
    if record.get('status')=='review_required':
        quality=record.get('quality',{})
        if not (quality.get('clipped_samples',0) or quality.get('duration_seconds',0)>8):return False
    elif record.get('error') not in QUALITY_ERRORS:return False
    if record.get('batch_id'):
        batch,_=snapshot(Path(receipts).parent/'batches'/record['batch_id']/'receipt.json')
        if (batch.get('identity')!=batch_identity(batch['jobs'])
                or request_id(batch['identity'])!=record['batch_id']
                or key_for(job) not in {key_for(j) for j in batch['jobs']}
                or batch.get('error')!=record.get('error')):return False
        verified_file(batch['master'],batch['master_sha256'])
        verified_file(batch['alignment'],batch['alignment_sha256'])
    else:
        verified_file(record['source'],record['source_sha256'])
    return True


def preview(plan,receipts,unknown_decisions=None):
    jobs={job['id']:job for job in plan['jobs']}
    if len(jobs)!=len(plan['jobs']):raise ValueError('Duplicate planned job IDs')
    decisions={}
    for decision in (unknown_decisions or {}).get('decisions',[]):
        jid=decision.get('job_id')
        if (jid not in jobs or jid in decisions or decision.get('request_id')!=key_for(jobs[jid])
                or decision.get('action')!='allow_existing_take_fallback' or not decision.get('reason','').strip()):
            raise ValueError('Explicit unknown-outcome decision is missing, duplicate, or stale')
        decisions[jid]=decision
    verified={};records={};gaps=[]
    for jid,job in jobs.items():
        try:
            record=current_receipt(job,receipts);records[jid]=record
            if record and record.get('status')=='accepted_acoustic':
                row=inspect_job(job,receipts)
                if row['status']=='accepted' and row['receipt_sha256']==record['_preview_receipt_sha256']:
                    verified[jid]=row
                else:gaps.append({'job_id':jid,'request_id':key_for(job),'status':'held_invalid_accepted_audio',
                                  'reason':row.get('reason','Accepted receipt failed acoustic/hash checks')})
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:
            gaps.append({'job_id':jid,'request_id':key_for(job),'status':'held_invalid_receipt','reason':str(error)})
    candidates=defaultdict(list)
    for jid in verified:candidates[contract(jobs[jid])].append(jid)
    fallbacks=[];already_gapped={r['job_id'] for r in gaps};usage=defaultdict(int)
    for jid,job in jobs.items():
        if jid in verified or jid in already_gapped:continue
        record=records.get(jid);key=key_for(job)
        if record is None or record.get('status') in ('not_generated','missing'):
            gaps.append({'job_id':jid,'request_id':key,'status':'pending_unattempted',
                         'reason':'Unattempted jobs cannot be finalized through existing-take fallback'})
            continue
        try:is_quality=received_quality_failure(job,record,receipts)
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as error:
            gaps.append({'job_id':jid,'request_id':key,'status':'held_quality_evidence_unverified','reason':str(error)})
            continue
        explicit=decisions.get(jid)
        if not is_quality and explicit is None:
            gaps.append({'job_id':jid,'request_id':key,'status':'held_unknown_requires_explicit_decision',
                         'reason':'Unknown/provider/transport outcomes need a separate reviewed decision; reservations remain retained',
                         'receipt_status':record.get('status'),'error':record.get('error')})
            continue
        pool=[other for other in candidates[contract(job)] if jobs[other]['take']!=job['take']]
        if not pool:
            gaps.append({'job_id':jid,'request_id':key,'status':'no_suitable_accepted_take',
                         'reason':'No hash-verified accepted alternative with identical actor/family/event/age/delivery/nonverbal semantics'})
            continue
        donor=min(pool,key=lambda other:(usage[other],abs(jobs[other]['take']-job['take']),other))
        usage[donor]+=1;proof=verified[donor]
        reason=('Documented reuse of another accepted take after hash-verified returned-audio quality rejection; '
                'same actor/family/event/age/delivery/nonverbal semantics. Missing variation remains a gap; no new recording.')
        if explicit:reason='Explicit reviewed unknown-outcome reuse: '+explicit['reason']+'. Original reservation retained; no new recording.'
        fallbacks.append({'job_id':jid,'replacement_job_id':donor,'reason':reason,
            'request_id':key,'replacement_request_id':key_for(jobs[donor]),
            'source_sha256':proof['source_sha256'],'native_sha256':proof['native_sha256'],
            'new_recordings':0,'basis':'explicit_unknown_decision' if explicit else 'returned_quality_failure'})
    contexts=[]
    for key,group in sorted(_groups(jobs.values()).items()):
        accepted=[verified[j['id']] for j in group if j['id'] in verified]
        source={r['source_sha256'] for r in accepted};native={r['native_sha256'] for r in accepted}
        expected=len({j['take'] for j in group});distinct=min(len(source),len(native))
        ids={j['id'] for j in group}
        contexts.append(dict(zip(('family','event','age','delivery','voice_id','nonverbal','semantic'),key),
            planned_take_count=expected,accepted_request_records=len(accepted),
            distinct_source_waveforms=len(source),distinct_native_waveforms=len(native),
            missing_distinct_variation=max(0,expected-distinct),
            fallback_job_ids=[r['job_id'] for r in fallbacks if r['job_id'] in ids],
            held_or_pending_job_ids=[r['job_id'] for r in gaps if r['job_id'] in ids]))
    return {'schema':'berber060-fallback-preview/v1','preview_only':True,'fallbacks':fallbacks,'gaps':gaps,
        'contexts':contexts,'summary':{'planned_jobs':len(jobs),'accepted_request_records':len(verified),
            'accepted_distinct_source_waveforms':len({r['source_sha256'] for r in verified.values()}),
            'accepted_distinct_native_waveforms':len({r['native_sha256'] for r in verified.values()}),
            'documented_fallback_jobs':len(fallbacks),'new_recordings_from_fallbacks':0,
            'pending_unattempted_jobs':sum(r['status']=='pending_unattempted' for r in gaps),
            'held_or_missing_jobs':len(gaps),'contexts_missing_variation':sum(r['missing_distinct_variation']>0 for r in contexts)},
        'limits':['Preview candidates are not package approval, encoded WEM validation, ASR, listening, or native audibility proof.',
                  'Fallbacks reuse accepted audio and never increase distinct recordings. Unattempted jobs remain pending.',
                  'All original uncertain reservations remain retained; this planner never reconciles charges.']}


def _groups(jobs):
    groups=defaultdict(list)
    for job in jobs:groups[contract(job)].append(job)
    return groups


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,default=ART/'recording-plan.json')
    parser.add_argument('--receipts',type=Path,default=OUT/'receipts')
    parser.add_argument('--unknown-decisions',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if (args.receipts.parent/'generation.lock').exists():raise ValueError('Wait for generation to stop before previewing fallback coverage')
    plan,plan_sha=snapshot(args.plan)
    decisions=snapshot(args.unknown_decisions)[0] if args.unknown_decisions else None
    report=preview(plan,args.receipts,decisions);report['plan_sha256']=plan_sha
    if snapshot(args.plan)[1]!=plan_sha:raise ValueError('Plan changed while previewing; rerun idle')
    if args.output:write(args.output,report)
    print(json.dumps(report['summary'],sort_keys=True))


if __name__=='__main__':main()
