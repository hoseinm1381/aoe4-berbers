"""Preview safely recoverable saved batch members; --apply explicitly promotes them.

Default preview has no exports/production writes. --apply requires idle generation.
Neither mode sends provider requests, synthesizes, or changes budget records.
Opt-in partial validator retains all original global/quiet-cut/acoustic criteria.
"""
import argparse,uuid
from datetime import datetime,timezone
from collections import Counter
from pathlib import Path
from common import OUT,ART,read,write,sha
from coverage import snapshot
from batch_generation import aligned_splits,job_key,_load_pcm,RATE,batch_identity,request_id,single_identity,_receipt,QUALITY_FAILURES
from generation import wave_bytes,prepare_native


def inspect_record(record,current):
    master=Path(record['master']);alignment=Path(record['alignment'])
    if not master.is_file() or not alignment.is_file():raise ValueError('No saved source/alignment')
    if sha(master)!=record.get('master_sha256') or sha(alignment)!=record.get('alignment_sha256'):
        raise ValueError('Saved source/alignment digest differs')
    pcm=_load_pcm(master);timings,digest=snapshot(alignment)
    if digest!=record['alignment_sha256'] or sha(master)!=record['master_sha256']:
        raise ValueError('Saved source changed during preview')
    result=aligned_splits(record['jobs'],timings,pcm,allow_partial=True)
    current_keys={job_key(j):j['id'] for j in current}
    eligible={job_key(j) for j in record['jobs'] if current_keys.get(job_key(j))==j['id']}
    safe_keys={s['request_id'] for s in result['splits']}
    unsafe_keys={s['request_id'] for s in result['rejected']}
    already=0;recoverable=0
    for key in sorted(safe_keys&eligible):
        receipt=OUT/'receipts'/(key+'.json')
        if receipt.is_file():
            value,_=snapshot(receipt)
            if value.get('status')=='accepted_acoustic' and value.get('request_id')==key:
                already+=1;continue
        recoverable+=1
    return {'safe_current_plan_members':len(safe_keys&eligible),'recoverable_not_already_accepted':recoverable,
        'already_accepted_current_members':already,'unsafe_current_plan_members':len(unsafe_keys&eligible),
        'stale_or_other_plan_members':len(record['jobs'])-len(eligible),
        'boundary_failure_count':len(result['boundary_errors']),
        'unsafe_reasons':dict(Counter(e['error'] for r in result['rejected'] for e in r['errors'])),
        'master_sha256':record['master_sha256'],'alignment_sha256':record['alignment_sha256']}


def preview():
    current,plan_digest=snapshot(ART/'recording-plan.json');rows=[]
    for path in sorted((OUT/'batches').glob('*/receipt.json')):
        try:
            record,receipt_digest=snapshot(path)
            # Accepted batches need no recovery; started/unknown responses with no
            # verified saved source are held, never charged again by this script.
            if record.get('status')=='accepted_acoustic':continue
            row={'batch_id':record.get('batch_id',path.parent.name),'receipt_sha256':receipt_digest}
            if not record.get('master_sha256') or not record.get('alignment_sha256'):
                row.update(status='held_missing_verified_sources',recoverable_not_already_accepted=0)
            else:
                row.update(inspect_record(record,current['jobs']),status='previewed')
                if sha(path)!=receipt_digest:raise ValueError('Batch receipt changed during preview')
            rows.append(row)
        except (ValueError,OSError,KeyError,TypeError) as error:
            rows.append({'batch_id':path.parent.name,'status':'held_global_or_source_failure','error':str(error),'recoverable_not_already_accepted':0})
    if sha(ART/'recording-plan.json')!=plan_digest:raise ValueError('Recording plan changed during preview')
    report={'mode':'preview_only','recording_plan_sha256':plan_digest,'batch_count':len(rows),
        'recoverable_current_members':sum(r.get('recoverable_not_already_accepted',0) for r in rows),
        'unsafe_current_members':sum(r.get('unsafe_current_plan_members',0) for r in rows),
        'statuses':dict(Counter(r['status'] for r in rows)),'batches':rows,
        'provider_calls':0,'production_receipts_changed':False,'budget_changed':False,
        'proof_limit':'Concurrent read-only snapshot; rerun after queue stops before any explicit recovery. No source or receipt has been promoted.'}
    write(OUT/'partial-recovery-preview.json',report)
    print({k:v for k,v in report.items() if k!='batches'})
    return report


def _unchanged_file(path,expected):
    for entry in (path,path.parent):
        if entry.is_symlink() or entry.is_junction():raise ValueError('Recovery destination is a reparse point')
    if path.exists() and (not path.is_file() or sha(path)!=sha(expected)):
        raise ValueError('Existing different source/native bytes preserved: '+str(path))


def apply_record(path,record,receipt_digest,current,backup):
    if record.get('status')!='rejected_or_unknown' or record.get('error') not in QUALITY_FAILURES:
        return {'status':'held_not_finished_quality_rejection','recovered':0}
    if record.get('identity')!=batch_identity(record['jobs']) or request_id(record['identity'])!=record.get('batch_id') or path.parent.name!=record['batch_id']:
        raise ValueError('Saved batch identity differs')
    # This performs unchanged global gates and confirms both retained source hashes.
    inspect_record(record,current)
    pcm=_load_pcm(record['master']);result=aligned_splits(record['jobs'],read(record['alignment']),pcm,allow_partial=True)
    keys={job_key(j):j['id'] for j in current};by_key={job_key(j):j for j in record['jobs']}
    candidates=[]
    for span in result['splits']:
        key=span['request_id'];job=by_key[key]
        if keys.get(key)!=job['id']:continue
        rp=OUT/'receipts'/(key+'.json')
        if not rp.is_file():raise ValueError('Current nonaccepted receipt is required')
        previous,digest=snapshot(rp)
        if previous.get('request_id')!=key or previous.get('job_id')!=job['id'] or previous.get('identity')!=single_identity(job):
            raise ValueError('Current receipt identity differs; never reassign an old retake')
        if previous.get('status')=='accepted_acoustic':continue
        if previous.get('batch_id')!=record['batch_id'] or previous.get('status') not in ('rejected_or_unknown','review_required'):
            raise ValueError('Current receipt no longer belongs to this finished rejected batch')
        source=ART.resolve()/'masters'/(key+'.wav');native=OUT.resolve()/'wav'/(key+'.wav')
        if Path(previous['source']).resolve()!=source or Path(previous['native_path']).resolve()!=native:
            raise ValueError('Current source/native owner path differs')
        candidates.append((job,span,rp,previous,digest,source,native))
    if not candidates:return {'status':'no_current_nonaccepted_safe_members','recovered':0}
    backup.mkdir(parents=True,exist_ok=False)
    (backup/'batch.old-receipt.json').write_bytes(path.read_bytes())
    proof={'mode':'explicit_partial_recovery','batch_id':record['batch_id'],'master_sha256':record['master_sha256'],
        'alignment_sha256':record['alignment_sha256'],'sample_rate':RATE,'partial_validation':result}
    proof_path=backup/'partial-split-proof.json';write(proof_path,proof)
    prepared=[]
    # Stage and compare every candidate before changing any production file.
    for job,span,rp,previous,digest,source,native in candidates:
        key=job_key(job)
        old=rp.read_bytes()
        if sha(rp)!=digest:raise ValueError('Receipt changed before backup')
        (backup/(key+'.old-receipt.json')).write_bytes(old)
        cut=backup/'cuts'/(key+'.wav');nw=backup/'native'/(key+'.wav')
        wave_bytes(cut,pcm[span['start_sample']*2:span['end_sample']*2],RATE);native_info=prepare_native(cut,nw)
        _unchanged_file(source,cut);_unchanged_file(native,nw)
        prepared.append((job,span,rp,digest,source,native,cut,nw,native_info))
    if sha(path)!=receipt_digest or sha(record['master'])!=record['master_sha256'] or sha(record['alignment'])!=record['alignment_sha256']:
        raise ValueError('Batch changed before recovery promotion')
    for job,span,rp,digest,source,native,cut,nw,native_info in prepared:
        if sha(rp)!=digest:raise ValueError('Receipt changed before recovery promotion')
        for target,staged in ((source,cut),(native,nw)):
            target.parent.mkdir(parents=True,exist_ok=True);_unchanged_file(target,staged)
            if not target.exists():
                with target.open('xb') as stream:stream.write(staged.read_bytes())
        item=_receipt(job,record['batch_id'])
        item.update(status='accepted_acoustic',source_sha256=sha(source),quality=span['quality'],native_wav=native_info,
            provider_receipt=record.get('provider_receipt',{}),split_proof=str(proof_path),partial_recovery_proof=str(proof_path),
            prior_receipt=str(backup/(job_key(job)+'.old-receipt.json')),batch_master=record['master'],batch_alignment=record['alignment'],
            generation_mode='timestamp_batch_partial_recovery',batch_seed=record['identity']['seed'],
            identity_note='Original single-job cache identity retained; hash-verified original batch context and seed; strict per-clip quality proof')
        write(rp,item)
    record.update(status='partially_accepted_acoustic',partial_recovery_proof=str(proof_path),
        partial_recovered_request_ids=[job_key(p[0]) for p in prepared],partial_errors=result['rejected'])
    write(path,record)
    return {'status':'partially_accepted_acoustic','recovered':len(prepared),'proof':str(proof_path)}


def apply():
    lock=OUT/'generation.lock'
    if lock.exists():raise ValueError('Generation active; partial recovery requires absent generation.lock')
    token='partial-recovery-'+uuid.uuid4().hex
    try:
        with lock.open('x',encoding='utf8') as stream:stream.write(token)
    except FileExistsError:raise ValueError('Generation started; recovery refused') from None
    report={'mode':'explicit_apply','provider_calls':0,'budget_changed':False,'recovered_current_members':0,'batches':[]}
    try:
        current,plan_digest=snapshot(ART/'recording-plan.json')
        report['recording_plan_sha256']=plan_digest
        run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
        for path in sorted((OUT/'batches').glob('*/receipt.json')):
            record,digest=snapshot(path)
            if record.get('status')!='rejected_or_unknown':continue
            try:
                if sha(ART/'recording-plan.json')!=plan_digest:raise ValueError('Current plan changed during recovery')
                result=apply_record(path,record,digest,current['jobs'],OUT/'partial-recovery'/run/path.parent.name)
            except (ValueError,OSError,KeyError,TypeError) as error:
                promoted=0
                batch_backup=OUT/'partial-recovery'/run/path.parent.name
                for old_receipt in batch_backup.glob('*.old-receipt.json'):
                    if old_receipt.name=='batch.old-receipt.json':continue
                    key=old_receipt.name.removesuffix('.old-receipt.json');rp=OUT/'receipts'/(key+'.json')
                    if rp.is_file():
                        value=read(rp)
                        if value.get('status')=='accepted_acoustic' and value.get('partial_recovery_proof')==str(batch_backup/'partial-split-proof.json'):promoted+=1
                result={'status':'incomplete' if promoted else 'held','error':str(error),'recovered':promoted}
            result['batch_id']=path.parent.name;report['batches'].append(result)
            report['recovered_current_members']+=result['recovered']
        report['status']='incomplete' if any(r['status']=='incomplete' for r in report['batches']) else 'completed'
        write(OUT/'partial-recovery-apply.json',report)
    finally:
        if lock.is_file() and lock.read_text(encoding='utf8')==token:lock.unlink()
    print({k:v for k,v in report.items() if k!='batches'})
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    apply() if args.apply else preview()
