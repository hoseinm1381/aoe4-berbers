"""Compose native speech payloads over immutable 0.5.1; never rebuild old art."""
import argparse,copy,hashlib,json,shutil,time,uuid
from pathlib import Path,PurePosixPath
from zipfile import ZipFile,ZIP_DEFLATED
from common import ROOT,OUT,ART,BASE,BASE_SHA,GUID,ARCH,read,write,sha,run

def safe_member(name):
    p=PurePosixPath(name)
    if '\\' in name or ':' in name or p.is_absolute() or '..' in p.parts or p.as_posix()!=name:raise ValueError('Unsafe archive member')
    return name

def member_hashes(archive,folder):
    # Previous-release cleanup retains exact restore sources for duplicate cache files.
    import sys
    parent=str(ROOT/'research')
    if parent not in sys.path:sys.path.insert(0,parent)
    from restore_cleanup_cache import restore
    restore(folder)
    inventory=json.loads(run(ARCH,'list',archive,'--verify'))
    if not inventory['archive']['verification']['verified']:raise ValueError('Archive CRC/SHA1 verification failed')
    if inventory['archive']['name'].replace('-','').lower()!=GUID.replace('-',''):raise ValueError('Project identity mismatch')
    folder=Path(folder)
    if not folder.exists():run(ARCH,'unpack',archive,'--output',folder)
    result={safe_member(r['path']):sha(folder/r['path']) for r in inventory['members']}
    return inventory,result

def recording_counts(plan,receipts=None):
    from batch_generation import job_key,single_identity
    jobs=[j for j in plan['jobs'] if j['family']=='tuareg'];accepted=[]
    for job in jobs:
        key=job_key(job);path=Path(receipts or OUT/'receipts')/(key+'.json')
        try:
            row=read(path)
            if row.get('status')!='accepted_acoustic' or row.get('request_id')!=key or row.get('job_id')!=job['id'] or row.get('identity')!=single_identity(job):continue
            if row.get('quality',{}).get('clipped_samples',0) or not 0<row.get('quality',{}).get('duration_seconds',0)<=8:continue
            if sha(row['source'])!=row['source_sha256'] or sha(row['native_path'])!=row['native_wav']['sha256']:continue
            accepted.append(row)
        except (OSError,ValueError,KeyError,TypeError):continue  # Changing/missing source is not final acceptance.
    return {'planned_request_records':len(jobs),'accepted_request_records':len(accepted),
        'unique_source_waveforms':len({r['source_sha256'] for r in accepted}),
        'unique_native_waveforms':len({r['native_wav']['sha256'] for r in accepted})}


def metadata_payload(plan):
    counts=recording_counts(plan)
    text='''-- Native speech expectations only. Engine owns all speech timing.
BerberTuaregVoice_Profile = {
    revision = "berber060-native-v1",
    speaker = "b03xx",
    native_profile = "audio:malian_b03xx.spd",
    -- Byte-distinct accepted source snapshot; not paid HTTP calls or release acceptance.
    source_recordings = %d,
    planned_request_records = %d,
    accepted_request_records_snapshot = %d,
    unique_native_waveforms_snapshot = %d,
    acceptance_snapshot_only = true,
    media_slots = 1278,
    temporary_effort_slots = 0,
    age_reuse = { [1] = 1, [2] = 2, [3] = 3, [4] = 4 },
    all_unit_families = 26,
}
local BerberTuaregVoice_logged = false
function BerberTuaregVoice_LogSetup()
    if BerberTuaregVoice_logged then return end
    BerberTuaregVoice_logged = true
    print("BERBER_NATIVE_VOICE revision=060-v1 families=26 routing=native sidecar_required=true playback=unverified")
end
'''%(counts['unique_source_waveforms'],counts['planned_request_records'],counts['accepted_request_records'],counts['unique_native_waveforms'])
    profile=next(p for p in read(OUT/'profiles/manifest.json')['families'] if p['family']=='tuareg')
    if (profile['speaker'],profile['profile_resource'],profile['unique_media'])!=('b03xx','malian_b03xx.spd',1278):raise ValueError('Tuareg metadata/profile mismatch')
    path=ART/'metadata/tuareg_voice_profile.scar';path.parent.mkdir(exist_ok=True);path.write_text(text,encoding='utf8')
    return {'member':'scar/units/tuareg_voice_profile.scar','file':str(path),'sha256':sha(path),'purpose':'expectation metadata; no engine speech callbacks or gameplay changes'}

def compose():
    if sha(BASE)!=BASE_SHA:raise ValueError('Protected 0.5.1 archive changed')
    # Preserve the old metadata/count snapshot before metadata_payload mutates it.
    from prior_readbacks import capture_existing
    capture_existing()
    manifest=read(OUT/'bindings/payload-manifest.json')
    if manifest['status']!='passed' or manifest['base_sha256']!=BASE_SHA:raise ValueError('Unverified native binding input')
    if sha(OUT/'profiles/manifest.json')!=manifest['profile_manifest_sha256']:raise ValueError('Profile/binding manifest changed')
    plan=read(ART/'recording-plan.json');payloads=list(manifest['payloads'])+[metadata_payload(plan)]
    work=OUT/'integration';work.mkdir(exist_ok=True)
    inventory,baseline=member_hashes(BASE,work/'base-readback')
    write(OUT/'baseline-member-sha256.json',baseline)
    expected={safe_member(p['member']):p['sha256'] for p in payloads}
    if len(expected)!=len(payloads):raise ValueError('Conflicting payload members')
    for p in payloads:
        if sha(p['file'])!=p['sha256']:raise ValueError('Payload input changed')
    canonical=OUT/'candidate.sga'
    previous_sha=sha(canonical) if canonical.exists() else None
    token=uuid.uuid4().hex
    intermediates=[]
    current=BASE
    for alias,prefix in [('attrib','attrib/'),('data','scar/')]:
        selected=[p for p in payloads if p['member'].startswith(prefix)]
        listing=work/f'compose-{token}-{alias}-members.txt'
        listing.write_text(''.join(p['member']+'='+p['file']+'\n' for p in selected),encoding='utf8')
        target=work/f'compose-{token}-{alias}.sga'
        if target.exists():raise FileExistsError('Fresh composition output already exists')
        run(ARCH,'set-members',current,listing,target,'--alias',alias)
        current=target
        if alias=='attrib':
            verified=json.loads(run(ARCH,'list',target,'--verify'))
            if not verified['archive']['verification']['verified']:raise ValueError('Intermediate archive verification failed')
            intermediates.append((target,sha(target)))
    candidate_inventory,candidate=member_hashes(current,work/('candidate-readback-'+sha(current)[:12]))
    if set(candidate)!=set(baseline)|set(expected):raise ValueError('Unexpected candidate archive member set')
    changed={p for p in candidate if candidate[p]!=baseline.get(p)}
    if changed!=set(expected):raise ValueError('Whole archive changed outside exact speech payloads')
    for p,h in expected.items():
        if candidate[p]!=h:raise ValueError('Payload readback differs')
    if any(p.startswith('art/') and candidate[p]!=h for p,h in baseline.items()):raise ValueError('0.5.1 art changed')
    final_sha=sha(current)
    if (sha(canonical) if canonical.exists() else None)!=previous_sha:raise ValueError('Canonical candidate changed during composition')
    for attempt in range(8):
        try:
            current.replace(canonical)
            break
        except PermissionError:
            if attempt==7:raise
            time.sleep(min(.05*2**attempt,1.6))
    if sha(canonical)!=final_sha:raise ValueError('Promoted candidate hash differs')
    result={'status':'passed','version':'0.6.0','base':str(BASE),'base_sha256':BASE_SHA,
        'archive':str(canonical),'archive_sha256':final_sha,'base_members':len(baseline),
        'candidate_members':len(candidate),'changed_members':sorted(changed),'payloads':payloads,
        'unchanged_members_sha256_identical':True,'all_051_art_bytes_preserved':True,
        'native_rgds_semantic_undo':'passed for all 84 owners; admitted speech-only changes',
        'archive_crc_sha1':'passed','proof_layer':'native typed composition; no new Content Editor cook or audible acceptance implied',
        'native_playback':'pending'}
    write(OUT/'composition-report.json',result)
    # Only this run's verified intermediate is disposable after publication.
    for path,expected_hash in intermediates:
        if path.parent!=work or path.is_symlink() or path.resolve().parent!=work.resolve() or sha(path)!=expected_hash:
            raise ValueError('Composition intermediate changed; retained for investigation')
        path.unlink()
    print('060_COMPOSED',result['archive_sha256'],'speech payloads',len(changed));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['compose']);a=p.parse_args();compose()
