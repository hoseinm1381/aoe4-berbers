"""Build/package an isolated official native cheering command trial."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
import zipfile
import shrek_trigger_probe as editor_builder

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_q_command_test'
CANDIDATE=WORK/'candidate'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
ARCHIVER=EXT/'bin/sga-archiver.exe'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1'
VERSION='0.1.3-tuareg-q-command.1'
GM='scar/winconditions/berber_future_kingdom_GM.scar'
MODULE='scar/Units/tuareg_q_cheer_trial.scar'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inspect(path):return json.loads(subprocess.check_output([str(ARCHIVER),'list',str(path),'--verify'],text=True))
def original_guard():
    baseline=json.loads((WORK/'source-baseline.json').read_text())
    for file,digest in baseline.items():assert sha(ROOT/file)==digest,file
    return len(baseline)
def prepare():
    assert not CANDIDATE.exists()
    WORK.mkdir(exist_ok=True)
    sources=[ROOT/'Berber_future_kingdom.aoe4mod']+[p for p in (ROOT/'assets').rglob('*') if p.is_file()]
    (WORK/'source-baseline.json').write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in sources},indent=2))
    CANDIDATE.mkdir();shutil.copy2(ROOT/'Berber_future_kingdom.aoe4mod',CANDIDATE/'Berber_future_kingdom.aoe4mod')
    shutil.copytree(ROOT/'assets',CANDIDATE/'assets')
    target=CANDIDATE/'assets'/MODULE
    target.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/'art/tuareg_shield/tuareg_q_cheer_trial.scar',target)
    gm=CANDIDATE/'assets'/GM
    original=gm.read_bytes();marker=b'import("Units/tuareg_voice_profile.scar")'
    assert original.count(marker)==1
    updated=original.replace(marker,marker+b'\r\nimport("Units/tuareg_q_cheer_trial.scar")')
    assert updated.replace(b'\r\nimport("Units/tuareg_q_cheer_trial.scar")',b'')==original
    gm.write_bytes(updated)
    report={'schema':'tuareg-q-command-source/v1','guid':GUID,'source_changes':['assets/'+GM],
            'source_additions':['assets/'+MODULE],'ability_data':'unchanged original .2, failed hook omitted',
            'permission':'user permits temporary stop for animation trial','duration_seconds':15,
            'original_sources_preserved':original_guard()}
    (WORK/'candidate-source.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
def build():
    editor_builder.WORK=WORK;editor_builder.CANDIDATE=CANDIDATE
    editor_builder.build()
def package():
    original_guard()
    build=json.loads((WORK/'candidate-build.json').read_text());assert build['status']=='succeeded'
    donor=Path(build['archives'][0]['path']);assert sha(donor)==build['archives'][0]['sha256']
    working=json.loads((ROOT/'output/tuareg_shield_test/delivery-verification.json').read_text())
    base=Path(working['archive']);assert sha(base)==working['archive_sha256']
    donor_inventory=inspect(donor)
    members=[next(x['path'] for x in donor_inventory['members'] if x['path'].lower()==p.lower()) for p in [GM,MODULE]]
    package_dir=WORK/'package';package_dir.mkdir(exist_ok=True)
    archive=package_dir/'Berber_future_kingdom.sga';assert not archive.exists()
    graft=subprocess.run([str(ARCHIVER),'graft',str(base),str(donor),str(archive),*members],check=True,capture_output=True,text=True)
    (WORK/'graft-result.json').write_text(graft.stdout)
    before=inspect(base);after=inspect(archive)
    assert after['archive']['verification']['verified'] is True
    assert after['archive']['name'].replace('-','').lower()==GUID
    old={x['path'].lower():x for x in before['members']};new={x['path'].lower():x for x in after['members']}
    assert set(new)-set(old)=={MODULE.lower()} and len(new)==264
    changes=[p for p in old if (old[p]['crc'],old[p]['size'])!=(new[p]['crc'],new[p]['size'])]
    assert changes==[GM.lower()]
    readback=WORK/'readback';assert not readback.exists()
    subprocess.run([str(ARCHIVER),'unpack',str(archive),'--output',str(readback)],check=True,capture_output=True)
    for logical in [GM,MODULE]:
        extracted=readback/next(x['path'] for x in after['members'] if x['path'].lower()==logical.lower())
        assert sha(extracted)==sha(CANDIDATE/'assets'/logical)
    report={'schema':'tuareg-q-command-delivery/v1','version':VERSION,'guid':GUID,
            'archive_sha256':sha(archive),'archive_members':len(new),'changed_members':changes,
            'added_members':[MODULE],'unchanged_previous_members':len(old)-len(changes),
            'original_sources_preserved':original_guard(),'original_ability_data':'byte-preserved',
            'native_rendering':'pending fresh user test','temporary_stop':'approved for this trial',
            'animation':'stock native gesture, 15s command lifetime; custom pose not exported'}
    (WORK/'archive-inventory.json').write_text(json.dumps(after,indent=2))
    (package_dir/'PROBE-EVIDENCE.json').write_text(json.dumps(report,indent=2))
    shutil.copy2(WORK/'TEST-PROBE.txt',package_dir/'TEST-PROBE.txt')
    sys.path.insert(0,str(EXT));from garrison_shared import mod_bundle
    details={'id':'berber_future_kingdom','name':'The Berber Dynasties','version':VERSION,
             'summary':'Q native animation command trial: temporary 15-second stop',
             'author':'hossein81 and marcokistan','updated':'2026-10-11','min_garrison':'0.1.3',
             'content_types':['game-mode','tuning-pack'],
             'description':'User-authorized temporary-stop animation trial. Detect existing Tuareg Q activation, grant/command native cheer_toggle, then explicitly stop/remove after 15 seconds. Original ability fields, visuals, voices, upgrades retained. Stock gestures are used; custom shield pose and native acceptance remain pending.',
             'changelog':'Replace failed attribute-hook experiment with official native cheering command lifecycle in isolated SCAR, with cast/state/start/stop diagnostics.'}
    mod_bundle.write_manifest(package_dir,bundle_key='berber_future_kingdom',members=[{'mod_key':'berber_future_kingdom','role':'tuning','path':archive.name,'sha256':sha(archive)}],details=details)
    zip_path=WORK/f'berber_future_kingdom-{VERSION}.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(package_dir.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        assert hashlib.sha256(z.read(archive.name)).hexdigest()==report['archive_sha256']
    report.update(zip=str(zip_path),zip_sha256=sha(zip_path))
    (WORK/'delivery.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','build','package'])
    args=parser.parse_args();globals()[args.stage]()
