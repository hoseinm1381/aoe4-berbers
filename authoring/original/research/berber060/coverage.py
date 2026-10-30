"""Offline, read-only generation snapshot; writes only coverage reports."""
import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from common import OUT, ART, write

ERA = {'clowest':'lowest','clow':'low','cmed':'med','chigh':'high','cnone':'none'}
DELIVERY = {'inorm':'norm','ihigh':'high','istealth':'stealth','cnone':'none','inone':'none'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(path, attempts=3):
    """Atomic writers may replace files concurrently; never read their .tmp files."""
    path = Path(path)
    for attempt in range(attempts):
        try:
            before = path.stat()
            data = path.read_bytes()
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError('File changed during snapshot')
            return json.loads(data.decode('utf-8-sig')), digest(data)
        except (OSError, ValueError) as error:
            if attempt + 1 == attempts:
                raise ValueError('Unavailable or changing snapshot: '+str(path)) from error
            time.sleep(.02)


def identity(job):
    return {'voice_id':job['voice_id'],'output_format':'pcm_24000',
        'text':job['generation_text'],'model_id':job.get('model_id','eleven_v3'),
        'language_code':'ar','seed':job['seed'],'use_pvc_as_ivc':True,
        'voice_settings':{'stability':.5,'similarity_boost':.78,'style':0,
                          'use_speaker_boost':False,'speed':1.0}}


def key_for(job):
    return digest(json.dumps(identity(job),sort_keys=True,ensure_ascii=False,
                             separators=(',',':')).encode())


def verified_file(path, expected):
    path = Path(path)
    before = path.stat()
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    after = path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError('Audio changed while reading')
    if not expected or h.hexdigest()!=expected:
        raise ValueError('Audio hash mismatch')
    return after.st_size


def inspect_job(job, receipts):
    key = key_for(job)
    row = {k:job[k] for k in ('id','family','age','delivery','event','take')}
    row.update(request_id=key,status='missing',receipt_status=None,
               duration_seconds=0,source_bytes=0,native_bytes=0,source_sha256=None,native_sha256=None)
    path = Path(receipts)/(key+'.json')
    if not path.exists():
        return row
    try:
        record, receipt_hash = snapshot(path)
        if not isinstance(record,dict):raise ValueError('Receipt is not an object')
        row.update(receipt_status=record.get('status'),receipt_sha256=receipt_hash)
        if record.get('request_id')!=key or record.get('identity')!=identity(job):
            raise ValueError('Receipt identity does not match current planned job')
        state = record.get('status')
        row['status'] = ('review_required' if state=='review_required' else
                         'rejected' if state in ('rejected','rejected_or_unknown') else
                         'accepted' if state=='accepted_acoustic' else 'unknown')
        if state=='rejected_or_unknown':
            row['status']='rejected_or_unknown'
        if row['status']=='accepted':
            quality=record.get('quality',{})
            if not isinstance(quality,dict):raise ValueError('Receipt quality is not an object')
            if quality.get('clipped_samples',0) or not 0<float(quality.get('duration_seconds',0))<=8:
                row.update(status='review_required',reason='Clipping or invalid/excessive duration')
            else:
                row['source_bytes']=verified_file(record['source'],record.get('source_sha256'))
                row['native_bytes']=verified_file(record['native_path'],record.get('native_wav',{}).get('sha256'))
                row['duration_seconds']=float(quality['duration_seconds'])
                row.update(source_sha256=record['source_sha256'],native_sha256=record['native_wav']['sha256'])
        # Flag a replaced receipt rather than mixing old acceptance with new files.
        if digest(path.read_bytes())!=receipt_hash:
            raise ValueError('Receipt changed during audio verification')
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        row.update(status='unknown',reason=str(error),duration_seconds=0,source_bytes=0,native_bytes=0,
                   source_sha256=None,native_sha256=None)
    return row


def normalized_path(value):
    return value.replace('\\','/').lower()


def waveform_counts(rows):
    """Request records remain separate from byte-distinct acoustic assets."""
    accepted=[row for row in rows if row['status']=='accepted']
    result={'accepted_request_records':len(accepted)}
    for kind in ('source','native'):
        hashes=defaultdict(list)
        for row in accepted:
            hashes[row[kind+'_sha256']].append(row)
        result['unique_'+kind+'_waveforms']=len(hashes)
        result[kind+'_duplicate_request_records']=len(accepted)-len(hashes)
        result[kind+'_duplicate_groups']=[{'sha256':sha,'job_ids':sorted(row['id'] for row in group),
            'takes':sorted({row['take'] for row in group})}
            for sha,group in sorted(hashes.items()) if len(group)>1]
    return result


def build_report(plan, profiles, receipts):
    rows=[inspect_job(job,receipts) for job in plan['jobs']]
    by_id={row['id']:row for row in rows}
    counts=Counter(row['status'] for row in rows)
    contexts=defaultdict(lambda:{'paths':set(),'planned':set(),'accepted':set(),'takes':defaultdict(set)})
    assigned=set();assignment_errors=[]
    for assignment in plan['assignments']:
        path=normalized_path(assignment['path']);family=assignment['family']
        assigned.add((family,path));row=by_id.get(assignment['job_id'])
        if row is None:
            assignment_errors.append({'family':family,'path':path,'reason':'Unknown job_id'})
            continue
        if row['family']!=family:
            assignment_errors.append({'family':family,'path':path,'reason':'Cross-family job assignment'})
            continue
        key=(family,ERA.get(assignment['era'],assignment['era']),
             DELIVERY.get(assignment['delivery'],assignment['delivery']),assignment['event'])
        context=contexts[key];context['paths'].add(path);context['planned'].add(row['id'])
        context['takes'][row['take']].add(row['id'])
        if row['status']=='accepted':context['accepted'].add(row['id'])
    expected={(family['family'],normalized_path(media['path']))
              for family in profiles['families'] for media in family['media']}
    context_rows=[]
    for key,context in sorted(contexts.items()):
        accepted=[by_id[jid] for jid in sorted(context['accepted'])]
        waveforms=waveform_counts(accepted)
        accepted_takes=len({row['take'] for row in accepted})
        distinct=min(waveforms['unique_source_waveforms'],waveforms['unique_native_waveforms'])
        context_rows.append(dict(zip(('family','age','delivery','event'),key),
            native_slots=len(context['paths']),planned_selectable_recordings=len(context['planned']),
            accepted_selectable_recordings=distinct,
            planned_take_count=len(context['takes']),accepted_take_records=accepted_takes,
            duplicate_variation_gap=max(0,accepted_takes-distinct),
            distinct_take_shortfall=max(0,len(context['takes'])-distinct),
            takes=[{'take':take,'planned':len(ids),
                    'accepted':len({by_id[jid]['native_sha256'] for jid in ids & context['accepted']}),
                    'accepted_request_records':len(ids & context['accepted'])}
                   for take,ids in sorted(context['takes'].items())],**waveforms))
    families=[]
    for family in sorted({r['family'] for r in rows}):
        group=[r for r in rows if r['family']==family]
        families.append({'family':family,'planned':len(group),'statuses':dict(Counter(r['status'] for r in group)),
            'duration_seconds':round(sum(r['duration_seconds'] for r in group if r['status']=='accepted'),4),
            'source_bytes':sum(r['source_bytes'] for r in group if r['status']=='accepted'),
            'native_bytes':sum(r['native_bytes'] for r in group if r['status']=='accepted'),
            **waveform_counts(group)})
    return {'schema':'berber060-coverage/v2','statuses':dict(counts),'planned_recordings':len(rows),
        'accepted_new_recordings':counts['accepted'],'families':families,'contexts':context_rows,
        'accepted_new_recordings_note':'Legacy job/request-record count; not byte-distinct audio or paid HTTP call count.',
        **waveform_counts(rows),
        'contexts_with_duplicate_variation':sum(bool(row['duplicate_variation_gap']) for row in context_rows),
        'distinct_variation_complete':all(not row['distinct_take_shortfall'] for row in context_rows)
            and bool(context_rows) and counts['accepted']==len(rows)
            and assigned==expected and not assignment_errors,
        'duration_seconds':round(sum(f['duration_seconds'] for f in families),4),
        'source_bytes':sum(f['source_bytes'] for f in families),
        'native_bytes':sum(f['native_bytes'] for f in families),
        'native_assignment_slots':len(assigned),'profile_native_slots':len(expected),
        'profile_paths_without_assignment':[{'family':f,'path':p} for f,p in sorted(expected-assigned)],
        'assignments_outside_profile':[{'family':f,'path':p} for f,p in sorted(assigned-expected)],
        'assignment_errors':assignment_errors,'chronology_gaps':plan.get('chronology_gaps',[]),
        'jobs':rows,'proof_limits':[
            'Accepted means current-plan receipt plus source/native SHA256 checks and recorded acoustic quality; not listening, ASR, language approval, packaging, or native audibility.',
            'Authored Arabic fallback uses modern regional/classical proxy voices; not reconstructed medieval Amazigh or Tuareg speech.',
            'Native slot aliases can share a recording; slot count is not distinct recording count.',
            'Accepted job/request records are not paid HTTP calls: several batch members share one billed call. Budget/provider receipts establish call accounting.',
            'Distinct waveform counts use exact verified WAV SHA256 (uniform generation WAV format); differing hashes do not establish perceptibly distinct delivery or native audibility.',
            'A final distinct-variation claim additionally requires no per-context distinct take shortfall, rather than merely all request records accepted.',
            'Chronology labels and available banks do not prove runtime age scheduling. Missing separate banks remain gaps.',
            'Concurrent generation snapshot spans an interval, not one atomic global instant; rerun after generation stops for final acceptance.']}


def casting_documentation(art):
    """Retained casting decisions are documentation, never acoustic acceptance."""
    art=Path(art)
    path=art/'casting-overrides.json'
    if not path.exists():return []
    overrides,_=snapshot(path)
    return [dict(family=family,voice_id=value['voice_id'],
                 reason=value.get('reason',''),
                 qualification=value.get('qualification',''),
                 historical_language=value.get('historical_language','Modern Arabic regional/classical proxy; not reconstructed medieval speech.'),
                 provider_voice_age_label=value.get('provider_voice_age_label','Provider apparent voice-age metadata; human age not verified.'),
                 qualification_report=value.get('qualification_report'))
            for family,value in sorted(overrides.items())]


def markdown(report):
    lines=['# Voice coverage and gaps','',
        'Snapshot UTC: '+report['snapshot_started_utc']+' to '+report['snapshot_finished_utc'],
        '',f"Accepted current-plan request records: **{report['accepted_request_records']} / {report['planned_recordings']}**.",
        f"Distinct verified WAVs: **{report['unique_source_waveforms']} source / {report['unique_native_waveforms']} native**. Request records do not establish distinct audio or paid HTTP call counts.",
        'Statuses: '+', '.join(f'{k}={v}' for k,v in sorted(report['statuses'].items()))+'.',
        f"Accepted source duration: {report['duration_seconds']:.2f}s; source bytes: {report['source_bytes']}; native WAV bytes: {report['native_bytes']}.",'',
        '| Family | Planned | Accepted records | Distinct source/native | Missing | Other | Source seconds |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for family in report['families']:
        counts=family['statuses'];accepted=counts.get('accepted',0);missing=counts.get('missing',0)
        lines.append(f"| {family['family']} | {family['planned']} | {accepted} | {family['unique_source_waveforms']}/{family['unique_native_waveforms']} | {missing} | {family['planned']-accepted-missing} | {family['duration_seconds']:.2f} |")
    lines+=['','## Duplicate audio and variation gaps','',
        f"Duplicate source/native request records: {report['source_duplicate_request_records']}/{report['native_duplicate_request_records']}; contexts with duplicate take variation: {report['contexts_with_duplicate_variation']}; distinct variation complete: {report['distinct_variation_complete']}.",
        'Exact duplicates remain accepted acoustic request records but count only once as distinct selectable audio. Cross-context alias reuse is reported separately from duplicate takes within one context. Differing hashes alone do not prove audible variation.','']
    for context in report['contexts']:
        if context['duplicate_variation_gap']:
            name='/'.join(str(context[k]) for k in ('family','age','delivery','event'))
            lines.append(f"- {name}: {context['accepted_take_records']} accepted take records, {context['unique_source_waveforms']} distinct source / {context['unique_native_waveforms']} native WAVs; duplicate variation gap {context['duplicate_variation_gap']}.")
    lines+=['','## Native assignments and chronological bank gaps','',
        f"Assigned slots: {report['native_assignment_slots']}; profile slots: {report['profile_native_slots']}; missing assignments: {len(report['profile_paths_without_assignment'])}; assignments outside profile: {len(report['assignments_outside_profile'])}; assignment errors: {len(report['assignment_errors'])}.",'',
        'Separate Age I banks are absent for fishing boat, transport ship, and King; separate Age II fire ship bank is absent. Existing later-age banks are shared/remapped, not newly distinct early-age performances. See exact chronology entries below.','']
    for gap in report['chronology_gaps']:
        lines.append('- '+json.dumps(gap,ensure_ascii=False,sort_keys=True))
    lines+=['','## Casting substitutions and language qualification','',
        'Casting decisions do not establish native-speaker pronunciation, human listening approval, historical dialect authenticity, or native playback. These remain unverified. Voice age is a provider apparent-age proxy; chronology labels do not prove a human actor age or historical linguistic evolution.',
        'Retained script and recast history: [history.md]('+str(Path(__file__).absolute().with_name('history.md'))+').']
    for actor in report.get('casting_substitutions',[]):
        lines.append(f"- {actor['family']}: actor `{actor['voice_id']}`. {actor['reason']} Qualification scope: {actor['qualification']} Language: {actor['historical_language']} Age: {actor['provider_voice_age_label']}")
        if actor.get('qualification_report'):
            lines.append('  Retained [qualification report]('+actor['qualification_report']+').')
    if report.get('casting_decisions_path'):
        lines.append('Current [casting decisions]('+report['casting_decisions_path']+'); abandoned actor sources and decision proofs are retained in [recast history]('+report['recast_history_path']+').')
    lines+=['','## Evidence limits','']+['- '+limit for limit in report['proof_limits']]
    if report.get('plan_changed_during_snapshot') or report.get('profiles_changed_during_snapshot'):
        lines+=['','**Inputs changed during this snapshot; rerun before making an acceptance claim.**']
    lines+=['','Exact per-family/age/delivery/event/take selectable counts and individual job gaps are in `coverage.json`.','']
    return '\n'.join(lines)


def generate(plan_path=None, profiles_path=None, out=None, art=None):
    out=Path(out or OUT);art=Path(art or ART)
    plan_path=Path(plan_path or art/'recording-plan.json')
    profiles_path=Path(profiles_path or out/'profiles/manifest.json')
    started=datetime.now(timezone.utc).isoformat()
    plan,plan_sha=snapshot(plan_path);profiles,profiles_sha=snapshot(profiles_path)
    report=build_report(plan,profiles,out/'receipts')
    report.update(casting_substitutions=casting_documentation(art),
                  casting_decisions_path=str((art/'casting-overrides.json').absolute()),
                  recast_history_path=str((art/'recast-history').absolute()))
    report.update(snapshot_started_utc=started,snapshot_finished_utc=datetime.now(timezone.utc).isoformat(),
        plan_sha256=plan_sha,profiles_sha256=profiles_sha,
        plan_changed_during_snapshot=digest(plan_path.read_bytes())!=plan_sha,
        profiles_changed_during_snapshot=digest(profiles_path.read_bytes())!=profiles_sha,
        generation_lock_present=(out/'generation.lock').exists())
    write(out/'coverage.json',report)
    art.mkdir(parents=True,exist_ok=True)
    (art/'VOICE_GAPS.md').write_text(markdown(report),encoding='utf8')
    print(json.dumps({k:report[k] for k in ('planned_recordings','accepted_new_recordings','statuses','duration_seconds','source_bytes','generation_lock_present')}))
    return report


if __name__=='__main__':
    generate()
