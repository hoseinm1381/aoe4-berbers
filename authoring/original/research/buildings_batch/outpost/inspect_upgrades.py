import subprocess
from pathlib import Path
p=Path('research/buildings_batch/outpost');a='C:/Users/RS/AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for key in ['arrowslits','springald','cannon','fortify']:
 r=p/(key+'.rgd')
 try:
  subprocess.run([a,'extract-member','E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga','attrib/upgrade/races/common/research/upgrade_outpost_'+key+'.rgd',str(r)],check=True,capture_output=True)
  subprocess.run([a,'decode-rgd',str(r),str(r.with_suffix('.xml'))],check=True,capture_output=True)
 except subprocess.CalledProcessError as e: print(key,e.stderr.decode(errors='replace'))
