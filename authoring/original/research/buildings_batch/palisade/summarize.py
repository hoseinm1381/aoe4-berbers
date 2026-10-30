import json,subprocess
from pathlib import Path
q=Path('research/buildings_batch/palisade');d=json.loads(next((q/'stock').glob('*/decoded-static.json')).read_text());s=[]
for g in d['geometry']['groups']:
 p=g['positions'];s.append({'name':g['name'],'n':len(p),'bounds':[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]})
(q/'donor_summary.json').write_text(json.dumps(s,indent=2));print(s)
a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for name,path in [('segments','attrib/attachments/attachment_lists/civilizations/common/buildings/building_defense_palisade_segments_west.rgd')]:
 subprocess.run([a,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',path,str(q/(name+'.rgd'))],check=True,capture_output=True);subprocess.run([a,'decode-rgd',str(q/(name+'.rgd')),str(q/(name+'.xml'))],check=True,capture_output=True)
