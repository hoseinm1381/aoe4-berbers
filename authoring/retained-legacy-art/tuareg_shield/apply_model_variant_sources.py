"""One-time migration: integrate Garrison variants using canonical art references.

This intentionally refuses existing migration backups/resources. Later rebuilds
use the existing editor instances and assets; do not rerun this migration.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shield_test'
rows=[]
for age in range(1,5):
    relative=Path(f'assets/attrib/instances/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.xml')
    path=ROOT/relative
    backup=WORK/'failure-probe1'/relative
    assert not backup.exists()
    backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup)
    # Installed model_variants.art_reference emits these native File paths.
    # Generic @variant syntax was not expanded in these attachment File fields.
    body=f'art\\scenario\\garrison\\tuareg_shield_assets\\tuareg_body_age{age}\\tuareg_body_age{age}'
    shield='art\\scenario\\garrison\\tuareg_shield_assets\\tuareg_shield_model\\tuareg_shield_model'
    root=ET.parse(path).getroot()
    root.find('.//file[@name="animator0"]').set('value',body)
    contents=root.find('./group/list/template_reference/list')
    official=ET.parse(WORK/f'official-source/instances/attachments/attachment_lists/civilizations/malian/units/tier{age}_spearman_mal.xml').getroot()
    donor=official.find('.//template_reference[@value="options\\attachment_types\\animator_sim_attachment"]')
    assert donor is not None
    override=ET.Element(donor.tag,dict(donor.attrib))
    override.set('List.ParentItemID',override.get('List.ItemID'))
    model=copy.deepcopy(donor.find('./file[@name="animator"]'))
    model.set('value',shield);model.set('overrideParent','True');override.append(model);contents.append(override)
    ET.indent(root,space='\t');ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
    rows.append({'age':age,'body_reference':body,'shield_reference':shield,'source':str(relative),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
resources=[]
for source in sorted((WORK/'model-variant-readback/art').rglob('*')):
    if not source.is_file():continue
    relative=source.relative_to(WORK/'model-variant-readback')
    target=ROOT/'assets'/relative
    assert not target.exists(),target
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    resources.append({'file':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
assert len(resources)==20
report={'schema':'tuareg-shield-model-integration/v1','references':rows,'resources':resources,
        'geometry_resources':5,'models':'unchanged stock geometry/rig/material variants cooked through Garrison',
        'native_runtime':'pending'}
(WORK/'model-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
with (WORK/'progress.md').open('a',encoding='utf-8') as ledger:
    ledger.write('\n- Native trial .1 failed: only spears visible. Garrison launch confirmed; client log states owner-provider promotion was not installed. Previous package carried zero geometry and only attribute/UI resources.\n- Repair: documented Garrison Model Variants route now cooks unchanged four body models and the Donso shield into 20 real model/object/geometry/material resources. Canonical art references are used in editable attachment File fields. Native owner-provider admission and appearance still require a fresh Garrison trial.\n')
print(json.dumps({'updated_attachment_sources':len(rows),'added_model_resources':len(resources),'geometry_resources':5}))
