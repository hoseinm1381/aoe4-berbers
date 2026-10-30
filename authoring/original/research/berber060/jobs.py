"""Compile exact native assignments into a smaller, selectable recording set."""
from collections import defaultdict,Counter
import hashlib
from common import OUT, ART, read, write
from scripts import line_text,PERSONAS

ERA={'clowest':('lowest',1),'clow':('low',2),'cmed':('med',3),'chigh':('high',4),'cnone':('none',0)}
DELIVERY={'inorm':'norm','ihigh':'high','istealth':'stealth','cnone':'none','inone':'none'}

def take_count(event, native_slots):
    frequent=event.startswith(('select','move','attack','engage','ambientcombat',
        'acknowledge','brace','stop','hold','charge','weaponaim','weaponfire',
        'resource','structurebuild','structurerepair','healorder'))
    return min(3 if frequent else 2,native_slots)
NETWORK_SEED_STEP=1000003
PERFORMANCE_SEED_STEP=5000011


def text_override_prompt(text,delivery,combat_tag=None,nonverbal=False):
    """Keep legacy delivery by default; only explicit HIGH speech may use angry."""
    if combat_tag is not None:
        if combat_tag!='angry' or delivery!='high' or nonverbal:
            raise ValueError('combat_tag angry is allowed only for HIGH spoken text revisions')
        return '[angry] '+text
    if delivery=='high':return '[shouting] '+text
    if delivery=='stealth':return '[whispering] '+text
    return text


def apply_performance_overrides(jobs,overrides):
    """Apply an immutable one-shot delivery decision after every existing epoch."""
    from batch_generation import job_key
    for jid,override in overrides.items():
        if jid not in jobs:raise ValueError('Controlled delivery refers to a missing semantic job')
        job=jobs[jid]
        if (job['delivery']!='high' or job.get('script',{}).get('nonverbal')
                or job.get('nonverbal') or job['event'].lower().startswith('effort')
                or job.get('model_id','eleven_v3')!='eleven_v3'):
            raise ValueError('Controlled delivery cannot change a noncombat/nonverbal job')
        if any(job[k]!=override.get(k) for k in ('family','event','age','delivery','take','voice_id')):
            raise ValueError('Controlled delivery changes actor or native context')
        if (override.get('epoch')!=1 or type(override.get('epoch')) is not int
                or override.get('action')!='controlled_combat_delivery'
                or not override.get('reason','').strip()):
            raise ValueError('Controlled delivery requires one explained epoch')
        if (not job['generation_text'].startswith('[shouting] ')
                or job['generation_text']!=override.get('prior_prompt')
                or job['seed']!=override.get('prior_seed') or job_key(job)!=override.get('prior_request_id')):
            raise ValueError('Controlled delivery source prompt/epoch identity changed')
        updated=dict(job,generation_text='[angry] '+job['generation_text'][len('[shouting] '):],
            seed=(job['seed']+PERFORMANCE_SEED_STEP)%(2**32),force_single=True)
        if (updated['generation_text']!=override.get('replacement_prompt')
                or job_key(updated)!=override.get('replacement_request_id')):
            raise ValueError('Controlled delivery replacement identity changed')
        job.update(generation_text=updated['generation_text'],seed=updated['seed'],force_single=True,
            performance_override_epoch=1,performance_override_reason=override['reason'],
            prior_performance_request_id=override['prior_request_id'])
    return jobs

def casting():
    candidates=read(OUT/'account/shared-arabic.json')['voices']
    saved=read(OUT/'account/arabic-voices.json')['voices']
    cast={}
    # Regional Arabic fallback actors; no claim these are Tuareg/Amazigh natives.
    preferred={'tuareg':'NVRXBDmA6I8ZAldiUWuB','mehari':'dbXZnF5pfQqN00XGwlRF',
        'zenata':'wZ6E1XvJnMjmRvpvp2vY','archer':'DWzI1mgotR4xUap1D5w3',
        'handgunner':'C5sH6vPhsC46AKaQmXXJ','imam':'F2jHHIMyJTh1pdwoLzNQ',
        'king':'7QPNlmYo518u6QuJ5nDI','scout':'Rs6W7zDzDMy5M4DoQvwj',
        'sanhaja':'HiEyBzS3AMj0Ksl354zu','masmuda':'cXKxmnaaadsos6OYJ96c'}
    # A replacement must not return its old actor to the automatic pool and
    # cascade into every already-recorded family. Freeze the accepted roster.
    if (ART/'casting-lock.json').exists():preferred.update(read(ART/'casting-lock.json'))
    cast_overrides=read(ART/'casting-overrides.json') if (ART/'casting-overrides.json').exists() else {}
    preferred.update({family:row['voice_id'] for family,row in cast_overrides.items()})
    allvoices={v['voice_id']:v for v in candidates}
    allvoices.update({v['voice_id']:v for v in saved})
    used=set()
    for family,persona in PERSONAS.items():
        voice_id=preferred.get(family)
        pool=[]
        for vid,v in allvoices.items():
            labels=v.get('labels') or {};gender=v.get('gender') or labels.get('gender')
            rate=v.get('rate') or (v.get('sharing') or {}).get('rate') or 1
            if vid in used or gender!=persona['gender'] or v.get('category') not in ('professional','high_quality') or rate>1:continue
            accent=v.get('accent') or labels.get('accent','')
            score=10 if accent in ('algerian','moroccan','tunisian') else 5 if accent=='modern standard' else 0
            pool.append((-score,vid))
        if voice_id is None:
            if not pool:raise ValueError('No distinct qualified actor: '+family)
            # Reserve explicitly directed characters until their turn.
            pool=[x for x in pool if x[1] not in preferred.values()]
            voice_id=sorted(pool)[0][1]
        if voice_id in used or voice_id not in allvoices:raise ValueError('Actor identity collision/unavailable')
        v=allvoices[voice_id];labels=v.get('labels') or {}
        if family in cast_overrides:
            if ((v.get('gender') or labels.get('gender'))!=persona['gender'] or
                v.get('category') not in ('professional','high_quality') or
                (v.get('rate') or (v.get('sharing') or {}).get('rate') or 1)>1):
                raise ValueError('Replacement character fails gender/category/rate qualification')
        cast[family]={'voice_id':voice_id,'name':v['name'],'gender':persona['gender'],
            'accent':v.get('accent') or labels.get('accent'),'persona':persona,'rate_multiplier':1,
            'language':'ar','qualification':'pilot pending; regional/classical Arabic approximation'}
        used.add(voice_id)
    write(ART/'casting.json',cast);return cast

def compile_jobs():
    profiles=read(OUT/'profiles/manifest.json');cast=casting()
    jobs={};assignments=[];gaps=[];statistics=[]
    for profile in profiles['families']:
        family=profile['family'];groups=defaultdict(list)
        for media in profile['media']:
            if not media.get('parsed'):raise ValueError('Unparsed native media')
            groups[(media['event'],media['delivery'],media['era'])].append(media)
        for (event,delivery,era),media in sorted(groups.items()):
            age,age_n=ERA[era];style=DELIVERY[delivery]
            count=take_count(event,len(media));pool=[]
            for take in range(1,count+1):
                line=line_text(family,event,age,take,style)
                if not line['text'] or line['review_status']=='unresolved':raise ValueError('Unresolved script '+str((family,event,age,take,style)))
                text=line['text']
                if not line.get('nonverbal'):
                    if style=='high':text='[shouting] '+text
                    elif style=='stealth':text='[whispering] '+text
                else:
                    # Tags supply the direction; the vowel/grunt supplies vocal content.
                    endings={'effortcough':'أَحْ أَحْ','effortthroatclear':'أَهَمْ','effortwarcry':'آآه!'}
                    text+=' '+endings.get(event,'آه!' if event in ('effortpainbig','effortdeath','effortfear','effortpanic') else 'هُهْ!')
                # Native aliases with the same phrase/age/performance may share a recording.
                material={'family':family,'age':age,'delivery':style,'text':text,'take':take,
                    'effort_event':event if line.get('nonverbal') else None,'voice_id':cast[family]['voice_id']}
                digest=hashlib.sha256(str(sorted(material.items())).encode()).hexdigest()
                jid=family+'-'+digest[:16]
                if jid not in jobs:
                    jobs[jid]={'id':jid,'family':family,'event':event,'age':age,'delivery':style,'take':take,
                        'voice_id':cast[family]['voice_id'],'model_id':'eleven_v3','generation_text':text,
                        'seed':int(digest[:8],16),'script':line,'selectable_native_slot_count':len(media)}
                pool.append(jid)
            for index,m in enumerate(sorted(media,key=lambda x:x['path'].lower())):
                assignments.append({'family':family,'path':m['path'].replace('\\','/').lower(),
                    'event':event,'delivery':delivery,'era':era,'job_id':pool[index%count]})
        statistics.append({'family':family,'native_media_slots':len(profile['media']),
            'unique_jobs':sum(j['family']==family for j in jobs.values()),'declared_playable_ages':profile.get('declared_playable_ages',profile['ages'])})
        gaps.extend({'family':family,'gap':g} for g in profile.get('coverage_gaps',[]))
    text_overrides=read(ART/'text-overrides.json') if (ART/'text-overrides.json').exists() else {}
    for jid,override in text_overrides.items():
        if jid not in jobs:
            candidates=[j for j in jobs.values() if all(j[k]==override.get(k) for k in ('family','event','age','delivery','take'))]
            if not override.get('allow_actor_replacement') or len(candidates)!=1:
                raise ValueError('Pronunciation revision refers to a missing job')
            job=candidates[0]
        else:job=jobs[jid]
        if any(job[k]!=override[k] for k in ('family','event','age','delivery')):
            raise ValueError('Pronunciation revision changes its native context')
        if not override.get('text','').strip() or not override.get('english','').strip() or not override.get('reason','').strip():
            raise ValueError('Unexplained pronunciation revision')
        job['script'].update(text=override['text'],english=override['english'])
        nonverbal=bool(job.get('script',{}).get('nonverbal') or job.get('nonverbal') or job['event'].lower().startswith('effort'))
        job['generation_text']=text_override_prompt(override['text'],job['delivery'],override.get('combat_tag'),nonverbal)
        job.update(force_single=True,pronunciation_revision=override['reason'],documented_override_reason=override['reason'])
        if override.get('combat_tag') is not None:job['combat_tag']=override['combat_tag']
    overrides=read(ART/'retake-overrides.json') if (ART/'retake-overrides.json').exists() else {}
    for jid,override in overrides.items():
        if jid not in jobs:continue
        jobs[jid]['seed']=(jobs[jid]['seed']+override['seed_offset'])%(2**32)
        jobs[jid]['force_single']=jobs[jid].get('force_single',False) or override.get('force_single',False)
        jobs[jid]['retake_reason']=override['reason']
    credentials=read(ART/'credential-retries.json') if (ART/'credential-retries.json').exists() else {}
    for jid,epoch in credentials.items():
        if jid in jobs:
            jobs[jid]['seed']=(jobs[jid]['seed']+10000000*epoch)%(2**32)
            jobs[jid]['credential_retry_epoch']=epoch
    network=read(ART/'network-retries.json') if (ART/'network-retries.json').exists() else {}
    for jid,epoch in network.items():
        if jid in jobs:
            jobs[jid]['seed']=(jobs[jid]['seed']+NETWORK_SEED_STEP*epoch)%(2**32)
            jobs[jid]['network_retry_epoch']=epoch
    performance=read(ART/'performance-overrides.json') if (ART/'performance-overrides.json').exists() else {}
    apply_performance_overrides(jobs,performance)
    result={'schema':'berber060-recording-jobs/v1','jobs':list(jobs.values()),'assignments':assignments,
        'families':statistics,'chronology_gaps':gaps,'native_playback':'pending'}
    chars=sum(len(j['generation_text']) for j in jobs.values())
    result['estimate']={'unique_recordings':len(jobs),'native_alias_paths':len(assignments),'characters_including_tags':chars,
        'current_list_usd':round(chars*.08/1000,4),'conservative_usd_with_20_percent_retry':round(chars*.30/1000*1.2,4),
        'hard_cap_usd':100,'pricing_source':'https://elevenlabs.io/pricing/api','pricing_checked':'2026-10-16'}
    if result['estimate']['conservative_usd_with_20_percent_retry']>100:raise ValueError('Complete job estimate exceeds approved cap')
    write(ART/'recording-plan.json',result)
    selected=[]
    for family in cast:
        family_jobs=[j for j in jobs.values() if j['family']==family]
        for predicate in [lambda j:j['event']=='select' and j['delivery']=='norm',lambda j:j['event']=='attack' and j['delivery']=='high',lambda j:j['event']=='select' and j['delivery']=='stealth',lambda j:j['event']=='effortpain',lambda j:j['event']=='effortdeath']:
            matches=[j for j in family_jobs if predicate(j)]
            if matches and matches[0] not in selected:selected.append(matches[0])
    write(OUT/'character-pilot-jobs.json',selected)
    print(result['estimate']);print('pilot_jobs',len(selected));return result

if __name__=='__main__':compile_jobs()
