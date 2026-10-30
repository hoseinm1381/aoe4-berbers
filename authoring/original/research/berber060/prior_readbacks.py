"""Compact, verified reproduction proof before superseding a 0.6.0 composition."""
import hashlib,json,zipfile
from pathlib import Path,PurePosixPath
from common import OUT, BASE, BASE_SHA, ARCH, read, write, sha,run
from cleanup import safe,tree

SCAR='scar/units/tuareg_voice_profile.scar'

def _files(root,folder):
    return {Path(r['path']).relative_to(folder.relative_to(root)).as_posix():r['sha256'] for r in tree(root,folder)}

def _keep(path,raw):
    """Resume a partial compact capture only when already written bytes agree."""
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('Prior-composition compact snapshot changed: '+str(path))
    else:path.write_bytes(raw)

def _inventory_names(inventory):
    if not inventory.get('archive',{}).get('verification',{}).get('verified'):
        raise ValueError('Archive inventory CRC/SHA1 verification not passed')
    names=[]
    for member in inventory['members']:
        name=member['path'];path=PurePosixPath(name)
        if '\\' in name or ':' in name or path.is_absolute() or '..' in path.parts or path.as_posix()!=name:
            raise ValueError('Unsafe prior archive member name')
        names.append(name)
    if len(names)!=len(set(names)):raise ValueError('Duplicate prior archive member names')
    return set(names)

def _sidecar_zip(path,readback,extras):
    if not path.exists():
        with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for name in sorted(extras):archive.write(readback/name,name)
    _validate_sidecars(path,extras)

def _validate_sidecars(path,extras):
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or set(names)!=set(extras) or archive.testzip():
            raise ValueError('Prior unpack sidecar evidence member set/CRC differs')
        for name,expected in extras.items():
            with archive.open(name) as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
            if actual!=expected:raise ValueError('Prior unpack sidecar evidence changed')

def _validate_proof(root,folder,require_readback=True):
    root=Path(root).resolve();folder=safe(root,folder)
    proof_path=safe(root,folder/'proof.json');proof=read(proof_path)
    digest=proof['archive_sha256']
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest) or folder!=root/'prior-compositions'/digest:
        raise ValueError('Prior-composition proof identity/path differs')
    readback=safe(root,root/'integration'/('candidate-readback-'+digest[:12]))
    if Path(proof['readback'])!=readback:raise ValueError('Prior-composition readback namespace differs')
    allowed={'proof.json','composition-report.json','old-tuareg_voice_profile.scar','member-sha256.json',
        'readback-file-sha256.json','archive-inventory.json','unpack-sidecar-evidence.zip',
        'base-readback-file-sha256.json','base-archive-inventory.json','base-unpack-sidecar-evidence.zip'}
    if set(_files(root,folder))!=allowed:raise ValueError('Unexpected compact proof file set')
    for name,key in [('composition-report.json','report_sha256'),('member-sha256.json','member_map_sha256'),('old-tuareg_voice_profile.scar','old_scar_sha256'),
        ('readback-file-sha256.json','readback_file_map_sha256'),('archive-inventory.json','archive_inventory_sha256'),
        ('unpack-sidecar-evidence.zip','sidecar_evidence_sha256'),
        ('base-readback-file-sha256.json','base_readback_file_map_sha256'),('base-archive-inventory.json','base_archive_inventory_sha256'),
        ('base-unpack-sidecar-evidence.zip','base_sidecar_evidence_sha256')]:
        if sha(safe(root,folder/name))!=proof[key]:raise ValueError('Prior-composition compact file changed: '+name)
    report=read(folder/'composition-report.json')
    if report['status']!='passed' or report['archive_sha256']!=digest or report['base_sha256']!=BASE_SHA:
        raise ValueError('Prior-composition report not the qualified source')
    base=proof['base']
    if Path(base['path']).resolve()!=BASE.resolve() or base['sha256']!=BASE_SHA or sha(BASE)!=BASE_SHA:
        raise ValueError('Retained 0.5.1 rebuild archive changed')
    if Path(proof['archiver']['path']).resolve()!=ARCH.resolve() or sha(ARCH)!=proof['archiver']['sha256']:
        raise ValueError('Retained archive rebuild tool changed')
    baseline_path=safe(root,root/'baseline-member-sha256.json')
    if sha(baseline_path)!=proof['baseline_member_map_sha256']:raise ValueError('Retained baseline hash map changed')
    baseline=read(baseline_path);payloads=proof['payloads']
    if len(payloads)!=85 or sum(p['member'].startswith('attrib/') for p in payloads)!=84 or {p['member'] for p in payloads if not p['member'].startswith('attrib/')}!={SCAR}:
        raise ValueError('Prior-composition payload slice differs')
    old_report_payloads={p['member']:p['sha256'] for p in report['payloads']}
    if len(old_report_payloads)!=85 or old_report_payloads!={p['member']:p['sha256'] for p in payloads} or set(report['changed_members'])!=set(old_report_payloads):
        raise ValueError('Prior-composition original payload claims differ')
    for payload in payloads:
        path=Path(payload['file'])
        if payload['member']==SCAR:
            if path!=folder/'old-tuareg_voice_profile.scar':raise ValueError('Old metadata must use the compact retained copy')
            safe(root,path)
        else:
            # Authoritative binding inputs remain release-owned and undeleted.
            safe(root,path)
        if sha(path)!=payload['sha256']:raise ValueError('Retained prior payload changed: '+payload['member'])
    expected={**baseline,**old_report_payloads};members=read(folder/'member-sha256.json')
    if members!=expected:raise ValueError('Prior-composition expected member map differs')
    if _inventory_names(read(folder/'archive-inventory.json'))!=set(expected):raise ValueError('Prior native archive inventory differs from expected members')
    allfiles=read(folder/'readback-file-sha256.json')
    if {name:allfiles.get(name) for name in expected}!=expected:raise ValueError('Prior native readback member hashes differ')
    extras={name:digest for name,digest in allfiles.items() if name not in expected}
    _validate_sidecars(folder/'unpack-sidecar-evidence.zip',extras)
    if _inventory_names(read(folder/'base-archive-inventory.json'))!=set(baseline):raise ValueError('Base archive inventory differs from retained baseline')
    basefiles=read(folder/'base-readback-file-sha256.json')
    if {name:basefiles.get(name) for name in baseline}!=baseline:raise ValueError('Base native readback hashes differ')
    _validate_sidecars(folder/'base-unpack-sidecar-evidence.zip',{name:digest for name,digest in basefiles.items() if name not in baseline})
    if require_readback and _files(root,readback)!=allfiles:raise ValueError('Superseded readback has extra, missing, or modified members')
    return proof

def capture_existing(root=None):
    """Explicit compose hook only. Never removes archives/readbacks or author inputs."""
    root=Path(root or OUT).resolve();report_path=safe(root,root/'composition-report.json')
    if not report_path.exists():return None
    report=read(report_path)
    if report['status']!='passed' or report['base_sha256']!=BASE_SHA or sha(BASE)!=BASE_SHA:
        raise ValueError('Existing composition/base not verified before superseding')
    digest=report['archive_sha256'];archive=safe(root,Path(report['archive']).resolve())
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid composition digest')
    folder=safe(root,root/'prior-compositions'/digest)
    if (folder/'proof.json').exists():
        # A previous capture already proved old archive bytes. Later compose may
        # have overwritten the shared archive/SCAR before failing to publish its report.
        prior=_validate_proof(root,folder)
        if sha(report_path)!=prior['report_sha256']:raise ValueError('Existing composition report changed after capture')
        return prior
    if sha(archive)!=digest:raise ValueError('Existing composition archive changed before superseding')
    readback=safe(root,root/'integration'/('candidate-readback-'+digest[:12]))
    if not readback.exists():return None  # Already cleaned: no full readback to admit.
    baseline_path=safe(root,root/'baseline-member-sha256.json');baseline=read(baseline_path)
    payloads=report['payloads'];mapping={p['member']:p['sha256'] for p in payloads}
    if len(payloads)!=85 or len(mapping)!=85 or sum(p.startswith('attrib/') for p in mapping)!=84 or set(mapping)-{p for p in mapping if p.startswith('attrib/')}!={SCAR}:
        raise ValueError('Existing composition is not exact 84 binding + metadata slice')
    if set(report['changed_members'])!=set(mapping):raise ValueError('Existing composition changed-member slice differs')
    expected={**baseline,**mapping}
    inventory=json.loads(run(ARCH,'list',archive,'--verify'))
    if _inventory_names(inventory)!=set(expected):raise ValueError('Existing native archive inventory differs from baseline + old payloads')
    allfiles=_files(root,readback)
    if {name:allfiles.get(name) for name in expected}!=expected:raise ValueError('Existing composition native readback differs from baseline + old payloads')
    extras={name:digest for name,digest in allfiles.items() if name not in expected}
    base_inventory=json.loads(run(ARCH,'list',BASE,'--verify'))
    if _inventory_names(base_inventory)!=set(baseline):raise ValueError('Base native archive inventory differs from baseline map')
    base_readback=safe(root,root/'integration/base-readback');basefiles=_files(root,base_readback)
    if {name:basefiles.get(name) for name in baseline}!=baseline:raise ValueError('Base native readback differs from baseline')
    baseextras={name:digest for name,digest in basefiles.items() if name not in baseline}
    # Verify every original old input BEFORE taking any compact snapshot.
    for payload in payloads:
        if payload['member']!=SCAR:safe(root,Path(payload['file']).resolve())
        if sha(payload['file'])!=payload['sha256']:raise ValueError('Existing payload changed before compact capture')
    folder.mkdir(parents=True,exist_ok=True)
    partial=set(_files(root,folder))
    if not partial<={'composition-report.json','old-tuareg_voice_profile.scar','member-sha256.json',
        'readback-file-sha256.json','archive-inventory.json','unpack-sidecar-evidence.zip',
        'base-readback-file-sha256.json','base-archive-inventory.json','base-unpack-sidecar-evidence.zip'}:
        raise ValueError('Unexpected partial compact capture files')
    old_scar=next(p for p in payloads if p['member']==SCAR)
    _keep(folder/'composition-report.json',report_path.read_bytes())
    _keep(folder/'old-tuareg_voice_profile.scar',Path(old_scar['file']).read_bytes())
    write(folder/'member-sha256.json',expected)
    write(folder/'readback-file-sha256.json',allfiles)
    write(folder/'archive-inventory.json',inventory)
    _sidecar_zip(folder/'unpack-sidecar-evidence.zip',readback,extras)
    write(folder/'base-readback-file-sha256.json',basefiles)
    write(folder/'base-archive-inventory.json',base_inventory)
    _sidecar_zip(folder/'base-unpack-sidecar-evidence.zip',base_readback,baseextras)
    retained=[{'member':p['member'],'file':str(folder/'old-tuareg_voice_profile.scar') if p['member']==SCAR else str(Path(p['file']).resolve()),'sha256':p['sha256']} for p in payloads]
    proof={'schema':'berber060-prior-composition/v1','archive_sha256':digest,'readback':str(readback),
        'report_sha256':sha(folder/'composition-report.json'),'member_map_sha256':sha(folder/'member-sha256.json'),
        'old_scar_sha256':sha(folder/'old-tuareg_voice_profile.scar'),
        'readback_file_map_sha256':sha(folder/'readback-file-sha256.json'),
        'archive_inventory_sha256':sha(folder/'archive-inventory.json'),
        'sidecar_evidence_sha256':sha(folder/'unpack-sidecar-evidence.zip'),
        'native_archive_members':len(expected),'preserved_nonmember_files':len(extras),
        'base_readback_file_map_sha256':sha(folder/'base-readback-file-sha256.json'),
        'base_archive_inventory_sha256':sha(folder/'base-archive-inventory.json'),
        'base_sidecar_evidence_sha256':sha(folder/'base-unpack-sidecar-evidence.zip'),
        'preserved_base_nonmember_files':len(baseextras),
        'baseline_member_map_sha256':sha(baseline_path),'base':{'path':str(BASE.resolve()),'sha256':BASE_SHA},
        'archiver':{'path':str(ARCH.resolve()),'sha256':sha(ARCH)},
        'payloads':retained,'recipe':'Replay 84 retained attrib payloads over verified 0.5.1 BASE using release.compose set-members; then replay saved old SCAR, not metadata_payload. Verify native archive member map. Preserve/restore unpack nonmember helper evidence from unpack-sidecar-evidence.zip and verify the full readback-file map; never assume helpers are archive members.',
        'scope':'Compact source/reproduction proof; old full archive is not retained by this operation'}
    write(folder/'proof.json',proof)
    return _validate_proof(root,folder)

def validated_prior_readbacks(root,current_archive_sha256):
    root=Path(root).resolve();parent=safe(root,root/'prior-compositions')
    if not parent.exists():return []
    admitted=[];selected=set()
    for folder in sorted(parent.iterdir()):
        safe(root,folder)
        if not folder.is_dir() or not (folder/'proof.json').is_file():raise ValueError('Unfinished/unrecognized prior-composition proof')
        proof=_validate_proof(root,folder,require_readback=False)
        if proof['archive_sha256']==current_archive_sha256:continue
        readback=Path(proof['readback'])
        if readback.exists():
            _validate_proof(root,folder,require_readback=True)
            if readback in selected:raise ValueError('Conflicting compact proofs share a readback namespace')
            selected.add(readback)
            inputs=[folder/name for name in ('proof.json','composition-report.json','old-tuareg_voice_profile.scar','member-sha256.json',
                'readback-file-sha256.json','archive-inventory.json','unpack-sidecar-evidence.zip',
                'base-readback-file-sha256.json','base-archive-inventory.json','base-unpack-sidecar-evidence.zip')]
            inputs.extend([BASE,ARCH,root/'baseline-member-sha256.json'])
            inputs.extend(Path(p['file']) for p in proof['payloads'])
            admitted.append({'target':readback,'proof':folder/'proof.json','archive_sha256':proof['archive_sha256'],
                'protected_rebuild_inputs':list(dict.fromkeys(inputs))})
    return admitted

def validated_base_readback(root):
    """Admit the full BASE unpack only when native members AND helpers are proved."""
    root=Path(root).resolve();parent=safe(root,root/'prior-compositions');target=safe(root,root/'integration/base-readback')
    if not parent.exists() or not target.exists():return None
    actual=_files(root,target)
    for folder in sorted(parent.iterdir()):
        _validate_proof(root,folder,require_readback=False)
        if read(folder/'base-readback-file-sha256.json')==actual:
            return {'target':target,'proof':folder/'proof.json'}
    raise ValueError('Base unpack differs from qualified native/helper evidence')
