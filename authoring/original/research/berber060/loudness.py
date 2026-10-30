"""Offline, small stock speech reference and optional reversible gain-only matching."""
import argparse, hashlib, json, math, re, shutil, subprocess, tempfile, time, wave
from pathlib import Path
import numpy as np
from common import OUT, ART, ARCH, read, write, run, sha
from encoding import decoder

def measure(path):
    path=Path(path)
    with wave.open(str(path),'rb') as w:
        if w.getsampwidth()!=2: raise ValueError('Expected decoded s16le WAV')
        rate=w.getframerate();channels=w.getnchannels()
        a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
    if not len(a) or not np.all(np.isfinite(a)):raise ValueError('Invalid PCM')
    peak=float(np.max(np.abs(a)));rms=float(np.sqrt(np.mean(a*a)))
    result={'path':str(path),'sha256':sha(path),'duration_seconds':len(a)/rate/channels,
        'sample_rate':rate,'channels':channels,'rms_dbfs':20*math.log10(max(rms,1e-12)),
        'sample_peak_dbfs':20*math.log10(max(peak,1e-12)),
        'clipped_samples':int(np.count_nonzero(np.abs(a)>=.999))}
    ffmpeg=shutil.which('ffmpeg')
    if ffmpeg:
        process=subprocess.run([ffmpeg,'-hide_banner','-nostats','-i',str(path),'-af',
            'loudnorm=I=-23:TP=-1:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,encoding='utf8',errors='replace')
        if process.returncode:raise ValueError('FFmpeg loudness measurement failed')
        candidates=re.findall(r'\{[^{}]*"input_i"[^{}]*\}',process.stderr,re.S)
        if not candidates:raise ValueError('FFmpeg loudness summary missing')
        summary=json.loads(candidates[-1])
        lufs=float(summary['input_i']);lra=float(summary['input_lra'])
        result.update(integrated_lufs=lufs if math.isfinite(lufs) else None,true_peak_dbtp=float(summary['input_tp']),
            integrated_lufs_status='finite' if math.isfinite(lufs) else 'unavailable_short_or_gated',
            loudness_range_lu=lra if math.isfinite(lra) else None,measurement='FFmpeg loudnorm first-pass EBU R128/BS.1770')
    else:result['measurement']='RMS/sample peak only; FFmpeg unavailable'
    return result

def gain_decision(measured,target_lufs,peak_limit_db=-1,max_boost_db=6,target_rms_dbfs=None):
    current=measured.get('integrated_lufs');true_peak=measured.get('true_peak_dbtp')
    rms_proxy=current is None or not math.isfinite(current)
    if rms_proxy:
        current=measured.get('rms_dbfs');target=target_rms_dbfs
    else:target=target_lufs
    if current is None or target is None or true_peak is None or not all(math.isfinite(x) for x in (current,true_peak,target,target_lufs,peak_limit_db,max_boost_db)):
        raise ValueError('Finite loudness metric, target and true peak required')
    if not -40<=target_lufs<=-10 or not -6<=peak_limit_db<=0 or not 0<=max_boost_db<=12:
        raise ValueError('Unsafe normalization configuration')
    if rms_proxy and not -50<=target_rms_dbfs<=-10:raise ValueError('Unsafe RMS target')
    requested=target-current
    gain=min(requested,max_boost_db,peak_limit_db-true_peak)
    return {'requested_gain_db':requested,'applied_gain_db':gain,'target_lufs':target_lufs,
        'target_rms_dbfs':target_rms_dbfs,'matching_metric':'rms_proxy' if rms_proxy else 'integrated_lufs',
        'matching_basis':'Short/nonfinite integrated loudness: stock RMS proxy; not an EBU integrated-loudness match' if rms_proxy else 'Measured integrated LUFS',
        'predicted_lufs':None if rms_proxy else current+gain,
        'predicted_rms_dbfs':measured.get('rms_dbfs',0)+gain if measured.get('rms_dbfs') is not None else None,
        'predicted_true_peak_dbtp':true_peak+gain,
        'target_constrained':gain<requested-1e-6,'policy':'gain only; no compression, limiting, trimming or time changes'}

def normalize_to_reference(source,target,target_lufs,peak_limit_db=-1,max_boost_db=6,target_rms_dbfs=None):
    """Explicit opt-in copy only. Never mutates receipts, masters or native generation."""
    source=Path(source);target=Path(target)
    if source.resolve()==target.resolve() or target.exists():raise ValueError('Choose a new output copy')
    before=measure(source);decision=gain_decision(before,target_lufs,peak_limit_db,max_boost_db,target_rms_dbfs)
    with wave.open(str(source),'rb') as w:
        params=w.getparams();a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
    output=np.rint(a*10**(decision['applied_gain_db']/20))
    if np.max(np.abs(output))>32767:raise ValueError('Gain would clip PCM')
    target.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(target),'wb') as w:w.setparams(params);w.writeframes(output.astype('<i2').tobytes())
    after=measure(target)
    if after.get('true_peak_dbtp',-100)>peak_limit_db+.15:
        target.unlink();raise ValueError('Measured true peak exceeds permitted ceiling')
    return {'source':before,'output':after,'decision':decision,'native_playback':'not_tested','listening':'not_performed'}

def reference_target(event,nonverbal=False,reference_path=None):
    """Small observed command cluster; effort targets follow their native event."""
    reference_path=Path(reference_path or OUT/'loudness/stock-reference.json')
    reference=read(reference_path)
    effort=nonverbal or event.lower().startswith('effort')
    matches=[r['stock']['integrated_lufs'] for r in reference['rows']
             if r.get('status')=='measured' and r['event'].lower()==event.lower() and r.get('kind')=='effort'
             and r['stock'].get('integrated_lufs') is not None and math.isfinite(r['stock']['integrated_lufs'])]
    rms_matches=[r['stock']['rms_dbfs'] for r in reference['rows']
             if r.get('status')=='measured' and r['event'].lower()==event.lower() and r.get('kind')=='effort' and 'rms_dbfs' in r['stock']]
    command_rms=[r['stock']['rms_dbfs'] for r in reference['rows'] if r.get('status')=='measured' and r.get('kind')=='command' and 'rms_dbfs' in r['stock']]
    fallback_rms=float(np.median(command_rms)) if command_rms else None
    if effort and (matches or rms_matches):
        return {'target_lufs':float(np.median(matches)) if matches else -21.5,
                'basis':'Median measured stock reference for this effort event' if matches else 'No finite integrated effort reference; conservative command LUFS fallback and event-matched RMS proxy',
                'target_rms_dbfs':float(np.median(rms_matches)) if rms_matches else fallback_rms,
                'rms_basis':'Measured same-effort stock RMS proxy for short/nonfinite LUFS' if rms_matches else 'Conservative measured command stock RMS proxy for unreferenced effort',
                'reference_event':event,'reference_count':len(matches),'reference_sha256':sha(reference_path)}
    return {'target_lufs':-21.5,'basis':'Measured command cluster rounded from -21.48 LUFS; conservative fallback for an unmeasured effort event' if effort else
        'Measured command cluster rounded from -21.48 LUFS (four native commands: -21.80..-21.12)',
        'target_rms_dbfs':fallback_rms,'rms_basis':'Conservative measured command stock RMS proxy for short/nonfinite LUFS',
        'reference_event':event,'reference_count':0 if effort else 4,'reference_sha256':sha(reference_path)}

def _replace_with_retry(source,target):
    """Atomic rename, with the same bounded Windows sharing retry as common.write."""
    for attempt in range(8):
        try:
            Path(source).replace(target)
            return
        except PermissionError:
            if attempt==7:raise
            time.sleep(min(.05*2**attempt,1.6))

def _rebuild_pending(original,pending,proof):
    """Recreate an interrupted local staging file from the recorded gain recipe."""
    gain=proof['decision']['applied_gain_db']
    if not isinstance(gain,(int,float)) or not math.isfinite(gain) or gain>12:
        raise ValueError('Invalid recorded normalization gain')
    with wave.open(str(original),'rb') as w:
        params=w.getparams();samples=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
    output=np.rint(samples*10**(gain/20))
    if np.max(np.abs(output))>32767:raise ValueError('Recorded normalization gain would clip')
    with tempfile.TemporaryDirectory(prefix='normalize-rebuild-',dir=pending.parent) as folder:
        temporary=Path(folder)/'rebuilt.wav'
        with wave.open(str(temporary),'wb') as w:w.setparams(params);w.writeframes(output.astype('<i2').tobytes())
        if sha(temporary)!=proof['output']['sha256']:
            raise ValueError('Recorded normalization recipe does not reproduce output hash')
        _replace_with_retry(temporary,pending)

def normalize_native(request_id,event,expected_sha256,nonverbal=False):
    """Explicit local native-copy replacement. Caller alone updates receipt metadata.

    Retains the pre-normalization native copy for lossless reconstruction. Never
    reads or writes receipts, budget, provider APIs, or synthesis master sources.
    Call only after generation has stopped; expected hash prevents stale updates.
    """
    if not re.fullmatch('[0-9a-f]{64}',request_id) or not re.fullmatch('[0-9a-f]{64}',expected_sha256):
        raise ValueError('Invalid request identity or expected source hash')
    target=OUT/'wav'/f'{request_id}.wav'
    with wave.open(str(target),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,48000):
            raise ValueError('Native copy must be mono 48kHz s16le')
    destination=OUT/'loudness';destination.mkdir(parents=True,exist_ok=True)
    original=destination/'native-pre-normalization'/f'{request_id}.wav';original.parent.mkdir(exist_ok=True)
    provenance=destination/'normalization-provenance'/f'{request_id}.json'
    pending=destination/'native-pending'/f'{request_id}.wav';pending.parent.mkdir(exist_ok=True)
    if provenance.exists():
        prior=read(provenance)
        if prior.get('request_id')!=request_id or prior.get('event')!=event or prior.get('nonverbal')!=nonverbal:
            raise ValueError('Normalization provenance identity differs from requested recording')
        source_hash=prior['source']['sha256'];output_hash=prior['output']['sha256']
        if prior['recipe']['retained_input_sha256']!=source_hash or sha(original)!=source_hash:
            raise ValueError('Retained normalization input changed')
        if expected_sha256 not in (source_hash,output_hash):
            raise ValueError('Expected native hash differs from normalization provenance')
        actual=sha(target)
        if actual==output_hash:return prior
        if actual!=source_hash:raise ValueError('Native source changed before normalization')
        if pending.exists():
            if sha(pending)!=output_hash:raise ValueError('Pending normalized copy changed')
        else:_rebuild_pending(original,pending,prior)
        # Proof is already durable, so a failed rename can be retried locally.
        if sha(target)!=source_hash:raise ValueError('Native source changed during normalization')
        _replace_with_retry(pending,target)
        return prior
    if sha(target)!=expected_sha256:raise ValueError('Native source changed before normalization')
    if original.exists():
        if sha(original)!=expected_sha256:
            raise ValueError('Existing retained original differs from current normalization state')
    else:shutil.copyfile(target,original)
    if sha(original)!=expected_sha256:raise ValueError('Retained normalization input changed')
    reference=reference_target(event,nonverbal)
    with tempfile.TemporaryDirectory(prefix='normalize-',dir=destination) as folder:
        temporary=Path(folder)/'normalized.wav'
        result=normalize_to_reference(original,temporary,reference['target_lufs'],target_rms_dbfs=reference.get('target_rms_dbfs'))
        if sha(target)!=expected_sha256:raise ValueError('Native source changed during normalization')
        _replace_with_retry(temporary,pending)
    result['output']['path']=str(target)
    ffmpeg=shutil.which('ffmpeg')
    version=subprocess.run([ffmpeg,'-version'],capture_output=True,text=True).stdout.splitlines()[0] if ffmpeg else None
    result.update(request_id=request_id,event=event,nonverbal=nonverbal,reference=reference,
        ffmpeg_version=version,ffmpeg_path=ffmpeg,
        recipe={'retained_input':str(original),'retained_input_sha256':sha(original),
            'target_lufs':reference['target_lufs'],'peak_limit_dbtp':-1,'max_boost_db':6,
            'target_rms_dbfs':reference.get('target_rms_dbfs'),'matching_metric':result['decision']['matching_metric'],
            'sample_operation':'s16le round(input_sample * 10**(applied_gain_db / 20))',
            'filter':'FFmpeg loudnorm measurement only; output is gain-only NumPy PCM'},
        native_promotion={'protocol':'proof-before-atomic-promotion/v1','pending_output':str(pending),
            'expected_input_sha256':expected_sha256,'expected_output_sha256':result['output']['sha256']},
        receipt_update_required=True)
    # This write MUST complete before replacing the current native file. The
    # immutable proof supports either prepared (old audio) or promoted (new audio).
    write(provenance,result)
    if sha(target)!=expected_sha256:raise ValueError('Native source changed before promotion')
    if sha(pending)!=result['output']['sha256']:raise ValueError('Pending normalized copy changed')
    _replace_with_retry(pending,target)
    return result

def reference():
    profiles={r['family']:r for r in read(OUT/'profiles/manifest.json')['families']}
    plan=read(ART/'recording-plan.json');jobs={j['id']:j for j in plan['jobs']}
    # Native assignment list finds corresponding generated clips without scanning all receipts.
    cases=[('villager','select'),('scout','select'),('tuareg','attack'),('imam','select'),
           ('handgunner','effortpain'),('king','effortdeath'),('tuareg','effortpain'),('villager','effortdeath')]
    from generation import request_id
    from batch_generation import single_identity
    destination=OUT/'loudness';destination.mkdir(parents=True,exist_ok=True)
    rows=[]
    for family,event in cases:
        candidates=[j for j in jobs.values() if j['family']==family and j['event']==event]
        candidates.sort(key=lambda j:(j['delivery']!='norm',j['age']!='med',j['id']))
        accepted=[]
        for j in candidates:
            path=OUT/'receipts'/(request_id(single_identity(j))+'.json')
            if path.exists():
                receipt=read(path)
                if receipt['status']=='accepted_acoustic':accepted.append((j,receipt))
        if not accepted:
            rows.append({'family':family,'event':event,'status':'accepted_new_clip_unavailable'});continue
        j,receipt=accepted[0];profile=profiles[family]
        mapping={'lowest':'clowest','low':'clow','med':'cmed','high':'chigh','none':'cnone'}
        deliveries={'norm':'inorm','high':'ihigh','stealth':'istealth','none':'cnone'}
        matching=[m for m in read(OUT/'profiles'/f'{family}-media.json') if m.get('parsed') and m['event']==event and m['era']==mapping[j['age']] and m['delivery']==deliveries[j['delivery']]]
        if not matching:raise ValueError('Corresponding stock media not found')
        media=sorted(matching,key=lambda m:(m['take'],m['alternate'],m['path']))[0]
        member_key=hashlib.sha256(media['path'].replace('\\','/').lower().encode()).hexdigest()[:12]
        stock_wem=destination/'stock'/f'{family}-{event}-{member_key}.wem';stock_wem.parent.mkdir(parents=True,exist_ok=True)
        if not stock_wem.exists():run(ARCH,'extract-member',profile['donor_archive'],media['path'],stock_wem)
        stock_wav=stock_wem.with_suffix('.wav')
        if not stock_wav.exists():run(decoder(),'-i','-o',stock_wav,stock_wem)
        source=Path(receipt['native_path'])
        if sha(source)!=receipt['native_wav']['sha256']:raise ValueError('Accepted native source changed')
        stock_measure=measure(stock_wav);new_measure=measure(source)
        rows.append({'family':family,'event':event,'kind':'effort' if event.startswith('effort') else 'command',
            'age':j['age'],'delivery':j['delivery'],'status':'measured','donor_archive':profile['donor_archive'],
            'donor_profile_sha256':profile['donor_sha256'],'stock_media_path':media['path'],
            'stock_wem_sha256':sha(stock_wem),'new_request_id':receipt['request_id'],
            'stock':stock_measure,'new':new_measure,
            'lufs_delta_new_minus_stock':new_measure.get('integrated_lufs',0)-stock_measure.get('integrated_lufs',0)})
    measured=[r for r in rows if r['status']=='measured']
    summary={}
    for kind in ('command','effort'):
        subset=[r for r in measured if r['kind']==kind]
        if subset:
            summary[kind]={'n':len(subset),'stock_median_lufs':float(np.median([r['stock']['integrated_lufs'] for r in subset])),
                'new_median_lufs':float(np.median([r['new']['integrated_lufs'] for r in subset])),
                'median_paired_delta_lu':float(np.median([r['lufs_delta_new_minus_stock'] for r in subset])),
                'stock_min_max_lufs':[min(r['stock']['integrated_lufs'] for r in subset),max(r['stock']['integrated_lufs'] for r in subset)]}
    result={'scope':'Small objective reference; actual shipping stock speech and accepted native 48k copies',
        'rows':rows,'summary':summary,'listening':'not_performed','native_playback':'not_tested',
        'normalizer':'Optional gain-only normalize_to_reference; no source/receipt mutation performed'}
    ffmpeg=shutil.which('ffmpeg')
    result['ffmpeg_version']=subprocess.run([ffmpeg,'-version'],capture_output=True,text=True).stdout.splitlines()[0] if ffmpeg else None
    result['decoder_executable_sha256']=sha(decoder())
    result['archive_provenance']={r['archive']:r.get('archive_sha256') for r in read(OUT/'inventory/stock-profiles.json')}
    write(destination/'stock-reference.json',result)
    print(json.dumps(summary,indent=2));return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Offline stock reference and explicit gain-only native copy matching')
    parser.add_argument('action',choices=['reference','normalize'],nargs='?',default='reference')
    parser.add_argument('--request-id');parser.add_argument('--event');parser.add_argument('--expected-sha256')
    parser.add_argument('--nonverbal',action='store_true');args=parser.parse_args()
    if args.action=='reference':reference()
    else:
        if not all((args.request_id,args.event,args.expected_sha256)):parser.error('normalize requires --request-id, --event, --expected-sha256')
        print(json.dumps(normalize_native(args.request_id,args.event,args.expected_sha256,args.nonverbal),indent=2))
