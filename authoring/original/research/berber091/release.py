"""Package and verify final091 from final090 metadata, without recooking art."""
import json,sys,zipfile,hashlib
from pathlib import Path
from repair import ROOT,OUT,BASE,BASE_SHA,sha,read,write

BASE_ZIP=ROOT/'output/berber_update_0_9_0/Berber-0.9.0.zip'
BASE_ZIP_SHA='25105f16e2e90b31c69f6d37cdd13ba37eb602c8b4b0772160e9501bd99d210a'
FINAL=OUT/'Berber_future_kingdom.sga'
ZIP=OUT/'Berber-0.9.1.zip'

NOTES='''# Berber 0.9.1 — UV repair

Restores original donor UV0 coordinates in all 22 previously flagged RRGeom files:
Town Center and Barracks I–IV, Mehari II/III/IV-upgrade, Sanhaja IV,
Scout I–IV plus its alternate Age II model, Trader III male/female and IV female,
and Zenata II/IV. All 58,700 non-finite UV vertices are resolved.

Only UV0 byte spans change. All current positions, normals, real tangent lanes,
skin/bone data, indices, topology and every other model byte are unchanged.
All other SGA members are SHA-256 identical to final 0.9.0: gameplay attributes,
SCAR, icons, voices, materials, stamps, animation graphs and the 0.9.0 Fez/Wonder
and Castle-landmark changes are preserved. No asset or gameplay redesign.

UV recovery uses hash-verified originals, also matched to fresh extracts from
the installed official game archives. No zero filling or guessed coordinates.
Native archive CRC/SHA1, every decoded member SHA-256, all 22 UV regressions,
exact UV-only byte checks and ZIP/member hashes passed.

No Content Editor cook is needed: the existing native RRGeom layout and file
lengths are retained. Composition/readback is verified; fresh native import,
visual appearance and gameplay acceptance remain pending.

Close AoE4 fully. Import Berber-0.9.1.zip in normal Garrison, enable it and use
Garrison Play. Select Malians + Berber Game Mode + Berber Tuning Pack.
No voice installer. Check the seven affected families across their listed ages,
near/far zoom, two player colours, construction/damage and unit actions.
Keep 0.9.0 and working 0.8.1 as retained rollback/evidence.
'''

def verify():
    report=read(OUT/'release-validation.json')
    assert sha(ZIP)==report['zip_sha256']
    assert sha(FINAL)==report['sga_sha256']
    assert sha(BASE)==BASE_SHA and sha(BASE_ZIP)==BASE_ZIP_SHA
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        names=z.namelist();assert len(names)==len(set(names))
        assert set(names)==set(report['zip_members'])
        assert sum(Path(n).name.lower()=='garrison.json' for n in names)==1
        for n,digest in report['zip_members'].items():
            with z.open(n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,n
        manifest=json.loads(z.read('garrison.json'))
        assert manifest['details']['version']=='0.9.1'
        assert manifest['members'][0]['sha256']==report['sga_sha256']
        assert 'remain unqualified or unresolved' not in z.read('VOICE_GAPS.md').decode()
    return report

def build():
    assert sha(BASE_ZIP)==BASE_ZIP_SHA and sha(BASE)==BASE_SHA
    memberproof=read(OUT/'member-sha256-proof.json');uv=read(OUT/'uv-repair-proof.json')
    assert memberproof['status']==uv['status']=='passed'
    assert sha(FINAL)==memberproof['archive_sha256']
    assert len(memberproof['changed_existing'])==22 and memberproof['new_members']==[]
    assert uv['nonfinite_uv_vertices_after']==0
    assert not ZIP.exists(),'Existing delivery preserved'
    with zipfile.ZipFile(BASE_ZIP) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='Berber_future_kingdom.sga'}
    manifest=json.loads(files['garrison.json']);old_manifest=json.loads(files['garrison.json'])
    digest=sha(FINAL)
    manifest['members'][0]['sha256']=digest
    summary='Repairs all 22 invalid-UV model files; preserves final 0.9.0 models and gameplay'
    manifest['details'].update(version='0.9.1',updated='2026-10-18',summary=summary,
        changelog=summary,description=summary+'. Normal Garrison import/Play; no voice installer. Fresh native acceptance pending.')
    files['garrison.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    coverage=json.loads(files['VOICE_COVERAGE.json'])
    coverage.update(version='0.9.1',runtime_test='Pending for 0.9.1; voice members are SHA-256 identical to 0.9.0. Earlier Villager overlap fix was operator-confirmed.')
    files['VOICE_COVERAGE.json']=(json.dumps(coverage,indent=2)+'\n').encode()
    files['VOICE_GAPS.md']=b'''# Voice coverage limitations retained in 0.9.1

All audio and scripted speech members are unchanged from final 0.9.0.
Earlier Spearman playback and the 0.8.1 Villager overlap fix were operator-confirmed.
Complete age/context/lifecycle, group, enemy/ally and multiplayer acceptance
remains separate. Scripted local-player playback retains its command-callback,
polling and cooldown limits. Villager action takes are shared across ages.
The former 22-invalid-UV warning is resolved by 0.9.1; see UV_REPAIR.md.
'''
    files['START-HERE.txt']=b'''BERBER 0.9.1

Close AoE4 completely. Import Berber-0.9.1.zip in normal Garrison and enable it.
Use Garrison Play; select Malians, Berber Game Mode and Berber Tuning Pack.
Start a fresh match. No voice installer or alternate runtime is required.

All 22 flagged model UVs are repaired; current geometry and gameplay are preserved.
Read UV_REPAIR.md for exact scope and acceptance checks. VISUAL_CHANGES.md
describes the inherited 0.9.0 visual update. Native acceptance remains pending.
'''
    files['UV_REPAIR.md']=NOTES.encode('utf8')
    assert manifest['bundle_key']==old_manifest['bundle_key']
    assert manifest['details']['id']==old_manifest['details']['id']
    with zipfile.ZipFile(ZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(FINAL,'Berber_future_kingdom.sga')
        for name,raw in files.items():z.writestr(name,raw)
    hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
    hashes['Berber_future_kingdom.sga']=digest
    report={'version':'0.9.1','status':'package_verified_runtime_pending','zip':str(ZIP),
       'zip_sha256':sha(ZIP),'zip_bytes':ZIP.stat().st_size,'sga_sha256':digest,'zip_members':hashes,
       'source_baseline':'final 0.9.0','source_baseline_sha256':BASE_SHA,
       'changed_existing_member_count':22,'new_member_count':0,'unchanged_member_count':memberproof['unchanged_member_count'],
       'uv_nonfinite_vertices_before':uv['nonfinite_uv_vertices_before'],'uv_nonfinite_vertices_after':0,
       'uv_only_byte_proof':'passed','full_decoded_member_sha256':'passed','native_archive_crc_sha1':'passed',
       'content_editor_cook':'not run; existing native geometry receives layout-preserving UV-only span edits',
       'voice_install_required':False,'import_test':'pending','native_gameplay':'pending'}
    write(OUT/'release-validation.json',report)
    (OUT/'UV_REPAIR.md').write_text(NOTES,encoding='utf8')
    verify();print(json.dumps({k:report[k] for k in ('version','zip','zip_bytes','zip_sha256','sga_sha256')},indent=2))

if __name__=='__main__':
    if '--verify' in sys.argv: print('091_DELIVERY_VERIFIED',verify()['zip_sha256'])
    else: build()
