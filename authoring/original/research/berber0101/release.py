"""Package the verified 0101 owner-precondition repair on final0100 without recooking art."""
from pathlib import Path
import hashlib,json,sys,zipfile
from pipeline import ROOT,OUT,BASE,BASE_SHA,sha,write

BASE_ZIP=ROOT/'output/berber_update_0_10_0/Berber-0.10.0.zip'
BASE_ZIP_SHA='086e656592d3e75d29d25c6237e2789f0b820476ad638ba573e7e3d77ab95088'
FINAL=OUT/'Berber_future_kingdom.sga'
ZIP=OUT/'Berber-0.10.1.zip'
NOTES='# Berber 0.10.1 - AI world-ownership crash fix\n\nFixed fatal SCAR error on elm_med_wild in BerberAI.Observe. World-owned\nobjects have no player owner; Entity_GetPlayerOwner raises an engine error\ninstead of returning nil. Check World_OwnsEntity before retrieving an owner.\nThe identical defect in FindDeposit is also fixed, allowing neutral trees,\nfood, gold and stone deposits to be considered without an owner lookup.\n\nNeutral relic/site/trade/sheep processing and normal player/enemy ownership\nremain intact. Only the military and economy SCAR members differ from final\n0.10.0. All other 8,371 members, including art, audio, tuning, voices, UV repairs,\ncontroller lifecycle and AI strategies, are unchanged.\n\nThe provided warnings.log confirms this exact fault. A prior match is not\nrequired to trigger it; the log does not establish cross-match contamination.\nStrict Lua5.1 regression fixtures reproduce the fault before the patch and pass\nafterwards. They also check gathering, neutral objectives, enemy contacts,\nfull ticks and normal game-over/new-match setup. Simulations are not native\nengine or multiplayer acceptance. No Content Editor recook was needed for\nthis two-file SCAR overlay. Garrison import and native retest remain pending.\n'
ACCEPTANCE='''# Berber 0.10.1 native acceptance - pending

Use a fresh process and fresh save, final 0.10.1 ZIP, normal Garrison Play,
Berber Game Mode + Tuning Pack. Choose Malians for every Berber slot.
Keep 0.9.1 as rollback. Naval/island maps are outside this candidate's scope.

1. Verify each lobby Easy/Intermediate/Hard/Hardest and every higher setting
   logs its intended `[BerberAI0100 p=...] profile=... originalDifficulty=...`.
   Berber slots must show nativeAI=disabled; English/other AI must remain active.
   Confirm higher settings have no inherited native resource multipliers.
2. Check normal and Nomad starts. Nomad workers must construct one initial TC.
   Verify gathering/depositing, continuous workers, housing, increasing farms,
   resource exhaustion recovery, repairs, expansion and all landmark ages.
3. Observe construction of age-limited Tents, nearby production, influence
   accumulation, reward villagers and assignment of those new villagers.
4. First alliance costs zero. A later switch from exactly 100 gold must succeed
   and leave zero, not reject or charge twice. Verify 150s shared cooldown,
   exclusive marker/bonuses, non-trader queue cancellation and trader survival.
5. Easy: Sanhaja + Tuareg. Intermediate: Market Zenata + Range archers ~2:1;
   kill archers and verify replacement before more cavalry and supported raids.
   Hard: Market/Marrakech Masmuda + Stable/Ribat Mehari ~1:1; kill a scout and
   verify replacement to two; inspect legal upgrades and avoid landmark duplicates.
   Hardest: scout mounted/armored/exposed-economy threats and observe stable,
   affordable alliance changes only after two strategic evaluations.
6. Verify normal train/build/research costs, time, population and prerequisites;
   failed placement and blocked queues must recover without spam or free units.
7. Observe fog-respecting scouting, sheep return, trade routes, relic pickup /
   deposit, Sacred Site capture and enabled victory-condition responses.
8. Cause a sustained income stall with a blocked economic action. Non-Easy aid
   must be <=100 total per180s; Easy gets zero. Inspect recovery log entries.
9. Test save/load without extra controllers or reset aid clocks. Defeat one AI;
   it must stop. Finish/restart a match without leaked rules or duplicated bonuses.
10. Repeat mixed-civ teams, FFA and maximum-player connected-land matches in
    actual multiplayer; test migration, sync, responsiveness and long play.

Minute logs include age, workers, alliance, scouts, core units and aid totals.
Record map, seed, lobby settings, game/Garrison versions, timestamps and exact
warnings.log. A scripted command log proves an attempted order; live unit counts
and the match itself must demonstrate that the native engine accepted it.
'''

def verify():
    report=json.loads((OUT/'release-validation.json').read_text())
    assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
    assert sha(FINAL)==report['sga_sha256'] and sha(ZIP)==report['zip_sha256']
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(z.namelist()))
        assert sum(Path(n).name.lower()=='garrison.json' for n in z.namelist())==1
        assert set(z.namelist())==set(report['zip_members'])
        for n,h in report['zip_members'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
        manifest=json.loads(z.read('garrison.json'))
        assert manifest['details']['version']=='0.10.1'
        assert manifest['members'][0]['sha256']==report['sga_sha256']
        assert manifest['details']['cover']=='cover.png'
        assert z.read('cover.png')==(ROOT/'assets/mod.png').read_bytes()
    return report

def build():
    assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
    member=json.loads((OUT/'member-sha256-proof.json').read_text())
    tests=json.loads((OUT/'test-validation.json').read_text())
    mcp=json.loads((OUT/'mcp-check.json').read_text())
    assert member['status']==tests['status']=='passed' and sha(FINAL)==member['archive_sha256']
    assert mcp['review']['unresolved_engine_calls']==[]
    for p,h in tests['source_sha256'].items():assert sha(ROOT/p)==h
    assert not ZIP.exists(),'Preserve existing delivery'
    with zipfile.ZipFile(BASE_ZIP) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='Berber_future_kingdom.sga'}
    manifest=json.loads(files['garrison.json']);old=json.loads(files['garrison.json'])
    manifest['members'][0]['sha256']=sha(FINAL)
    summary='Fix AI fatal SCAR error on world-owned trees and resource deposits; preserve 0.10.0 gameplay, art and voices'
    manifest['details'].update(version='0.10.1',updated='2026-10-18',summary=summary,changelog=summary,
      description=summary+'. Connected land normal/Nomad, teams/FFA candidate. Preserves final0.9.1 art/UV/audio. No voice installer.')
    assert manifest['bundle_key']==old['bundle_key'] and manifest['details']['id']==old['details']['id']
    manifest['details']['cover']='cover.png'
    files['cover.png']=(ROOT/'assets/mod.png').read_bytes()
    files['garrison.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    voice=json.loads(files['VOICE_COVERAGE.json']);voice['version']='0.10.1'
    voice['runtime_test']='Audio/speech members identical to final0.9.1. Fresh0.10.1 native acceptance pending.'
    files['VOICE_COVERAGE.json']=(json.dumps(voice,indent=2)+'\n').encode()
    files['START-HERE.txt']=b'''BERBER 0.10.1 - AI OWNERSHIP CRASH FIX
Close AoE4. Import Berber-0.10.1.zip in normal Garrison and enable it.
Launch with Garrison Play. Select Malians for Berber computers, Berber Game Mode
and Berber Tuning Pack. Start a fresh connected-land match. No voice installer.
Read AI_CHANGES.md and NATIVE_AI_ACCEPTANCE.md. Native testing is pending.
'''
    files['AI_CHANGES.md']=NOTES.encode();files['NATIVE_AI_ACCEPTANCE.md']=ACCEPTANCE.encode()
    with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(FINAL,'Berber_future_kingdom.sga')
        for n,raw in files.items():z.writestr(n,raw)
    hashes={n:hashlib.sha256(v).hexdigest() for n,v in files.items()};hashes['Berber_future_kingdom.sga']=sha(FINAL)
    report={'version':'0.10.1','status':'package_verified_native_acceptance_pending','zip':str(ZIP),
      'zip_bytes':ZIP.stat().st_size,'zip_sha256':sha(ZIP),'sga_sha256':sha(FINAL),'zip_members':hashes,
      'baseline':'final0.10.0','baseline_sha256':BASE_SHA,'changed_existing_members':member['changed_existing'],
      'new_members':member['new_members'],'unchanged_member_count':member['unchanged_member_count'],
      'art_audio_tuning_and_all22uvs_preserved':True,'lua51_tests':tests['tests'],
      'native_archive_crc_sha1':'passed','all_member_sha256':'passed','mcp':'reviewed; no unresolved engine names',
      'content_editor':'not run; SCAR-only overlay composed on validated native0100 archive',
      'garrison_import':'pending','native_gameplay':'pending','native_multiplayer':'pending','native_performance':'pending'}
    write(OUT/'release-validation.json',report)
    (OUT/'AI_CHANGES.md').write_text(NOTES,encoding='utf8')
    (OUT/'NATIVE_AI_ACCEPTANCE.md').write_text(ACCEPTANCE,encoding='utf8')
    (OUT/'SHA256SUMS.txt').write_text(sha(ZIP)+'  '+ZIP.name+'\n'+sha(FINAL)+'  '+FINAL.name+'\n',encoding='ascii')
    verify();print('PACKAGE_VERIFIED',ZIP.stat().st_size,'bytes',sha(ZIP))

if __name__=='__main__':
    if '--verify' in sys.argv:print('DELIVERY_VERIFIED',verify()['zip_sha256'])
    else:build()
