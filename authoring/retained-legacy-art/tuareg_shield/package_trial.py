"""Verify the exact corrected cook, then package deployable Berber trial content."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shield_test'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
GUID='1d3145e8f1b2427f8bb0067851fcf0f1'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def strings(path):
    return [n.get('Value') for n in ET.parse(path).getroot().iter('RGDNode') if n.get('Type')=='CString']

build=json.loads((WORK/'build-result.json').read_text())
assert build['status']=='succeeded' and build['exit_code']==0 and len(build['archives'])==1
release=json.loads((WORK/'release-result.json').read_text())
assert release['status']=='verified' and release['editor_archive_sha256']==build['archives'][0]['sha256']
archive=Path(release['archive']); assert sha(archive)==release['sha256']
inventory=json.loads((WORK/'evidence/final-inventory.json').read_text())
assert Path(inventory['archive']['path']).resolve()==archive.resolve(),'Readback belongs to another build'
assert inventory['archive']['verification']['verified'] is True
assert inventory['archive']['name'].replace('-','').lower()==GUID
assert {r['alias'] for r in inventory['archive']['tocs']}=={'attrib','data','info','locale'}
assert len(inventory['members'])==263
readback=WORK/'final-readback-v2-combined'
for age in range(1,5):
    path=readback/f'attrib/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.xml'
    values=strings(path)
    assert f'art\\scenario\\garrison\\tuareg_shield_assets\\tuareg_body_age{age}\\tuareg_body_age{age}' in values
    assert 'art\\scenario\\garrison\\tuareg_shield_assets\\tuareg_shield_model\\tuareg_shield_model' in values
    assert not any(v.startswith('@') for v in values)
    assert 'MetaRig_LArmPalmSocket' in values
    for family,folder in [('ebps','units'),('sbps','berbers')]:
        path=readback/f'attrib/{family}/races/malian/{folder}/unit_spearman_tuareg_{age}_ber.xml'
        values=strings(path); assert 'tuarg' in values
        if family=='ebps':
            refs=[v for v in values if 'tuareg_shield_tier' in v]
            assert refs==[f'{GUID}:tuareg_shield_tier{tier}_ber' for tier in range(age,5)]

# Compare every unchanged archive member against the pre-shield production cook.
before=json.loads((ROOT/'output/tuareg_voice_test/logs/berber-full-archive.json').read_text())
previous={r['path']:r for r in before['members']}
current={r['path']:r for r in inventory['members']}
allowed={f'attrib/ebps/races/malian/units/unit_spearman_tuareg_{age}_ber.rgd' for age in range(1,5)}
archive_changes=[name for name in previous if current[name]['crc']!=previous[name]['crc'] or current[name]['size']!=previous[name]['size']]
assert set(archive_changes)<=allowed,archive_changes
new_attachments={f'attrib/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.rgd' for age in range(1,5)}
model_names=[f'tuareg_body_age{age}' for age in range(1,5)]+['tuareg_shield_model']
new_models={f'art/scenario/garrison/tuareg_shield_assets/{name}/{name}.{ext}' for name in model_names for ext in ['rgm','rgo','rrgeom','rrmaterial']}
assert set(current)-set(previous)==new_attachments|new_models
assert sha(ROOT/'assets/scar/winconditions/berber_future_kingdom_GM.scar')==sha(readback/'scar/winconditions/berber_future_kingdom_GM.scar')
validation=json.loads((WORK/'tuning-validation.json').read_text());assert validation['summary']['errors']==0
sys.path.insert(0,str(WORK/'tools'))
from verify_source import check
from verify_geometry_contract import verify as verify_geometry
preservation=check()
geometry=verify_geometry(WORK/'evidence/final-inventory.json')
integration=json.loads((WORK/'model-integration.json').read_text())
for item in integration['resources']:
    source=ROOT/item['file']
    relative=source.relative_to(ROOT/'assets')
    assert sha(source)==item['sha256']
    assert sha(readback/relative)==item['sha256'],f'Native resource changed during original-project cook: {relative}'
geometry['garrison_donor_hashes_preserved']=len(integration['resources'])

package=WORK/'package';package.mkdir(exist_ok=True)
shutil.copy2(archive,package/'Berber_future_kingdom.sga')
shutil.copy2(archive,WORK/'Berber_future_kingdom_tuareg_shields.sga')
for name in ['TEST_TUAREG_SHIELDS.md','START-HERE.txt']:
    shutil.copy2(WORK/name,package/name)
sys.path.insert(0,str(EXT))
from garrison_shared import mod_bundle
details={'id':'berber_future_kingdom','name':'The Berber Dynasties','version':'0.1.3-tuareg-shields.2',
         'summary':'Tuareg shields, Ages I-IV; native voices preserved',
         'author':'hossein81 and marcokistan','updated':'2026-10-10','min_garrison':'0.1.3',
         'content_types':['game-mode','tuning-pack'],
         'description':'Solo shield trial for the existing Berber civilization. Choose The Berber Dynasties tuning pack, Berber Civilization game mode, Malians civilization. Four Abbasid age appearances use the stock Donso shield. The ability and native tuarg voice routing are preserved. Shield lift is omitted pending qualification. Native gameplay acceptance remains pending.',
         'changelog':'Replace the attribute-only failed trial with five real Garrison model/object/geometry/material resource sets and canonical art references. Preserve original GUID, gameplay, upgrades, SCAR and voices.'}
mod_bundle.write_manifest(package,bundle_key='berber_future_kingdom',members=[{'mod_key':'berber_future_kingdom','role':'tuning','path':'Berber_future_kingdom.sga','sha256':sha(archive)}],details=details)
zip_path=WORK/'berber_future_kingdom-0.1.3-tuareg-shields.2.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(package.iterdir()):
        if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    manifest=json.loads(z.read('garrison.json'))
    assert hashlib.sha256(z.read(manifest['members'][0]['path'])).hexdigest()==manifest['members'][0]['sha256']
report={'schema':'tuareg-shield-delivery/v1','status':'built_packaged_native_acceptance_pending',
        'archive':str(WORK/'Berber_future_kingdom_tuareg_shields.sga'),'archive_sha256':sha(archive),
        'zip':str(zip_path),'zip_sha256':sha(zip_path),'archive_members':len(current),
        'unchanged_previous_archive_members':len(previous)-len(archive_changes),'changed_previous_members':archive_changes,
        'added_private_attachments':4,'rewired_tier_references':10,'source_preservation':preservation,
        'geometry_contract':geometry,'archive_integration':release,
        'previous_native_trial':'failed: only spears; no owner-provider promotion installed',
        'content_editor_exit':0,'tuning_validation':validation['summary'],'compiled_speaker_bindings_preserved':8,
        'blender_source':str(ROOT/'art/tuareg_shield/Tuareg_Shield_Ages_I_IV.blend'),
        'blender_checks':json.loads((WORK/'evidence/blender-assembly.json').read_text()),
        'lift':'omitted; no native visual control/ability timing qualification',
        'native_runtime':'not_run; user solo matrix required'}
(WORK/'delivery-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','zip','archive_members','unchanged_previous_archive_members','added_private_attachments','tuning_validation']},indent=2))
