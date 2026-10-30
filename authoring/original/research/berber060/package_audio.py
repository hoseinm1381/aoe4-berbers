"""Fail-closed offline native companion packaging. Never installs or calls APIs.

Fallback input: {"fallbacks":[{"job_id":...,"replacement_job_id":...,"reason":...}]}.
Only current accepted recordings with identical family/event/age/delivery may replace
another take. No fallback chains, implicit substitutions or stale request keys.
"""
import argparse, re, shutil, tempfile
from pathlib import Path
from common import OUT, ART, read, write, sha
from profiles import parse_profile
from batch_generation import job_key, single_identity
from encoding import inspect_wem

INSTALLER=Path(__file__).with_name('Install-BerberNativeAudio.ps1')


def relative(value):
    if not isinstance(value,str) or not value or '\\' in value or re.search(r'[:<>"|?*\x00-\x1f]',value):
        raise ValueError('Unsafe native relative path')
    for part in value.split('/'):
        if not part or part in ('.','..') or part[-1] in '. ' or re.match(r'^(CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|CLOCK\$|COM[0-9¹²³]|LPT[0-9¹²³])(?:\.|$)',part,re.I):
            raise ValueError('Unsafe native path component')
    return value


def checked(path,digest,size=None):
    path=Path(path)
    if not path.is_file() or sha(path)!=digest or (size is not None and path.stat().st_size!=size):
        raise ValueError('Missing/corrupt source: '+str(path))
    return path


def prepare(plan,profiles,receipts,encoding,fallbacks=None):
    """Validate all inputs before stage creation; return manifest plus source map."""
    jobs={j['id']:j for j in plan['jobs']}
    if len(jobs)!=len(plan['jobs']):raise ValueError('Duplicate recording job')
    replacements={};fallback_rows=(fallbacks or {}).get('fallbacks',[])
    for row in fallback_rows:
        a,b=row['job_id'],row['replacement_job_id']
        if a in replacements or a==b or a not in jobs or b not in jobs or not row.get('reason','').strip():
            raise ValueError('Invalid documented fallback')
        if any(jobs[a][k]!=jobs[b][k] for k in ('family','event','age','delivery')):
            raise ValueError('Fallback changes family/event/age/delivery')
        replacements[a]=b
    if set(replacements)&set(replacements.values()):raise ValueError('Fallback chains refused')
    assignments={}
    for row in plan['assignments']:
        path=relative(row['path']).lower()
        if path in assignments:raise ValueError('Case-insensitive alias collision: '+path)
        if row['job_id'] not in jobs or row['family']!=jobs[row['job_id']]['family']:
            raise ValueError('Unknown or wrong-family assignment')
        assignments[path]=row
    sources={};files=[];profile_rows=[];expected=set();seen_families=set();seen_identities=set()
    def add(path,source,digest,size,suffix):
        payload='payloads/'+digest+suffix
        sources.setdefault(payload,str(source))
        files.append({'path':path,'payload':payload,'sha256':digest,'bytes':size})
    for p in profiles['families']:
        family=p['family'];race=p['race'];speaker=p['speaker'];identity=p['private_media_identity']
        name=race+'_'+speaker+'.spd'
        if race not in ('malian','abbasid') or not re.fullmatch(r'b\d{2}x+',speaker) or not re.fullmatch(race+r'_'+speaker[:3]+r'x+',identity):
            raise ValueError('Nonprivate profile namespace')
        if family in seen_families or name.lower() in seen_identities:raise ValueError('Duplicate profile family/identity')
        seen_families.add(family);seen_identities.add(name.lower())
        source=checked(p['profile_path'],p['profile_sha256']);rows=parse_profile(source.read_bytes())
        if {r['race']['text'].lower() for r in rows}!={race} or {r['speaker']['text'].lower() for r in rows}!={speaker}:
            raise ValueError('Profile binary identity mismatch')
        references={relative(m['text'].replace('\\','/')).lower() for r in rows for m in r['media']}
        declared={relative(m['path'].replace('\\','/')).lower() for m in p['media']}
        if references!=declared:raise ValueError('Profile manifest references differ from SPD')
        prefix='civ_'+race+'/'+identity+'/'
        if any(not r.startswith(prefix) or not r.endswith('.wem') for r in references):raise ValueError('Profile media outside private namespace')
        if expected&references:raise ValueError('Cross-profile alias collision')
        expected.update(references)
        for path in references:
            if path not in assignments or assignments[path]['family']!=family:raise ValueError('SPD reference missing/wrong-family assignment: '+path)
        profile_rows.append({'family':family,'race':race,'speaker':speaker,'media_identity':identity,'path':name})
        add(name,source,p['profile_sha256'],source.stat().st_size,'.spd')
    if set(assignments)!=expected:raise ValueError('Extra or missing native alias assignment')
    accepted={}
    for jid in sorted({replacements.get(r['job_id'],r['job_id']) for r in assignments.values()}):
        job=jobs[jid];key=job_key(job);receipt_path=Path(receipts)/(key+'.json')
        if not receipt_path.is_file():raise ValueError('Current accepted receipt missing: '+jid)
        r=read(receipt_path)
        if r.get('status')!='accepted_acoustic' or r.get('request_id')!=key or r.get('identity')!=single_identity(job) or r.get('job_id')!=jid or r.get('family')!=job['family']:
            raise ValueError('Receipt is not a current accepted job: '+jid)
        if r.get('quality',{}).get('clipped_samples',0) or r.get('quality',{}).get('duration_seconds',0)>8:
            raise ValueError('Receipt has rejected acoustic quality')
        native=checked(r['native_path'],r['native_wav']['sha256'])
        e=encoding.get(key)
        if not e or Path(e['source']).resolve()!=native.resolve() or e['source_sha256']!=r['native_wav']['sha256']:
            raise ValueError('Medium encoding missing or stale: '+jid)
        wem=checked(e['wem'],e['sha256'],e['bytes']);inspection=inspect_wem(wem)
        if inspection['sha256']!=e['sha256'] or inspection['bytes']!=e['bytes']:raise ValueError('WEM inspection differs')
        accepted[jid]=(wem,e)
    for path,row in sorted(assignments.items()):
        wem,e=accepted[replacements.get(row['job_id'],row['job_id'])]
        add(path,wem,e['sha256'],e['bytes'],'.wem')
    return {'schema':'berber-native-audio/v1','profiles':profile_rows,'files':sorted(files,key=lambda r:r['path']),
        'fallbacks':fallback_rows,'native_playback':'pending','coverage':{'native_aliases':len(expected),'accepted_recordings':len(accepted)},'_sources':sources}


def validate(destination):
    """Rehash each deduplicated blob, then prove all SPD references are covered."""
    root=Path(destination).resolve();manifest=read(root/'native-audio-manifest.json')
    if manifest.get('schema')!='berber-native-audio/v1':raise ValueError('Unexpected package schema')
    paths={};payloads={}
    for row in manifest['files']:
        path=relative(row['path']).lower();payload=relative(row['payload'])
        if path in paths:raise ValueError('Package destination collision')
        physical=root/payload
        if physical.resolve()!=physical or any(p.is_symlink() or p.is_junction() for p in [physical,*physical.parents] if p!=root and root in p.parents):
            raise ValueError('Package reparse point refused')
        signature=(row['sha256'],row['bytes'])
        if payload in payloads and payloads[payload]!=signature:raise ValueError('Conflicting payload metadata')
        if payload not in payloads:checked(physical,*signature)
        payloads[payload]=signature;paths[path]=row
    expected=set();families=set();identities=set()
    for p in manifest['profiles']:
        name=relative(p['path']);race=p['race'];speaker=p['speaker'];identity=p['media_identity']
        if p['family'] in families or name.lower() in identities:raise ValueError('Duplicate package profile')
        families.add(p['family']);identities.add(name.lower())
        if race not in ('malian','abbasid') or not re.fullmatch(r'b\d{2}x+',speaker) or name!=race+'_'+speaker+'.spd' or not re.fullmatch(race+r'_'+speaker[:3]+r'x+',identity):raise ValueError('Invalid private package identity')
        if name.lower() not in paths:raise ValueError('Packaged profile missing')
        rows=parse_profile((root/paths[name.lower()]['payload']).read_bytes())
        if any(r['race']['text'].lower()!=race or r['speaker']['text'].lower()!=speaker for r in rows):raise ValueError('Packaged SPD identity mismatch')
        refs={relative(m['text'].replace('\\','/')).lower() for r in rows for m in r['media']}
        if any(not r.startswith('civ_'+race+'/'+identity+'/') or not r.endswith('.wem') for r in refs):raise ValueError('Packaged SPD namespace mismatch')
        if expected&refs:raise ValueError('Packaged cross-family collision')
        expected.update(refs);expected.add(name.lower())
    if set(paths)!=expected:raise ValueError('Package inventory differs from all SPD references')
    return {'status':'passed','files':len(paths),'payloads':len(payloads),'profiles':len(families),'native_playback':'pending'}


def stage(prepared,destination):
    # Resolve the documented output junction once; emit a physically portable package.
    destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Destination already exists; preserve/review previous package')
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='native-package-',dir=destination.parent))
    try:
        for payload,source in prepared['_sources'].items():
            target=temporary/relative(payload);target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source,target)
        shutil.copyfile(INSTALLER,temporary/INSTALLER.name)
        write(temporary/'native-audio-manifest.json',{k:v for k,v in prepared.items() if k!='_sources'})
        validate(temporary)
        temporary.rename(destination)
    except Exception:
        # No recursive deletion: leave a bounded failed stage for diagnosis.
        raise
    return destination


def load_medium(path):
    path=Path(path).resolve()
    if path.name!='encoding-manifest.json' or path.parent.name!='Medium':
        raise ValueError('A Wwise Medium encoding manifest is required')
    data=read(path)
    for key,row in data.items():
        wem=Path(row['wem']).resolve()
        if wem.parent!=(path.parent/'Windows') or wem.name!=key+'.wem':
            raise ValueError('Encoding row outside Medium/key namespace')
    return data


def build(plan=ART/'recording-plan.json',profiles=OUT/'profiles/manifest.json',receipts=OUT/'receipts',
          encoding=OUT/'wem/Medium/encoding-manifest.json',fallbacks=None,destination=OUT/'native-package'):
    profile_data=read(profiles)
    if len(profile_data['families'])!=26:raise ValueError('Exactly 26 private profiles required')
    result=prepare(read(plan),profile_data,receipts,load_medium(encoding),read(fallbacks) if fallbacks else None)
    path=stage(result,destination)
    report=validate(path);report['physical_package_root']=str(path)
    write(OUT/'native-package-validation.json',report)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,default=ART/'recording-plan.json')
    parser.add_argument('--profiles',type=Path,default=OUT/'profiles/manifest.json')
    parser.add_argument('--receipts',type=Path,default=OUT/'receipts')
    parser.add_argument('--encoding',type=Path,default=OUT/'wem/Medium/encoding-manifest.json')
    parser.add_argument('--fallbacks',type=Path)
    parser.add_argument('--destination',type=Path,default=OUT/'native-package')
    print(build(**vars(parser.parse_args())))
