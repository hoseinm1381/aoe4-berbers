import subprocess,json,os
from pathlib import Path
G=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
for name in ['Data','Scenarios','ArtHigh']:
 p=subprocess.run([str(G),'inspect',f'E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/{name}.sga'],capture_output=True,text=True)
 d=json.loads(p.stdout); rows=[x for x in d.get('archive',{}).get('members',[]) if 'lumber_camp' in x.get('path','') or 'lumbercamp' in x.get('path','')];print(name,rows)


