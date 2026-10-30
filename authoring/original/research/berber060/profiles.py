"""Hash-qualified native SPD clones. Layout preserved; native playback separate."""
import struct, hashlib, re
from pathlib import Path
from common import ROOT, OUT, read, write, sha

def chunks(data):
    if len(data) < 24 or data[:16] != b'Relic Chunky\r\n\x1a\x00':
        raise ValueError('Not a Relic Chunky container')
    if struct.unpack_from('<I', data, 16)[0] != 4:
        raise ValueError('Unsupported Chunky version')
    offset = 24
    result = []
    while offset < len(data):
        if offset + 20 > len(data):
            raise ValueError('Truncated chunk header')
        kind, tag, version, size, name_size = struct.unpack_from('<4s4sIII', data, offset)
        start = offset + 20 + name_size
        end = start + size
        if kind != b'DATA' or end > len(data):
            raise ValueError('Invalid or truncated chunk')
        result.append((tag, start, end, version))
        offset = end
    return result


def parse_profile(data):
    parts = chunks(data)
    if [tag for tag, *_ in parts] != [b'RFCI', b'RFUP', b'RNEW', b'RSHI', b'ROBJ', b'RERF']:
        raise ValueError('Unexpected speech profile chunk layout')
    _, start, end, version = parts[0]
    if version != 4131415:
        raise ValueError('Unexpected reflected profile version')
    if end - start < 16:
        raise ValueError("Truncated profile table header")
    count = struct.unpack_from('<I', data, start + 12)[0]
    first = start + 16
    table_end = first + count * 120
    if not 0 < count <= 10000 or table_end > end:
        raise ValueError('Invalid profile record count')

    def text_at(location, size):
        if location < table_end or location + size >= end or data[location + size] != 0:
            raise ValueError('String reference outside the pool or not terminated')
        return dict(offset=location, size=size, text=data[location:location + size].decode('ascii'))

    def record_string(header):
        pointer = header + 4
        location = pointer + struct.unpack_from('<i', data, pointer)[0]
        size = struct.unpack_from('<I', data, header + 12)[0]
        return text_at(location, size)

    records = []
    for index in range(count):
        record = first + index * 120
        pointer = record + 52
        media_start = pointer + struct.unpack_from('<i', data, pointer)[0]
        media_count = struct.unpack_from('<I', data, record + 60)[0]
        if not 1 <= media_count <= 64 or not table_end <= media_start < end or media_start + media_count * 24 > end:
            raise ValueError('Invalid media list')
        media = []
        for number in range(media_count):
            item = media_start + number * 24
            location = item + struct.unpack_from('<q', data, item)[0]
            size = struct.unpack_from('<Q', data, item + 8)[0]
            entry = text_at(location, size)
            if not entry['text'].lower().endswith('.wem'):
                raise ValueError('Unexpected media resource')
            media.append(entry)
        records.append(dict(index=index, context=record_string(record), race=record_string(record + 16),
                            speaker=record_string(record + 32), media=media))
    return records


FAMILY_DONORS = {
    'villager':'malian_villagermale','scout':'malian_scout','tuareg':'malian_donso',
    'trader':'malian_villagermale','mehari':'abbasid_camelrider','sanhaja':'abbasid_camelarcher',
    'zenata':'malian_sofa','archer':'malian_archer','masmuda':'malian_archer',
    'lancer':'abbasid_knight','imam':'malian_imam','handgunner':'malian_musofadigunner',
    'ram':'malian_seige','siege_tower':'malian_seige','springald':'malian_seigeranged',
    'mangonel':'malian_seigeranged','trebuchet':'malian_seigeranged','bombard':'malian_seigeranged',
    'fishing_boat':'malian_tradeship','trade_ship':'malian_tradeship','transport_ship':'malian_scoutship',
    'arrow_ship':'malian_ship','combat_ship':'malian_ship','fire_ship':'malian_fireship',
    'warship':'abbasid_warship','king':'malian_knight',
}
ROLE_DONORS={**FAMILY_DONORS,'masmuda':'abbasid_crossbowman'}
AGES={
    'villager':[1,2,3,4],'scout':[1,2,3,4],'tuareg':[1,2,3,4],'trader':[2,3,4],
    'mehari':[2,3,4],'sanhaja':[2,3,4],'zenata':[2,3,4],'archer':[2,3,4],
    'masmuda':[2,3,4],'lancer':[3,4],'imam':[3,4],'handgunner':[4],
    'ram':[2,3,4],'siege_tower':[2,3,4],'springald':[3,4],'mangonel':[3,4],
    'trebuchet':[3,4],'bombard':[4],'fishing_boat':[1,2,3,4],'trade_ship':[2,3,4],
    'transport_ship':[1,2,3,4],'arrow_ship':[2,3,4],'combat_ship':[2,3,4],
    'fire_ship':[2,3,4],'warship':[4],'king':[1,2,3,4],
}
ERA_PLAN={1:'clowest',2:'clow',3:'cmed',4:'chigh'}

def coverage_comparison():
    stocks={p.stem:[parse_media(m['text']) for r in parse_profile(p.read_bytes()) for m in r['media']]
            for p in (OUT/'inventory/stock').glob('*.spd')}
    result=[]
    for family,era in [('fishing_boat','clowest'),('transport_ship','clowest'),('king','clowest'),('masmuda','clow'),('fire_ship','clow')]:
        donor=stocks[ROLE_DONORS[family]]
        events={p['event'] for p in donor if p['parsed']}
        # cMed is the nearest existing chronological donor form in all five.
        wanted={(p['event'],p['delivery']) for p in donor if p['parsed'] and p['era']=='cmed'}
        candidates=[]
        for key,media in stocks.items():
            parsed=[p for p in media if p['parsed']]
            if era not in {p['era'] for p in parsed}: continue
            missing=events-{p['event'] for p in parsed}
            available={(p['event'],p['delivery']) for p in parsed if p['era']==era}
            candidates.append({'donor':key,'missing_event_names':sorted(missing),
                'missing_early_event_delivery_pairs':[list(p) for p in sorted(wanted-available)],
                'extra_event_names':sorted({p['event'] for p in parsed}-events)})
        result.append({'family':family,'current_donor':FAMILY_DONORS[family],'reference_role_donor':ROLE_DONORS[family],'missing_planning_era':era,
            'reference_planning_era':'cmed','current_donor_events':sorted(events),'candidates':candidates})
    write(OUT/'profiles/early-age-donor-comparison.json',{
        'scope':'39 actual Malian/Abbasid profiles; all original contexts; no binary structure growth',
        'age_mapping_status':'Era naming follows prior planning inference; actual native chronological mappings retained by binding audit',
        'families':result})

def donor_decisions():
    decisions=[]
    for family,candidate in [('fishing_boat','malian_villagermale'),('transport_ship','malian_villagermale'),
                             ('king','malian_scout'),('masmuda','malian_archer')]:
        reference=ROLE_DONORS[family]
        original=(OUT/'inventory/stock'/(reference+'.spd')).read_bytes()
        alternative=(OUT/'inventory/stock'/(candidate+'.spd')).read_bytes()
        before={r['context']['text'].lower() for r in parse_profile(original)}
        after={r['context']['text'].lower() for r in parse_profile(alternative)}
        missing=sorted(before-after)
        decisions.append({'family':family,'role_donor':reference,'candidate':candidate,
            'source_sha256':hashlib.sha256(original).hexdigest(),
            'candidate_sha256':hashlib.sha256(alternative).hexdigest(),
            'missing_original_native_contexts':missing,
            'added_native_contexts':sorted(after-before),
            'accepted':not missing,
            'ruling':'role-faithful context superset; native playback pending' if not missing else
                'Retain role donor: candidate drops native reachable contexts; root conditional authorization not satisfied',
            'native_playback':'unverified'})
    write(OUT/'profiles/donor-decisions.json',decisions)

def parse_media(path):
    """Parse naming evidence only; no invented chronology-to-age assignment."""
    normalized=path.replace('\\','/')
    parts=normalized.split('/')
    if len(parts)!=3 or not parts[-1].lower().endswith('.wem'):
        return {'path':path,'parsed':False,'reason':'unexpected path shape'}
    # Folder and filename share a race/speaker token, including case variations.
    identity=parts[-2]
    filename=parts[-1][:-4]
    if not filename.lower().startswith(identity.lower()+'_'):
        return {'path':path,'parsed':False,'reason':'media identity mismatch'}
    tail=filename[len(identity)+1:]
    m=re.fullmatch(r'(.+)_((?:i|c)[a-z]+)_(c[a-z]+)_(\d+)((?:_alt\d+)?)',tail,re.I)
    if not m:
        return {'path':path,'parsed':False,'reason':'unrecognized event/delivery/era/take','raw_tail':tail}
    event,delivery,era,take,alternate=m.groups()
    return {'path':path,'parsed':True,'identity':identity,'event':event.lower(),
            'delivery':delivery.lower(),'era':era.lower(),'take':int(take),
            'alternate':int(alternate[4:]) if alternate else 0,'alternate_suffix':alternate,
            'effort':event.lower().startswith('effort'),'age':None,
            'age_note':'chronology label observed; runtime age scheduling unverified'}

def qualify(data):
    rows=parse_profile(data)
    races=sorted({r['race']['text'] for r in rows})
    speakers=sorted({r['speaker']['text'] for r in rows})
    identities=sorted({m['text'].replace('\\','/').split('/')[1] for r in rows for m in r['media']})
    return {'sha256':hashlib.sha256(data).hexdigest(),'races':races,'speakers':speakers,
            'media_identities':identities,'records':len(rows)}

def clone_private(original, qualification, speaker, media_identity, occupied=()):
    """Bounded writes at parsed field spans; all source bytes must match qualification."""
    if hashlib.sha256(original).hexdigest()!=qualification['sha256']:
        raise ValueError('Donor hash mismatch')
    actual=qualify(original)
    if actual!=qualification: raise ValueError('Donor qualification mismatch')
    if len(actual['races'])!=1 or len({s.lower() for s in actual['speakers']})!=1:
        raise ValueError('Mixed donor identities unsupported')
    if not re.fullmatch('[a-zA-Z0-9]+',speaker): raise ValueError('Unsafe private speaker')
    if speaker.lower() in {s.lower() for s in occupied}|{s.lower() for s in actual['speakers']}:
        raise ValueError('Private identity collision')
    if not re.fullmatch('[a-zA-Z0-9]+_[a-zA-Z0-9]+',media_identity): raise ValueError('Unsafe media identity')
    if media_identity.lower() in {s.lower() for s in actual['media_identities']}:
        raise ValueError('Stock media identity collision')
    output=bytearray(original); edits={}
    def change(field,value):
        raw=value.encode('ascii'); at=field['offset']
        if len(raw)!=field['size']: raise ValueError('Identity edit would relocate pointers')
        for i,b in enumerate(raw):
            if at+i in edits and edits[at+i]!=b: raise ValueError('Conflicting shared string spans')
            edits[at+i]=b
    rows=parse_profile(original)
    for row in rows:
        change(row['speaker'],speaker)
        for media in row['media']:
            path=media['text']; sep='\\' if '\\' in path else '/'; parts=path.split(sep)
            if len(parts)!=3: raise ValueError('Unexpected media shape')
            identity=parts[1]
            if identity not in actual['media_identities'] or not parts[2].lower().startswith(identity.lower()+'_'):
                raise ValueError('Unexpected media identity')
            # Rewrite precisely the folder token and leading filename identity.
            new=sep.join((parts[0],media_identity,media_identity+parts[2][len(identity):]))
            change(media,new)
    for at,b in edits.items(): output[at]=b
    result=bytes(output); reread=parse_profile(result)
    if len(result)!=len(original) or len(rows)!=len(reread): raise ValueError('Layout changed')
    for old,new in zip(rows,reread):
        if old['context']!=new['context'] or old['race']!=new['race']:
            raise ValueError('Native context or race changed')
    if any(a!=b and i not in edits for i,(a,b) in enumerate(zip(original,result))):
        raise ValueError('Out of bounds modification')
    return result,set(edits)

def main():
    stock=read(OUT/'inventory/stock-profiles.json')
    observed={Path(x['member']).stem:x for x in stock}
    qualifications={}
    for key,item in observed.items():
        data=Path(item['path']).read_bytes(); q=qualify(data)
        if q['sha256']!=item['sha256']: raise ValueError('Inventory fixture changed')
        qualifications[key]=q
    write(OUT/'profiles/qualified-donors.json',qualifications)
    occupied={s for q in qualifications.values() for s in q['speakers']}
    families=[]
    for index,(family,key) in enumerate(FAMILY_DONORS.items(),1):
        fixture=observed[key]; original=Path(fixture['path']).read_bytes(); q=qualifications[key]
        speaker='b'+str(index).zfill(2)+'x'*(len(q['speakers'][0])-3)
        token=q['media_identities'][0].split('_',1)[1]
        private_token='b'+str(index).zfill(2)+'x'*(len(token)-3)
        race=q['races'][0]; identity=race+'_'+private_token
        private,allowed=clone_private(original,q,speaker,identity,occupied)
        occupied.add(speaker)
        target=OUT/'profiles/audio'/f'{race}_{speaker}.spd'
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(private)
        rows=parse_profile(original); cloned=parse_profile(private)
        media=sorted({m['text'] for r in rows for m in r['media']})
        parsed=[parse_media(m) for m in media]
        private_media=sorted({m['text'] for r in cloned for m in r['media']})
        details=[]
        for old,new in zip(rows,cloned):
            details.append({'index':old['index'],'context':old['context']['text'],
                'race':old['race']['text'],'donor_speaker':old['speaker']['text'],'speaker':new['speaker']['text'],
                'media':[{'donor':a['text'],'private':b['text']} for a,b in zip(old['media'],new['media'])]})
        row={'family':family,'donor':key,'donor_member':fixture['member'],'donor_archive':fixture['archive'],
            'donor_sha256':q['sha256'],'race':race,'donor_speakers':q['speakers'],'speaker':speaker,
            'profile_path':str(target),'profile_resource':target.name,'profile_sha256':sha(target),
            'private_media_identity':identity,'record_count':len(rows),'unique_media':len(media),
            'events':sorted({p['event'] for p in parsed if p['parsed']}),
            'deliveries':sorted({p['delivery'] for p in parsed if p['parsed']}),
            'eras':sorted({p['era'] for p in parsed if p['parsed']}),
            'unparsed':[p for p in parsed if not p['parsed']],
            'age_mapping':'All donor chronological forms retained; label-to-runtime-age scheduling unverified',
            'native_playback':'unverified','allowed_byte_span_size':len(allowed),
            'changed_bytes':sum(a!=b for a,b in zip(original,private))}
        row.update(ages=AGES[family],profile=target.relative_to(OUT/'profiles').as_posix(),
            donor_speaker=q['speakers'][0],
            records=[{'context':r['context']['text'],'race':r['race']['text'],
                      'speaker':r['speaker']['text'],'media_paths':[m['text'] for m in r['media']]} for r in cloned],
            media=[parse_media(m) for m in private_media])
        row['declared_playable_ages']=AGES[family]
        row['coverage_gaps']=[{'age':age,'missing_planning_era':ERA_PLAN[age],
            'missing_contexts_at_planning_era':sorted({re.sub(r'_c(?:lowest|low|med|high)$','_'+ERA_PLAN[age],r['context']['text'].lower())
                for r in rows if re.search(r'_c(?:lowest|low|med|high)$',r['context']['text'],re.I)}),
            'status':'chronology form absent; native binding remap or approved donor needed'}
            for age in AGES[family] if ERA_PLAN[age] not in row['eras']]
        write(OUT/'profiles'/f'{family}-records.json',details)
        write(OUT/'profiles'/f'{family}-media.json',parsed)
        families.append(row)
    write(OUT/'profiles/manifest.json',{'schema':'berber060-private-spd/v1','families':families,
        'coverage':'all donor records/media retained; no universal donor','native_playback':'unverified'})
    coverage_comparison()
    donor_decisions()
    print(f'{len(families)} private clones, {sum(r["unique_media"] for r in families)} unique family media slots')

if __name__=='__main__': main()

