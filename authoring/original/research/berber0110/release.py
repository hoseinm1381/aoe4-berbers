"""Package the verified 0110 approved build order on final0101 without recooking art."""
from pathlib import Path
import hashlib,json,sys,zipfile
from pipeline import ROOT,OUT,BASE,BASE_SHA,sha,write

BASE_ZIP=ROOT/'output/berber_update_0_10_1/Berber-0.10.1.zip'
BASE_ZIP_SHA='ff5512ea42f771214b603495d526745c42b87519607daa229959e589c2213720'
FINAL=OUT/'Berber_future_kingdom.sga'
ZIP=OUT/'Berber-0.11.0.zip'
NOTES='# Berber 0.11.0 - approved build-order AI candidate\n\nAll difficulties use Zenata: a coordinated nine-food/eight-wood/five-gold opening,\ncontinuous villagers, first-Lancer raids, six-archer support waves, timed Castle\nand Imperial plans, trade and conditional second TC, protection, relics/sites,\nhealing and siege. Full AI map knowledge is intentional. Conditional villager\ngather bonuses are +10/+20/+30/+50% against a higher-income enemy, checked each\nminute; no direct free-resource recovery grants remain.\n\nVillager targets:60/75/90/105. Trader targets:10/20/30/40. Starts:normal land only.\nThe full approved design and behavior-test reports are retained with the editable\nproject. This release preserves final0.10.1 art, tuning, voices and all UV repairs.\nOnly AI SCAR modules change; the current game-mode entry and speech stay intact.\n\nFixes include spawned-only world AND squad enumeration for the death/despawn\nfatal index report, and retained world-ownership guards for neutral objects.\nStrict Lua tests cover the approved behavior, invalid handles and lifecycle.\nNative command success, pathfinding, trade route handling, actual total income\nincluding relic/trade, market stone purchases, multiplayer sync and performance\nstill require operator testing. References and mocks do not prove those gates.\n\nImport this ZIP in normal Garrison; enable, launch via Play, select both Berber\nGame Mode and Tuning Pack. Start a fresh normal connected-land match. Choose\nMalians for Berber AI slots. No custom voice installer or runtime is included.\n'
ACCEPTANCE='# Berber 0.11.0 native acceptance - pending\n\nUse a fresh process with0.11.0, Berber Game Mode AND Tuning Pack, normal land.\n1. Test all difficulties: exact opening/rallies/builders, nonstop villagers,\n   no premature farms/towers, Tent adjacency, market influence and paid queues.\n2. Confirm Lancer first raid/TC avoidance; six-archer departure/protection,\n   targeting, combined guard ratios, regroup and individual healing hysteresis.\n3. Kill/despawn units and destroy resources/targets repeatedly, then continue\n   a long match. No EGroup/SGroup invalid index or world-owner fatal may recur.\n4. Verify houses at two spaces, farm transitions, towers, villager shelter/overflow\n   and scout-hit exception below10%health; job restoration after construction.\n5. Check trade placement/routes/escort, exact producer/home market, trader caps,\n   normal stone-buy ability price/payment, temporary mining,10:30 second TC.\n6. Observe expansion10:00/every2min/retry1min and influence capacity/Tent caps.\n7. Verify random Castle12-14min, eight wood builders/Mosque; Imperial21:00,\n  15-trader landmark choice/20 builders; saving pauses permit villagers/houses,\n   all other new spending resumes after observed foundation.\n8. Validate core/economic/Blacksmith upgrades, normal prerequisites/costs,\n   independent relic/site Imams, dedicated healer, siege demand and attacks.\n9. Measure native food/wood/gold/stone income with villager gathering, trade,\n   relics and passive producers separately. Prove Player_GetResourceRate covers\n   every source before accepting total-income-based assistance. Confirm bonus\n   on/off perminute/highest-incomeenemy, actual harvest increase/no stacking.\n10. Save/load, finish/restart matches and multiplayer with multiple Berber AI,\n    mixed civs/teams/FFA; confirm synchronized RNG, no duplicate jobs/modifiers,\n    normal costs and responsive performance at maximum players.\n\nRecord game/Garrison versions, map/seed, exact ZIP/SGA hashes, settings and fresh\nwarnings.log. All above native gates are pending; mocked simulation is separate.\n'

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
        assert manifest['details']['version']=='0.11.0'
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
    summary='Approved Zenata build-order AI, economy, raids, protection and timed age-ups; death/despawn repair; native testing pending'
    manifest['details'].update(version='0.11.0',updated='2026-10-18',summary=summary,changelog=summary,
      description=summary+'. Normal starts on connected land, teams/FFA candidate. Preserves final0.9.1 art/UV/audio. No voice installer.')
    assert manifest['bundle_key']==old['bundle_key'] and manifest['details']['id']==old['details']['id']
    manifest['details']['cover']='cover.png'
    files['cover.png']=(ROOT/'assets/mod.png').read_bytes()
    files['garrison.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    voice=json.loads(files['VOICE_COVERAGE.json']);voice['version']='0.11.0'
    voice['runtime_test']='Audio/speech members identical to final0.9.1. Fresh0.11.0 native acceptance pending.'
    files['VOICE_COVERAGE.json']=(json.dumps(voice,indent=2)+'\n').encode()
    files['START-HERE.txt']=b'''BERBER 0.11.0 - APPROVED BUILD ORDER AI
Close AoE4. Import Berber-0.11.0.zip in normal Garrison and enable it.
Launch with Garrison Play. Select Malians for Berber computers, Berber Game Mode
and Berber Tuning Pack. Start a fresh connected-land match. No voice installer.
Read AI_CHANGES.md and NATIVE_AI_ACCEPTANCE.md. Native testing is pending.
'''
    files['AI_CHANGES.md']=NOTES.encode();files['NATIVE_AI_ACCEPTANCE.md']=ACCEPTANCE.encode()
    files['AI_BUILD_ORDER.md']=(ROOT/'docs/superpowers/specs/2026-10-18-berber-ai-build-order-design.md').read_bytes()
    with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(FINAL,'Berber_future_kingdom.sga')
        for n,raw in files.items():z.writestr(n,raw)
    hashes={n:hashlib.sha256(v).hexdigest() for n,v in files.items()};hashes['Berber_future_kingdom.sga']=sha(FINAL)
    report={'version':'0.11.0','status':'package_verified_native_acceptance_pending','zip':str(ZIP),
      'zip_bytes':ZIP.stat().st_size,'zip_sha256':sha(ZIP),'sga_sha256':sha(FINAL),'zip_members':hashes,
      'baseline':'final0.10.1','baseline_sha256':BASE_SHA,'changed_existing_members':member['changed_existing'],
      'new_members':member['new_members'],'unchanged_member_count':member['unchanged_member_count'],
      'art_audio_tuning_and_all22uvs_preserved':True,'lua51_tests':tests['tests'],
      'native_archive_crc_sha1':'passed','all_member_sha256':'passed','mcp':'reviewed; no unresolved engine names',
      'content_editor':'not run; SCAR-only overlay composed on validated native0101 archive',
      'garrison_import':'pending','native_gameplay':'pending','native_multiplayer':'pending','native_performance':'pending'}
    write(OUT/'release-validation.json',report)
    (OUT/'AI_CHANGES.md').write_text(NOTES,encoding='utf8')
    (OUT/'NATIVE_AI_ACCEPTANCE.md').write_text(ACCEPTANCE,encoding='utf8')
    (OUT/'SHA256SUMS.txt').write_text(sha(ZIP)+'  '+ZIP.name+'\n'+sha(FINAL)+'  '+FINAL.name+'\n',encoding='ascii')
    verify();print('PACKAGE_VERIFIED',ZIP.stat().st_size,'bytes',sha(ZIP))

if __name__=='__main__':
    if '--verify' in sys.argv:print('DELIVERY_VERIFIED',verify()['zip_sha256'])
    else:build()
