"""Compatible Wwise encoding and independently decoded media QA."""
import argparse,hashlib,json,struct,urllib.request,zipfile,wave
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.signal import correlate,correlation_lags
from common import ART,OUT,WWISE,write,read,run,sha
from generation import pcm_quality

VGM_URL='https://github.com/vgmstream/vgmstream/releases/download/r2117/vgmstream-win64.zip'
VGM_SHA='6c4a8a3813864fefed081bbd337dbc0ad93bf88e0b92f5db98d7ab258b22dc6c'
PROJECT=ART/'wwise/BerberVoices/BerberVoices.wproj'

def decoder():
    folder=OUT/'tools/vgmstream-r2117';exe=folder/'vgmstream-cli.exe'
    if exe.exists():return exe
    archive=OUT/'tools/vgmstream-win64-r2117.zip';archive.parent.mkdir(parents=True,exist_ok=True)
    if not archive.exists():
        with urllib.request.urlopen(urllib.request.Request(VGM_URL,headers={'User-Agent':'Berber-voice-build'}),timeout=90) as r:archive.write_bytes(r.read())
    if sha(archive)!=VGM_SHA:raise ValueError('Official decoder download digest mismatch')
    folder.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('Decoder archive corrupt')
        for n in z.namelist():
            p=Path(n)
            if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe decoder member')
        z.extractall(folder)
    write(OUT/'tools/decoder-provenance.json',{'url':VGM_URL,'zip_sha256':VGM_SHA,'executable_sha256':sha(exe),'source':'Official vgmstream r2117 GitHub release; independently reported release asset digest'})
    return exe

def inspect_wem(path):
    data=Path(path).read_bytes()
    if data[:4]!=b'RIFF' or data[8:12]!=b'WAVE' or struct.unpack_from('<I',data,4)[0]+8!=len(data):raise ValueError('Invalid RIFF size/header')
    offset=12;fmt=None;tags=[]
    while offset<len(data):
        tag,size=struct.unpack_from('<4sI',data,offset);end=offset+8+size
        if end>len(data):raise ValueError('Truncated RIFF chunk')
        if tag==b'fmt ':fmt=struct.unpack_from('<HHI',data,offset+8)
        tags.append(tag.decode('ascii'));offset=end+size%2
    if fmt!=(65535,1,48000) or 'data' not in tags:raise ValueError('Not qualified mono48k Wwise Vorbis')
    return {'sha256':sha(path),'bytes':len(data),'format':fmt,'chunks':tags}

def encode(paths,quality='Medium'):
    if quality not in ('Low','Medium','High'):raise ValueError('Unknown conversion quality')
    if not PROJECT.exists():run(WWISE,'create-new-project',PROJECT,'--platform','Windows','--quiet')
    out=OUT/'wem'/quality;out.mkdir(parents=True,exist_ok=True)
    sources=ET.Element('ExternalSourcesList',SchemaVersion='1',Root=str(OUT/'wav'))
    unique={Path(p).stem:Path(p) for p in paths}
    cache_path=out/'encoding-manifest.json';cache=read(cache_path) if cache_path.exists() else {}
    missing=[(key,p) for key,p in unique.items() if not (out/'Windows'/f'{key}.wem').is_file() or cache.get(key,{}).get('source_sha256')!=sha(p)]
    if missing:
        for key,p in missing:
            if p.parent!=OUT/'wav':raise ValueError('Wwise input must be the release-owned WAV tree')
            ET.SubElement(sources,'Source',Path=p.name,Conversion='Vorbis Quality '+quality,Destination=key)
        xml=OUT/'wwise'/f'sources-{quality}.wsources';xml.parent.mkdir(exist_ok=True)
        ET.indent(sources);ET.ElementTree(sources).write(xml,encoding='utf8',xml_declaration=True)
        log=run(WWISE,'convert-external-source',PROJECT,'--source-file',xml,'--platform','Windows','--output',out,'--no-wwise-dat',timeout=1200)
        (OUT/'wwise'/f'conversion-{quality}.log').write_text(log,encoding='utf8')
    result=[]
    for key,p in unique.items():
        wem=out/'Windows'/f'{key}.wem'
        result.append({'source':str(p),'source_sha256':sha(p),'wem':str(wem),**inspect_wem(wem)})
        cache[key]=result[-1]
    write(cache_path,cache)
    return result

def decoded_check(row):
    exe=decoder();target=OUT/'decoded-qa'/Path(row['wem']).with_suffix('.wav').name
    target.parent.mkdir(exist_ok=True)
    run(exe,'-i','-o',target,row['wem'],timeout=60)
    with wave.open(str(target),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,48000):raise ValueError('Decoded media format differs')
        decoded=w.readframes(w.getnframes())
    quality=pcm_quality(decoded,48000)
    with wave.open(row['source'],'rb') as w:reference=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
    value=np.frombuffer(decoded,dtype='<i2').astype(float)
    if abs(len(reference)-len(value))>4800:raise ValueError('Decoded duration differs by >100ms')
    corr=correlate(value,reference,mode='full',method='fft');lag=int(correlation_lags(len(value),len(reference))[np.argmax(corr)])
    a=reference[max(0,-lag):min(len(reference),len(value)-lag)]
    b=value[max(0,lag):min(len(value),len(reference)+lag)]
    gain=float(np.dot(a,b)/max(1,np.dot(b,b)))
    snr=float(10*np.log10(max(1,np.dot(a,a))/max(1,np.dot(a-gain*b,a-gain*b))))
    return {**quality,'snr_db':snr,'alignment_lag_samples':lag,'decoded_sha256':sha(target),'quality_scope':'objective decode and signal comparison; listening separate'}

def comparison_sources(plan=None,families=('tuareg','handgunner','imam','villager','king')):
    # Runtime import avoids a module cycle: final_audio also uses this encoder.
    from final_audio import normalized_receipts
    from batch_generation import job_key
    plan=plan or read(ART/'recording-plan.json')
    accepted=normalized_receipts(plan)
    selected=[]
    for family in families:
        available=[(j,accepted[job_key(j)]) for j in plan['jobs'] if j['family']==family and job_key(j) in accepted]
        for effort in (False,True):
            rows=[(j,r) for j,r in available if j['event'].startswith('effort')==effort]
            rows.sort(key=lambda pair:(pair[0]['event']!=('effortpain' if effort else 'select'),
                pair[0].get('delivery')!='norm',pair[0].get('age')!='med',pair[0]['id']))
            if rows:
                job,receipt=rows[0]
                selected.append({**receipt,'comparison_event':job['event'],'comparison_kind':'effort' if effort else 'command'})
    return selected


def compare():
    if (OUT/'generation.lock').exists() or (OUT/'normalization.lock').exists():raise ValueError('Wait for synthesis and full normalization')
    selected=comparison_sources()
    if len({r['family'] for r in selected})<3:raise ValueError('Representative current normalized families not ready')
    plan_sha256=sha(ART/'recording-plan.json');rows=[]
    provenance={str(Path(r['native_path']).resolve()):r for r in selected}
    for quality in ('Low','Medium','High'):
        for row in encode([Path(r['native_path']) for r in selected],quality):
            source=provenance[str(Path(row['source']).resolve())]
            checked=decoded_check(row)
            if checked['clipped_samples']:raise ValueError('Comparison decoded clipping; no quality recommendation')
            rows.append({'conversion':quality,**row,'decode':checked,'request_id':source['request_id'],
                'normalization_provenance_sha256':source['normalization']['provenance_sha256'],
                'family':source['family'],'kind':source['comparison_kind'],'event':source['comparison_event']})
    if sha(ART/'recording-plan.json')!=plan_sha256:raise ValueError('Recording plan changed during comparison')
    # encode() independently inspects genuine mono48k Wwise Vorbis for every row.
    report={'status':'objective_comparison_complete','rows':rows,'listening':'pending','native_playback':'pending',
        'recording_plan_sha256':plan_sha256,'chosen_quality':'Medium',
        'rationale':'Provisional objective bandwidth/SNR compromise informed by the initial pilot; current normalized Low/Medium/High rows provide updated size and source-comparison evidence. Listening and native acceptance remain pending.',
        'selection':'Current-plan job_key accepted, lossless/native hash and normalization provenance verified; one command and one effort where available for five representative families',
        'selected_recordings':len(selected),'selected_families':sorted({r['family'] for r in selected})}
    write(OUT/'encoding-comparison.json',report)
    print([(q,sum(r['bytes'] for r in rows if r['conversion']==q),round(min(r['decode']['snr_db'] for r in rows if r['conversion']==q),2)) for q in ('Low','Medium','High')])
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['decoder','compare']);a=p.parse_args()
    print(decoder()) if a.action=='decoder' else compare()
