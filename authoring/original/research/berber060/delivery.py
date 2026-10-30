"""Offline final delivery. Requires complete validated audio; never installs it."""
import argparse, hashlib, shutil, zipfile, json, math
from collections import defaultdict
from pathlib import Path
from common import ROOT, OUT, ART, BASE, BASE_SHA, read, write, sha
from coverage import generate
from review_script import export as export_register,validate_export
from final_audio import require_current_validation, normalized_receipts
from package_audio import validate as validate_audio, prepare, load_medium, relative


def zip_tree(folder, target):
    folder=Path(folder);target=Path(target)
    paths=sorted(p for p in folder.rglob('*') if p.is_file())
    if any(p.is_symlink() or p.is_junction() for p in folder.rglob('*')):
        raise ValueError('Package stage contains a link')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in paths:z.write(p,p.relative_to(folder).as_posix())
    with zipfile.ZipFile(target) as z:
        if z.testzip():raise ValueError('ZIP CRC failed')
        if set(z.namelist())!={p.relative_to(folder).as_posix() for p in paths}:
            raise ValueError('ZIP member set differs')
        hashes={p.relative_to(folder).as_posix():sha(p) for p in paths}
        for name,digest in hashes.items():
            with z.open(name) as stream:
                actual=hashlib.file_digest(stream,'sha256').hexdigest()
            if actual!=digest:raise ValueError('ZIP content digest differs')
    return {'zip':str(target),'sha256':sha(target),'bytes':target.stat().st_size,
            'members':hashes,'crc':'passed','member_sha256':'passed'}


INSTALL='''Berber Dynasties 0.6.0 native voice candidate

1. Keep the verified 0.5.1 ZIP and its audio as rollback.
2. Extract the native-audio companion ZIP to an ordinary local directory.
   Keep all payloads and native-audio-manifest.json together. Junction or
   symlink paths are deliberately refused by the installer.
3. Close Age of Empires IV completely. In PowerShell, from the extracted
   companion directory (substitute your actual game installation path):
   .\\Install-BerberNativeAudio.ps1 -Action Validate -AudioRoot "E:\\Games\\steamapps\\common\\Age of Empires IV\\cardinal\\audio"
   .\\Install-BerberNativeAudio.ps1 -Action Install -AudioRoot "E:\\Games\\steamapps\\common\\Age of Empires IV\\cardinal\\audio"
   .\\Install-BerberNativeAudio.ps1 -Action Verify -AudioRoot "E:\\Games\\steamapps\\common\\Age of Empires IV\\cardinal\\audio"
4. Import the Garrison ZIP, select The Berber Dynasties version 0.6.0,
   then start the game. Both packages are required for the new voices.
5. Restart the game completely after every native audio change.

Uninstall: close the game, then run the same script with -Action Uninstall
and the same AudioRoot. Only unchanged files owned by its saved install
state are removed. Modified files are preserved and reported. Restore
0.5.1 through Garrison for rollback. Do not delete stock game archives.

Installation, playback and listening are separate acceptance gates.
Review VOICE_GAPS.md for historical, chronology and recording limitations.
Native gameplay tests remain pending unless EVIDENCE.json says otherwise.
Test each available age, individual/group orders, normal/combat/stealth,
pain/death/efforts, work/trade/religion, siege, navy and King modes.
Include unchanged stock units as controls and record any missing trigger.
'''

REBUILD='''# Rebuilding Berber 0.6.0

The authoritative base is the retained, verified 0.5.1 archive; never rebuild
these skins/models from older authoring sources. All new source and recipes
are isolated under art/voices_0_6_0 and research/berber060.

Use Python 3.13 (NumPy/SciPy), installed Garrison native tools, and Wwise
2023.1.3.8471. The retained recording plan, casting, lossless masters,
batch alignments, receipts, current voice-script.csv plus its plan/cast/hash manifest,
private profiles, binding payloads and scripts
are required inputs. Credentials are not included. Rebuild is offline;
do not run generation or credential-resume scripts to rebuild a delivery.

On this Windows host, run helpers through research/berber060/run_local.py
(Python313 run_local.py helper.py [arguments]). It limits BLAS threads and
uses CPython's process-local fallback for the stalled WMI platform query;
it does not change Windows services or persistent system settings.

Run coverage.py for hash-checked recording coverage. Regenerate missing
48kHz WAV intermediates from accepted lossless source using
generation.prepare_native, then replay the exact retained normalization recipe and
verify final WAV hashes against receipts. Retain normalized WAV caches until this
restore route is verified byte-for-byte. Encode through encoding.encode(paths,'Medium').
Run encoding.py compare on current normalized sources (Low/Medium/High), then
final_audio.py for independent decoding of every Medium source. Run
package_audio.py, release.py compose, then delivery.py build. Every step
validates its source hashes. Recreate missing official donors through the
inventory/profile extraction route; retain donor provenance manifests.

The native companion stores unique WEM payloads once. Installation expands
native aliases using verified private hardlinks where supported, copies
otherwise. Download size therefore differs from installed logical size.
'''


def require_complete_audio(coverage,manifest,prepared):
    unresolved={r['id'] for r in coverage['jobs'] if r['status']!='accepted'}
    fallbacks=manifest.get('fallbacks',[])
    fallback_ids=[r['job_id'] for r in fallbacks]
    if len(set(fallback_ids))!=len(fallback_ids) or set(fallback_ids)!=unresolved:
        raise ValueError('Fallbacks do not exactly cover unresolved current jobs')
    for field in ('profiles','files','fallbacks'):
        if manifest.get(field,[])!=prepared.get(field,[]):
            raise ValueError('Native manifest is not the current validated recording payload: '+field)


def audio_statistics(coverage,manifest):
    accepted=[r for r in coverage['jobs'] if r['status']=='accepted'];sources={};natives=set()
    for row in accepted:
        if not row.get('source_sha256') or not row.get('native_sha256'):raise ValueError('Accepted waveform hash missing')
        digest=row['source_sha256'];duration=row['duration_seconds']
        if digest in sources and abs(sources[digest]-duration)>1e-6:raise ValueError('Same source waveform has conflicting durations')
        sources[digest]=duration;natives.add(row['native_sha256'])
    return {'planned_request_records':len(coverage['jobs']),'accepted_request_records':len(accepted),
        'unique_source_waveforms':len(sources),'unique_native_waveforms':len(natives),
        'unique_encoded_wem_payloads':len({r['sha256'] for r in manifest['files'] if r['path'].lower().endswith('.wem')}),
        'accepted_request_source_duration_seconds':round(sum(r['duration_seconds'] for r in accepted),4),
        'unique_source_waveform_duration_seconds':round(sum(sources.values()),4),
        'count_scope':'Current accepted job/request records, byte-distinct verified WAVs and unique WEM blobs are separate; none establishes paid HTTP calls or perceptibly distinct performances.'}


def comparison_summary(report,plan_digest,receipts):
    if report.get('status')!='objective_comparison_complete' or report.get('chosen_quality')!='Medium' or report.get('recording_plan_sha256')!=plan_digest:
        raise ValueError('Current normalized Low/Medium/High comparison required')
    seen=set();keys=set();quality={q:[] for q in ('Low','Medium','High')}
    for row in report['rows']:
        q=row['conversion'];key=row['request_id'];receipt=receipts.get(key)
        if q not in quality or (key,q) in seen or not receipt or row['source_sha256']!=receipt['native_wav']['sha256'] or row['normalization_provenance_sha256']!=receipt['normalization']['provenance_sha256']:
            raise ValueError('Comparison contains superseded or unnormalized source')
        snr=row['decode']['snr_db']
        if row['decode'].get('clipped_samples') or not isinstance(snr,(int,float)) or not math.isfinite(snr):raise ValueError('Invalid comparison decode measurements')
        seen.add((key,q));keys.add(key);quality[q].append(row)
    if not keys or seen!={(key,q) for key in keys for q in quality}:raise ValueError('Incomplete comparison quality set')
    return {'chosen_quality':'Medium','selection_status':'provisional_objective_bandwidth_snr_comparison',
        'rationale':report.get('rationale'),'representative_recordings':len(keys),
        'qualities':{q:{'unique_encoded_bytes':sum({r['sha256']:r['bytes'] for r in rows}.values()),'minimum_snr_db':min(r['decode']['snr_db'] for r in rows)} for q,rows in quality.items()},
        'listening':'pending','native_playback':'pending'}


def encoded_variations(plan,manifest,plan_sha256,audio_manifest_sha256):
    aliases={};files_seen=set()
    for row in manifest['files']:
        path=relative(row['path'].replace('\\','/')).lower()
        if path in files_seen:raise ValueError('Duplicate case-insensitive native file alias')
        files_seen.add(path)
        if path.endswith('.wem'):aliases[path]=row['sha256']
    assigned=set();groups=defaultdict(lambda:{'jobs':set(),'paths':set(),'wem_hashes':set()})
    for row in plan['assignments']:
        path=relative(row['path'].replace('\\','/')).lower()
        if path in assigned:raise ValueError('Duplicate native assignment alias')
        if path not in aliases:raise ValueError('Native assignment is missing from actual WEM payload map')
        assigned.add(path)
        key=tuple(row[k] for k in ('family','event','delivery','era'));group=groups[key]
        group['jobs'].add(row['job_id']);group['paths'].add(path);group['wem_hashes'].add(aliases[path])
    if assigned!=set(aliases):raise ValueError('Actual WEM payload map has aliases outside current assignments')
    contexts=[]
    for key,group in sorted(groups.items()):
        planned=len(group['jobs']);actual=len(group['wem_hashes'])
        contexts.append({**dict(zip(('family','event','delivery','era'),key)),
            'planned_distinct_takes':planned,'native_slots':len(group['paths']),
            'encoded_distinct_recordings':actual,'distinct_take_shortfall':max(0,planned-actual)})
    shortfalls=[r for r in contexts if r['distinct_take_shortfall']]
    return {'schema':'berber060-encoded-variations/v1','plan_sha256':plan_sha256,
        'audio_manifest_sha256':audio_manifest_sha256,'native_slots':len(assigned),'contexts':contexts,
        'contexts_with_shortfalls':len(shortfalls),'missing_distinct_takes':sum(r['distinct_take_shortfall'] for r in contexts),
        'encoded_variation_complete':bool(contexts) and not shortfalls,
        'proof_scope':'Actual validated WEM SHA256 by family/native event/delivery/era; repeated aliases do not inflate unique planned job IDs. Different encoded bytes do not prove perceptibly distinct performances.',
        'listening':'pending','native_playback':'pending'}


def render_delivery_gaps(coverage,manifest,encoded=None):
    lines=['\n## Current delivery evidence and remaining gaps\n',
        'Listening, historical pronunciation/native-speaker review, installation and native playback remain pending. Byte-distinct audio does not prove perceptibly different takes.\n']
    for heading,rows in [('Documented recording substitutions',manifest.get('fallbacks',[])),
        ('Retained chronology gaps',coverage.get('chronology_gaps',[])),
        ('Contexts with distinct take shortfalls',[r for r in coverage.get('contexts',[]) if r.get('distinct_take_shortfall',0)]),
        ('Encoded WEM distinct take shortfalls',[r for r in (encoded or {}).get('contexts',[]) if r.get('distinct_take_shortfall',0)])]:
        lines.append('### '+heading+'\n')
        lines.extend('- '+json.dumps(row,ensure_ascii=False,sort_keys=True) for row in rows)
        if not rows:lines.append('None recorded in the current report.')
        lines.append('')
    return '\n'.join(lines)


def build():
    if (OUT/'generation.lock').exists() or (OUT/'normalization.lock').exists():raise ValueError('Generation or normalization still active')
    if sha(BASE)!=BASE_SHA:raise ValueError('0.5.1 rollback changed')
    composition=read(OUT/'composition-report.json')
    if composition['status']!='passed':raise ValueError('Composition not validated')
    candidate=Path(composition['archive'])
    if sha(candidate)!=composition['archive_sha256']:raise ValueError('Candidate changed')
    coverage=generate()
    if any(coverage[k] for k in ('profile_paths_without_assignment','assignments_outside_profile','assignment_errors')):
        raise ValueError('Unresolved native assignment coverage')
    native=(OUT/'native-package').resolve();audio_validation=validate_audio(native)
    audio_manifest=read(native/'native-audio-manifest.json')
    fallbacks=audio_manifest.get('fallbacks',[])
    prepared=prepare(read(ART/'recording-plan.json'),read(OUT/'profiles/manifest.json'),
        OUT/'receipts',load_medium(OUT/'wem/Medium/encoding-manifest.json'),{'fallbacks':fallbacks})
    require_complete_audio(coverage,audio_manifest,prepared)
    decoded_validation=require_current_validation(read(ART/'recording-plan.json'),audio_manifest,load_medium(OUT/'wem/Medium/encoding-manifest.json'))
    plan=read(ART/'recording-plan.json')
    encoded=encoded_variations(plan,audio_manifest,sha(ART/'recording-plan.json'),sha(native/'native-audio-manifest.json'))
    encoded_path=OUT/'encoded-variations.json';write(encoded_path,encoded)
    comparison=comparison_summary(read(OUT/'encoding-comparison.json'),sha(ART/'recording-plan.json'),normalized_receipts(plan))
    stats=audio_statistics(coverage,audio_manifest)
    from spend_report import generate as spend_evidence
    spending=spend_evidence()
    if spending['credit_receipt_conflicts']:raise ValueError('Provider credit receipts conflict; reconcile before reporting')
    register=export_register()
    register_manifest=register.with_suffix('.manifest.json');register_proof=read(register_manifest)
    if register_proof['plan_sha256']!=sha(ART/'recording-plan.json'):raise ValueError('Voice register is stale')
    stage=(OUT.resolve()/'package')
    if stage.is_symlink() or stage.is_junction():raise ValueError('Package stage is a link')
    stage.mkdir(exist_ok=True)
    for p in stage.iterdir():
        if p.is_symlink() or p.is_junction() or not p.is_file():raise ValueError('Package member is not an ordinary file')
        if p.name not in {'Berber_future_kingdom.sga','garrison.json','COVERAGE.json','EVIDENCE.json','VOICE_GAPS.md','INSTALL_AND_TEST.txt','REBUILD_060.md','HISTORICAL_REFERENCES.md','voice-script.csv','voice-script.manifest.json','ENCODED_VARIATIONS.json'}:
            raise ValueError('Unexpected existing package member')
    archive=stage/'Berber_future_kingdom.sga';shutil.copyfile(candidate,archive)
    manifest=read(BASE.parent/'garrison.json')
    manifest['members'][0]['sha256']=sha(archive)
    manifest['details'].update(version='0.6.0',updated='2026-10-16',
        summary='26 private unit voice characters; native companion required',
        description='Native unit speech expansion built on verified 0.5.1. Authored Arabic fallback; see VOICE_GAPS.md. Native gameplay acceptance pending.',
        changelog='Speech profiles, paired native bindings, supported chronology and variations. 0.5.1 art and gameplay preserved.')
    write(stage/'garrison.json',manifest);write(stage/'COVERAGE.json',coverage)
    validate_export(register_proof,register)
    shutil.copyfile(register,stage/'voice-script.csv')
    shutil.copyfile(register_manifest,stage/'voice-script.manifest.json')
    if sha(stage/'voice-script.csv')!=register_proof['csv_sha256'] or read(stage/'voice-script.manifest.json')!=register_proof:raise ValueError('Packaged register/proof changed')
    budget=read(OUT/'budget.json')
    evidence={'build_package':'validated composition and audio manifest; final ZIP checks recorded separately',
        'native_installation':'pending','audible_gameplay':'pending','language_native_speaker_review':'pending',
        'base_sha256':BASE_SHA,'sga_sha256':sha(archive),'audio_validation':audio_validation,'decoded_media_validation':decoded_validation,
        'recording_statistics':stats,'accepted_request_records':stats['accepted_request_records'],'documented_fallbacks':fallbacks,
        'chronology_gaps':coverage.get('chronology_gaps',[]),
        'distinct_variation_complete':bool(coverage.get('distinct_variation_complete',False) and encoded['encoded_variation_complete']),
        'encoded_variations':{'report':'ENCODED_VARIATIONS.json','sha256':sha(encoded_path),
            'plan_sha256':encoded['plan_sha256'],'audio_manifest_sha256':encoded['audio_manifest_sha256'],
            'encoded_variation_complete':encoded['encoded_variation_complete'],'contexts_with_shortfalls':encoded['contexts_with_shortfalls'],
            'missing_distinct_takes':encoded['missing_distinct_takes']},
        'contexts_with_distinct_take_shortfalls':[r for r in coverage.get('contexts',[]) if r.get('distinct_take_shortfall',0)],
        'voice_script_register':register_proof,'compression_comparison':comparison,'credit_usage':{k:v for k,v in spending.items() if k!='provider_receipts'},
        'conservative_reserved_usd':round(sum(r['reserved_usd'] for r in budget['reservations'].values()),6),
        'spending_cap_usd':budget['cap_usd'],'account_invoice_usage':'not available through this key',
        'composition':composition}
    write(stage/'EVIDENCE.json',evidence)
    for folder in (stage,native):
        shutil.copyfile(encoded_path,folder/'ENCODED_VARIATIONS.json')
        shutil.copyfile(ART/'VOICE_GAPS.md',folder/'VOICE_GAPS.md')
        (folder/'INSTALL_AND_TEST.txt').write_text(INSTALL,encoding='utf8')
        (folder/'REBUILD_060.md').write_text(REBUILD,encoding='utf8')
        shutil.copyfile(ROOT/'research/berber060/history.md',folder/'HISTORICAL_REFERENCES.md')
    for folder in (stage,native):
        with (folder/'VOICE_GAPS.md').open('a',encoding='utf8') as stream:stream.write(render_delivery_gaps(coverage,audio_manifest,encoded))
    validate_export(register_proof,register)
    if sha(ART/'recording-plan.json')!=encoded['plan_sha256'] or sha(native/'native-audio-manifest.json')!=encoded['audio_manifest_sha256']:
        raise ValueError('Encoded variation proof sources changed before ZIP')
    main=zip_tree(stage,OUT/'berber_future_kingdom-0.6.0.zip')
    audio=zip_tree(native,OUT/'berber_native_audio-0.6.0.zip')
    if main['members']['Berber_future_kingdom.sga']!=composition['archive_sha256']:
        raise ValueError('Packaged SGA differs')
    report={'status':'passed','version':'0.6.0','garrison':main,'native_audio':audio,
        'sga_sha256':sha(archive),'audio_installed_logical_bytes':sum(r['bytes'] for r in audio_manifest['files']),
        'native_installation':'pending','audible_gameplay':'pending','cleanup':'pending'}
    write(OUT/'release-validation.json',report)
    print('DELIVERY_VERIFIED',main['sha256'],audio['sha256']);return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['build'])
    parser.parse_args();build()
