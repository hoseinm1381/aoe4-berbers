"""Encode accepted native copies and independently decode every unique WEM."""
import math
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from common import ART,OUT,read,write,sha
from batch_generation import job_key,single_identity
from encoding import encode,decoded_check,decoder,WWISE


def _normalized_receipt(job):
    """Read-only per-job validation; every original identity/hash gate retained."""
    key=job_key(job);path=OUT/'receipts'/(key+'.json')
    if not path.is_file():return None
    receipt=read(path)
    if receipt.get('status')!='accepted_acoustic':return None
    if receipt.get('request_id')!=key or receipt.get('job_id')!=job['id'] or receipt.get('identity')!=single_identity(job):
        raise ValueError('Accepted source is not the current job identity')
    norm=receipt.get('normalization')
    if not norm:raise ValueError('Stock loudness matching not recorded')
    provenance=Path(norm['provenance'])
    if not provenance.is_file() or sha(provenance)!=norm['provenance_sha256']:raise ValueError('Normalization provenance missing or changed')
    proof=read(provenance);native=Path(receipt['native_path'])
    if proof.get('request_id')!=key or proof.get('event')!=job['event'] or proof.get('output',{}).get('sha256')!=receipt['native_wav']['sha256']:
        raise ValueError('Normalization provenance does not prove current output')
    retained=Path(proof['recipe']['retained_input']);input_hash=proof['recipe']['retained_input_sha256']
    if input_hash!=proof['source']['sha256'] or not retained.is_file() or sha(retained)!=input_hash:
        raise ValueError('Retained normalization rebuild input changed')
    if not native.is_file() or sha(native)!=receipt['native_wav']['sha256']:raise ValueError('Normalized native source changed')
    if not Path(receipt['source']).is_file() or sha(receipt['source'])!=receipt['source_sha256']:raise ValueError('Lossless master changed')
    return key,receipt


def normalized_receipts(plan,workers=6):
    """Bounded parallel reads, with deterministic plan-order results/errors.

    workers=1 retains a serial path for parity checks. No source/receipt writes.
    """
    if type(workers) is not int or not 1<=workers<=6:
        raise ValueError('Normalized receipt validation workers must be 1–6')
    if workers==1:
        return {pair[0]:pair[1] for pair in map(_normalized_receipt,plan['jobs']) if pair is not None}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return {pair[0]:pair[1] for pair in executor.map(_normalized_receipt,plan['jobs']) if pair is not None}


def valid_decode(row):
    try:
        proof=row['decode']
        return (row.get('status')=='passed' and proof['clipped_samples']==0 and
            all(isinstance(proof[k],(int,float)) and math.isfinite(proof[k]) for k in ('duration_seconds','peak','rms','snr_db')) and
            0<proof['duration_seconds']<=8.1 and 0<proof['peak']<=1 and proof['rms']>=.0007)
    except (KeyError,TypeError,ValueError):return False


def validate_rows(report,expected):
    if report.get('status')!='passed' or report.get('quality')!='Medium':raise ValueError('Current passed Medium decode proof required')
    def signature(row):
        return (str(Path(row['source']).resolve()),row['source_sha256'],row['sha256'],row['bytes'],row['request_id'],row['normalization_provenance_sha256'])
    expected_signatures={signature(r) for r in expected};actual=[signature(r) for r in report['rows']]
    if len(actual)!=len(set(actual)) or set(actual)!=expected_signatures or len(expected)!=len(expected_signatures):
        raise ValueError('Decode proof does not exactly cover current sources/payloads/normalization')
    if not all(valid_decode(r) for r in report['rows']):raise ValueError('Cached decode proof has clipping/silence/invalid measurements')


def require_current_validation(plan,manifest,encoding):
    report=read(OUT/'decoded-media-validation.json')
    if report.get('recording_plan_sha256')!=sha(ART/'recording-plan.json'):raise ValueError('Decode report uses an older recording plan')
    if report.get('validator_sha256')!=sha(__file__) or report.get('encoding_code_sha256')!=sha(Path(__file__).with_name('encoding.py')):
        raise ValueError('Decode validation code changed since proof')
    decoder_path=OUT/'tools/vgmstream-r2117/vgmstream-cli.exe'
    if not decoder_path.is_file() or report.get('decoder_sha256')!=sha(decoder_path) or report.get('wwise_sha256')!=sha(WWISE):
        raise ValueError('Decode/encoder tooling changed since proof')
    receipts=normalized_receipts(plan);expected=[]
    for key,r in receipts.items():
        e=encoding.get(key)
        if not e or e['source_sha256']!=r['native_wav']['sha256'] or Path(e['source']).resolve()!=Path(r['native_path']).resolve():
            raise ValueError('Current normalized Medium encoding missing')
        expected.append({**e,'request_id':key,'normalization_provenance_sha256':r['normalization']['provenance_sha256']})
    validate_rows(report,expected)
    payloads={r['sha256'] for r in manifest['files'] if r['path'].lower().endswith('.wem')}
    if payloads!={r['sha256'] for r in expected}:raise ValueError('Packaged WEM payloads differ from current independently decoded set')
    return {'status':'passed','report_sha256':sha(OUT/'decoded-media-validation.json'),'recordings':len(expected),
        'unique_payloads':len(payloads),'clarity_listening':'pending','native_playback':'pending'}


def build(workers=6):
    if (OUT/'generation.lock').exists() or (OUT/'normalization.lock').exists():
        raise ValueError('Wait for synthesis and normalization')
    plan=read(ART/'recording-plan.json');plan_digest=sha(ART/'recording-plan.json')
    receipts=normalized_receipts(plan);paths=[Path(r['native_path']) for r in receipts.values()]
    if not paths:raise ValueError('No accepted sources')
    decoder_path=decoder()  # Serialize pinned-tool admission before parallel reads.
    rows=encode(paths,'Medium');target=OUT/'decoded-media-validation.json'
    by_source={str(Path(r['native_path']).resolve()):(key,r) for key,r in receipts.items()}
    for row in rows:
        key,r=by_source[str(Path(row['source']).resolve())]
        row.update(request_id=key,normalization_provenance_sha256=r['normalization']['provenance_sha256'])
    previous=read(target) if target.exists() else {}
    same_tools=(previous.get('status')=='passed' and previous.get('decoder_sha256')==sha(decoder_path) and
        previous.get('wwise_sha256')==sha(WWISE) and previous.get('validator_sha256')==sha(__file__) and
        previous.get('encoding_code_sha256')==sha(Path(__file__).with_name('encoding.py')))
    cached={(r['sha256'],r['source_sha256']):r for r in previous.get('rows',[]) if same_tools and valid_decode(r)}
    result=[]
    def check(row):
        old=cached.get((row['sha256'],row['source_sha256']))
        if old:return {**old,**row}
        checked=decoded_check(row)
        result={**row,'decode':checked,'status':'passed'}
        if not valid_decode(result):raise ValueError('Decoded Vorbis has clipping/silence/invalid measurements: '+row['wem'])
        return result
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(check,row) for row in rows]):
            result.append(future.result())
            if len(result)%100==0:print('DECODED_PROGRESS',len(result),len(rows),flush=True)
    result.sort(key=lambda row:row['wem'])
    report={'status':'passed','quality':'Medium','codec':'genuine Wwise Vorbis, mono48k',
        'wwise':str(WWISE),'wwise_sha256':sha(WWISE),'decoder_sha256':sha(decoder()),
        'unique_recordings_encoded':len(result),'unique_payloads':len({r['sha256'] for r in result}),
        'encoded_bytes':sum({r['sha256']:r['bytes'] for r in result}.values()),
        'minimum_snr_db':min(r['decode']['snr_db'] for r in result),'rows':result,
        'proof_scope':'Independent decoding, source/duration comparison and clipping/silence checks',
        'clarity_listening':'pending','native_playback':'pending'}
    report.update(recording_plan_sha256=plan_digest,validator_sha256=sha(__file__),encoding_code_sha256=sha(Path(__file__).with_name('encoding.py')))
    if sha(ART/'recording-plan.json')!=plan_digest:raise ValueError('Recording plan changed during final decoding')
    validate_rows(report,rows)
    write(target,report);print('AUDIO_OBJECTIVE_VERIFIED',len(result),report['encoded_bytes']);return report


if __name__=='__main__':build()
