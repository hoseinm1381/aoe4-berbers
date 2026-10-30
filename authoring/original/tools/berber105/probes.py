"""Real source preparation and native composition probes, outside delivery."""
from pathlib import Path
import copy,json,struct,subprocess,sys,wave,zipfile
import workspace as w
import build,uv,audio_prepare

def main():
    work=w.OUT/'work/probes';work.mkdir(parents=True,exist_ok=True)
    hashes=w.archive_hashes(w.BASE);w.save(w.HERE/'baseline-members.json.gz',hashes)
    names=list(hashes);frozen=w.HERE/'frozen';frozen.mkdir(exist_ok=True)
    selected=[n for n in names if n.endswith('.scar')]
    selected+=list({r['member'] for r in w.read(w.HERE/'uv-donors.json')['models']})
    selected += [n for n in names if n.startswith('attrib/attachments/') and 'bind_villager_' in n]
    selected += [n for n in names if n.startswith('attrib/ai/')]
    for at in range(0,len(selected),45):
        args=[w.ARCH,'extract',w.BASE,frozen]
        for n in selected[at:at+45]:args+=['--member',n]
        w.run(*args)
    for name in selected:assert w.sha(frozen/name)==hashes[name],name
    sys.path.insert(0,str(w.EXT));from garrison_shared import relic_chunky as rc,rgd
    geometry=[];overrides={}
    models=w.read(w.HERE/'uv-donors.json')['models']
    chosen=[next(r for r in models if '/bt026/' in r['member']),next(r for r in models if '/bt026/' not in r['member'] and '/bb026/' not in r['member'])]
    for r in chosen:
        name=r['member'];baseline=(frozen/name).read_bytes();doc,groups=uv.groups(baseline)
        replacements={};damaged=0
        for g in groups:
            buf=bytearray(g['chunk'].payload)
            # Real native position edit plus a simulated stale-export UV defect.
            x=struct.unpack_from('<f',buf,16)[0];struct.pack_into('<f',buf,16,x+0.001)
            struct.pack_into('<2e',buf,28,float('inf'),float('inf'));damaged+=1
            replacements[g['chunk'].offset]=bytes(buf)
        raw=rc.rebuild(doc,lambda c:replacements.get(c.offset))
        assert any(g['bad'] for g in uv.groups(raw)[1]),'Unprotected stale export must fail finite UV checks'
        repaired,proof=build.protect(name,raw,baseline)
        after=uv.groups(repaired)[1];assert all(not g['bad'] for g in after)
        assert struct.unpack_from('<f',after[0]['chunk'].payload,16)[0]!=struct.unpack_from('<f',groups[0]['chunk'].payload,16)[0]
        target=work/'payload'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(repaired);overrides[name]=str(target)
        geometry.append({'member':name,'real_position_edit_preserved':True,'unprotected_uv_failure_observed':True,'protected_uv_passed':True,'corrections':proof})
    voice=next(n for n in selected if n.startswith('attrib/attachments/') and 'bind_villager_a1_' in n)
    baseline=(frozen/voice).read_bytes();doc=rgd.read(baseline)
    nodes=[n for _,n in rgd.flatten(doc.nodes) if n.key=='attachment_speaker_code'];assert len(nodes)==52 and all(n.value=='' for n in nodes)
    nodes[0].value='stale_native_speaker';damaged=build.encode(doc,rgd)
    assert any(n.value!='' for _,n in rgd.flatten(rgd.read(damaged).nodes) if n.key=='attachment_speaker_code')
    fixed,proof=build.protect(voice,damaged,baseline)
    assert all(n.value=='' for _,n in rgd.flatten(rgd.read(fixed).nodes) if n.key=='attachment_speaker_code')
    # Lua parser runs on the actual packaged sources, and a scratch edit checks
    # that the same composition route accepts deliberate script changes.
    from lupa.lua53 import LuaRuntime
    lua=LuaRuntime();compile=lua.eval('function(s,n) local f,e=load(s,n);return f~=nil,e end')
    for n in selected:
        if n.endswith('.scar'):
            ok,error=compile((frozen/n).read_text(encoding='utf-8-sig'),n);assert ok,(n,error)
    gm='scar/winconditions/berber_future_kingdom_gm.scar';text=(frozen/gm).read_text();assert 'import("ai/berber_ai_controller.scar")' not in text
    edited=work/'gm.scar';edited.write_text(text+'\n-- Disposable 1.0.5 source-edit verification.\n');overrides[gm]=str(edited)
    w.save(work/'overrides.json',overrides)
    build.compose(work/'scoped-edit.sga',work/'overrides.json')
    selected_audio,candidates,metadata=audio_prepare.inventory(w.ROOT);assert len(selected_audio)==48
    music=selected_audio['DA_A1'];music_hash=w.sha(music);sample=work/'music-sample.mp3'
    subprocess.run(['ffmpeg','-v','error','-i',str(music),'-t','3','-ar','48000','-ac','2','-map_metadata','-1','-b:a','192k',str(sample)],check=True,capture_output=True)
    decoded=audio_prepare.decode(sample);assert len(decoded)>0
    source=next(p for p in w.walk(w.ROOT/'art/voices_0_6_0/masters') if p.suffix.lower()=='.wav');voice_hash=w.sha(source)
    voice_sample=work/'voice-sample.wav'
    subprocess.run(['ffmpeg','-v','error','-i',str(source),'-ar','48000','-ac','1','-c:a','pcm_s16le',str(voice_sample)],check=True,capture_output=True)
    with wave.open(str(voice_sample)) as f:assert (f.getnchannels(),f.getframerate(),f.getsampwidth())==(1,48000,2)
    assert w.sha(music)==music_hash and w.sha(source)==voice_hash
    if (w.OUT/'inventory.json.gz').exists():
        inventory=w.read(w.OUT/'inventory.json.gz');sourcehash={r['path']:r['sha256'] for r in inventory}
        for p in [*selected_audio.values(),source]:assert w.sha(p)==sourcehash[str(p)]
    report={'status':'passed','baseline_members':len(hashes),'frozen_resources':len(selected),'native_geometry_edits':geometry,'speaker_override_red_green':proof,'lua_syntax_checked':sum(n.endswith('.scar') for n in selected),'music_source_slots':48,'music_encode_full_decode':'passed','voice_pcm_encode':'passed','native_runtime':'not run'}
    w.save(w.OUT/'development-probes.json',report);print('DEVELOPMENT_PROBES_PASSED',flush=True)
if __name__=='__main__':main()
