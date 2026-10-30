import subprocess,json,sqlite3
from pathlib import Path
Q=Path(__file__).parent;exe='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
targets=[('attachment','Attrib.sga','attrib/attachments/attachment_lists/building_defense_wall_stone_gate_mal.rgd'),('native.simbox','Data.sga','art/civilizations/malian/structures/stonewall/mal_stonewall_smallgate_mp/mal_stonewall_smallgate_mp.simbox'),('native.markers','Data.sga','art/civilizations/malian/structures/stonewall/mal_stonewall_smallgate_mp/mal_stonewall_smallgate_mp.markers')]
for name,archive,path in targets:
 p=Q/(name+'.rgd' if name=='attachment' else name)
 if not p.exists():
  r=subprocess.run([exe,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/'+archive,path,str(p)],capture_output=True,text=True)
  print(name,r.returncode,r.stderr[:200])
 if p.exists():
  out=Q/(name.replace('.','_')+'.xml');r=subprocess.run([exe,'decode-rgd',str(p),str(out)],capture_output=True,text=True);print('decode',name,r.returncode)
