"""Berber1.0.0 isolated music composition on final0.11.0, never editable AI."""
from pathlib import Path
import hashlib,io,json,os,re,shutil,subprocess,sys,unittest,importlib.util,zipfile
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('legacy_pipeline',ROOT/'research/berber0110/pipeline.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
OUT=ROOT/'output/berber_update_1_0_0';WORK=OUT/'work'
BASE=ROOT/'output/berber_update_0_11_0/Berber_future_kingdom.sga'
BASE_ZIP=BASE.parent/'Berber-0.11.0.zip'
BASE_SHA='21932382a903257310697d47731c6c8f5d54a48d3ef2b575493fd6afcf018e1b'
BASE_ZIP_SHA='9ddd72c1739fa21ca4c0a6a577f3fa3e9d557bec04d713698334d25a390e61ce'
FINAL=OUT/'Berber_future_kingdom.sga';ZIP=OUT/'Berber-1.0.0.zip'
VERSION='1.0.0';GM='scar/winconditions/berber_future_kingdom_gm.scar'
sha=pipeline.sha;write=pipeline.write;run=pipeline.run
INSTRUCTIONS="""BERBER DYNASTY1.0.0 - import candidate

Contains the complete final0.11.0 civilization and approved build-order AI,
with48 instrumental music tracks across Dark,Feudal,Castle,Imperial ages.
Three themes per age, each Peace/Skirmish/War/MassiveBattle. All existing
AI,art,voices,tuning and22 repairedUV models are preserved exactly.

Close AoE4. Import Berber-1.0.0.zip into normal Garrison, enable and Play.
Select Berber Game Mode AND Berber Tuning Pack; select Malians for Berber.
This updates the same installed mod identity. Retained0.11.0 ZIP is rollback.
Read AI_BUILD_ORDER.md and NATIVE_AI_ACCEPTANCE.md for the inherited AI scope.

Music follows the local player's current age and combat activity automatically.
A small upper-right Music - / percentage / + panel changes custom music gain
in1percent steps,0to100,default3. Zero mutes only music; + resumes it.
This gain is independent of AoE4 native audio sliders. Unit voices retain
existing behavior. No manual theme/intensity/debug/WAV controls are included.

Combat uses the accepted Test2 sensor: unique non-scout damage-dealing enemy
or local-player attackers over8seconds;1-5Skirmish,6-19War,20+Massive.
Escalation needs1stable second; deescalation12seconds after activity expires.
Peace rotates themes after two loops. New ages, themes and combat intensities
choose an entry at10seconds,25percent or40percent of original duration,
avoiding consecutive identical entries. First10seconds are absent afterward,
including loops. Only initial DarkAge AtlasPeace starts at original beginning.
Mute/retry/restore retain non-opening selection; interrupted opening is retired.
Crossfades/sample-accurate seams are not promised by this transport.

New audio files omit cover images and unnecessary tags. Source masters remain
outside the mod. MP3 source originals are retained; each edit is encoded once
from original decoded audio, never through an intermediate lossy file. No unit
voices or model/texture quality were reduced. Existing baseline assets are
retained; unknown references are not treated as proof of unused content.

Archive/ZIP integrity,all-member hashes,Lua/static/MCP checks are offline gates.
User confirmed prior DarkAgeTest2 playback. New1.0.0 import,all-age transitions,
compactHUD,pause/speed/save/load,multiplayer and inheritedAI native behavior
remain separate acceptance gates. Test a fresh match and age through all4ages.
"""


def tests():
    sys.path.insert(0,str(SOURCE));import test_music,test_audio
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(m) for m in (test_music,test_audio)])
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (OUT/'tests.log').write_text(stream.getvalue(),encoding='utf8');assert result.wasSuccessful(),stream.getvalue()
    write(OUT/'test-validation.json',dict(status='passed',tests=result.testsRun,sources={p.name:sha(p) for p in SOURCE.glob('*.scar')},native='pending'))
    return result.testsRun


def stage():
    assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
    from audio_prepare import prepare
    members=prepare(ROOT,WORK,OUT)
    assert len(members)==145
    payload=WORK/'payload';payload.mkdir(parents=True,exist_ok=True)
    pipeline.extract(BASE,WORK/'baseline',[GM,'scar/garrison/garrison.scar','scar/berber_scripted_speech.scar'])
    assert sha(WORK/'baseline/scar/garrison/garrison.scar')==sha(SOURCE/'fixtures/garrison.scar')
    raw=(WORK/'baseline'/GM).read_bytes();needle=b'import("ai/berber_ai_controller.scar")'
    assert raw.count(needle)==1 and b'berber_music.scar' not in raw
    eol=b'\r\n' if b'\r\n' in raw else b'\n'
    target=payload/GM;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw.replace(needle,needle+eol+b'import("music/berber_music.scar")'));members[GM]=target
    for p in SOURCE.glob('*.scar'):
        target=payload/'scar/music'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        members['scar/music/'+p.name]=target
    assert len(members)==149
    write(OUT/'payload-proof.json',dict(baseline_sha256=BASE_SHA,members={n:sha(p) for n,p in members.items()},game_mode_recipe='Frozen0110 bytes plus one music import; no editable AI source consumed'))
    old=json.loads((BASE.parent/'archive-inventory.json').read_text())
    suspicious=[m for m in old['members'] if re.search(r'\.(blend|psd|bak|tmp|log|zip|py)$',m['path'],re.I)]
    write(OUT/'size-audit.json',dict(baseline_bytes=BASE.stat().st_size,baseline_zip_bytes=BASE_ZIP.stat().st_size,
        largest_baseline_members=sorted(old['members'],key=lambda x:x['size'],reverse=True)[:25],authoring_suffix_candidates=suspicious,
        removal_decision='No baseline member removed: runtime references not proven unused. All features preserved.',
        reductions=['Pack only playbackMP3s, not source masters or debug referenceWAV','Strip music embedded artwork/metadata','No redundant test control module','ZIPDeflatelevel9'],native_audio_quality='New audio native acceptance pending'))
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
        endpoint_methods='bed,stopBed,setBedGain defined in exact frozen0110 loader; never music session/stop/pulse',
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
    m['details'].update(name='Berber Dynasty',version=VERSION,
        summary='Berber1.0.0: approved0.11.0 AI plus48 adaptive tracks across all four ages and compact music volume controls.',
        description='Berber civilization with0.11.0 AI, original art and voices,48 instrumental music tracks and age/combat-aware soundtrack. Import candidate: new age switching and compact HUD require native acceptance.',
        changelog='Adds all-age adaptive music and compact +/-volume UI. Existing0.11.0 AI/gameplay/art/voices retained byte-identically. Embedded music artwork omitted; high ZIP compression. See START-HERE.txt.',cover='cover.png')
    files['garrison.json']=(json.dumps(m,indent=2)+'\n').encode()
    files['START-HERE.txt']=INSTRUCTIONS.encode()
    files['RELEASE_NOTES.md']=INSTRUCTIONS.encode()
    audio=json.loads((OUT/'audio-manifest.json').read_text())
    files['MUSIC_CATALOG.md']=(SOURCE/'MUSIC_CATALOG.md').read_bytes()
    with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.write(FINAL,'Berber_future_kingdom.sga')
        for n,raw in files.items():z.writestr(n,raw)
    expected={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()};expected['Berber_future_kingdom.sga']=sha(FINAL)
    write(OUT/'release-validation.json',dict(status='candidate_native_acceptance_pending',version=VERSION,
        zip=str(ZIP),zip_bytes=ZIP.stat().st_size,zip_sha256=sha(ZIP),sga_bytes=FINAL.stat().st_size,sga_sha256=sha(FINAL),zip_members=expected,
        music_tests=count,baseline_sha256=BASE_SHA,ai_sources_used=False,existing_ai_members_unchanged=True,
        original_music_tracks=48,playback_variants=145,volume_controls='Two buttons,1percent steps,0to100,default3;0mutes onlymusic',
        retained_dark_age_test='User confirmedTest2 works;1.0.0 extends it',
        native_gameplay='Inherited0.11.0 gate remains pending',native_audio='New age routing/compactHUD pending',native_multiplayer='pending'))
    (OUT/'RELEASE_NOTES.md').write_text(INSTRUCTIONS,encoding='utf8')
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
        with zipfile.ZipFile(BASE_ZIP) as bz:assert z.read('cover.png')==bz.read('cover.png')
    return r

def cleanup():
    r=verify();physical=OUT.resolve();target=WORK.resolve()
    assert physical==Path('F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output/berber_update_1_0_0')
    assert target==physical/'work' and not physical.is_junction() and not WORK.is_junction() and not WORK.is_symlink()
    rows=[]
    for directory,folders,files in os.walk(target,followlinks=False):
        for name in folders+files:
            p=Path(directory)/name;st=p.stat(follow_symlinks=False)
            assert p.is_relative_to(target) and not st.st_file_attributes&0x400 and not p.is_symlink()
            if p.is_file():rows.append(dict(path=str(p),bytes=p.stat().st_size))
    protected_paths=[BASE,BASE_ZIP,FINAL,ZIP,*SOURCE.rglob('*'),
        ROOT/'output/berber_dark_age_music_test_2/Berber-Dark-Age-Music-Test-2.zip',
        ROOT/'output/berber_dark_age_music_test_2/Berber_future_kingdom.sga',
        *list((ROOT/'art/music_dark_age_20261018').rglob('*')),
        *list((ROOT/'art/music_next_ages_20261018').rglob('*'))]
    protected={str(p):sha(p) for p in protected_paths if p.is_file()}
    total=sum(x['bytes'] for x in rows)
    write(OUT/'cleanup-plan.json',dict(absolute_target=str(target),files=rows,bytes_before=total,protected_hashes=protected,
        rebuild='Frozen0110 + retained48 music originals and scripts; allMP3 variants regenerated from originalFLAC/WAV/MP3; no external cache deletion'))
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
        members=stage();count=tests();evidence();compose(members);package(count);print('PACKAGE_VERIFIED',sha(ZIP))
    elif action=='verify':print('DELIVERY_VERIFIED',verify()['zip_sha256'])
    elif action=='cleanup':cleanup()
