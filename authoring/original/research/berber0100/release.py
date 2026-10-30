"""Package the verified 0100 SCAR overlay on final091 without recooking art."""
from pathlib import Path
import hashlib,json,sys,zipfile
from pipeline import ROOT,OUT,BASE,BASE_SHA,sha,write

BASE_ZIP=ROOT/'output/berber_update_0_9_1/Berber-0.9.1.zip'
BASE_ZIP_SHA='8e2b1ad7b05ef596bd23b92f0b84f67c4afae570e4f7ce07ee73df9d80952b78'
FINAL=OUT/'Berber_future_kingdom.sga'
ZIP=OUT/'Berber-0.10.0.zip'
NOTES='''# Berber 0.10.0 - scripted AI candidate

Import with normal Garrison, enable, launch with Garrison Play. Select Malians
for Berber computer players, Berber Game Mode AND Berber Tuning Pack.
Other civilizations retain native AI. Use a fresh match on a connected land map.

| Lobby difficulty | Strategy | Villager target | Decision interval |
|---|---|---:|---:|
| Easy | Sanhaja camel archers + Tuareg spearmen, defensive | 60 | 8s |
| Intermediate | Zenata Lancers + normal archers, 2:1 raids | 80 | 5s |
| Hard | Masmuda crossbowmen + Mehari, 1:1; two scouts and upgrades | 100 | 3s |
| Hardest and higher | Adaptive alliances, combined armies and siege | 110 | 2s |

Native Berber AI is disabled; the SCAR controller handles construction, normal
and Nomad starts, economy, housing/farms, expansion, repairs, garrisoning,
research/landmarks, scouting, trade, relic/site orders and combat decisions.
Army ratios are targets, not free units; costs, prerequisites, production times,
population and fog remain engine-controlled. Naval economy/fleets are deferred.
Hardest and higher use Expert's normal native difficulty setting internally,
while retaining the original lobby value for selecting the scripted profile.

Markets train alliance troops; Archery Ranges supply Intermediate's archers;
Stables/Ribat supply Mehari. Tribal Tents respect the 1/2/3/4 age caps and are
placed near production within their 20-unit influence range. Alliances use
normal ability commands, preserving bonuses and queue/cooldown behavior.
The old manual gold deduction after a paid alliance ability has been removed:
first pick remains free and the ability's existing modifier charges 100 per
later switch once. Native cost/cooldown acceptance is still required.

Recovery aid applies to Intermediate and above only: after 60 seconds without
economic income and a specific blocked economic action, grant only its missing
resources, at most 100 TOTAL every 180 seconds. No lifetime cap. Easy gets none.
No free combat units, instant research, stat bonuses or map reveal are added.

All existing 0.9.1 art, audio and tuning records are byte-identical, including
all 22 UV repairs and the inherited 0.9.0 landmarks. The shipped speech scripts
remain intact. Only the game-mode import and alliance cost callback change;
seven new AI SCAR files are added.

## Evidence and acceptance

The Lua5.1 regression suite passes, including abstract eight-slot normal/Nomad control-flow
runs of 30 simulated minutes each. These mocks do NOT emulate native combat,
pathfinding, command validation or multiplayer. Installed official API/wrapper
provenance and static/MCP checks are recorded alongside the ZIP. Static tuning
checks have zero errors; inherited locale/version warnings remain unchanged.

Content Editor cook, Garrison import, native commands/costs, lobby difficulty
values, visual/play balance, save/load, multiplayer synchronization and maximum
player performance have NOT been tested for this release. This is a CANDIDATE.
The AoE4 MCP used here provides reference/validation tools, not a game runner.

Read NATIVE_AI_ACCEPTANCE.md before treating the AI as qualified.
'''
ACCEPTANCE='''# Berber 0.10.0 native acceptance - pending

Use a fresh process and fresh save, final 0.10.0 ZIP, normal Garrison Play,
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
        assert set(z.namelist())==set(report['zip_members'])
        for n,h in report['zip_members'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
        manifest=json.loads(z.read('garrison.json'))
        assert manifest['details']['version']=='0.10.0'
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
    summary='Scripted Berber AI with four difficulty strategies, Tribal Tents, alliances and unique units; native acceptance pending'
    manifest['details'].update(version='0.10.0',updated='2026-10-18',summary=summary,changelog=summary,
      description=summary+'. Connected land normal/Nomad, teams/FFA candidate. Preserves final0.9.1 art/UV/audio. No voice installer.')
    assert manifest['bundle_key']==old['bundle_key'] and manifest['details']['id']==old['details']['id']
    manifest['details']['cover']='cover.png'
    files['cover.png']=(ROOT/'assets/mod.png').read_bytes()
    files['garrison.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    voice=json.loads(files['VOICE_COVERAGE.json']);voice['version']='0.10.0'
    voice['runtime_test']='Audio/speech members identical to final0.9.1. Fresh0.10.0 native acceptance pending.'
    files['VOICE_COVERAGE.json']=(json.dumps(voice,indent=2)+'\n').encode()
    files['START-HERE.txt']=b'''BERBER 0.10.0 - SCRIPTED AI CANDIDATE
Close AoE4. Import Berber-0.10.0.zip in normal Garrison and enable it.
Launch with Garrison Play. Select Malians for Berber computers, Berber Game Mode
and Berber Tuning Pack. Start a fresh connected-land match. No voice installer.
Read AI_CHANGES.md and NATIVE_AI_ACCEPTANCE.md. Native testing is pending.
'''
    files['AI_CHANGES.md']=NOTES.encode();files['NATIVE_AI_ACCEPTANCE.md']=ACCEPTANCE.encode()
    with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(FINAL,'Berber_future_kingdom.sga')
        for n,raw in files.items():z.writestr(n,raw)
    hashes={n:hashlib.sha256(v).hexdigest() for n,v in files.items()};hashes['Berber_future_kingdom.sga']=sha(FINAL)
    report={'version':'0.10.0','status':'package_verified_native_acceptance_pending','zip':str(ZIP),
      'zip_bytes':ZIP.stat().st_size,'zip_sha256':sha(ZIP),'sga_sha256':sha(FINAL),'zip_members':hashes,
      'baseline':'final0.9.1','baseline_sha256':BASE_SHA,'changed_existing_members':member['changed_existing'],
      'new_members':member['new_members'],'unchanged_member_count':member['unchanged_member_count'],
      'art_audio_tuning_and_all22uvs_preserved':True,'lua51_tests':tests['tests'],
      'native_archive_crc_sha1':'passed','all_member_sha256':'passed','mcp':'reviewed; no unresolved engine names',
      'content_editor':'not run; SCAR-only overlay composed on validated native091 archive',
      'garrison_import':'pending','native_gameplay':'pending','native_multiplayer':'pending','native_performance':'pending'}
    write(OUT/'release-validation.json',report)
    (OUT/'AI_CHANGES.md').write_text(NOTES,encoding='utf8')
    (OUT/'NATIVE_AI_ACCEPTANCE.md').write_text(ACCEPTANCE,encoding='utf8')
    (OUT/'SHA256SUMS.txt').write_text(sha(ZIP)+'  '+ZIP.name+'\n'+sha(FINAL)+'  '+FINAL.name+'\n',encoding='ascii')
    verify();print('PACKAGE_VERIFIED',ZIP.stat().st_size,'bytes',sha(ZIP))

if __name__=='__main__':
    if '--verify' in sys.argv:print('DELIVERY_VERIFIED',verify()['zip_sha256'])
    else:build()
