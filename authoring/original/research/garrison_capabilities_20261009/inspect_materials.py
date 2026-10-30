"""Read-only guide/game inventory. Writes research extracts, never game/mod assets."""
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

OUT = Path(__file__).resolve().parent
EXT = Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
GAME = Path(r'E:\Games\steamapps\common\Age of Empires IV')
DOC = Path(r'C:\Users\RS\Downloads\Garrison_Audio_Guide_EN.docx')
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(DOC) as archive:
    root = ET.fromstring(archive.read('word/document.xml'))
    lines = []
    for index,p in enumerate(root.findall('.//w:body//w:p',NS),1):
        text = ''.join(p.itertext()) if False else ''.join(t.text or '' for t in p.findall('.//w:t',NS))
        if text.strip():
            lines.append(f'[{index}] {text}')
    (OUT/'audio-guide.txt').write_text('\n'.join(lines),encoding='utf-8')
    media = [name for name in archive.namelist() if name.startswith('word/media/')]
    rels = ET.fromstring(archive.read('word/_rels/document.xml.rels'))
    links = [r.attrib.get('Target') for r in rels if r.attrib.get('TargetMode')=='External']
    (OUT/'audio-guide-provenance.json').write_text(json.dumps({'file':str(DOC),'sha256':hashlib.sha256(DOC.read_bytes()).hexdigest(),
                                   'paragraphs':len(lines),'media':media,'external_links':links},indent=2),encoding='utf-8')
    for name in media:
        target = OUT/'docx-images'/Path(name).name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(archive.read(name))
guide = OUT/'guide'
guide.mkdir(exist_ok=True)
for path in (EXT/'guide').glob('*.html'):
    raw = path.read_text(encoding='utf-8')
    main = re.search(r'<main>(.*?)</main>',raw,re.S)
    if main:
        text = html.unescape(re.sub(r'<[^>]*>',' ',main.group(1)))
        text = re.sub(r'[ \t]+',' ',text)
        (guide/(path.stem+'.txt')).write_text(text,encoding='utf-8')
archiver = EXT/'bin/sga-archiver.exe'
for archive in ['Attrib.sga','UI.sga','UIArt.sga','Data.sga']:
    result = subprocess.run([str(archiver),'list',str(GAME/'cardinal/archives'/archive)],capture_output=True,encoding='utf-8')
    assert result.returncode==0,result.stderr
    data = json.loads(result.stdout)
    (OUT/(archive+'-inventory.json')).write_text(result.stdout,encoding='utf-8')
    matched = [row['path'] for row in data['members'] if re.search(r'civ|race|malian|music|loading|frontend|lobby',row['path'],re.I)]
    (OUT/(archive+'-selected-paths.txt')).write_text('\n'.join(matched),encoding='utf-8')
    print(archive,len(data['members']),'members;',len(matched),'relevant names')
print('Audio guide:',len(lines),'paragraphs;',len(media),'embedded images;',len(links),'links')
