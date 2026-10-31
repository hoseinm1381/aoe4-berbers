"""Use current official editor XML and serializer-issued IDs for minimal child instances."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'output/tuareg_shield_test'
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
ARCHIVE=Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\ReferenceAttributes.sga')
rows=[]
for age in range(1,5):
    member=f'instances/attachments/attachment_lists/civilizations/malian/units/tier{age}_spearman_mal.xml'
    official=WORK/'official-source'/member
    if not official.exists():
        official.parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run([str(EXT/'bin/sga-archiver.exe'),'extract-member',str(ARCHIVE),member,str(official)],capture_output=True,encoding='utf-8')
        assert result.returncode==0,result.stderr
    source=ET.parse(official).getroot()
    generated=ET.parse(WORK/f'derived-readback/attrib/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.xml').getroot()
    identifier=generated.find("./RGDNode/RGDNode[@Key='pbgid']").get('Value')
    output=ET.Element('instance',version=source.get('version'),description=f'Tuareg Age {age}: Abbasid body, inherited Donso shield',template=source.get('template'))
    group=ET.SubElement(output,'group',name='attachment_lists')
    lists=ET.SubElement(group,'list',name='attachment_lists')
    parent_list=source.find("./group/list/template_reference")
    outer=ET.SubElement(lists,parent_list.tag,dict(parent_list.attrib))
    outer.set('List.ParentItemID',outer.get('List.ItemID'))
    contents=ET.SubElement(outer,'list',name='attachment_list')
    merge=parent_list.find("./list/template_reference[@value='options\\attachment_types\\animator_merge_mesh_attachment']")
    assert merge is not None
    override=ET.SubElement(contents,merge.tag,dict(merge.attrib))
    override.set('List.ParentItemID',override.get('List.ItemID'))
    meshes=ET.SubElement(override,'list',name='meshes')
    body=copy.deepcopy(merge.find('./list/file'))
    body.set('List.ParentItemID',body.get('List.ItemID'))
    body.set('overrideParent','True')
    body.set('value',f'art\\civilizations\\abbasids\\humans\\abb_infantry_light_age0{age}\\abb_infantry_light_age0{age}')
    meshes.append(body)
    ET.SubElement(output,'uniqueid',name='pbgid',value=identifier)
    ET.SubElement(output,'instance_reference',name='parent_pbg',value=f'attachments\\attachment_lists\\civilizations\\malian\\units\\tier{age}_spearman_mal')
    destination=ROOT/f'assets/attrib/instances/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.xml'
    assert not destination.exists()
    destination.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(output,space='\t')
    ET.ElementTree(output).write(destination,encoding='utf-8',xml_declaration=True)
    loose=ROOT/f'assets/attrib/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.rgd'
    expected=(WORK/f'derived-readback/attrib/attachments/attachment_lists/garrison/tuareg_shield_assets/tuareg_shield_tier{age}_ber.rgd').read_bytes()
    assert loose.read_bytes()==expected
    loose.unlink()  # Remove only this run's verified unsupported loose input.
    rows.append({'age':age,'source':str(destination.relative_to(ROOT)),'pbgid':int(identifier),'official_parent':member,
                 'official_source_sha256':hashlib.sha256(official.read_bytes()).hexdigest(),
                 'inheritance':'exact parent list identities; override only original body mesh; shield inherited'})
(WORK/'editor-attachment-sources.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
with (WORK/'progress.md').open('a',encoding='utf-8') as ledger:
    ledger.write('\n- Correction: current ReferenceAttributes.sga supplies authoritative editable donor XML. Added four minimal children of the official Donso tier lists, overriding only body mesh with exact inherited list identities. IDs come from Garrison serialization. Removed only this run\'s loose RGD inputs; Content Editor now owns compilation of all new instances.\n- The first main cook dropped unresolved references and is rejected, not packaged.\n')
print(json.dumps({'private_editor_instances':len(rows),'generated_ids':[r['pbgid'] for r in rows]}))
