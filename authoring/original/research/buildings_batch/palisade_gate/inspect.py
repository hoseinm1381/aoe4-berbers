import json,subprocess
from pathlib import Path
O=Path('research/buildings_batch/palisade_gate');a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for key,path in [('core','attrib/ebps/races/core/buildings/building_defense_palisade_gate.rgd'),('mal','attrib/ebps/races/malian/buildings/building_defense_wall_mal/building_defense_palisade_gate_mal.rgd')]:
 r=O/(key+'.rgd');x=r.with_suffix('.xml');subprocess.run([a,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',path,str(r)],check=True,capture_output=True);subprocess.run([a,'decode-rgd',str(r),str(x)],check=True,capture_output=True)
d=json.loads(next((O/'stock').glob('*/decoded-static.json')).read_text());print(list(d));print(list(d['geometry']));summary=[]
for g in d['geometry']['groups']:
 v=g['positions'];summary.append({'name':g['name'],'n':len(v),'bounds':[[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]})
(O/'donor_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(str(d.get('model',{}))[:2000])
