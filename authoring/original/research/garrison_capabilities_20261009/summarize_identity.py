import hashlib
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
EXT = Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT))
from garrison_shared import attribute_overrides,mod_bundle

report = {'garrison_editable_families':attribute_overrides.EDITABLE_FAMILIES,'package_roles':mod_bundle.ROLES}
ui = OUT/'official/ui/lobby/semimodalpages/createcustommatchsemimodalpage.xaml'
lines = ui.read_text().splitlines()
keys = ['CivName','RaceList','CivList','SelectedRace','Civilizations','RaceInfo','Races','ImagePath']
report['lobby_identity_bindings'] = [{'line':index,'text':line.strip()} for index,line in enumerate(lines,1)
                                      if any(key in line for key in keys)]
report['lobby_civ_combo_context'] = []
for index,line in enumerate(lines):
    if 'ItemsSource=' in line and any(key in '\n'.join(lines[max(0,index-8):index+8]) for key in ['Civ','Race']):
        report['lobby_civ_combo_context'].append({'line':index+1,'text':'\n'.join(x.strip() for x in lines[max(0,index-5):index+5])})
node = ET.parse(OUT/'official/attrib/racebps/malian.decoded.xml').getroot()
bag = next(x for x in node.iter('RGDNode') if x.attrib.get('Key')=='race_bag')
chosen = ['name','icon','icon_secondary','image_small','pattern','image','front_end_music_layer_event','ui_visibility','multiplayer','ui_priority']
report['malian_identity'] = {x.attrib['Key']:x.attrib.get('Value') for x in bag if x.attrib.get('Key') in chosen}
game = Path(r'E:\Games\steamapps\common\Age of Empires IV')
music = []
events = []
for event,node in ET.iterparse(game/'cardinal/audio/SoundbanksInfo.xml',events=('end',)):
    name = node.attrib.get('Name') or node.findtext('ShortName') or node.findtext('Name')
    if name and re.search(r'mus.*(mal|civ)|malian',name,re.I):
        music.append({'kind':node.tag,'name':name,'id':node.attrib.get('Id') or node.findtext('Id'),'object_path':node.findtext('ObjectPath')})
    if name and node.tag=='Event' and 'mus_' in name:
        events.append({'name':name,'id':node.attrib.get('Id') or node.findtext('Id')})
report['malian_music_metadata'] = music[:60]
report['malian_music_files'] = [row for row in music if row['kind']=='File' and ('music_mal' in row['name'].lower() or 'mal_stingers' in row['name'].lower() or 'mus_mal' in row['name'].lower())]
report['unique_malian_music_file_ids'] = len({row['id'] for row in report['malian_music_files']})
report['music_events_count'] = len(events)
report['music_event_examples'] = events[:20]
report['source_hashes'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ui,OUT/'official/attrib/racebps/malian.rgd',
                                      game/'cardinal/audio/SoundbanksInfo.xml',EXT/'guide/garrison-audio.html']}
(OUT/'identity-evidence.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['garrison_editable_families','package_roles','lobby_identity_bindings','lobby_civ_combo_context','malian_identity','malian_music_metadata']},indent=2))
