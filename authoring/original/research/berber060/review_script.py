"""Readable source dialogue register; contains no credential or paid operation."""
import csv,hashlib,json,uuid
from common import ART,read,write,sha


def export():
    plan_bytes=(ART/'recording-plan.json').read_bytes();cast_bytes=(ART/'casting.json').read_bytes()
    plan=json.loads(plan_bytes.decode('utf-8-sig'));cast=json.loads(cast_bytes.decode('utf-8-sig'))
    plan_digest=hashlib.sha256(plan_bytes).hexdigest();cast_digest=hashlib.sha256(cast_bytes).hexdigest()
    ids=[job['id'] for job in plan['jobs']]
    if not ids or len(ids)!=len(set(ids)) or any(not isinstance(jid,str) or not jid for jid in ids):raise ValueError('Register requires distinct nonempty current job IDs')
    expected=plan.get('estimate',{}).get('unique_recordings',len(ids))
    if expected!=len(ids):raise ValueError('Current plan job count differs from its declared recording count')
    for job in plan['jobs']:
        if job['family'] not in cast or job['voice_id']!=cast[job['family']]['voice_id']:
            raise ValueError('Register actor differs from the current plan/cast')
    target=ART/'voice-script.csv'
    fields=['job_id','family','actor_name','actor_voice_id','actor_accent','gender',
        'age','context','delivery','take','language','text','synthesis_prompt','performance_override_reason','meaning','performance_direction',
        'pronunciation_reference','historical_reference','review_status','nonverbal']
    if target.is_symlink() or target.is_junction():raise ValueError('Register destination is a link')
    temporary=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
    with temporary.open('x',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for job in plan['jobs']:
            script=job['script'];actor=cast[job['family']]
            writer.writerow(dict(job_id=job['id'],family=job['family'],actor_name=actor['name'],
                actor_voice_id=actor['voice_id'],actor_accent=actor.get('accent'),gender=actor['gender'],
                age=job['age'],context=job['event'],delivery=job['delivery'],take=job['take'],
                language=script['language'],text=script['text'],synthesis_prompt=job['generation_text'],
                performance_override_reason=(job.get('performance_override_reason') or job.get('documented_override_reason') or job.get('pronunciation_revision','')),meaning=script['english'],
                performance_direction=script.get('performance_direction',''),
                pronunciation_reference=script.get('phonetics') or (
                    'Nonverbal vocal effort; listening review pending' if script.get('nonverbal') else
                    'Arabic orthography; vowels not fully specified; native pronunciation review pending'),
                historical_reference=script['source'],review_status=script['review_status'],
                nonverbal=script.get('nonverbal',False)))
    with temporary.open(encoding='utf-8-sig',newline='') as stream:written=list(csv.DictReader(stream))
    if len(written)!=len(ids) or [row['job_id'] for row in written]!=ids:raise ValueError('Written register rows differ from current plan')
    if sha(ART/'recording-plan.json')!=plan_digest or sha(ART/'casting.json')!=cast_digest:
        raise ValueError('Register source plan/cast changed during export')
    temporary.replace(target)
    proof={'schema':'berber060-voice-script/v1','plan_sha256':plan_digest,'cast_sha256':cast_digest,
        'csv_sha256':sha(target),'rows':len(written),'families':len({j['family'] for j in plan['jobs']}),
        'performance_override_rows':sum(bool(j.get('performance_override_reason')) for j in plan['jobs']),
        'documented_override_rows':sum(bool(j.get('performance_override_reason') or j.get('documented_override_reason') or j.get('pronunciation_revision')) for j in plan['jobs']),
        'language_native_speaker_review':'pending','native_playback':'pending'}
    write(target.with_suffix('.manifest.json'),proof)
    validate_export(proof,target)
    return target


def validate_export(proof,target):
    if proof.get('schema')!='berber060-voice-script/v1' or sha(ART/'recording-plan.json')!=proof['plan_sha256'] or sha(ART/'casting.json')!=proof['cast_sha256'] or sha(target)!=proof['csv_sha256']:
        raise ValueError('Voice register source/proof is stale')
    with target.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    if len(rows)!=proof['rows'] or len({r['job_id'] for r in rows})!=len(rows):raise ValueError('Voice register row count/identity differs')
    return proof


if __name__=='__main__':print(export())
