"""Offline Whisper spotchecks. No provider calls, model downloads, or audio edits."""
import argparse, difflib, hashlib, importlib, json, re, sys, unicodedata, wave
from pathlib import Path
from common import OUT, ART, read, write, sha
from batch_generation import job_key,single_identity

OPTIONS={'language':'ar','task':'transcribe','fp16':False,'temperature':0,
         'condition_on_previous_text':False,'beam_size':1,'best_of':1,'verbose':None}
ENGLISH_DIRECTIONS=('grunting','groaning','screaming','whispering','shouting','cough','coughing',
    'pain','death','sigh','sighing','breath','breathing','laugh','laughing','grunt','groan','scream')
VOWEL_RENDERINGS={'ا','اه','ااه','اااه','ها','هه','ه','هاه','اها','اوه'}

def normalized_arabic(value):
    value=re.sub(r'\[[^\]]*\]','',value)
    value=unicodedata.normalize('NFKC',value).translate(str.maketrans('أإآٱى','ااااي'))
    return ''.join(c.lower() for c in value if c.isalnum() and c!='ـ')

def assess(expected,transcript,nonverbal,segments):
    flags=[];expected_norm=normalized_arabic(expected);actual_norm=normalized_arabic(transcript)
    similarity=difflib.SequenceMatcher(None,expected_norm,actual_norm).ratio()
    if nonverbal:
        words=re.findall(r'[a-z]+',transcript.lower())
        if any(w in ENGLISH_DIRECTIONS for w in words):flags.append('possible_spoken_English_direction_word')
        if actual_norm and actual_norm not in VOWEL_RENDERINGS:flags.append('ASR_lexical_output_on_nonverbal_uncertain')
    elif not actual_norm:flags.append('empty_command_transcription')
    elif similarity<.75:flags.append('possible_command_mismatch')
    elif actual_norm!=expected_norm:flags.append('command_text_differs_ASR_uncertain')
    if any(s.get('avg_logprob',0)<-1 for s in segments):flags.append('low_ASR_log_probability')
    if any(s.get('no_speech_prob',0)>.6 for s in segments):flags.append('high_ASR_no_speech_probability')
    return {'flags':flags,'normalized_expected':expected_norm,'normalized_transcript':actual_norm,
        'nonverbal_vowel_rendering':nonverbal and actual_norm in VOWEL_RENDERINGS,
        'character_similarity':similarity,'verdict':'independent uncertain ASR evidence; no listening, pronunciation or native-playback approval'}

def select_samples():
    plan=read(ART/'recording-plan.json');jobs=plan['jobs'];current={j['id']:j for j in jobs}
    pilot_path=OUT/'character-pilot-jobs.json'
    pilots=read(pilot_path) if pilot_path.exists() else []
    pilot_ids={j['id'] for j in pilots if j['id'] in current}
    rows=[];missing=[]
    families=list(dict.fromkeys(j['family'] for j in jobs))
    for family in families:
        for kind in ('command','effort'):
            candidates=[j for j in jobs if j['family']==family and
                ((j['event']=='select' and j['delivery']=='norm' and not j['script'].get('nonverbal')) if kind=='command' else
                 (j['event'] in ('effortpain','effortdeath') and j['script'].get('nonverbal')))]
            candidates.sort(key=lambda j:(j['id'] not in pilot_ids,j['event']!='effortpain',j['age']!='med',j['id']))
            chosen=None
            for job in candidates:
                path=OUT/'receipts'/f'{job_key(job)}.json'
                if not path.exists():continue
                receipt=read(path)
                if receipt.get('status')!='accepted_acoustic' or receipt.get('identity')!=single_identity(job):continue
                source=Path(receipt['source'])
                if not source.is_file() or sha(source)!=receipt['source_sha256']:raise ValueError('Accepted lossless source changed')
                chosen={'job':job,'receipt':receipt,'source':str(source),'kind':kind};break
            if chosen:rows.append(chosen)
            else:missing.append({'family':family,'kind':kind,'status':'current_accepted_sample_unavailable'})
    if len(rows)>52:raise ValueError('Spotcheck scope exceeds 52 clips')
    return rows,missing

def whisper_module():
    # This project has coverage.py, unrelated to Numba's optional coverage package.
    # Hide only our script directory during third-party imports; edit no packages.
    original=list(sys.path);local=Path(__file__).absolute().parent
    try:
        sys.path[:]=[p for p in sys.path if Path(p or '.').absolute()!=local]
        loaded=sys.modules.get('coverage')
        if loaded and Path(getattr(loaded,'__file__','')).absolute()==local/'coverage.py':
            del sys.modules['coverage']
        return importlib.import_module('whisper')
    finally:sys.path[:]=original

def cached_model():
    whisper=whisper_module()
    path=Path.home()/'.cache/whisper/small.pt'
    expected=whisper._MODELS['small'].split('/')[-2]
    if not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('Installed Whisper model URL digest invalid')
    if not path.is_file():raise ValueError('Required cached small model absent; download prohibited')
    actual=sha(path)
    if actual!=expected:raise ValueError('Cached small model digest mismatch; download prohibited')
    return path,actual

def run_spotchecks(limit=None):
    import torch
    whisper=whisper_module()
    path,model_sha=cached_model()
    torch.set_num_threads(4)
    try:torch.set_num_interop_threads(1)
    except RuntimeError:pass
    samples,missing=select_samples()
    if limit is not None:samples=samples[:limit]
    destination=OUT/'local-asr';destination.mkdir(parents=True,exist_ok=True)
    report={'scope':'At most one current accepted selection command and one pain/death effort per actor',
        'model':'Whisper small multilingual','model_path':str(path),'model_sha256':model_sha,
        'model_digest_verified_against_installed_URL':True,'cpu_threads':4,'torch_version':torch.__version__,
        'options':OPTIONS,'listening':'not_performed','native_playback':'not_tested',
        'pronunciation_review':'not_established_by_ASR','rows':[],'missing':missing,'status':'in_progress'}
    report['flag_policy']={'possible_command_mismatch_character_similarity_below':.75,
        'direction_words':'literal English token match only; Arabic ASR may miss or translate English words',
        'nonverbal_vowel_spellings':'Common Arabic ah/ha spellings retained as uncertain vowel renderings, not classified as lexical direction words'}
    model=None
    for index,sample in enumerate(samples,1):
        job,receipt=sample['job'],sample['receipt'];source=Path(sample['source'])
        material={'source_sha256':receipt['source_sha256'],'model_sha256':model_sha,'options':OPTIONS}
        cache_id=hashlib.sha256(json.dumps(material,sort_keys=True).encode()).hexdigest()
        cache_path=destination/'cache'/f'{cache_id}.json'
        if cache_path.exists():
            result=read(cache_path)
            if result['identity']!=material:raise ValueError('Local ASR cache identity changed')
        else:
            if model is None:
                # A local filepath is used instead of a model name. Block the
                # downloader as an additional guard against any accidental fetch.
                original_download=whisper._download
                def no_download(*args,**kwargs):raise RuntimeError('Model downloads prohibited')
                whisper._download=no_download
                try:model=whisper.load_model(str(path),device='cpu')
                finally:whisper._download=original_download
            transcription=model.transcribe(str(source),**OPTIONS)
            segments=[{k:s[k] for k in ('start','end','text','avg_logprob','no_speech_prob','compression_ratio') if k in s}
                      for s in transcription.get('segments',[])]
            result={'identity':material,'transcript':transcription.get('text','').strip(),
                'language':transcription.get('language'),'segments':segments}
            write(cache_path,result)
        expected=job['script'].get('text',job['generation_text'])
        with wave.open(str(source),'rb') as audio:duration=audio.getnframes()/audio.getframerate()
        row={'family':job['family'],'voice_id':job['voice_id'],'kind':sample['kind'],'event':job['event'],
            'job_id':job['id'],'request_id':receipt['request_id'],'expected':expected,
            'generation_text':job['generation_text'],'source':str(source),'source_sha256':receipt['source_sha256'],
            'duration_seconds':duration,'cache_path':str(cache_path),'transcript':result['transcript'],
            'segments':result['segments'],**assess(expected,result['transcript'],sample['kind']=='effort',result['segments'])}
        report['rows'].append(row);write(destination/'spotchecks.json',report)
        print(f"LOCAL_ASR {index}/{len(samples)} {job['family']} {sample['kind']} flags={','.join(row['flags']) or 'none'}",flush=True)
    report['status']='completed';report['checked_clips']=len(report['rows'])
    report['flagged_clips']=sum(bool(r['flags']) for r in report['rows'])
    write(destination/'spotchecks.json',report)
    lines=['# Offline ASR spotchecks','','Whisper small multilingual ran locally on CPU with four threads. Its cached model digest was verified against the installed Whisper model URL. No model download, paid request, audio edit or receipt mutation occurred.','','Transcriptions are uncertain independent machine evidence. Efforts can make ASR hallucinate words; flags require human review. This does not approve voice acting, Arabic pronunciation or native playback.','',f'Checked {len(report["rows"])} clips; {report["flagged_clips"]} have at least one automatic flag; {len(missing)} requested sample slots unavailable.','','| Actor family | Kind | Expected | ASR | Flags |','|---|---|---|---|---|']
    for row in report['rows']:
        escaped=[str(v).replace('|','/').replace('\n',' ') for v in (row['family'],row['kind'],row['expected'],row['transcript'],', '.join(row['flags']))]
        lines.append('| '+' | '.join(escaped)+' |')
    lines+=['','Detailed source/model hashes, expected text, ASR segment confidence measures and cache identities are in spotchecks.json.']
    (destination/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int);args=parser.parse_args()
    run_spotchecks(args.limit)
