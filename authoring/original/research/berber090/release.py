"""Package validated090; preserve081 voice metadata and one manifest only."""
import json,sys,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research'))
import package_unified_release as packages
OUT=ROOT/'output/berber_update_0_9_0'


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def verify():
    report=json.loads((OUT/'release-validation.json').read_text(encoding='utf8'))
    archive=Path(report['zip'])
    assert sha(archive)==report['zip_sha256']
    assert sha(OUT/'Berber_future_kingdom.sga')==report['sga_sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(report['zip_members'])
        assert sum(Path(n).name.lower()=='garrison.json' for n in z.namelist())==1
        for name,digest in report['zip_members'].items():
            with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
        manifest=json.loads(z.read('garrison.json'))
        assert manifest['details']['version']=='0.9.0'
        assert manifest['members'][0]['sha256']==report['sga_sha256']
    packages.check()
    return report


def build():
    composition=json.loads((OUT/'composition-report.json').read_text(encoding='utf8'))
    strong=json.loads((OUT/'member-sha256-proof.json').read_text(encoding='utf8'))
    assert composition['status']=='passed' and strong['status']=='passed'
    assert sha(OUT/'Berber_future_kingdom.sga')==composition['archive_sha256']
    assert strong['archive_sha256']==composition['archive_sha256']
    assert strong['all_unrelated_decoded_member_sha256_identical']
    for kind in ('fez','wonder'):
        art=ROOT/'art/building_remix_0_9_0'/kind
        proof=json.loads((art/'export-validation.json').read_text(encoding='utf8'))
        assert proof['status']=='passed' and proof['preflight']['ok']
        assert sha(proof['source'])==proof['source_sha256']
    report=packages.build('0.9.0','Larger Castle landmarks; detailed Fez Madrasa and distinct Koutoubia Wonder',
                          OUT/'Berber_future_kingdom.sga',OUT)
    notes='''# Berber 0.9.0 — visual update

- Great Mosque of Tlemcen and Dar al-Jihad of Marrakech are 1.40 times their
  working 0.8.1 visible dimensions. Placement/pathfinding footprints and other
  gameplay attributes are unchanged.
- Madrasa of Fez: detailed recessed horseshoe windows, cedar balconies/screens,
  carved geometric friezes, muqarnas entrance cornice, zellij, pitched tile roofs
  and an octagonal courtyard fountain.
- Koutoubia Wonder: distinct low prayer halls, parallel roof bays, open arcaded
  court and a much taller/wider decorated minaret with copper finial.
- Existing 0.8.1 audio and Villager/Spearman speech fixes are preserved. No voice
  installer is required; do not reinstall an older native voice companion.

Close AoE4 completely, import this ZIP in normal Garrison and use Garrison Play.
Select Malians, Berber Game Mode and Berber Tuning Pack. Start a fresh match.
Working 0.8.1 ZIP remains available for rollback.

Source mesh/preflight, fresh native cook, exact changed-resource readback,
all unchanged archive-member SHA256 and final ZIP checks passed. Garrison import
and native gameplay are left to the player and remain pending.

Please inspect both Castle landmarks, Fez and Wonder through construction and
completion, at near/far zoom, with two player colours. Check damaged/destruction
states, entrances/rally/production, research, landmark abilities, Wonder victory
and unchanged unit voices. Native graphs/markers/flags and damage-visibility
conditions are retained; visual lifecycle acceptance still needs this test.
One authored native LOD0 is used; lower LOD activation is not claimed.
'''
    note_bytes=notes.encode('utf8')
    with zipfile.ZipFile(report['zip'],'a',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('VISUAL_CHANGES.md',note_bytes)
    report['zip_members']['VISUAL_CHANGES.md']=hashlib.sha256(note_bytes).hexdigest()
    report.update(zip_sha256=sha(report['zip']),zip_bytes=Path(report['zip']).stat().st_size,
        visual_source_preflight='passed',fresh_native_cook='passed',
        full_member_sha256='passed',import_test='pending; operator requested to import personally',
        native_gameplay='pending',unrelated_members_sha256_identical=True,
        current_release_archive=str(OUT/'Berber_future_kingdom.sga'),
        changed_existing_member_count=len(composition['changed_existing']),
        new_member_count=len(composition['new_members']),
        voice_install_required=False)
    (OUT/'release-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    verify()
    (OUT/'VISUAL_CHANGES.md').write_text(notes,encoding='utf8')
    print(json.dumps({k:report[k] for k in ('version','zip','zip_bytes','zip_sha256','sga_sha256','import_test')}))


if __name__=='__main__':
    if '--verify' in sys.argv:print(json.dumps({'status':'passed','zip':verify()['zip']}))
    else:build()
