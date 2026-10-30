"""Compose a music-only test overlay on frozen0100, never editable AI sources."""
from pathlib import Path
import hashlib,io,json,os,re,shutil,stat,subprocess,sys,unittest,warnings,zipfile

ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research/berber0100'))
import pipeline
OUT=ROOT/'output/berber_dark_age_music_test_2';WORK=OUT/'work'
BASE=ROOT/'output/berber_update_0_10_0/Berber_future_kingdom.sga'
BASE_ZIP=BASE.parent/'Berber-0.10.0.zip'
BASE_SHA='6cd768459540576754946f47f51f3e93ef6e974814149ea9f01d5cc93206de0c'
BASE_ZIP_SHA='086e656592d3e75d29d25c6237e2789f0b820476ad638ba573e7e3d77ab95088'
FINAL=OUT/'Berber_future_kingdom.sga';ZIP=OUT/'Berber-Dark-Age-Music-Test-2.zip'
VERSION='0.10.0-music.2';GM='scar/winconditions/berber_future_kingdom_gm.scar'
sha=pipeline.sha;write=pipeline.write;run=pipeline.run

INSTRUCTIONS='''BERBER DYNASTY - DARK AGE MUSIC TEST 2 (candidate)

This is a complete Berber test ZIP composed on the frozen0.10.0 release.
No editable/current AI source was used. Existing AI, tuning, visuals,22 UV fixes
and unit voices remain byte-identical. This test intentionally uses the Dark
Age music catalog in every game age. Naval/AI redesign work is outside scope.

INSTALL
1. Close AoE4. Import Berber-Dark-Age-Music-Test-2.zip into normal Garrison.
   This has the SAME Berber bundle/mod identity: it temporarily updates/replaces
   the installed Berber copy. Do not enable overlapping old copies. Original
   Berber-0.10.0.zip remains your rollback; reimport it to remove this test.
2. Enable and launch with Garrison Play. Select Berber Game Mode AND Berber
   Tuning Pack. Select Malians for Berber. Use a fresh solo land-map match.
3. The upper-right DARK AGE MUSIC TEST panel starts Auto/Atlas/Peace/3% volume.
   This is separate from AoE4's native Music/Master sliders.

CONTROLS
A/B/C choose Atlas Dawn / Caravan of the Dunes / Embers of the Ancestors.
Peace / Skirmish / War / Massive force MANUAL playback of that arrangement.
Auto battle returns to adaptive MP3 music. The theme stays through battles;
in uninterrupted peace, it rotates after approximately two complete loops.
Volume +/- uses the shipped setBedGain endpoint; test whether it works live.
Mute/resume affects music only. Native music stops the custom bed and restores
AoE4 music. WAV reference forces manual Atlas Peace from stereo48k16PCM WAV.
Compare it with A + Peace (MP3) if you hear silence, glitches or codec problems.

AUTO BATTLE TEST
Counts UNIQUE non-scout attackers that dealt damage in the last8seconds in
combat involving the local player and an enemy. Scout attackers, repair events,
world damage and unrelated fights are excluded. This is a damage-activity proxy,
not a precise attacks-per-second sensor.
1-5 attackers=Skirmish;6-19=War;20+=Massive;0=Peace. Escalation requires1second
stable demand; de-escalation requires12seconds stable lower demand, on top of
the8second sighting window. Music does not reveal remote third-party fights.
Every track change chooses a new random entry at 10 seconds,25% or40%.
Only initial Atlas Peace at game start plays from the beginning.
Retries, mute/resume and restore retain the selected entry. New intensity or
theme selections choose again, including peace. Consecutive selections avoid
repeating the same entry. WAV reference uses a fixed10-second entry. The first10seconds are removed from all subsequent playback. The remainder
is rotated: entry to end, then10seconds to entry, then loop. The HUD shows entry%.
Entry variants are encoded once from lossless masters at stereo48k192kbps.
Switches replace/restart the selected recording. No crossfade or sample-aligned
transition is promised. The HUD says 'submitted', not 'audible playback proven'.

PLEASE REPORT
- Does the HUD appear, and do you hear custom music instead of native music?
- Try all12 tracks: A/B/C times Peace/Skirmish/War/Massive. Give missing slot IDs.
- Is the WAV reference audible when MP3 is not? Are quality and volume acceptable?
- Do Volume +/- and Mute work without affecting villager/unit voices?
- Does a small fight trigger Skirmish, a larger fight War, and a huge fight Massive?
  Does scout-only harassment remain quiet? Does peace return too soon/too late?
- Do track changes click, gap, sound abrupt, restart too often, or loop badly?
- Check pause/resume, Native music, menu exit and a second fresh match.
- Provide map, match settings, game/Garrison versions and a HUD screenshot.
  Keep warnings.log and relevant %LOCALAPPDATA%/Garrison/events game/agent/audio
  logs. Search warnings.log for BERBER_MUSIC_TEST. Do not send unrelated logs.

Static/Lua/archive/ZIP checks are separate from native acceptance. Test1 music/HUD were user-confirmed working. Test2 random-entry transitions,
save/load and multiplayer remain pending native acceptance.
No installer or game-file replacement is required. Runtime belongs to Garrison.
'''

def tests():
    sys.path.insert(0,str(SOURCE));import test_music
    suite=unittest.defaultTestLoader.loadTestsFromModule(test_music);stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (OUT/'tests.log').write_text(stream.getvalue(),encoding='utf8')
    assert result.wasSuccessful(),stream.getvalue()
    write(OUT/'test-validation.json',dict(status='passed',tests=result.testsRun,
        engine='Lupa Lua5.1 with mocked engine; Garrison endpoint checked separately',
        sources={p.name:sha(p) for p in SOURCE.glob('*.scar')},native='pending'))
    return result.testsRun

def stage():
    assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
    payload=WORK/'payload';payload.mkdir(parents=True,exist_ok=True)
    pipeline.extract(BASE,WORK/'baseline',[GM,'scar/garrison/garrison.scar','scar/berber_scripted_speech.scar'])
    raw=(WORK/'baseline'/GM).read_bytes();needle=b'import("ai/berber_ai_controller.scar")'
    assert raw.count(needle)==1 and b'berber_dark_age_test.scar' not in raw
    eol=b'\r\n' if b'\r\n' in raw else b'\n'
    path=payload/GM;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw.replace(needle,needle+eol+b'import("music/berber_dark_age_test.scar")'))
    members={GM:path}
    for p in SOURCE.glob('*.scar'):
        target=payload/'scar/music'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        members['scar/music/'+p.name]=target
    catalog=json.loads((ROOT/'art/music_dark_age_20261018/catalog.json').read_text())
    proof=json.loads((ROOT/'art/music_dark_age_20261018/size-validation.json').read_text())
    for track in proof['tracks']:
        source=ROOT/'art/music_dark_age_20261018'/track['mp3_path'];assert sha(source)==track['mp3_sha256']
        name='audio/berber_dark_age/da_'+track['slot'].lower()+'.mp3'
        target=payload/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);members[name]=target
    intro=payload/'audio/berber_dark_age/intro_a1.mp3';shutil.copyfile(payload/'audio/berber_dark_age/da_a1.mp3',intro);members['audio/berber_dark_age/intro_a1.mp3']=intro
    from entry_audio import add_entries
    members.update(add_entries(ROOT,WORK,payload,proof,sha,write))
    first=proof['tracks'][0];source=ROOT/'art/music_dark_age_20261018'/first['flac_path']
    assert sha(source)==first['flac_sha256']
    reference=payload/'audio/berber_dark_age/reference_a1.wav'
    if True: # regenerate source WAV; prior failed staging may have trimmed it
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),'-map','0:a:0',
            '-map_metadata','-1','-c:a','pcm_s16le','-ar','48000','-ac','2',str(reference)],check=True)
    import wave
    with wave.open(str(reference),'rb') as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(48000,2,2)
        assert hashlib.sha256(w.readframes(w.getnframes())).hexdigest()==first['pcm_sha256']
    from entry_audio import rotate_pcm
    with wave.open(str(reference),'rb') as w: pcm=w.readframes(w.getnframes())
    with wave.open(str(reference),'wb') as w:
        w.setparams((2,2,48000,0,'NONE','not compressed'));w.writeframes(rotate_pcm(pcm,480000))
    members['audio/berber_dark_age/reference_a1.wav']=reference
    assert len(members)==42
    write(OUT/'payload-proof.json',dict(baseline_sha256=BASE_SHA,members={n:sha(p) for n,p in members.items()},
        game_mode_recipe='Frozen0100 game-mode bytes plus one music import; no source AI consumed',
        reference_pcm_sha256=first['pcm_sha256']))
    return members

def evidence():
    api=Path('E:/Games/steamapps/common/Age of Empires IV/scardocs/api/Essence_ScarFunctions.api')
    signatures={}
    for i,line in enumerate(api.read_text(encoding='utf8').splitlines(),1):
        m=re.match(r'(\w+)\(',line)
        if m:signatures[m[1]]=dict(file=str(api),line=i,signature=line)
    for f in (pipeline.LIB/'scripts').rglob('*.scar'):
        for i,line in enumerate(f.read_text(encoding='utf8',errors='replace').splitlines(),1):
            m=re.match(r'\s*function\s+(\w+)\s*\(',line)
            if m:signatures.setdefault(m[1],dict(file=str(f),line=i,signature=line.strip()))
    text='\n'.join(p.read_text() for p in SOURCE.glob('*.scar'));text=re.sub(r'--[^\n]*','',text)
    calls=set(re.findall(r'(?<![.\w])([A-Z]\w*)\s*\(',text))
    defined=set(re.findall(r'function\s+([A-Z]\w*)\s*\(',text));calls-=defined
    unresolved=sorted(calls-signatures.keys());assert not unresolved,unresolved
    write(OUT/'official-api-evidence.json',dict(status='passed',contracts={n:signatures[n] for n in sorted(calls)},
        unresolved=unresolved,shared_endpoint=sha(WORK/'baseline/scar/garrison/garrison.scar'),
        speech_session_owner=sha(WORK/'baseline/scar/berber_scripted_speech.scar'),
        endpoint_methods='bed,stopBed,setBedGain defined in exact frozen0100 loader; never music session/stop/pulse',
        ui_analogue='Installed official gameplay/diplomacy.scar:38-40,1249,1258-1280'))

def compose(members):
    listing=WORK/'set-members.txt';listing.write_text('\n'.join(n+'='+str(p.resolve()) for n,p in members.items())+'\n')
    assert not FINAL.exists();run(pipeline.ARCH,'set-members',BASE,listing,FINAL,'--alias','data')
    inventory=json.loads(run(pipeline.ARCH,'list',FINAL,'--verify'));assert inventory['archive']['verification']['verified']
    write(OUT/'archive-inventory.json',inventory)
    old=json.loads((BASE.parent/'member-sha256-proof.json').read_text());assert old['archive_sha256']==BASE_SHA
    names=[m['path'] for m in inventory['members']]
    new,method=pipeline.archive_hashes(FINAL,WORK/'readback',names)
    before=old['after'];assert set(before)<=set(new)
    changed=[n for n in before if before[n]!=new[n]];assert changed==[GM],changed
    assert set(new)-set(before)==set(members)-{GM}
    for n,p in members.items():assert new[n]==sha(p)
    protected=[n for n in before if n.startswith(('scar/ai/','art/','audio/','attrib/')) or 'speech' in n]
    assert all(new[n]==before[n] for n in protected)
    write(OUT/'member-sha256-proof.json',dict(status='passed',baseline_sha256=BASE_SHA,archive_sha256=sha(FINAL),
        before=before,after=new,changed_existing=changed,new_members=sorted(set(new)-set(before)),
        unchanged_existing_members=len(before)-1,all_existing_ai_art_audio_tuning_preserved=True,
        method=method,native_verification=inventory['archive']['verification']))

def package(count):
    assert not ZIP.exists()
    with zipfile.ZipFile(BASE_ZIP) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='Berber_future_kingdom.sga'}
    m=json.loads(files['garrison.json']);m['members'][0]['sha256']=sha(FINAL)
    m['details'].update(name='Berber Dynasty - Dark Age Music TEST',version=VERSION,
        summary='Test2: random first-half combat entries, automatic battles, manual HUD; new native acceptance pending',
        description='Frozen Berber0.10.0 plus isolated music test. Existing AI/art/voices unchanged. Read START-HERE.txt.',
        changelog='All transitions random entries at10seconds/25/40percent; Test1 preserved; no AI redesign or tuning edits.',cover='cover.png')
    files['garrison.json']=(json.dumps(m,indent=2)+'\n').encode()
    files['START-HERE.txt']=INSTRUCTIONS.encode();files['MUSIC_TEST_REPORT.txt']=INSTRUCTIONS.encode()
    with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(FINAL,'Berber_future_kingdom.sga')
        for n,raw in files.items():z.writestr(n,raw)
    expected={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()};expected['Berber_future_kingdom.sga']=sha(FINAL)
    write(OUT/'release-validation.json',dict(status='candidate_native_acceptance_pending',version=VERSION,
        zip=str(ZIP),zip_bytes=ZIP.stat().st_size,zip_sha256=sha(ZIP),sga_sha256=sha(FINAL),zip_members=expected,
        tests=count,baseline_sha256=BASE_SHA,ai_sources_used=False,existing_ai_members_unchanged=True,
        raw_audio_added_bytes=sum(p.stat().st_size for p in (WORK/'payload/audio/berber_dark_age').iterdir()),
        native_gameplay='pending',native_audio='pending',native_hud='pending',native_multiplayer='pending'))
    (OUT/'MUSIC_TEST_REPORT.txt').write_text(INSTRUCTIONS,encoding='utf8')
    (OUT/'SHA256SUMS.txt').write_text(sha(ZIP)+'  '+ZIP.name+'\n'+sha(FINAL)+'  '+FINAL.name+'\n')
    verify()

def verify():
    r=json.loads((OUT/'release-validation.json').read_text());assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
    assert sha(FINAL)==r['sga_sha256'] and sha(ZIP)==r['zip_sha256']
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(r['zip_members']) and len(z.namelist())==len(set(z.namelist()))
        assert sum(Path(n).name.lower()=='garrison.json' for n in z.namelist())==1
        for n,h in r['zip_members'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
        m=json.loads(z.read('garrison.json'));assert m['details']['version']==VERSION
        assert m['members'][0]['sha256']==r['sga_sha256'] and m['details']['cover']=='cover.png'
        assert z.read('cover.png')==(ROOT/'assets/mod.png').read_bytes()
    return r

def cleanup():
    r=verify();physical=OUT.resolve();target=WORK.resolve()
    assert physical==Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/berber_dark_age_music_test_2')
    assert target==physical/'work' and not physical.is_junction() and not WORK.is_junction() and not WORK.is_symlink()
    rows=[]
    for directory,folders,files in os.walk(target,followlinks=False):
        for name in folders+files:
            p=Path(directory)/name;st=p.stat(follow_symlinks=False)
            assert p.is_relative_to(target) and not st.st_file_attributes&0x400 and not p.is_symlink()
            if p.is_file():rows.append(dict(path=str(p),bytes=p.stat().st_size))
    protected={str(p):sha(p) for p in [BASE,BASE_ZIP,FINAL,ZIP,*SOURCE.rglob('*'),
        ROOT/'output/berber_dark_age_music_test_1/Berber-Dark-Age-Music-Test-1.zip',
        ROOT/'output/berber_dark_age_music_test_1/Berber_future_kingdom.sga',
        ROOT/'art/music_dark_age_20261018/lossless/DA_A1.flac',
        ROOT/'art/music_dark_age_20261018/catalog.json',ROOT/'art/music_dark_age_20261018/size-validation.json',
        *list((ROOT/'art/music_dark_age_20261018/compact_mp3').glob('*.mp3')),*list((ROOT/'art/music_dark_age_20261018/lossless').glob('*.flac'))] if p.is_file()}
    total=sum(x['bytes'] for x in rows)
    write(OUT/'cleanup-plan.json',dict(absolute_target=str(target),files=rows,bytes_before=total,protected_hashes=protected,
        rebuild='Frozen0100 + retained music source/config/scripts; decoded WAV reference regenerated from losslessA1; no external cache deletion'))
    for p,h in protected.items():assert sha(p)==h
    shutil.rmtree(target)
    assert not target.exists()
    for p,h in protected.items():assert sha(p)==h
    verify()
    write(OUT/'cleanup-report.json',dict(status='passed',bytes_before=total,bytes_after=0,bytes_reclaimed=total,
        drive='F:',protected_inputs_rehashed=len(protected),temporary_cache_retained=0,post_cleanup_zip_and_hashes='passed'))
    r.update(cleanup='passed',cleanup_bytes_reclaimed=total);write(OUT/'release-validation.json',r)
    print('CLEANUP_PASSED',total,'bytes reclaimed')

if __name__=='__main__':
    action=sys.argv[1]
    if action=='build':
        count=tests();members=stage();evidence();compose(members);package(count);print('PACKAGE_VERIFIED',sha(ZIP))
    elif action=='verify':print('DELIVERY_VERIFIED',verify()['zip_sha256'])
    elif action=='cleanup':cleanup()
