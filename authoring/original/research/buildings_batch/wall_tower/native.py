from pathlib import Path
import subprocess,json,xml.etree.ElementTree as E
q=Path('research/buildings_batch/wall_tower'); a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for key,name in [('attachment','attrib/attachments/attachment_lists/civilizations/malian/buildings/building_defense_wall_mal/building_defense_wall_stone_tower_mal.rgd'),('schema','attrib/statemodel_schema/buildings/tower.rgd')]:
 p=q/(key+'.rgd');x=p.with_suffix('.xml')
 if not p.exists():subprocess.run([a,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga',name,str(p)],check=True,capture_output=True)
 if not x.exists():subprocess.run([a,'decode-rgd',str(p),str(x)],check=True,capture_output=True)

