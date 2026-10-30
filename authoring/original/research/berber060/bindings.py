"""Speech-only native RGD composition; does not cook, install or prove playback."""
from __future__ import annotations
import argparse, copy, hashlib, sys
from pathlib import Path
from common import ROOT, OUT, BASE, BASE_SHA, EXT, read, write, sha
sys.path.insert(0, str(EXT))
from garrison_shared import rgd

SPEAKERS = ('/speech_ext/speaker_code', '/squad_speech_ext/squad_speaker_code')
RACE = '/squad_speech_ext/squad_speech_parameters/squad_race_code'
AGE = '/squad_speech_ext/age_mapping/'

def semantic(nodes):
    return [(n.key,n.hash,n.kind,semantic(n.value) if isinstance(n.value,list) else n.value) for n in nodes]

def encode(doc):
    keys = {h:k for h,k in doc.keys}
    for _, n in rgd.flatten(doc.nodes):
        if n.key is not None: keys[n.hash] = n.key
    doc.keys = list(keys.items())
    payload = rgd.write(doc)
    if semantic(rgd.read(payload).nodes) != semantic(doc.nodes):
        raise ValueError('RGD typed roundtrip changed semantics')
    return payload

def verify_undo(original, candidate, changes):
    restored = copy.deepcopy(candidate)
    lookup = dict(rgd.flatten(restored.nodes))
    for change in changes:
        path = change['field']
        is_age=AGE in path and path.rsplit('/',1)[-1] in ('age_number','age_number[1]','age_number[2]','age_number[3]')
        if not path.endswith(SPEAKERS + (RACE,)) and not is_age:
            raise ValueError('Unadmitted non-speech change')
        node = lookup[path]
        if node.kind != ('Int' if is_age else 'CString') or node.value != change['after']:
            raise ValueError('Changed field/type differs from proof')
        if is_age and (type(change['after']) is not int or change['after'] not in (1,2,3,4)):
            raise ValueError('Invalid native speech age value')
        node.value = change['before']
    if semantic(restored.nodes) != semantic(original.nodes):
        raise ValueError('Non-speech or unrecorded native semantic difference')

def patch(data, speaker, race, age_mapping=None):
    if not speaker or race not in ('malian','abbasid'):
        raise ValueError('Unsupported manifest speaker/race contract')
    original = rgd.read(data)
    doc = copy.deepcopy(original)
    changes = []
    for path, node in rgd.flatten(doc.nodes):
        value = None
        if path.endswith(SPEAKERS): value = speaker
        # Explicit race is needed where private donor race differs from Malian
        # inheritance. This field already exists in native SBPS; invent none.
        elif path.endswith(RACE) and race == 'abbasid': value = race
        if value is not None and value != node.value:
            if node.kind != 'CString': raise ValueError('Native speech field type changed')
            changes.append(dict(field=path,kind=node.kind,before=node.value,after=value))
            node.value = value
    if not any(c['field'].endswith(SPEAKERS) for c in changes):
        raise ValueError('Owner has no changeable native speaker field')
    if age_mapping is not None:
        if len(age_mapping)!=4 or any(type(a)is not int or a not in (1,2,3,4) for a in age_mapping):raise ValueError('Invalid age map')
        groups={}
        for path,node in rgd.flatten(doc.nodes):
            if AGE in path:groups.setdefault(path.rsplit('/',1)[0],[]).append((path,node))
        if not groups:raise ValueError('Native owner has no speech age map')
        for group,entries in groups.items():
            if len(entries)!=4 or any(n.kind!='Int' for _,n in entries):raise ValueError('Unexpected native speech age table')
            for (path,node),value in zip(entries,age_mapping):
                if node.value!=value:
                    changes.append({'field':path,'kind':'Int','before':node.value,'after':value});node.value=value
    payload = encode(doc)
    verify_undo(original, rgd.read(payload), changes)
    return payload, changes

def validate_base(base=BASE):
    if sha(base) != BASE_SHA: raise ValueError('Wrong authoritative 0.5.1 base')

def build(manifest_path, audit_path=OUT/'binding-audit.json', destination=OUT/'bindings', base=BASE):
    validate_base(base)
    manifest = read(manifest_path)
    profiles = {r['family']:r for r in manifest['families']}
    audit = read(audit_path)
    if audit['base_sha256'] != BASE_SHA: raise ValueError('Wrong audit base')
    if len(profiles) != 26 or len(manifest['families']) != 26:
        raise ValueError('Exactly 26 distinct profiles required')
    indexed = {r['member']:r for r in audit['rows']}
    selected = {}
    for family in audit['families']:
        profile = profiles[family['family']]
        for member in family['owners']:
            # Official campaign camel-archer is an unselected shared owner.
            # The audit family does not include it, and dormant Malian combat
            # counterpart is excluded by the admitted family owner inventory.
            if member in selected: raise ValueError('Conflicting family owners')
            selected[member] = (family['family'],profile)
    payloads=[]
    for member,(family,profile) in sorted(selected.items()):
        row=indexed[member]; source=Path(row['file'])
        if sha(source) != row['sha256']: raise ValueError('Corrupted audited source: '+member)
        age_mapping=[2,2,3,4] if family in ('masmuda','king') and '/sbps/' in member else None
        payload, changes=patch(source.read_bytes(),profile['speaker'],profile['race'],age_mapping)
        target=Path(destination)/'payloads'/member
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(payload)
        payloads.append(dict(family=family,member=member,file=str(target),sha256=sha(target),
            source=str(source),source_sha256=row['sha256'],source_owner=row.get('owner','0.5.1 mod'),
            changes=changes,semantic_roundtrip='passed',semantic_undo='passed',
            speaker=profile['speaker'],race=profile['race']))
    report=dict(schema='berber060-native-speech-bindings/v1',status='passed',
        base=str(base),base_sha256=BASE_SHA,profile_manifest=str(manifest_path),
        profile_manifest_sha256=sha(manifest_path),payloads=payloads,
        family_count=len(profiles),owner_count=len(payloads),
        fields_policy='Existing typed native speaker/race CStrings; Masmuda and King speech age II corrected to cLow with explicit [2,2,3,4] map; all other semantics preserved',
        proof_layer='native typed RGD composition; no fresh Content Editor build or native playback',
        runtime_limits=['Explicit Abbasid squad race follows private SPD donor contract; native routing remains unverified',
            'King Age I shares Age II form; boat/fire early-form gaps retained and documented; native chronology playback unverified',
            'Dormant Malian combat ship and unrelated units are not payload members'])
    write(Path(destination)/'payload-manifest.json',report)
    return report

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',type=Path,default=OUT/'profiles/manifest.json')
    parser.add_argument('--audit',type=Path,default=OUT/'binding-audit.json')
    args=parser.parse_args();result=build(args.manifest,args.audit)
    print('Speech-only native binding owners:',result['owner_count'])
