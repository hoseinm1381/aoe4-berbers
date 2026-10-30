"""Apply stock-referenced gain to accepted native copies after synthesis stops."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import copy,wave
from common import OUT,ART,read,write,sha
from generation import pcm_quality
from batch_generation import job_key,single_identity
from loudness import normalize_native


def normalize_job(job):
    key=job_key(job);path=OUT/'receipts'/f'{key}.json'
    if not path.exists():return {'job_id':job['id'],'status':'not_accepted'}
    receipt=read(path)
    original_receipt=copy.deepcopy(receipt)
    if receipt['status']!='accepted_acoustic':return {'job_id':job['id'],'status':'not_accepted'}
    if receipt['job_id']!=job['id'] or receipt['request_id']!=key or receipt['identity']!=single_identity(job):
        raise ValueError('Accepted receipt is not the current recording identity')
    if sha(receipt['source'])!=receipt['source_sha256']:raise ValueError('Lossless source changed')
    target=OUT/'wav'/f'{key}.wav';proof_path=OUT/'loudness/normalization-provenance'/f'{key}.json'
    expected=receipt['native_wav']['sha256'];proof=None
    if proof_path.exists():
        recorded=receipt.get('normalization')
        if recorded and sha(proof_path)!=recorded['provenance_sha256']:
            raise ValueError('Recorded normalization provenance changed')
        prior=read(proof_path)
        if prior.get('request_id')!=key or prior.get('event')!=job['event']:
            raise ValueError('Normalization provenance identity differs from recording')
        if prior.get('recipe',{}).get('retained_input_sha256')!=prior['source']['sha256']:
            raise ValueError('Normalization recipe input hash differs from source proof')
        if sha(target)==prior['output']['sha256']:
            # Reconcile an interruption after replacing audio but before updating
            # its receipt. Both old and new hashes must be proved by provenance.
            if expected not in (prior['source']['sha256'],prior['output']['sha256']):
                raise ValueError('Normalization provenance differs from accepted receipt')
            if sha(prior['recipe']['retained_input'])!=prior['source']['sha256']:
                raise ValueError('Retained normalization input changed')
            proof=prior
    if proof is None:proof=normalize_native(key,job['event'],expected,job['script'].get('nonverbal',False))
    if sha(target)!=proof['output']['sha256']:raise ValueError('Normalized output changed')
    with wave.open(str(target),'rb') as stream:
        if (stream.getnchannels(),stream.getsampwidth(),stream.getframerate())!=(1,2,48000):
            raise ValueError('Normalized format changed')
        acoustic=pcm_quality(stream.readframes(stream.getnframes()),48000)
    if acoustic['clipped_samples']:raise ValueError('Normalization introduced clipping')
    receipt['native_wav'].update(proof['output']);receipt['native_wav'].update(acoustic)
    receipt['native_wav'].update(sha256=proof['output']['sha256'],normalization_gain_db=proof['decision']['applied_gain_db'])
    receipt['normalization']={'provenance':str(proof_path),'provenance_sha256':sha(proof_path),
        'reference':proof['reference'],'source_untouched':True}
    if receipt!=original_receipt:write(path,receipt)
    return {'job_id':job['id'],'request_id':key,'status':'normalized',
        'source_sha256':receipt['source_sha256'],'native_sha256':proof['output']['sha256'],
        'gain_db':proof['decision']['applied_gain_db'],'reference':proof['reference'],
        'output_lufs':proof['output'].get('integrated_lufs'),'output_true_peak_dbtp':proof['output'].get('true_peak_dbtp')}


def normalize_all(workers=6):
    if (OUT/'generation.lock').exists():raise ValueError('Generation still active')
    lock=OUT/'normalization.lock'
    with lock.open('x') as stream:stream.write('stock reference gain only')
    try:
        results=[];jobs=read(ART/'recording-plan.json')['jobs']
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for future in as_completed([pool.submit(normalize_job,job) for job in jobs]):
                results.append(future.result())
                if len(results)%100==0:print('NORMALIZED_PROGRESS',len(results),len(jobs),flush=True)
        report={'status':'passed','rows':results,'masters':'untouched','native_playback':'pending'}
        write(OUT/'loudness/normalization-report.json',report);return report
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':normalize_all()
