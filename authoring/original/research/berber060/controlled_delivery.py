"""Preview a single explicitly applied controlled-combat performance per clipped job.

No provider calls, receipt/budget edits, plan compilation, attenuation, or gate changes.
Only --apply writes performance-overrides and immutable compact decision evidence.
"""
import argparse
import json
import math
import uuid
import wave
from datetime import datetime,timezone
from pathlib import Path
from common import OUT, ART, write, sha
from coverage import snapshot,verified_file
from batch_generation import job_key,single_identity,QUALITY_FAILURES
from generation import pcm_quality
from jobs import PERFORMANCE_SEED_STEP,apply_performance_overrides

TAG_DOCUMENTATION='https://elevenlabs.io/docs/eleven-creative/playground/text-to-speech'
REASON=('One controlled combat-delivery performance after verified source clipping: retain the same '
    'Arabic words, actor, native HIGH context and semantic job ID; replace only leading [shouting] '
    'with documented Eleven v3 emotion tag [angry]. This requests urgency without an explicit '
    'maximum-volume instruction; it does not guarantee unclipped output. All acoustic gates remain.')


def raw_clipping_proof(record):
    verified_file(record['source'],record.get('source_sha256'))
    with wave.open(str(record['source']),'rb') as stream:
        if (stream.getnchannels(),stream.getsampwidth())!=(1,2):raise ValueError('Unexpected source PCM format')
        rate=stream.getframerate();pcm=stream.readframes(stream.getnframes())
    quality=pcm_quality(pcm,rate)
    if not quality['clipped_samples']:raise ValueError('Raw source is not actually clipped')
    if quality['clipped_samples']!=record.get('quality',{}).get('clipped_samples'):
        raise ValueError('Recorded/source clipping counts differ')
    if sha(record['source'])!=record['source_sha256']:raise ValueError('Source changed during clipping review')
    return {'source':record['source'],'source_sha256':record['source_sha256'],
            'source_pcm_quality':quality,'sample_rate':rate}


def preview(plan,budget,overrides,receipts):
    decisions=[];held=[];skipped=[]
    if budget.get('cap_usd')!=100:raise ValueError('Unexpected authorized spending ceiling')
    reserved=sum(row['reserved_usd'] for row in budget['reservations'].values())
    if not math.isfinite(reserved) or reserved<0:raise ValueError('Invalid conservative reservation total')
    for job in plan['jobs']:
        jid=job['id'];key=job_key(job)
        if jid in overrides or job.get('performance_override_epoch'):
            skipped.append({'job_id':jid,'reason':'One controlled-delivery attempt already commissioned'});continue
        if (job['delivery']!='high' or not job['generation_text'].startswith('[shouting] ')
                or job.get('script',{}).get('nonverbal') or job.get('nonverbal')
                or job['event'].lower().startswith('effort') or job.get('model_id','eleven_v3')!='eleven_v3'):
            continue
        path=Path(receipts)/(key+'.json')
        if not path.exists():
            skipped.append({'job_id':jid,'reason':'Unattempted; not a controlled-delivery repair candidate'});continue
        try:
            record,receipt_digest=snapshot(path)
            if (record.get('request_id')!=key or record.get('identity')!=single_identity(job)
                    or record.get('job_id')!=jid or record.get('family')!=job['family']):
                raise ValueError('Current receipt identity differs')
            if record.get('status')=='accepted_acoustic':continue
            if (record.get('status') not in ('review_required','failed_or_unknown','rejected_or_unknown','rejected')
                    or record.get('error') and record['error'] not in QUALITY_FAILURES
                    or record.get('quality',{}).get('clipped_samples',0)<=0):
                skipped.append({'job_id':jid,'reason':'Not a proved clipped quality outcome; unknown/missing work stays held'});continue
            proof=raw_clipping_proof(record)
            attempt=record.get('batch_id') or record.get('attempt_key') or key
            if attempt not in budget['reservations']:raise ValueError('Original conservative reservation missing')
            replacement=dict(job,generation_text='[angry] '+job['generation_text'][len('[shouting] '):],
                seed=(job['seed']+PERFORMANCE_SEED_STEP)%(2**32),force_single=True)
            replacement_key=job_key(replacement)
            if replacement_key in budget['reservations'] or (Path(receipts)/(replacement_key+'.json')).exists():
                raise ValueError('Controlled replacement identity already attempted')
            override={k:job[k] for k in ('family','event','age','delivery','take','voice_id')}
            override.update(action='controlled_combat_delivery',epoch=1,prior_prompt=job['generation_text'],
                replacement_prompt=replacement['generation_text'],prior_seed=job['seed'],
                prior_request_id=key,replacement_request_id=replacement_key,force_single=True,reason=REASON,
                original_attempt_key=attempt,receipt=str(path),receipt_sha256=receipt_digest,
                documentation=TAG_DOCUMENTATION,documentation_checked='2026-10-16',**proof)
            # Ensure the compiler agrees on every identity before proposing the decision.
            apply_performance_overrides({jid:dict(job)},{jid:override})
            decisions.append({'job_id':jid,'override':override,
                'new_estimated_upper_bound_usd':max(1,len(replacement['generation_text']))*.30/1000})
        except (OSError,ValueError,KeyError,TypeError,AttributeError,wave.Error) as error:
            held.append({'job_id':jid,'request_id':key,'reason':str(error)})
    new_cost=sum(row['new_estimated_upper_bound_usd'] for row in decisions)
    baseline=plan['estimate']['conservative_usd_with_20_percent_retry']
    if not math.isfinite(baseline) or baseline<0:raise ValueError('Invalid further-baseline reserve estimate')
    return {'schema':'berber060-controlled-delivery/v1','preview_only':True,'decisions':decisions,
        'held':held,'skipped':skipped,'reserved_before_usd':reserved,'new_estimate_usd':new_cost,
        'further_baseline_with_retry_usd':baseline,'ceiling_usd':100,
        'headroom_ok':reserved+new_cost+baseline<=100,'provider_calls':0,'budget_changed':False,
        'gates':'All original conservative reservations and acoustic/source/native acceptance gates retained',
        'documentation':TAG_DOCUMENTATION}


def prepare(apply=False,out=None,art=None):
    out=Path(out or OUT);art=Path(art or ART);lock=out/'generation.lock';owned=False
    if apply:
        try:
            with lock.open('x',encoding='utf8') as stream:stream.write('offline controlled-delivery planning')
            owned=True
        except FileExistsError:raise ValueError('Wait for active generation before controlled-delivery planning') from None
    elif lock.exists():raise ValueError('Wait for active generation before previewing controlled delivery')
    try:
        plan_path=art/'recording-plan.json';budget_path=out/'budget.json';override_path=art/'performance-overrides.json'
        plan,plan_hash=snapshot(plan_path);budget,budget_hash=snapshot(budget_path)
        overrides,override_hash=snapshot(override_path) if override_path.exists() else ({},None)
        report=preview(plan,budget,overrides,out/'receipts')
        report.update(plan_sha256=plan_hash,budget_sha256=budget_hash,prior_overrides_sha256=override_hash)
        if not apply:return report
        if not report['headroom_ok']:raise ValueError('Insufficient conservative $100 headroom including a further baseline')
        if (sha(plan_path)!=plan_hash or sha(budget_path)!=budget_hash
                or (sha(override_path) if override_path.exists() else None)!=override_hash):
            raise ValueError('Planning inputs changed before controlled-delivery apply')
        for decision in report['decisions']:
            proof=decision['override']
            if sha(proof['receipt'])!=proof['receipt_sha256'] or sha(proof['source'])!=proof['source_sha256']:
                raise ValueError('Clipping evidence changed before controlled-delivery apply')
        if not report['decisions']:return report
        token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
        proof_path=out/'controlled-delivery-decisions'/(token+'.json')
        report['preview_only']=False;write(proof_path,report)
        proof_hash=sha(proof_path)
        for decision in report['decisions']:
            overrides[decision['job_id']]={**decision['override'],'decision_file':str(proof_path),'decision_sha256':proof_hash}
        write(override_path,overrides)
        return report
    finally:
        if owned:lock.unlink(missing_ok=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    report=prepare(args.apply)
    print(json.dumps(report,ensure_ascii=True,indent=2))
